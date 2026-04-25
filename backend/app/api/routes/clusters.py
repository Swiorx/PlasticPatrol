import math
import sys
from pathlib import Path
from fastapi import APIRouter, Depends, File, HTTPException, status, UploadFile
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from typing import List
from pydantic import BaseModel

from app.db.session import get_db
from app.db.models import PlasticDebris, ClusterReservation, Notification, User
from app.api.deps import get_current_user

ROOT_DIR = Path(__file__).resolve().parents[4]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

MAX_COLLECT_DISTANCE_M = 100.0
MAX_ATTEMPTS = 3
_ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
_MAX_BYTES = 10 * 1024 * 1024

router = APIRouter()

RESERVATION_HOURS = 24
ACTIVE_STATUSES = ("reserved", "photo_verified")


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def _reserve_cluster(
    point_ids: List[int],
    center_lat: float,
    center_lon: float,
    eco_points: int,
    user: User,
    db: Session,
) -> dict:
    # One active reservation per user
    existing = db.query(ClusterReservation).filter(
        ClusterReservation.reserved_by == user.id,
        ClusterReservation.status.in_(ACTIVE_STATUSES),
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="You already have an active reservation")

    # Check no point in the cluster is reserved by someone else
    conflict = db.query(PlasticDebris).filter(
        PlasticDebris.id.in_(point_ids),
        PlasticDebris.is_reserved == True,
    ).first()
    if conflict:
        raise HTTPException(status_code=409, detail="Already reserved by another user")

    reserved_until = datetime.now(timezone.utc) + timedelta(hours=RESERVATION_HOURS)
    reservation = ClusterReservation(
        point_ids=point_ids,
        cluster_center_lat=center_lat,
        cluster_center_lon=center_lon,
        eco_points=eco_points,
        reserved_by=user.id,
        reserved_until=reserved_until,
        attempt_count=0,
        status="reserved",
    )
    db.add(reservation)

    db.query(PlasticDebris).filter(PlasticDebris.id.in_(point_ids)).update(
        {"is_reserved": True}, synchronize_session="fetch"
    )
    db.commit()
    db.refresh(reservation)

    return {"reservation_id": reservation.id, "reserved_until": reserved_until.isoformat()}


class ReserveRequest(BaseModel):
    point_ids: List[int]
    center_lat: float
    center_lon: float
    eco_points: int


@router.post("/reserve", status_code=status.HTTP_201_CREATED)
def reserve_cluster(
    body: ReserveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _reserve_cluster(
        point_ids=body.point_ids,
        center_lat=body.center_lat,
        center_lon=body.center_lon,
        eco_points=body.eco_points,
        user=current_user,
        db=db,
    )


@router.delete("/{reservation_id}/reserve", status_code=status.HTTP_204_NO_CONTENT)
def release_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reservation = db.query(ClusterReservation).filter(
        ClusterReservation.id == reservation_id,
        ClusterReservation.reserved_by == current_user.id,
        ClusterReservation.status == "reserved",
    ).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found or already collected")

    reservation.status = "expired"
    db.query(PlasticDebris).filter(PlasticDebris.id.in_(reservation.point_ids)).update(
        {"is_reserved": False}, synchronize_session="fetch"
    )
    db.commit()
    return None


@router.post("/{reservation_id}/collect")
async def collect_cluster(
    reservation_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if file.content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail="Use JPEG, PNG, or WebP.")

    reservation = db.query(ClusterReservation).filter(
        ClusterReservation.id == reservation_id,
        ClusterReservation.reserved_by == current_user.id,
        ClusterReservation.status == "reserved",
    ).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Active reservation not found")

    if datetime.now(timezone.utc) > reservation.reserved_until.replace(tzinfo=timezone.utc):
        raise HTTPException(status_code=410, detail="Reservation has expired")

    # Server-side proximity check using user's last known location
    if current_user.latitude is None or current_user.longitude is None:
        raise HTTPException(status_code=400, detail="User location not set — open the map first")

    dist = _haversine_m(
        current_user.latitude, current_user.longitude,
        reservation.cluster_center_lat, reservation.cluster_center_lon,
    )
    if dist > MAX_COLLECT_DISTANCE_M:
        raise HTTPException(
            status_code=400,
            detail=f"Too far from debris ({int(dist)}m). Must be within {int(MAX_COLLECT_DISTANCE_M)}m."
        )

    image_bytes = await file.read()
    if len(image_bytes) > _MAX_BYTES:
        raise HTTPException(status_code=413, detail="Image too large. Max 10MB.")

    reservation.attempt_count += 1

    try:
        from ml_classifier.predict import classify_image
        result = classify_image(image_bytes)
        ml_pass = result.get("label") == "debris"
    except Exception:
        ml_pass = False

    if not ml_pass:
        if reservation.attempt_count >= MAX_ATTEMPTS:
            reservation.status = "failed"
            db.query(PlasticDebris).filter(PlasticDebris.id.in_(reservation.point_ids)).update(
                {"is_reserved": False}, synchronize_session="fetch"
            )
            db.add(Notification(
                user_id=current_user.id,
                message="Reservation released after 3 failed photo attempts. The cluster is available again."
            ))
            db.commit()
            raise HTTPException(
                status_code=422,
                detail="No debris detected after 3 attempts. Reservation released."
            )

        db.commit()
        remaining = MAX_ATTEMPTS - reservation.attempt_count
        raise HTTPException(
            status_code=422,
            detail=f"No debris detected in photo. {remaining} attempt(s) remaining."
        )

    # ML pass
    reservation.status = "photo_verified"
    now = datetime.now(timezone.utc)
    db.query(PlasticDebris).filter(PlasticDebris.id.in_(reservation.point_ids)).update(
        {"is_collected": True, "collected_by": current_user.id, "collected_at": now},
        synchronize_session="fetch",
    )
    db.add(Notification(
        user_id=current_user.id,
        message=f"Photo verified! Debris cluster collected. Awaiting satellite confirmation for {reservation.eco_points} eco points."
    ))
    db.commit()

    return {
        "message": "Collected — awaiting satellite confirmation for eco points",
        "eco_points_pending": reservation.eco_points,
    }
