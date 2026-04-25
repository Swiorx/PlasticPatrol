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
    is_reserved = Column(Boolean, default=False, nullable=False)
    collected_by = Column(Integer, default=None)
    collected_at = Column(DateTime, default=None)
    eco_points = Column(Integer, default=0)


class ClusterReservation(Base):
    __tablename__ = "cluster_reservations"

    id = Column(Integer, primary_key=True, index=True)
    point_ids = Column(JSON, nullable=False)
    cluster_center_lat = Column(Float, nullable=False)
    cluster_center_lon = Column(Float, nullable=False)
    eco_points = Column(Integer, nullable=False)
    reserved_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    reserved_until = Column(DateTime, nullable=False)
    attempt_count = Column(Integer, default=0, nullable=False)
    status = Column(String, default="reserved", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
