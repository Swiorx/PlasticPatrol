import math
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.models import PlasticDebris, ClusterReservation, User, Notification

NEARBY_M = 100.0
VERIFICATION_DELAY = timedelta(days=2)


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def verify_collected_debris(db: Session) -> None:
    """
    Satellite re-verification of collected debris.

    Flow:
      1. Wait at least 2 days after collection for the satellite to revisit.
      2. If satellite no longer detects debris at that location → DELETE the
         debris records entirely, award eco points, notify user.
      3. If satellite still detects debris → revert collection, release
         reservation, notify user that verification failed.
      4. While awaiting verification (< 2 days), debris stays on the map
         as 'awaiting verification' and cannot be reserved.
    """
    now = datetime.now(timezone.utc)

    pending = db.query(
        PlasticDebris,
        func.ST_X(PlasticDebris.geom).label("lon"),
        func.ST_Y(PlasticDebris.geom).label("lat"),
    ).filter(
        PlasticDebris.is_collected == True,
        PlasticDebris.is_verified == False,
    ).all()

    photo_verified_reservations = db.query(ClusterReservation).filter(
        ClusterReservation.status == "photo_verified"
    ).all()
    # Build lookup: debris_point_id → reservation
    point_to_res: dict = {}
    for r in photo_verified_reservations:
        for pid in r.point_ids:
            point_to_res[pid] = r

    # Collect IDs to bulk-delete after the loop
    ids_to_delete: list[int] = []

    for debris, lon, lat in pending:
        if debris.collected_at is None:
            continue

        collected_at = debris.collected_at
        if collected_at.tzinfo is None:
            collected_at = collected_at.replace(tzinfo=timezone.utc)

        # Wait at least 2 days for satellite to revisit the location
        if now - collected_at < VERIFICATION_DELAY:
            continue

        # Check if any new uncollected point appeared near this location after collection
        new_points = db.query(
            PlasticDebris,
            func.ST_X(PlasticDebris.geom).label("lon2"),
            func.ST_Y(PlasticDebris.geom).label("lat2"),
        ).filter(
            PlasticDebris.is_collected == False,
            PlasticDebris.is_reserved == False,
            PlasticDebris.detected_at > collected_at,
        ).all()

        still_there = any(
            _haversine_m(lat, lon, float(lat2), float(lon2)) <= NEARBY_M
            for _, lon2, lat2 in new_points
        )

        owning_res = point_to_res.get(debris.id)

        if still_there:
            # Satellite still sees debris → revert collection
            if owning_res:
                owning_res.status = "failed"
                db.query(PlasticDebris).filter(PlasticDebris.id.in_(owning_res.point_ids)).update(
                    {"is_collected": False, "is_reserved": False, "collected_by": None, "collected_at": None},
                    synchronize_session="fetch",
                )
                db.add(Notification(
                    user_id=owning_res.reserved_by,
                    message="Satellite scan shows debris still present — collection could not be confirmed. No eco points awarded.",
                ))
            else:
                debris.is_collected = False
                debris.is_reserved = False
                debris.collected_by = None
                debris.collected_at = None
        else:
            # Satellite confirms clean → award points, then DELETE debris
            if owning_res:
                owning_res.status = "collected"
                user = db.query(User).filter(User.id == owning_res.reserved_by).first()
                if user:
                    user.eco_points += owning_res.eco_points
                    db.add(Notification(
                        user_id=user.id,
                        message=f"🛰️ Satellite confirmed cleanup! You earned {owning_res.eco_points} eco points. Debris removed from map.",
                    ))
                ids_to_delete.extend(owning_res.point_ids)
            else:
                # Non-cluster single-debris collection
                if debris.collected_by:
                    user = db.query(User).filter(User.id == debris.collected_by).first()
                    if user:
                        eco = debris.eco_points or 2
                        user.eco_points += eco
                        db.add(Notification(
                            user_id=user.id,
                            message=f"🛰️ Satellite confirmed cleanup! You earned {eco} eco points. Debris removed from map.",
                        ))
                ids_to_delete.append(debris.id)

    # Bulk-delete all confirmed-clean debris
    if ids_to_delete:
        db.query(PlasticDebris).filter(PlasticDebris.id.in_(ids_to_delete)).delete(synchronize_session="fetch")

    db.commit()
