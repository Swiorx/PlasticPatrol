from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float
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
    is_authorized = Column(Boolean, default=False) # True pentru personal autorizat
    hashed_password = Column(String, nullable=False)
    eco_points = Column(Integer, default=0)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    last_location_at = Column(DateTime, nullable=True)


class PlasticDebris(Base):
    __tablename__ = "plastic_debris"

    id = Column(Integer, primary_key=True, index=True)
    geom = Column(Geometry(geometry_type='POINT', srid=4326), nullable=False)
    size_category = Column(String, default="small") # ex: small, medium, large, beach
    detected_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_collected = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False) # True dupa confirmarea satelitului
    collected_by = Column(Integer, default=None) # ID-ul userului care a colectat
    collected_at = Column(DateTime, default=None) # Data colectării
    eco_points = Column(Integer, default=0) # Punctele care ar trebui acordate pentru colectare


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
