from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    hashed_password = Column(String, nullable=False)
    eco_points = Column(Integer, default=0)
    

class PlasticDebris(Base):
    __tablename__ = "plastic_debris"

    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    size_category = Column(String, default="small") # ex: small, medium, large
    detected_at = Column(DateTime, default=datetime.now(datetime.timezone.utc))
    is_collected = Column(Boolean, default=False)
    collected_by = Column(Integer, default=None) # ID-ul userului care a colectat
    collected_at = Column(DateTime, default=None) # Data colectării
    eco_points = Column(Integer, default=0) # Punctele care ar trebui acordate pentru colectare
    
