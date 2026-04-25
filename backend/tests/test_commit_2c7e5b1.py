"""
Integration tests for commit 2c7e5b1:
  - auth (register auto-login, login)
  - per-user location (POST /me/location)
  - scoped debris fetch (GET /me/debris)
  - geo.py bbox_for_user unit tests
  - schema validators (LocationIn)
"""

import math
import uuid
import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# App import — must be done inside the backend/ directory context
# ---------------------------------------------------------------------------
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _unique(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _register(username=None, email=None, password="securepass1") -> dict:
    username = username or _unique("user")
    email = email or f"{_unique('e')}@test.com"
    r = client.post("/api/users/register", json={
        "username": username,
        "email": email,
        "password": password,
    })
    return r


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ===========================================================================
# 1. Registration
# ===========================================================================

class TestRegister:
    def test_register_returns_token_and_user(self):
        r = _register()
        assert r.status_code == 201, r.text
        body = r.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert "user" in body
        assert body["user"]["eco_points"] == 0

    def test_register_duplicate_email_fails(self):
        email = f"{_unique('dup')}@test.com"
        _register(email=email)
        r = _register(email=email)
        assert r.status_code == 400
        assert "Email" in r.json()["detail"] or "email" in r.json()["detail"].lower()

    def test_register_duplicate_username_fails(self):
        username = _unique("dupuser")
        _register(username=username)
        r = _register(username=username)
        assert r.status_code == 400

    def test_register_short_password_rejected(self):
        r = _register(password="short")
        assert r.status_code == 422

    def test_register_invalid_email_rejected(self):
        r = client.post("/api/users/register", json={
            "username": _unique("u"),
            "email": "not-an-email",
            "password": "validpassword",
        })
        assert r.status_code == 422


# ===========================================================================
# 2. Login
# ===========================================================================

class TestLogin:
    def test_login_with_email_returns_token(self):
        email = f"{_unique('login')}@test.com"
        _register(email=email, password="mypassword1")
        r = client.post("/api/users/login", data={"username": email, "password": "mypassword1"})
        assert r.status_code == 200, r.text
        body = r.json()
        assert "access_token" in body
        assert body["user"]["email"] == email

    def test_login_with_username_returns_token(self):
        username = _unique("loginuser")
        _register(username=username, password="mypassword2")
        r = client.post("/api/users/login", data={"username": username, "password": "mypassword2"})
        assert r.status_code == 200, r.text
        assert "access_token" in r.json()

    def test_login_wrong_password_rejected(self):
        email = f"{_unique('badpw')}@test.com"
        _register(email=email, password="correctpass")
        r = client.post("/api/users/login", data={"username": email, "password": "wrongpass"})
        assert r.status_code == 401

    def test_login_unknown_user_rejected(self):
        r = client.post("/api/users/login", data={"username": "nobody@nope.com", "password": "x"})
        assert r.status_code == 401


# ===========================================================================
# 3. GET /me
# ===========================================================================

class TestGetMe:
    def test_me_returns_profile(self):
        r = _register()
        token = r.json()["access_token"]
        me = client.get("/api/users/me", headers=_auth_header(token))
        assert me.status_code == 200, me.text
        body = me.json()
        assert "id" in body
        assert "username" in body
        assert body["latitude"] is None
        assert body["longitude"] is None

    def test_me_requires_auth(self):
        r = client.get("/api/users/me")
        assert r.status_code == 401


# ===========================================================================
# 4. POST /me/location
# ===========================================================================

class TestUpdateLocation:
    def setup_method(self):
        r = _register()
        self.token = r.json()["access_token"]

    def test_update_location_stores_coords(self):
        r = client.post(
            "/api/users/me/location",
            json={"latitude": 44.4268, "longitude": 26.1025},
            headers=_auth_header(self.token),
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["latitude"] == pytest.approx(44.4268, abs=1e-6)
        assert body["longitude"] == pytest.approx(26.1025, abs=1e-6)

    def test_update_location_invalid_lat(self):
        r = client.post(
            "/api/users/me/location",
            json={"latitude": 999.0, "longitude": 26.0},
            headers=_auth_header(self.token),
        )
        assert r.status_code == 422

    def test_update_location_invalid_lon(self):
        r = client.post(
            "/api/users/me/location",
            json={"latitude": 44.0, "longitude": -999.0},
            headers=_auth_header(self.token),
        )
        assert r.status_code == 422

    def test_update_location_requires_auth(self):
        r = client.post(
            "/api/users/me/location",
            json={"latitude": 44.0, "longitude": 26.0},
        )
        assert r.status_code == 401


# ===========================================================================
# 5. GET /me/debris
# ===========================================================================

class TestGetDebris:
    def setup_method(self):
        r = _register()
        self.token = r.json()["access_token"]

    def test_debris_without_location_returns_400(self):
        r = client.get("/api/users/me/debris", headers=_auth_header(self.token))
        assert r.status_code == 400
        assert "Location" in r.json()["detail"] or "location" in r.json()["detail"].lower()

    def test_debris_with_location_returns_list(self):
        client.post(
            "/api/users/me/location",
            json={"latitude": 6.42, "longitude": 3.45},
            headers=_auth_header(self.token),
        )
        r = client.get("/api/users/me/debris?radius_km=50", headers=_auth_header(self.token))
        assert r.status_code == 200, r.text
        assert isinstance(r.json(), list)

    def test_debris_radius_validation(self):
        client.post(
            "/api/users/me/location",
            json={"latitude": 0.0, "longitude": 0.0},
            headers=_auth_header(self.token),
        )
        r = client.get("/api/users/me/debris?radius_km=0.5", headers=_auth_header(self.token))
        assert r.status_code == 422

    def test_debris_requires_auth(self):
        r = client.get("/api/users/me/debris")
        assert r.status_code == 401


# ===========================================================================
# 6. POST /me/refresh-satellite (no-location guard)
# ===========================================================================

class TestRefreshSatellite:
    def setup_method(self):
        r = _register()
        self.token = r.json()["access_token"]

    def test_refresh_without_location_returns_400(self):
        r = client.post("/api/users/me/refresh-satellite", headers=_auth_header(self.token))
        assert r.status_code == 400

    def test_refresh_requires_auth(self):
        r = client.post("/api/users/me/refresh-satellite")
        assert r.status_code == 401


# ===========================================================================
# 7. Unit tests — services/geo.py  bbox_for_user
# ===========================================================================

from app.services.geo import bbox_for_user  # noqa: E402


class TestBboxForUser:
    def test_returns_four_values(self):
        result = bbox_for_user(44.0, 26.0)
        assert len(result) == 4

    def test_bbox_order_min_max(self):
        min_lon, min_lat, max_lon, max_lat = bbox_for_user(44.0, 26.0)
        assert min_lon < max_lon
        assert min_lat < max_lat

    def test_bbox_centered_on_user(self):
        lat, lon = 44.0, 26.0
        min_lon, min_lat, max_lon, max_lat = bbox_for_user(lat, lon, radius_km=10.0)
        center_lat = (min_lat + max_lat) / 2
        center_lon = (min_lon + max_lon) / 2
        assert abs(center_lat - lat) < 1e-6
        assert abs(center_lon - lon) < 1e-6

    def test_larger_radius_gives_larger_bbox(self):
        small = bbox_for_user(44.0, 26.0, radius_km=5.0)
        large = bbox_for_user(44.0, 26.0, radius_km=50.0)
        small_width = small[2] - small[0]
        large_width = large[2] - large[0]
        assert large_width > small_width

    def test_lat_clamped_at_poles(self):
        min_lon, min_lat, max_lon, max_lat = bbox_for_user(89.9, 0.0, radius_km=200.0)
        assert max_lat <= 90.0
        min_lon, min_lat, max_lon, max_lat = bbox_for_user(-89.9, 0.0, radius_km=200.0)
        assert min_lat >= -90.0

    def test_approx_radius_km_10_degrees(self):
        min_lon, min_lat, max_lon, max_lat = bbox_for_user(0.0, 0.0, radius_km=111.32)
        half_height = (max_lat - min_lat) / 2
        assert abs(half_height - 1.0) < 0.02


# ===========================================================================
# 8. Unit tests — schemas/user.py  LocationIn validators
# ===========================================================================

from app.schemas.user import LocationIn, UserCreate  # noqa: E402
from pydantic import ValidationError as PydanticValidationError


class TestLocationInSchema:
    def test_valid_coords_accepted(self):
        loc = LocationIn(latitude=44.4, longitude=26.1)
        assert loc.latitude == 44.4
        assert loc.longitude == 26.1

    def test_lat_above_90_rejected(self):
        with pytest.raises(PydanticValidationError):
            LocationIn(latitude=91.0, longitude=0.0)

    def test_lat_below_neg90_rejected(self):
        with pytest.raises(PydanticValidationError):
            LocationIn(latitude=-91.0, longitude=0.0)

    def test_lon_above_180_rejected(self):
        with pytest.raises(PydanticValidationError):
            LocationIn(latitude=0.0, longitude=181.0)

    def test_lon_below_neg180_rejected(self):
        with pytest.raises(PydanticValidationError):
            LocationIn(latitude=0.0, longitude=-181.0)

    def test_boundary_values_accepted(self):
        loc = LocationIn(latitude=90.0, longitude=180.0)
        assert loc.latitude == 90.0
        assert loc.longitude == 180.0
        loc2 = LocationIn(latitude=-90.0, longitude=-180.0)
        assert loc2.latitude == -90.0


class TestUserCreateSchema:
    def test_password_min_8_enforced(self):
        with pytest.raises(PydanticValidationError):
            UserCreate(username="abc", email="x@y.com", password="short")

    def test_valid_user_create(self):
        u = UserCreate(username="testuser", email="a@b.com", password="longpassword")
        assert u.username == "testuser"
