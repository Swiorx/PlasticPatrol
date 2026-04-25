# backend/app/api/routes/stats.py
# Rute pentru statistici și dashboard
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from pydantic import BaseModel
from typing import List

from app.db.session import get_db
from app.db.models import PlasticDebris, User

router = APIRouter()


class MonthlyStats(BaseModel):
    year: int
    month: int
    count: int


class StatsResponse(BaseModel):
    total_detected: int
    total_collected: int
    total_verified: int
    total_pending_verification: int
    collection_rate_percent: float
    total_users: int
    total_eco_points_awarded: int
    monthly_detections: List[MonthlyStats]


@router.get("/", response_model=StatsResponse)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Returnează statisticile globale ale platformei PlasticPatrol.
    Include: total detectate, colectate, verificate, rata de curățare,
    și un grafic temporal cu detecțiile lunare.
    """
    total_detected = db.query(func.count(PlasticDebris.id)).scalar() or 0
    total_collected = db.query(func.count(PlasticDebris.id)).filter(
        PlasticDebris.is_collected == True
    ).scalar() or 0
    total_verified = db.query(func.count(PlasticDebris.id)).filter(
        PlasticDebris.is_verified == True
    ).scalar() or 0
    total_pending = db.query(func.count(PlasticDebris.id)).filter(
        PlasticDebris.is_collected == True,
        PlasticDebris.is_verified == False
    ).scalar() or 0

    collection_rate = (total_collected / total_detected * 100) if total_detected > 0 else 0.0

    total_users = db.query(func.count(User.id)).scalar() or 0
    total_eco_points = db.query(func.coalesce(func.sum(User.eco_points), 0)).scalar()

    # Detecții lunare (ultimele 12 luni)
    monthly = db.query(
        extract("year", PlasticDebris.detected_at).label("year"),
        extract("month", PlasticDebris.detected_at).label("month"),
        func.count(PlasticDebris.id).label("count")
    ).group_by("year", "month").order_by("year", "month").limit(12).all()

    monthly_detections = [
        MonthlyStats(year=int(m.year), month=int(m.month), count=m.count)
        for m in monthly
    ]

    return StatsResponse(
        total_detected=total_detected,
        total_collected=total_collected,
        total_verified=total_verified,
        total_pending_verification=total_pending,
        collection_rate_percent=round(collection_rate, 2),
        total_users=total_users,
        total_eco_points_awarded=total_eco_points,
        monthly_detections=monthly_detections
    )
