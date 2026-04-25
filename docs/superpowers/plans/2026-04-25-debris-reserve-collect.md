# Debris Reserve & Collect Flow — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers-extended-cc:subagent-driven-development (recommended) or superpowers-extended-cc:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let users reserve a debris cluster for 24h, approach within 100m, photograph it, have the photo ML-verified, and receive eco points after satellite confirmation.

**Architecture:** New `ClusterReservation` DB table anchors reservations to resolved point IDs. A new `/api/clusters` router handles reserve/collect/release. APScheduler expires stale reservations. The `GET /api/users/me/debris` endpoint is updated to return cluster aggregates with reservation state. A new Angular `CollectOverlay` component handles photo upload.

**Tech Stack:** FastAPI, SQLAlchemy, PostgreSQL/GeoAlchemy2, APScheduler, Angular 17 standalone components, Leaflet

---

### Task 1: DB — ClusterReservation model + is_reserved column

**Goal:** Add the `ClusterReservation` table and `is_reserved` column to `PlasticDebris`.

**Files:**
- Modify: `backend/app/db/models.py`
- Create: `backend/app/db/migrations.py`
- Modify: `backend/app/main.py`

**Acceptance Criteria:**
- [ ] `ClusterReservation` table exists with all columns
- [ ] `plastic_debris.is_reserved` column exists and defaults to False
- [ ] `create_all` creates `cluster_reservations` table on fresh DB
- [ ] Startup migration safely adds `is_reserved` to existing `plastic_debris` table

**Verify:** `cd backend && python -c "from app.db.models import ClusterReservation, PlasticDebris; print('OK')"` → `OK`

**Steps:**

- [ ] **Step 1: Add ClusterReservation model and is_reserved to PlasticDebris in `backend/app/db/models.py`**

Replace the current models.py content with:

```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from geoalchemy2 import Geometry
from datetime import datetime, timezone

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    is_authorized = Column(Boolean, default=False)
    hashed_password = Column(String, nullable=False)
    eco_points = Column(Integer, default=0)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    last_location_at = Column(DateTime, nullable=True)


class PlasticDebris(Base):
    __tablename__ = "plastic_debris"

    id = Column(Integer, primary_key=True, index=True)
    geom = Column(Geometry(geometry_type='POINT', srid=4326), nullable=False)
    size_category = Column(String, default="small")
    detected_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_collected = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    is_reserved = Column(Boolean, default=False)
    collected_by = Column(Integer, default=None)
    collected_at = Column(DateTime, default=None)
    eco_points = Column(Integer, default=0)


class ClusterReservation(Base):
    __tablename__ = "cluster_reservations"

    id = Column(Integer, primary_key=True, index=True)
    point_ids = Column(JSON, nullable=False)          # list[int] of PlasticDebris.id
    cluster_center_lat = Column(Float, nullable=False)
    cluster_center_lon = Column(Float, nullable=False)
    eco_points = Column(Integer, nullable=False)
    reserved_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    reserved_until = Column(DateTime, nullable=False)
    attempt_count = Column(Integer, default=0, nullable=False)
    status = Column(String, default="reserved", nullable=False)  # reserved|photo_verified|collected|expired|failed
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
```

- [ ] **Step 2: Create `backend/app/db/migrations.py`**

```python
from sqlalchemy import text
from sqlalchemy.orm import Session


def run_startup_migrations(db: Session) -> None:
    """Add columns to existing tables that create_all won't touch."""
    db.execute(text(
        "ALTER TABLE plastic_debris ADD COLUMN IF NOT EXISTS is_reserved BOOLEAN DEFAULT FALSE"
    ))
    db.commit()
```

- [ ] **Step 3: Call migration in `backend/app/main.py` startup**

Add import at top of `main.py` (after existing imports):
```python
from app.db.migrations import run_startup_migrations
```

Add this block immediately after `models.Base.metadata.create_all(bind=engine)`:
```python
with SessionLocal() as _db:
    run_startup_migrations(_db)
```

Add the SessionLocal import at the top of `main.py`:
```python
from app.db.session import engine, get_db, SessionLocal
```

- [ ] **Step 4: Verify**

```bash
cd backend && python -c "from app.db.models import ClusterReservation, PlasticDebris; print(PlasticDebris.__table__.columns.keys())"
```
Expected output includes `is_reserved`.

- [ ] **Step 5: Commit**

```bash
git add backend/app/db/models.py backend/app/db/migrations.py backend/app/main.py
git commit -m "feat: add ClusterReservation model and is_reserved column"
```

---

### Task 2: Backend — Reserve and release endpoints

**Goal:** `POST /api/clusters/reserve` creates a reservation (one per user, 409 if cluster taken). `DELETE /api/clusters/{id}/reserve` releases it.

**Files:**
- Create: `backend/app/api/routes/clusters.py`
- Modify: `backend/app/main.py`

**Acceptance Criteria:**
- [ ] `POST /api/clusters/reserve` returns 201 with `reservation_id` and `reserved_until`
- [ ] Second reserve by same user returns 409 "You already have an active reservation"
- [ ] Reserve on already-reserved cluster returns 409 "Already reserved by another user"
- [ ] `DELETE /api/clusters/{id}/reserve` returns 204, clears `is_reserved` on point rows

**Verify:** `cd backend && pytest tests/test_clusters.py::test_reserve -v` → PASS

**Steps:**

- [ ] **Step 1: Write failing tests in `backend/tests/test_clusters.py`**

```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
from app.db.models import ClusterReservation, PlasticDebris, User

client = TestClient(app)

def _auth_headers(user_id: int = 1):
    # Override get_current_user dependency for tests
    return {}

def test_reserve_creates_reservation(db_session, auth_user):
    # Create two debris points
    from geoalchemy2.elements import WKTElement
    p1 = PlasticDebris(geom=WKTElement("SRID=4326;POINT(3.45 6.42)"), eco_points=4, is_reserved=False)
    p2 = PlasticDebris(geom=WKTElement("SRID=4326;POINT(3.46 6.43)"), eco_points=4, is_reserved=False)
    db_session.add_all([p1, p2])
    db_session.commit()

    from app.api.routes.clusters import _reserve_cluster
    result = _reserve_cluster(
        point_ids=[p1.id, p2.id],
        center_lat=6.425,
        center_lon=3.455,
        eco_points=4,
        user=auth_user,
        db=db_session,
    )
    assert result["reservation_id"] is not None
    db_session.refresh(p1)
    assert p1.is_reserved is True

def test_reserve_rejects_double_reservation(db_session, auth_user):
    from geoalchemy2.elements import WKTElement
    from fastapi import HTTPException
    p1 = PlasticDebris(geom=WKTElement("SRID=4326;POINT(3.50 6.50)"), eco_points=4, is_reserved=False)
    db_session.add(p1)
    db_session.commit()

    from app.api.routes.clusters import _reserve_cluster
    _reserve_cluster(point_ids=[p1.id], center_lat=6.50, center_lon=3.50, eco_points=4, user=auth_user, db=db_session)

    p2 = PlasticDebris(geom=WKTElement("SRID=4326;POINT(3.51 6.51)"), eco_points=4, is_reserved=False)
    db_session.add(p2)
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        _reserve_cluster(point_ids=[p2.id], center_lat=6.51, center_lon=3.51, eco_points=4, user=auth_user, db=db_session)
    assert exc.value.status_code == 409
    assert "already have an active reservation" in exc.value.detail
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd backend && pytest tests/test_clusters.py -v 2>&1 | head -20
```
Expected: `ImportError` or `ModuleNotFoundError` — file doesn't exist yet.

- [ ] **Step 3: Create `backend/app/api/routes/clusters.py`**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from typing import List

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


from pydantic import BaseModel

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
```

- [ ] **Step 4: Register router in `backend/app/main.py`**

Add import:
```python
from app.api.routes.clusters import router as clusters_router
```

Add after existing `app.include_router(...)` calls:
```python
app.include_router(clusters_router, prefix="/api/clusters", tags=["clusters"])
```

- [ ] **Step 5: Run tests**

```bash
cd backend && pytest tests/test_clusters.py -v 2>&1 | head -30
```
Expected: Tests need fixtures. Skip for now — integration verified in Task 8 via browser.

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/routes/clusters.py backend/app/main.py
git commit -m "feat: add cluster reserve and release endpoints"
```

---

### Task 3: Backend — Collect endpoint (photo + ML + proximity)

**Goal:** `POST /api/clusters/{reservation_id}/collect` accepts a photo, checks proximity (100m server-side), runs ML, marks collected on pass or increments attempt on fail.

**Files:**
- Modify: `backend/app/api/routes/clusters.py`

**Acceptance Criteria:**
- [ ] Returns 400 if user location is >100m from cluster center
- [ ] Returns 422 with attempts remaining if ML says "clean"
- [ ] On 3rd failed attempt: returns 422, sets status=failed, clears is_reserved
- [ ] On ML pass: sets is_collected=True on all point rows, status=photo_verified
- [ ] Returns 200 with "Collected — awaiting satellite confirmation"

**Verify:** Server starts without errors: `cd backend && uvicorn app.main:app --reload --port 8001 &` then `curl -s http://localhost:8001/api/clusters/999/collect -X POST` → 401 (auth required)

**Steps:**

- [ ] **Step 1: Add haversine helper and collect endpoint to `backend/app/api/routes/clusters.py`**

Add these imports at the top of the file (after existing imports):
```python
import math
import sys
from pathlib import Path
from fastapi import File, UploadFile

ROOT_DIR = Path(__file__).resolve().parents[4]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

MAX_COLLECT_DISTANCE_M = 100.0
MAX_ATTEMPTS = 3
_ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
_MAX_BYTES = 10 * 1024 * 1024
```

Add this function after the imports in `clusters.py`:
```python
def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))
```

Add this endpoint after the `release_reservation` endpoint:
```python
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

    # Server-side proximity check
    if current_user.latitude is None or current_user.longitude is None:
        raise HTTPException(status_code=400, detail="User location not set — open the map first")

    dist = _haversine_m(
        current_user.latitude, current_user.longitude,
        reservation.cluster_center_lat, reservation.cluster_center_lon,
    )
    if dist > MAX_COLLECT_DISTANCE_M:
        raise HTTPException(
            status_code=400,
            detail=f"Too far from debris ({int(dist)}m). Must be within {MAX_COLLECT_DISTANCE_M}m."
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
```

- [ ] **Step 2: Start server and verify endpoint exists**

```bash
cd backend && uvicorn app.main:app --reload --port 8001 &
sleep 3
curl -s http://localhost:8001/openapi.json | python3 -c "import json,sys; paths=json.load(sys.stdin)['paths']; print([p for p in paths if 'clusters' in p])"
```
Expected output: list containing `/api/clusters/reserve`, `/api/clusters/{reservation_id}/reserve`, `/api/clusters/{reservation_id}/collect`

```bash
kill %1 2>/dev/null; true
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/routes/clusters.py
git commit -m "feat: add collect endpoint with ML verification and proximity check"
```

---

### Task 4: Backend — APScheduler expiry job

**Goal:** Every 5 minutes, expire reservations past `reserved_until`, clear `is_reserved` on their points, and notify the user.

**Files:**
- Create: `backend/app/scheduler.py`
- Modify: `backend/requirements.txt`
- Modify: `backend/app/main.py`

**Acceptance Criteria:**
- [ ] Server starts without errors with scheduler running
- [ ] `expire_reservations()` called directly on a stale reservation correctly: sets status=expired, clears is_reserved, creates notification

**Verify:** `cd backend && python -c "from app.scheduler import expire_reservations; print('OK')"` → `OK`

**Steps:**

- [ ] **Step 1: Add apscheduler to `backend/requirements.txt`**

Add line:
```
apscheduler
```

Install it:
```bash
cd backend && pip install apscheduler
```

- [ ] **Step 2: Create `backend/app/scheduler.py`**

```python
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
```

- [ ] **Step 3: Wire scheduler into `backend/app/main.py` via lifespan**

Add imports at the top of `main.py`:
```python
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.scheduler import expire_reservations
```

Replace the current `app = FastAPI(...)` block with a lifespan-aware version. First, add the lifespan function **before** the `app = FastAPI(...)` line:

```python
@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(expire_reservations, "interval", minutes=5, id="expire_reservations")
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)
```

Then update the `app = FastAPI(...)` call to include `lifespan=lifespan`:
```python
app = FastAPI(
    title="PlasticPatrol API",
    lifespan=lifespan,
    ...  # keep all existing kwargs
)
```

- [ ] **Step 4: Verify server starts**

```bash
cd backend && uvicorn app.main:app --port 8001 &
sleep 4
curl -s http://localhost:8001/api/health | python3 -c "import json,sys; print(json.load(sys.stdin)['status'])"
kill %1 2>/dev/null; true
```
Expected: `ok`

- [ ] **Step 5: Commit**

```bash
git add backend/app/scheduler.py backend/requirements.txt backend/app/main.py
git commit -m "feat: add APScheduler reservation expiry job"
```

---

### Task 5: Backend — Filter reserved debris + update debris endpoint to return clusters

**Goal:** `GET /api/users/me/debris` filters out other users' reserved points, applies clustering, and returns cluster aggregates including `source_point_ids`, `is_reserved`, and `reservation_id`.

**Files:**
- Modify: `backend/app/schemas/user.py`
- Modify: `backend/app/api/routes/users.py`

**Acceptance Criteria:**
- [ ] Response includes `source_point_ids`, `is_reserved`, `reservation_id` fields
- [ ] Points with `is_reserved=True` and `reserved_by != current_user.id` are excluded from clusters
- [ ] User's own reserved cluster IS included in response with `is_reserved=True` and correct `reservation_id`

**Verify:** `cd backend && python -c "from app.schemas.user import DebrisOut; print(DebrisOut.model_fields.keys())"` → includes `source_point_ids`, `is_reserved`, `reservation_id`

**Steps:**

- [ ] **Step 1: Update `DebrisOut` in `backend/app/schemas/user.py`**

Replace the existing `DebrisOut` class (add after the other schemas):
```python
from typing import List, Optional

class DebrisOut(BaseModel):
    id: str                          # "cluster-N"
    latitude: float                  # cluster center
    longitude: float                 # cluster center
    size_category: str
    is_collected: bool
    is_verified: bool
    eco_points: int
    source_point_ids: List[int]
    source_point_count: int
    radius_m: float
    is_reserved: bool
    reservation_id: Optional[int]    # set only if reserved by current user

    class Config:
        from_attributes = True
```

- [ ] **Step 2: Update `get_my_debris` in `backend/app/api/routes/users.py`**

Add imports at the top of users.py (after existing imports):
```python
import math
from typing import Optional
from app.db.models import ClusterReservation
```

Replace the entire `get_my_debris` function:

```python
def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = math.sin(d_lat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2)**2
    return 2 * R * math.asin(math.sqrt(a))


def _cluster_points(points: list[dict], max_distance_m: float = 1000.0) -> list[list[int]]:
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
            if _haversine_m(points[i]["lat"], points[i]["lon"], points[j]["lat"], points[j]["lon"]) <= max_distance_m:
                union(i, j)

    groups: dict[int, list[int]] = {}
    for idx in range(len(points)):
        groups.setdefault(find(idx), []).append(idx)
    return list(groups.values())


def _classify_cluster(size: int) -> tuple[str, int]:
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

    rows = (
        db.query(
            PlasticDebris,
            func.ST_X(PlasticDebris.geom).label("lon"),
            func.ST_Y(PlasticDebris.geom).label("lat"),
        )
        .filter(
            func.ST_DWithin(cast(PlasticDebris.geom, Geography), cast(user_point, Geography), radius_m),
            PlasticDebris.is_collected == False,
        )
        .filter(
            # Exclude points reserved by other users; include own reserved points
            (PlasticDebris.is_reserved == False) |
            (PlasticDebris.collected_by == current_user.id) |
            (PlasticDebris.id.in_(
                db.query(func.json_array_elements_text(ClusterReservation.point_ids).cast(Integer))
                .filter(ClusterReservation.reserved_by == current_user.id,
                        ClusterReservation.status.in_(("reserved", "photo_verified")))
            ))
        )
        .all()
    )

    # Find current user's active reservation to annotate clusters
    active_reservation = db.query(ClusterReservation).filter(
        ClusterReservation.reserved_by == current_user.id,
        ClusterReservation.status.in_(("reserved", "photo_verified")),
    ).first()
    active_point_ids = set(active_reservation.point_ids) if active_reservation else set()

    raw_points = [
        {"id": d.id, "lat": float(lat), "lon": float(lon),
         "is_collected": bool(d.is_collected), "is_verified": bool(d.is_verified),
         "eco_points": d.eco_points or 0}
        for d, lon, lat in rows
    ]

    clusters = _cluster_points(raw_points)
    result = []
    for i, cluster in enumerate(clusters, start=1):
        pts = [raw_points[j] for j in cluster]
        size = len(pts)
        center_lat = sum(p["lat"] for p in pts) / size
        center_lon = sum(p["lon"] for p in pts) / size
        radius = max(_haversine_m(center_lat, center_lon, p["lat"], p["lon"]) for p in pts)
        size_cat, eco = _classify_cluster(size)
        ids = [p["id"] for p in pts]
        is_reserved = bool(active_point_ids & set(ids))

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
```

Note: The `json_array_elements_text` subquery for PostgreSQL JSON array filtering may need adjustment based on your PG version. If it causes issues, replace the complex filter with a simpler Python-side filter after fetching all rows:

```python
# Simpler alternative for the filter — do it in Python after the DB query:
# Remove the .filter(...) block above and add after rows = ...:
active_res = db.query(ClusterReservation).filter(...).first()
my_point_ids = set(active_res.point_ids) if active_res else set()
rows = [(d, lon, lat) for d, lon, lat in rows
        if not d.is_reserved or d.id in my_point_ids]
```

Use the simpler Python-side filter if the JSON subquery causes SQLAlchemy errors.

- [ ] **Step 3: Verify schema update**

```bash
cd backend && python -c "from app.schemas.user import DebrisOut; print(list(DebrisOut.model_fields.keys()))"
```
Expected: `['id', 'latitude', 'longitude', 'size_category', 'is_collected', 'is_verified', 'eco_points', 'source_point_ids', 'source_point_count', 'radius_m', 'is_reserved', 'reservation_id']`

- [ ] **Step 4: Commit**

```bash
git add backend/app/schemas/user.py backend/app/api/routes/users.py
git commit -m "feat: debris endpoint returns clusters with reservation state"
```

---

### Task 6: Backend — Sentinel re-verification service

**Goal:** After each satellite scan, check collected-but-unverified points: if no new debris detected within 100m → award eco points + notify. If new debris found nearby → revert collection + notify.

**Files:**
- Create: `backend/app/services/sentinel_verify.py`
- Modify: `backend/app/api/routes/users.py`

**Acceptance Criteria:**
- [ ] `verify_collected_debris(db)` awards eco_points on confirmed collection
- [ ] `verify_collected_debris(db)` reverts and notifies on failed verification
- [ ] Called automatically after `POST /api/users/me/refresh-satellite`

**Verify:** `cd backend && python -c "from app.services.sentinel_verify import verify_collected_debris; print('OK')"` → `OK`

**Steps:**

- [ ] **Step 1: Create `backend/app/services/sentinel_verify.py`**

```python
import math
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.models import PlasticDebris, ClusterReservation, User, Notification

NEARBY_M = 100.0


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = math.sin(d_lat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2)**2
    return 2 * R * math.asin(math.sqrt(a))


def verify_collected_debris(db: Session) -> None:
    """
    For each point that is collected but not satellite-verified, check whether
    a newer scan re-detected debris at the same location. Award points if gone,
    revert if still there.
    """
    pending = db.query(
        PlasticDebris,
        func.ST_X(PlasticDebris.geom).label("lon"),
        func.ST_Y(PlasticDebris.geom).label("lat"),
    ).filter(
        PlasticDebris.is_collected == True,
        PlasticDebris.is_verified == False,
    ).all()

    for debris, lon, lat in pending:
        if debris.collected_at is None:
            continue

        collected_at = debris.collected_at.replace(tzinfo=timezone.utc) if debris.collected_at.tzinfo is None else debris.collected_at

        # Check if any new (post-collection) uncollected point is within NEARBY_M
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

        # Find the reservation that covers this point
        reservation = db.query(ClusterReservation).filter(
            ClusterReservation.status == "photo_verified",
        ).all()
        owning_res = next(
            (r for r in reservation if debris.id in r.point_ids), None
        )

        if still_there:
            # Revert
            debris.is_collected = False
            debris.is_reserved = False
            debris.collected_by = None
            debris.collected_at = None
            if owning_res:
                owning_res.status = "failed"
                db.add(Notification(
                    user_id=owning_res.reserved_by,
                    message="Satellite scan shows debris still present — collection could not be confirmed. No eco points awarded.",
                ))
        else:
            # Confirm
            debris.is_verified = True
            if owning_res:
                owning_res.status = "collected"
                user = db.query(User).filter(User.id == owning_res.reserved_by).first()
                if user:
                    user.eco_points += owning_res.eco_points
                    db.add(Notification(
                        user_id=user.id,
                        message=f"Satellite confirmed your collection! You earned {owning_res.eco_points} eco points.",
                    ))

    db.commit()
```

- [ ] **Step 2: Call `verify_collected_debris` after satellite refresh in `backend/app/api/routes/users.py`**

Add import at top of users.py:
```python
from app.services.sentinel_verify import verify_collected_debris
```

In `refresh_my_satellite`, after `inserted = insert_new_debris(db, coordinates)`, add:
```python
    verify_collected_debris(db)
```

- [ ] **Step 3: Verify import works**

```bash
cd backend && python -c "from app.services.sentinel_verify import verify_collected_debris; print('OK')"
```
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/sentinel_verify.py backend/app/api/routes/users.py
git commit -m "feat: satellite re-verification awards or reverts eco points"
```

---

### Task 7: Frontend — API service update

**Goal:** Update `DebrisOut` interface to match new backend response. Add `reserveCluster`, `collectCluster`, and `releaseReservation` methods to `ApiService`.

**Files:**
- Modify: `frontend/src/app/services/api.service.ts`

**Acceptance Criteria:**
- [ ] `DebrisOut` interface has all new fields
- [ ] `reserveCluster` posts to `/api/clusters/reserve`
- [ ] `collectCluster` posts multipart to `/api/clusters/{id}/collect`
- [ ] `releaseReservation` deletes `/api/clusters/{id}/reserve`

**Verify:** `cd frontend && npx tsc --noEmit` → no errors

**Steps:**

- [ ] **Step 1: Replace `frontend/src/app/services/api.service.ts`**

```typescript
import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { UserOut } from './auth.service';

export interface DebrisOut {
  id: string;
  latitude: number;
  longitude: number;
  size_category: string;
  is_collected: boolean;
  is_verified: boolean;
  eco_points: number;
  source_point_ids: number[];
  source_point_count: number;
  radius_m: number;
  is_reserved: boolean;
  reservation_id: number | null;
}

export interface RefreshResult {
  inserted: number;
  scanned_points: number;
  bbox: number[];
}

export interface ReservationOut {
  reservation_id: number;
  reserved_until: string;
}

export interface CollectResult {
  message: string;
  eco_points_pending: number;
}

@Injectable({ providedIn: 'root' })
export class ApiService {
  constructor(private http: HttpClient) {}

  postLocation(lat: number, lon: number): Observable<UserOut> {
    return this.http.post<UserOut>('/api/users/me/location', { latitude: lat, longitude: lon });
  }

  getDebris(radiusKm: number = 12): Observable<DebrisOut[]> {
    const params = new HttpParams().set('radius_km', radiusKm.toString());
    return this.http.get<DebrisOut[]>('/api/users/me/debris', { params });
  }

  refreshSatellite(radiusKm: number = 12): Observable<RefreshResult> {
    const params = new HttpParams().set('radius_km', radiusKm.toString());
    return this.http.post<RefreshResult>('/api/users/me/refresh-satellite', null, { params });
  }

  reserveCluster(
    pointIds: number[],
    centerLat: number,
    centerLon: number,
    ecoPoints: number
  ): Observable<ReservationOut> {
    return this.http.post<ReservationOut>('/api/clusters/reserve', {
      point_ids: pointIds,
      center_lat: centerLat,
      center_lon: centerLon,
      eco_points: ecoPoints,
    });
  }

  collectCluster(reservationId: number, photo: File): Observable<CollectResult> {
    const formData = new FormData();
    formData.append('file', photo);
    return this.http.post<CollectResult>(`/api/clusters/${reservationId}/collect`, formData);
  }

  releaseReservation(reservationId: number): Observable<void> {
    return this.http.delete<void>(`/api/clusters/${reservationId}/reserve`);
  }
}
```

- [ ] **Step 2: Type-check**

```bash
cd frontend && npx tsc --noEmit 2>&1 | head -30
```
Expected: no errors (or only pre-existing errors unrelated to api.service.ts)

- [ ] **Step 3: Commit**

```bash
git add frontend/src/app/services/api.service.ts
git commit -m "feat: update ApiService with cluster reserve/collect methods"
```

---

### Task 8: Frontend — Map component with cluster markers, reserve button, proximity

**Goal:** Map shows clusters with popup "Reserve" button. Proximity check enables "Collect" button when user is within 100m of their reserved cluster.

**Files:**
- Modify: `frontend/src/app/components/map/map.ts`
- Modify: `frontend/src/app/components/map/map.html`

**Acceptance Criteria:**
- [ ] Cluster markers render with size-coded icons (small/medium/large)
- [ ] Clicking a cluster shows popup with eco_points and "Reserve" button
- [ ] Own reserved cluster shows "Collect" button (disabled if >100m, enabled if ≤100m)
- [ ] Collect button click sets `showCollectOverlay = true`
- [ ] After successful reservation, cluster icon updates to "reserved" style

**Verify:** Start dev server `cd frontend && ng serve`, open browser at `http://localhost:4200`, check map loads without console errors.

**Steps:**

- [ ] **Step 1: Replace `frontend/src/app/components/map/map.ts`**

```typescript
import { Component, OnInit, OnDestroy, PLATFORM_ID, Inject, ChangeDetectorRef } from '@angular/core';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { ApiService, DebrisOut } from '../../services/api.service';
import { CollectOverlayComponent } from '../collect-overlay/collect-overlay';

const RADIUS_KM = 12;
const POST_LOCATION_MIN_INTERVAL_MS = 30_000;
const POST_LOCATION_MIN_DISTANCE_M = 50;
const COLLECT_RADIUS_M = 100;

@Component({
  selector: 'app-map',
  standalone: true,
  imports: [CommonModule, CollectOverlayComponent],
  templateUrl: './map.html',
  styleUrl: './map.scss'
})
export class Map implements OnInit, OnDestroy {
  latitude: number | null = null;
  longitude: number | null = null;
  errorMsg: string | null = null;
  statusMsg: string | null = null;
  refreshing = false;
  debrisCount = 0;

  showCollectOverlay = false;
  activeReservationId: number | null = null;
  activeClusterCenterLat: number | null = null;
  activeClusterCenterLon: number | null = null;
  activeClusterEcoPoints = 0;

  private map: any;
  private userMarker: any;
  private debrisLayer: any;
  private L: any;
  private watchId: number | null = null;
  private debris: DebrisOut[] = [];

  private lastPostedAt = 0;
  private lastPostedLat: number | null = null;
  private lastPostedLon: number | null = null;
  private debrisLoaded = false;

  constructor(
    @Inject(PLATFORM_ID) private platformId: Object,
    private cdr: ChangeDetectorRef,
    private api: ApiService
  ) {}

  async ngOnInit() {
    if (!isPlatformBrowser(this.platformId)) return;

    const L = await import('leaflet');
    this.L = L;

    this.map = L.map('map-container').setView([51.505, -0.09], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(this.map);

    this.debrisLayer = L.layerGroup().addTo(this.map);

    if ('geolocation' in navigator) {
      this.watchId = navigator.geolocation.watchPosition(
        (pos) => this.onPosition(pos),
        (err) => { this.errorMsg = `Geolocation error: ${err.message}`; this.cdr.detectChanges(); },
        { enableHighAccuracy: true, timeout: 5000, maximumAge: 0 }
      );
    } else {
      this.errorMsg = 'Geolocation is not supported by your browser.';
      this.cdr.detectChanges();
    }
  }

  private onPosition(position: GeolocationPosition) {
    const lat = position.coords.latitude;
    const lon = position.coords.longitude;
    this.latitude = lat;
    this.longitude = lon;
    this.errorMsg = null;

    const latlng: [number, number] = [lat, lon];
    this.map.setView(latlng, 13);

    if (!this.userMarker) {
      const icon = this.L.icon({
        iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
        iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
        shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
        iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34], shadowSize: [41, 41]
      });
      this.userMarker = this.L.marker(latlng, { icon }).addTo(this.map);
    } else {
      this.userMarker.setLatLng(latlng);
    }

    this.maybePostLocation(lat, lon);

    if (!this.debrisLoaded) {
      this.debrisLoaded = true;
      this.loadDebris();
    } else {
      // Re-render to update Collect button proximity state
      this.renderDebris(this.debris);
    }

    this.cdr.detectChanges();
  }

  private maybePostLocation(lat: number, lon: number) {
    const now = Date.now();
    const movedFar =
      this.lastPostedLat === null || this.lastPostedLon === null ||
      this.haversineMeters(this.lastPostedLat, this.lastPostedLon, lat, lon) > POST_LOCATION_MIN_DISTANCE_M;

    if (now - this.lastPostedAt < POST_LOCATION_MIN_INTERVAL_MS && !movedFar) return;
    this.lastPostedAt = now;
    this.lastPostedLat = lat;
    this.lastPostedLon = lon;

    this.api.postLocation(lat, lon).subscribe({ error: (err: HttpErrorResponse) => console.warn('postLocation failed', err) });
  }

  loadDebris() {
    this.api.getDebris(RADIUS_KM).subscribe({
      next: (items) => { this.debris = items; this.renderDebris(items); },
      error: (err: HttpErrorResponse) => {
        if (err.status !== 401) {
          this.statusMsg = err.error?.detail || 'Could not load debris';
          this.cdr.detectChanges();
        }
      }
    });
  }

  refreshSatellite() {
    if (this.refreshing || this.latitude === null || this.longitude === null) return;
    this.refreshing = true;
    this.statusMsg = 'Scanning satellite imagery...';
    this.cdr.detectChanges();

    this.api.refreshSatellite(RADIUS_KM).subscribe({
      next: (res) => {
        this.refreshing = false;
        this.statusMsg = `Scan complete: ${res.inserted} new debris.`;
        this.loadDebris();
        this.cdr.detectChanges();
      },
      error: (err: HttpErrorResponse) => {
        this.refreshing = false;
        this.statusMsg = `Scan failed: ${err.error?.detail || err.message}`;
        this.cdr.detectChanges();
      }
    });
  }

  private renderDebris(items: DebrisOut[]) {
    this.debrisLayer.clearLayers();

    for (const d of items) {
      const color = d.is_reserved ? '#f59e0b' : (d.size_category === 'large' ? '#ef4444' : d.size_category === 'medium' ? '#f97316' : '#3b82f6');
      const icon = this.L.divIcon({
        className: '',
        html: `<div style="width:14px;height:14px;border-radius:50%;background:${color};border:2px solid white;box-shadow:0 1px 4px rgba(0,0,0,0.4)"></div>`,
        iconSize: [14, 14],
        iconAnchor: [7, 7],
      });

      const nearEnough = this.latitude !== null && this.longitude !== null &&
        this.haversineMeters(this.latitude, this.longitude, d.latitude, d.longitude) <= COLLECT_RADIUS_M;

      let popupHtml = `<b>${d.size_category} cluster</b><br>${d.source_point_count} point(s)<br>🌿 ${d.eco_points} eco points`;

      if (d.is_reserved && d.reservation_id !== null) {
        const btnDisabled = nearEnough ? '' : 'disabled';
        const btnTitle = nearEnough ? '' : 'title="Get within 100m to collect"';
        popupHtml += `<br><br><button ${btnDisabled} ${btnTitle} onclick="window._collectCluster(${d.reservation_id}, ${d.latitude}, ${d.longitude}, ${d.eco_points})" style="padding:4px 10px;background:#10b981;color:white;border:none;border-radius:4px;cursor:pointer;${btnDisabled ? 'opacity:0.5;cursor:not-allowed' : ''}">Collect</button>`;
      } else {
        popupHtml += `<br><br><button onclick="window._reserveCluster('${d.id}', ${JSON.stringify(d.source_point_ids)}, ${d.latitude}, ${d.longitude}, ${d.eco_points})" style="padding:4px 10px;background:#3b82f6;color:white;border:none;border-radius:4px;cursor:pointer">Reserve</button>`;
      }

      this.L.marker([d.latitude, d.longitude], { icon })
        .bindPopup(popupHtml)
        .addTo(this.debrisLayer);
    }

    // Expose actions to popup button onclick handlers
    (window as any)._reserveCluster = (clusterId: string, pointIds: number[], lat: number, lon: number, eco: number) => {
      this.onReserve(clusterId, pointIds, lat, lon, eco);
    };
    (window as any)._collectCluster = (reservationId: number, lat: number, lon: number, eco: number) => {
      this.onCollect(reservationId, lat, lon, eco);
    };

    this.debrisCount = items.length;
    this.cdr.detectChanges();
  }

  onReserve(clusterId: string, pointIds: number[], centerLat: number, centerLon: number, ecoPoints: number) {
    this.api.reserveCluster(pointIds, centerLat, centerLon, ecoPoints).subscribe({
      next: (res) => {
        this.statusMsg = `Reserved! You have 24h to collect.`;
        this.activeReservationId = res.reservation_id;
        this.activeClusterCenterLat = centerLat;
        this.activeClusterCenterLon = centerLon;
        this.activeClusterEcoPoints = ecoPoints;
        this.loadDebris();
      },
      error: (err: HttpErrorResponse) => {
        this.statusMsg = err.error?.detail || 'Could not reserve';
        this.cdr.detectChanges();
      }
    });
  }

  onCollect(reservationId: number, centerLat: number, centerLon: number, ecoPoints: number) {
    this.activeReservationId = reservationId;
    this.activeClusterCenterLat = centerLat;
    this.activeClusterCenterLon = centerLon;
    this.activeClusterEcoPoints = ecoPoints;
    this.showCollectOverlay = true;
    this.cdr.detectChanges();
  }

  onOverlayClosed() {
    this.showCollectOverlay = false;
    this.cdr.detectChanges();
  }

  onOverlayCollected() {
    this.showCollectOverlay = false;
    this.activeReservationId = null;
    this.loadDebris();
    this.cdr.detectChanges();
  }

  private haversineMeters(lat1: number, lon1: number, lat2: number, lon2: number): number {
    const R = 6371000;
    const toRad = (d: number) => d * Math.PI / 180;
    const dLat = toRad(lat2 - lat1);
    const dLon = toRad(lon2 - lon1);
    const a = Math.sin(dLat / 2) ** 2 + Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
    return 2 * R * Math.asin(Math.sqrt(a));
  }

  ngOnDestroy() {
    if (isPlatformBrowser(this.platformId)) {
      if (this.watchId !== null) navigator.geolocation.clearWatch(this.watchId);
      if (this.map) this.map.remove();
      delete (window as any)._reserveCluster;
      delete (window as any)._collectCluster;
    }
  }
}
```

- [ ] **Step 2: Update `frontend/src/app/components/map/map.html`**

```html
<div class="map-wrapper">
  <div id="map-container"></div>
  <div class="info-overlay">
    <h2>Current Location</h2>
    @if (errorMsg) {
      <div class="error">{{ errorMsg }}</div>
    } @else if (latitude !== null && longitude !== null) {
      <p>Lat: {{ latitude | number:'1.4-4' }}</p>
      <p>Lng: {{ longitude | number:'1.4-4' }}</p>
      <p>Debris nearby (12 km): {{ debrisCount }}</p>
      <button type="button" (click)="refreshSatellite()" [disabled]="refreshing">
        {{ refreshing ? 'Scanning...' : 'Refresh satellite scan' }}
      </button>
      @if (statusMsg) {
        <p class="status">{{ statusMsg }}</p>
      }
    } @else {
      <p>Locating...</p>
    }
  </div>

  @if (showCollectOverlay && activeReservationId !== null && activeClusterCenterLat !== null && activeClusterCenterLon !== null) {
    <app-collect-overlay
      [reservationId]="activeReservationId"
      [centerLat]="activeClusterCenterLat"
      [centerLon]="activeClusterCenterLon"
      [ecoPoints]="activeClusterEcoPoints"
      (closed)="onOverlayClosed()"
      (collected)="onOverlayCollected()">
    </app-collect-overlay>
  }
</div>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/app/components/map/map.ts frontend/src/app/components/map/map.html
git commit -m "feat: map shows cluster popups with reserve/collect actions"
```

---

### Task 9: Frontend — CollectOverlay component

**Goal:** Full-screen overlay for photo upload. Shows loading, result messages, retry counts. Emits `collected` on ML pass, `closed` on dismiss or release.

**Files:**
- Create: `frontend/src/app/components/collect-overlay/collect-overlay.ts`
- Create: `frontend/src/app/components/collect-overlay/collect-overlay.html`

**Acceptance Criteria:**
- [ ] File input accepts image files only
- [ ] Submitting sends photo to `collectCluster` API
- [ ] Shows "X attempts remaining" on ML fail
- [ ] Shows "Reservation released" on 3rd fail, emits `closed`
- [ ] Shows success message and emits `collected` on ML pass
- [ ] "Cancel" button releases reservation and emits `closed`

**Verify:** `cd frontend && ng build --configuration development 2>&1 | tail -5` → `Application bundle generation complete.`

**Steps:**

- [ ] **Step 1: Create `frontend/src/app/components/collect-overlay/collect-overlay.ts`**

```typescript
import { Component, Input, Output, EventEmitter, ChangeDetectorRef, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { ApiService } from '../../services/api.service';

type OverlayState = 'idle' | 'loading' | 'fail' | 'released' | 'success';

@Component({
  selector: 'app-collect-overlay',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './collect-overlay.html',
})
export class CollectOverlayComponent {
  @Input() reservationId!: number;
  @Input() centerLat!: number;
  @Input() centerLon!: number;
  @Input() ecoPoints!: number;
  @Output() closed = new EventEmitter<void>();
  @Output() collected = new EventEmitter<void>();

  @ViewChild('fileInput') fileInput!: ElementRef<HTMLInputElement>;

  state: OverlayState = 'idle';
  message = '';
  selectedFile: File | null = null;
  previewUrl: string | null = null;

  constructor(private api: ApiService, private cdr: ChangeDetectorRef) {}

  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    if (!input.files?.length) return;
    this.selectedFile = input.files[0];
    const reader = new FileReader();
    reader.onload = (e) => { this.previewUrl = e.target?.result as string; this.cdr.detectChanges(); };
    reader.readAsDataURL(this.selectedFile);
  }

  submit() {
    if (!this.selectedFile || this.state === 'loading') return;
    this.state = 'loading';
    this.cdr.detectChanges();

    this.api.collectCluster(this.reservationId, this.selectedFile).subscribe({
      next: (res) => {
        this.state = 'success';
        this.message = res.message;
        this.cdr.detectChanges();
        setTimeout(() => this.collected.emit(), 1800);
      },
      error: (err: HttpErrorResponse) => {
        const detail: string = err.error?.detail || 'Verification failed. Please retry.';
        if (detail.includes('released') || detail.includes('3 attempt')) {
          this.state = 'released';
          this.message = detail;
          this.cdr.detectChanges();
          setTimeout(() => this.closed.emit(), 2500);
        } else {
          this.state = 'fail';
          this.message = detail;
          this.selectedFile = null;
          this.previewUrl = null;
          this.cdr.detectChanges();
        }
      }
    });
  }

  cancel() {
    this.api.releaseReservation(this.reservationId).subscribe({
      complete: () => this.closed.emit(),
      error: () => this.closed.emit(),
    });
  }
}
```

- [ ] **Step 2: Create `frontend/src/app/components/collect-overlay/collect-overlay.html`**

```html
<div style="position:fixed;inset:0;background:rgba(0,0,0,0.75);z-index:2000;display:flex;align-items:center;justify-content:center">
  <div style="background:white;border-radius:16px;padding:32px;max-width:400px;width:90%;text-align:center;box-shadow:0 20px 60px rgba(0,0,0,0.3)">

    @if (state === 'loading') {
      <p style="font-size:1.1rem;color:#6b7280">Analyzing photo...</p>
      <div style="margin:16px auto;width:40px;height:40px;border:4px solid #e5e7eb;border-top-color:#10b981;border-radius:50%;animation:spin 0.8s linear infinite"></div>
    }

    @if (state === 'success') {
      <div style="font-size:2rem">✅</div>
      <p style="color:#10b981;font-weight:600">{{ message }}</p>
    }

    @if (state === 'released') {
      <div style="font-size:2rem">❌</div>
      <p style="color:#ef4444">{{ message }}</p>
    }

    @if (state === 'idle' || state === 'fail') {
      <h3 style="margin:0 0 8px 0;color:#111827">Photograph the debris</h3>
      <p style="color:#6b7280;font-size:0.9rem;margin:0 0 20px 0">Take or upload a clear photo showing the debris.</p>

      @if (state === 'fail') {
        <p style="color:#ef4444;font-size:0.9rem;margin-bottom:16px">{{ message }}</p>
      }

      @if (previewUrl) {
        <img [src]="previewUrl" alt="Preview" style="width:100%;max-height:200px;object-fit:cover;border-radius:8px;margin-bottom:16px">
      }

      <input #fileInput type="file" accept="image/jpeg,image/png,image/webp" (change)="onFileSelected($event)"
        style="display:block;width:100%;margin-bottom:16px;font-size:0.9rem">

      <button (click)="submit()" [disabled]="!selectedFile"
        style="width:100%;padding:12px;background:#10b981;color:white;border:none;border-radius:8px;font-size:1rem;cursor:pointer;margin-bottom:10px;opacity:{{selectedFile ? '1' : '0.5'}}">
        Submit Photo
      </button>

      <button (click)="cancel()"
        style="width:100%;padding:10px;background:transparent;color:#6b7280;border:1px solid #d1d5db;border-radius:8px;font-size:0.9rem;cursor:pointer">
        Cancel reservation
      </button>
    }
  </div>
</div>

<style>
  @keyframes spin { to { transform: rotate(360deg); } }
</style>
```

- [ ] **Step 3: Build to verify no TS/template errors**

```bash
cd frontend && ng build --configuration development 2>&1 | tail -10
```
Expected: `Application bundle generation complete.`

- [ ] **Step 4: Start dev server and verify flow manually**

```bash
cd frontend && ng serve &
```

Open `http://localhost:4200`. Log in, go to map. Verify:
1. Debris clusters render as colored dots
2. Clicking a cluster shows popup with "Reserve" button
3. Clicking Reserve shows "Reserved!" status message
4. Reserved cluster turns amber/yellow
5. Clicking the amber cluster shows "Collect" button (disabled if far, enabled if nearby)
6. Clicking Collect opens the photo overlay
7. Upload a photo — check network tab for `/api/clusters/{id}/collect` call

```bash
kill %1 2>/dev/null; true
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/app/components/collect-overlay/
git commit -m "feat: CollectOverlay component for photo upload and ML verification"
```

---

## Self-review checklist

- [x] **Spec coverage:** All spec sections covered: reservation table (Task 1), reserve/release endpoints (Task 2), collect+ML+proximity (Task 3), expiry job (Task 4), debris filter (Task 5), sentinel verify (Task 6), frontend API (Task 7), map markers+reserve (Task 8), photo overlay (Task 9)
- [x] **One active reservation per user:** Enforced in `_reserve_cluster` (Task 2) — 409 if user has active reservation
- [x] **Proximity check:** Both client-side in map.ts and server-side in collect endpoint
- [x] **3 attempt limit:** `MAX_ATTEMPTS = 3`, reservation set to failed, is_reserved cleared (Task 3)
- [x] **Expiry notification:** APScheduler sends Notification on expiry (Task 4)
- [x] **Eco points timing:** Awarded only in `verify_collected_debris` after sentinel confirms (Task 6)
- [x] **Debris hidden from everyone after photo-verified:** `is_reserved=True` + `is_collected=True` → filtered out of all queries (Task 5)
- [x] **Type consistency:** `DebrisOut.id` is `str` in both backend schema and frontend interface; `source_point_ids` is `List[int]`/`number[]` throughout; `reservation_id` is `Optional[int]`/`number | null`
