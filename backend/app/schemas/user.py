# Clase Pydantic pentru validarea datelor despre utilizatori.

from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    eco_points: int
    is_active: bool
    is_authorized: bool
    latitude: float | None = None
    longitude: float | None = None

    class Config:
        from_attributes = True


class LocationIn(BaseModel):
    latitude: float
    longitude: float

    @field_validator("latitude")
    @classmethod
    def _check_lat(cls, v: float) -> float:
        if not -90.0 <= v <= 90.0:
            raise ValueError("latitude must be between -90 and 90")
        return v

    @field_validator("longitude")
    @classmethod
    def _check_lon(cls, v: float) -> float:
        if not -180.0 <= v <= 180.0:
            raise ValueError("longitude must be between -180 and 180")
        return v


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class DebrisOut(BaseModel):
    id: str
    latitude: float
    longitude: float
    size_category: str
    is_collected: bool
    is_verified: bool
    eco_points: int
    source_point_ids: List[int]
    source_point_count: int
    radius_m: float
    is_reserved: bool
    reservation_id: Optional[int]

    class Config:
        from_attributes = True

class ReservationOut(BaseModel):
    reservation_id: int
    point_ids: List[int]
    cluster_center_lat: float
    cluster_center_lon: float
    eco_points: int
    reserved_until: str
    status: str

    class Config:
        from_attributes = True
