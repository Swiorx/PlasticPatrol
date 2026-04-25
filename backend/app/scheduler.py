from datetime import datetime, timezone
from app.db.session import SessionLocal
from app.db.models import ClusterReservation, PlasticDebris, Notification


def expire_reservations() -> None:
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        stale = db.query(ClusterReservation).filter(
            ClusterReservation.status == "reserved",
            ClusterReservation.reserved_until < now,
        ).all()

        for r in stale:
            r.status = "expired"
            db.query(PlasticDebris).filter(PlasticDebris.id.in_(r.point_ids)).update(
                {"is_reserved": False}, synchronize_session="fetch"
            )
            db.add(Notification(
                user_id=r.reserved_by,
                message="Your debris reservation expired — the cluster is available again.",
            ))

        if stale:
            db.commit()
    finally:
        db.close()
