from datetime import datetime, timedelta, timezone

from flask import jsonify

# 全厂统一使用东八区自然日，禁止用 UTC 零点切日。
CN_TZ = timezone(timedelta(hours=8))


def now_cst() -> datetime:
    """当前东八区时间（带时区信息）。"""
    return datetime.now(CN_TZ)


def now_cst_naive() -> datetime:
    """当前东八区挂钟时间（naive，与数据库 DateTime 列保持一致）。"""
    return now_cst().replace(tzinfo=None)


def error(message: str, status: int = 400):
    return jsonify({"message": message}), status


def normalize_datetime(value: str) -> datetime:
    value = (value or "").strip()
    if not value:
        return now_cst_naive()
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
        return now_cst_naive()


def dt_to_json(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.strftime("%Y-%m-%d %H:%M:%S")
