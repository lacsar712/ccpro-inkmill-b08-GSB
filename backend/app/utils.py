from datetime import date, datetime, time, timedelta, timezone
import re

from flask import jsonify

# 全厂统一按东八区（UTC+8）自然日归班，不用 UTC 零点切日。
CST = timezone(timedelta(hours=8))

# 严格的 YYYY-MM-DD（月、日必须两位补零），拒绝 2026-9-1 等写法。
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# 班次边界（左闭右开）：08:00 归 morning，16:00 归 afternoon，00:00 归 night。
SHIFT_MORNING_START = time(8, 0)
SHIFT_AFTERNOON_START = time(16, 0)

SHIFT_KEYS = ("night", "morning", "afternoon")


def error(message: str, status: int = 400):
    return jsonify({"message": message}), status


def now_cst() -> datetime:
    return datetime.now(CST)


def today_cst() -> date:
    return now_cst().date()


def parse_shift_date(value: str | None) -> date:
    """严格解析 YYYY-MM-DD；空值回退东八区今天；非法格式或非法日历日抛 ValueError。"""
    if value is None or not value.strip():
        return today_cst()
    text = value.strip()
    if not DATE_RE.match(text):
        raise ValueError(f"非法日期: {value!r}")
    return datetime.strptime(text, "%Y-%m-%d").date()


def shift_bounds(day: date) -> dict[str, tuple[datetime, datetime]]:
    """各班在东八区墙上时钟的 [起, 止)  naive 时间区间（与库中 started_at 同约定）。"""
    night_start = datetime.combine(day, time(0, 0))
    morning_start = datetime.combine(day, SHIFT_MORNING_START)
    afternoon_start = datetime.combine(day, SHIFT_AFTERNOON_START)
    next_day_start = night_start + timedelta(days=1)
    return {
        "night": (night_start, morning_start),
        "morning": (morning_start, afternoon_start),
        "afternoon": (afternoon_start, next_day_start),
    }


def shift_key_of(started_at: datetime) -> str:
    """仅按遍次开始时间归班；跨午夜的遍次整段留在 startedAt 所在班，不拆分。"""
    t = started_at.time()
    if t < SHIFT_MORNING_START:
        return "night"
    if t < SHIFT_AFTERNOON_START:
        return "morning"
    return "afternoon"


def normalize_datetime(value: str) -> datetime:
    value = (value or "").strip()
    if not value:
        return datetime.now()
    for fmt in (
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(value.replace("Z", "")[:26], fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.now()


def dt_to_json(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.strftime("%Y-%m-%d %H:%M:%S")
