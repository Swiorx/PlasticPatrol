from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from typing import List
from pydantic import BaseModel

from app.db.session import get_db
from app.db.models import PlasticDebris, ClusterReservation, Notification, User
from app.api.deps import get_current_user

router = APIRouter()

RESERVATION_HOURS = 24
ACTIVE_STATUSES = ("reserved", "photo_verified")


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
    ).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")

    reservation.status = "expired"
    db.query(PlasticDebris).filter(PlasticDebris.id.in_(reservation.point_ids)).update(
        {"is_reserved": False}, synchronize_session="fetch"
    )
    db.commit()
    return None
