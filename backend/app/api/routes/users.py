# Rute pentru profilul utilizatorilor + autentificare + locație + scanare satelit per user.
# backend/app/api/routes/users.py
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import cast, func
from sqlalchemy.orm import Session
from geoalchemy2.elements import WKTElement
from geoalchemy2.types import Geography

from app.db.session import get_db
from app.db.models import User, PlasticDebris
from app.schemas.user import UserCreate, UserOut, LocationIn, TokenOut, DebrisOut
from app.core.security import get_password_hash, verify_password, create_access_token
from app.api.deps import get_current_user
from app.services.geo import bbox_for_user
from app.services.sentinel_verify import verify_collected_debris

# Make data_pipeline importable
_PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

router = APIRouter()


@router.get("/leaderboard", response_model=List[UserOut])
def get_leaderboard(db: Session = Depends(get_db), limit: int = 10):
    return db.query(User).order_by(User.eco_points.desc()).limit(limit).all()


@router.get("/", response_model=List[UserOut])
def get_all_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(User).offset(skip).limit(limit).all()


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email-ul este deja folosit")
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username-ul este deja folosit")

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token = create_access_token(subject=new_user.email)
    return TokenOut(access_token=access_token, user=UserOut.model_validate(new_user))


@router.post("/login", response_model=TokenOut)
async def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(
        (User.email == form_data.username) | (User.username == form_data.username)
    ).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email/Username sau parolă incorecte",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(subject=user.email)
    return TokenOut(access_token=access_token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/me/location", response_model=UserOut)
def update_my_location(
    payload: LocationIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    current_user.latitude = payload.latitude
    current_user.longitude = payload.longitude
    current_user.last_location_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/me/debris", response_model=List[DebrisOut])
def get_my_debris(
    radius_km: float = Query(12.0, ge=1.0, le=50.0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.latitude is None or current_user.longitude is None:
        raise HTTPException(status_code=400, detail="Location not set")

    user_point = WKTElement(
        f"SRID=4326;POINT({current_user.longitude} {current_user.latitude})"
    )
    radius_m = radius_km * 1000.0

    rows = (
        db.query(
            PlasticDebris,
            func.ST_X(PlasticDebris.geom).label("lon"),
            func.ST_Y(PlasticDebris.geom).label("lat"),
        )
        .filter(
            func.ST_DWithin(
                cast(PlasticDebris.geom, Geography),
                cast(user_point, Geography),
                radius_m,
            )
        )
        .all()
    )

    return [
        DebrisOut(
            id=d.id,
            latitude=lat,
            longitude=lon,
            size_category=d.size_category or "small",
            is_collected=bool(d.is_collected),
            is_verified=bool(d.is_verified),
            eco_points=d.eco_points or 0,
        )
        for d, lon, lat in rows
    ]


@router.post("/me/refresh-satellite")
def refresh_my_satellite(
    radius_km: float = Query(12.0, ge=1.0, le=50.0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.latitude is None or current_user.longitude is None:
        raise HTTPException(status_code=400, detail="Location not set")

    bbox = bbox_for_user(current_user.latitude, current_user.longitude, radius_km=radius_km)

    from data_pipeline.sentinel_fetcher import fetch_for_bbox, insert_new_debris

    try:
        coordinates = fetch_for_bbox(bbox)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Sentinel fetch failed: {exc}")

    inserted = insert_new_debris(db, coordinates)
    verify_collected_debris(db)
    return {"inserted": inserted, "scanned_points": len(coordinates), "bbox": bbox}
