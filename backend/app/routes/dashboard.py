from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy import func, select

from app.database import SessionLocal
from app.models.grind_pass import GrindPass
from app.models.mill import Mill
from app.models.viscosity_sample import ViscositySample
from app.models.workshop import Workshop
from app.utils import SHIFT_KEYS, error, parse_shift_date, shift_bounds

bp = Blueprint("dashboard", __name__, url_prefix="/api")


@bp.get("/dashboard")
@jwt_required()
def summary():
    db = SessionLocal()
    try:
        now = datetime.now()
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
def shifts():
    try:
        day = parse_shift_date(request.args.get("date"))
    except ValueError:
        return error("日期格式非法，应为 YYYY-MM-DD", 400)

    # 三个班次覆盖该东八区自然日 00:00 至次日 00:00，互不重叠。
    # 只按 started_at 落在哪一个区间归班；遍次不会因结束时间跨边界而被拆开。
    bounds = shift_bounds(day)

    db = SessionLocal()
    try:
        result = {}
        for key in SHIFT_KEYS:
            start, end = bounds[key]
            rows = (
                db.query(
                    func.count(GrindPass.id),
                    func.coalesce(func.sum(GrindPass.duration_min), 0),
                )
                .filter(GrindPass.started_at >= start)
                .filter(GrindPass.started_at < end)
                .one()
            )
            result[key] = {
                "passCount": int(rows[0]),
                "totalMinutes": float(rows[1]),
            }

        return jsonify({"date": day.isoformat(), "shifts": result})
    finally:
        db.close()
