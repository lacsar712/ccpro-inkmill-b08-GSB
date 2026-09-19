from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy import func, select

from app.database import SessionLocal
from app.models.grind_pass import GrindPass
from app.models.mill import Mill
from app.models.viscosity_sample import ViscositySample
from app.models.workshop import Workshop
from app.utils import error, now_cst_naive

bp = Blueprint("dashboard", __name__, url_prefix="/api")

# 三班边界（东八区自然日挂钟小时，左闭右开）：
#   night     00:00–08:00，00:00 归 night
#   morning   08:00–16:00，08:00 归 morning
#   afternoon 16:00–24:00，16:00 归 afternoon
SHIFTS = (
    {"key": "night", "name": "夜班", "window": "00:00–08:00", "start": 0, "end": 8},
    {"key": "morning", "name": "早班", "window": "08:00–16:00", "start": 8, "end": 16},
    {"key": "afternoon", "name": "午班", "window": "16:00–24:00", "start": 16, "end": 24},
)


@bp.get("/dashboard")
@jwt_required()
def summary():
    db = SessionLocal()
    try:
        now = now_cst_naive()
        since_24h = now - timedelta(hours=24)
        since_7d = now - timedelta(days=7)

        workshop_total = db.scalar(select(func.count()).select_from(Workshop)) or 0
        grinding_mill_count = (
            db.scalar(
                select(func.count()).select_from(Mill).where(Mill.status == "grinding")
            )
            or 0
        )
        samples_last_24h = (
            db.scalar(
                select(func.count())
                .select_from(ViscositySample)
                .where(ViscositySample.sampled_at >= since_24h)
            )
            or 0
        )
        passes_last_7d = (
            db.scalar(
                select(func.count())
                .select_from(GrindPass)
                .where(GrindPass.started_at >= since_7d)
            )
            or 0
        )

        return jsonify(
            {
                "workshopTotal": workshop_total,
                "grindingMillCount": grinding_mill_count,
                "samplesLast24h": samples_last_24h,
                "passesLast7d": passes_last_7d,
            }
        )
    finally:
        db.close()


@bp.get("/dashboard/shifts")
@jwt_required()
def shift_summary():
    raw_date = (request.args.get("date") or "").strip()
    if raw_date:
        # 严格只接受 YYYY-MM-DD（长度 + strptime 双重校验，拒绝 2026-9-1 等）。
        if len(raw_date) != 10:
            return error("日期格式非法，应为 YYYY-MM-DD", 400)
        try:
            day = datetime.strptime(raw_date, "%Y-%m-%d").date()
        except ValueError:
            return error("日期格式非法，应为 YYYY-MM-DD", 400)
    else:
        day = now_cst_naive().date()

    # 东八区自然日边界（naive 挂钟时间，与 started_at 列一致），绝不用 UTC 零点。
    day_start = datetime(day.year, day.month, day.day, 0, 0)
    day_end = day_start + timedelta(days=1)

    db = SessionLocal()
    try:
        # 只按遍次开始时间(started_at)落在当日取数；
        # 跨午夜遍次整段保留，不按结束时间拆分到次日。
        rows = db.execute(
            select(GrindPass.started_at, GrindPass.duration_min).where(
                GrindPass.started_at >= day_start,
                GrindPass.started_at < day_end,
            )
        ).all()
    finally:
        db.close()

    buckets = {s["key"]: {"pass_count": 0, "total_minutes": 0.0} for s in SHIFTS}
    for started_at, duration_min in rows:
        hour = started_at.hour
        for shift in SHIFTS:
            if shift["start"] <= hour < shift["end"]:
                bucket = buckets[shift["key"]]
                bucket["pass_count"] += 1
                bucket["total_minutes"] += float(duration_min or 0)
                break

    shifts = [
        {
            "key": s["key"],
            "name": s["name"],
            "window": s["window"],
            "passCount": buckets[s["key"]]["pass_count"],
            "totalMinutes": round(buckets[s["key"]]["total_minutes"], 2),
        }
        for s in SHIFTS
    ]
    return jsonify({"date": day.isoformat(), "shifts": shifts})
