"""
Admin-only routes protected by X-Admin-Secret header.
These endpoints are NOT accessible from the UI — they require a secret header
that only the operator knows.
"""
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.session import get_db
from app.core.config import settings

router = APIRouter()


def verify_admin_secret(x_admin_secret: str = Header(...)):
    """Dependency that checks the X-Admin-Secret header."""
    if x_admin_secret != settings.ADMIN_SECRET:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin secret",
        )


@router.delete(
    "/users/reset",
    dependencies=[Depends(verify_admin_secret)],
    summary="Delete all users and related data",
    description="⚠️ Dangerous! Truncates users, cluster_reservations, and notifications tables. "
                "Requires X-Admin-Secret header.",
)
def reset_users(db: Session = Depends(get_db)):
    tables = ["cluster_reservations", "notifications", "users"]
    for table in tables:
        db.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
    db.commit()
    return {
        "message": "All users and related data deleted",
        "tables_cleared": tables,
    }
