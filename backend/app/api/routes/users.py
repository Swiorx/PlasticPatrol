# Rute pentru profilul utilizatorilor + autentificare + locație + scanare satelit per user.
# backend/app/api/routes/users.py
import math
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import and_, cast, func, or_
from sqlalchemy.orm import Session
from geoalchemy2.elements import WKTElement
from geoalchemy2.types import Geography

from app.db.session import get_db
from app.db.models import User, PlasticDebris, ClusterReservation
from app.schemas.user import UserCreate, UserOut, LocationIn, TokenOut, DebrisOut, ReservationOut
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


def _haversine_m_u(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = math.sin(d_lat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2)**2
    return 2 * R * math.asin(math.sqrt(a))


def _cluster_points_u(points: list, max_distance_m: float = 1000.0) -> list:
    if not points:
        return []
    parent = list(range(len(points)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            if _haversine_m_u(points[i]["lat"], points[i]["lon"], points[j]["lat"], points[j]["lon"]) <= max_distance_m:
                union(i, j)

    groups: dict = {}
    for idx in range(len(points)):
        groups.setdefault(find(idx), []).append(idx)
    return list(groups.values())


def _classify_cluster_u(size: int) -> tuple:
    if size <= 2:
        return "small", 2
    if size <= 4:
        return "medium", 4
    return "large", 6


@router.get("/me/debris", response_model=List[DebrisOut])
def get_my_debris(
    radius_km: float = Query(12.0, ge=1.0, le=50.0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.latitude is None or current_user.longitude is None:
        raise HTTPException(status_code=400, detail="Location not set")

    user_point = WKTElement(f"SRID=4326;POINT({current_user.longitude} {current_user.latitude})")
    radius_m = radius_km * 1000.0

    # Find current user's active reservation
    active_reservation = db.query(ClusterReservation).filter(
        ClusterReservation.reserved_by == current_user.id,
        ClusterReservation.status.in_(("reserved", "photo_verified")),
    ).first()
    my_point_ids: set = set(active_reservation.point_ids) if active_reservation else set()

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
            ),
            or_(
                PlasticDebris.is_collected == False,
                and_(
                    PlasticDebris.is_collected == True,
                    PlasticDebris.is_verified == False,
                ),
            ),
        )
        .all()
    )

    # Exclude points reserved by OTHER users (keep own reserved points)
    filtered = [
        (d, lon, lat) for d, lon, lat in rows
        if not d.is_reserved or d.id in my_point_ids
    ]

    raw_points = [
        {"id": d.id, "lat": float(lat), "lon": float(lon),
         "is_collected": bool(d.is_collected), "is_verified": bool(d.is_verified),
         "eco_points": d.eco_points or 0}
        for d, lon, lat in filtered
    ]

    clusters = _cluster_points_u(raw_points)
    result = []
    for i, cluster in enumerate(clusters, start=1):
        pts = [raw_points[j] for j in cluster]
        size = len(pts)
        center_lat = sum(p["lat"] for p in pts) / size
        center_lon = sum(p["lon"] for p in pts) / size
        radius = max((_haversine_m_u(center_lat, center_lon, p["lat"], p["lon"]) for p in pts), default=0.0)
        size_cat, eco = _classify_cluster_u(size)
        ids = [p["id"] for p in pts]
        is_reserved = bool(my_point_ids & set(ids))

        result.append(DebrisOut(
            id=f"cluster-{i}",
            latitude=center_lat,
            longitude=center_lon,
            size_category=size_cat,
            is_collected=all(p["is_collected"] for p in pts),
            is_verified=all(p["is_verified"] for p in pts),
            eco_points=eco,
            source_point_ids=ids,
            source_point_count=size,
            radius_m=radius,
            is_reserved=is_reserved,
            reservation_id=active_reservation.id if is_reserved else None,
        ))

    return result


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

@router.get("/me/reservations", response_model=List[ReservationOut])
def get_my_reservations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reservations = db.query(ClusterReservation).filter(
        ClusterReservation.reserved_by == current_user.id,
        ClusterReservation.status.in_(("reserved", "photo_verified")),
    ).all()
    
    result = []
    for r in reservations:
        result.append(ReservationOut(
            reservation_id=r.id,
            point_ids=r.point_ids,
            cluster_center_lat=r.cluster_center_lat,
            cluster_center_lon=r.cluster_center_lon,
            eco_points=r.eco_points,
            reserved_until=r.reserved_until.isoformat(),
            status=r.status
        ))
    return result
