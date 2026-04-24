from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, cast
from geoalchemy2.functions import ST_AsText
from geoalchemy2.types import Geography
from geoalchemy2.elements import WKTElement
from typing import Optional
from datetime import datetime, timezone

from app.db.session import get_db
from app.db.models import PlasticDebris, User
from app.api.deps import get_current_user
from app.schemas.plastic import PlasticReportCreate

router = APIRouter()

@router.get("/")
def get_all_plastic_debris(
    skip: int = 0, 
    limit: int = 100, 
    lat: Optional[float] = None, 
    lon: Optional[float] = None, 
    radius_m: Optional[float] = None, 
    db: Session = Depends(get_db)
):
    """
    Returnează deșeurile de plastic. Suportă paginație (skip, limit) 
    și filtrare spațială opțională (lat, lon, radius_m).
    """
    query = db.query(
        PlasticDebris.id,
        ST_AsText(PlasticDebris.geom).label("coordinates"),
        PlasticDebris.size_category,
        PlasticDebris.detected_at,
        PlasticDebris.is_collected,
        PlasticDebris.is_verified,
        PlasticDebris.eco_points
    )

    # Filtrare Spațială
    if lat is not None and lon is not None and radius_m is not None:
        point = WKTElement(f"SRID=4326;POINT({lon} {lat})")
        # ST_DWithin convertit la Geography compară în METRI
        query = query.filter(func.ST_DWithin(cast(PlasticDebris.geom, Geography), cast(point, Geography), radius_m))

    results = query.offset(skip).limit(limit).all()
    
    return [
        {
            "id": r.id,
            "coordinates": r.coordinates,
            "size_category": r.size_category,
            "detected_at": r.detected_at,
            "is_collected": r.is_collected,
            "is_verified": r.is_verified,
            "eco_points": r.eco_points
        } for r in results
    ]

@router.delete("/{debris_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plastic_debris(
    debris_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Șterge un deșeu de plastic din baza de date după ID-ul său.
    Necesită autentificare (Token JWT valabil).
    """
    debris = db.query(PlasticDebris).filter(PlasticDebris.id == debris_id).first()
    if not debris:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Deșeul de plastic nu a fost găsit."
        )
        
    db.delete(debris)
    db.commit()
    return None

@router.post("/report", status_code=status.HTTP_201_CREATED)
def report_plastic_debris(
    report: PlasticReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Raportează manual un deșeu găsit pe plajă. 
    Se apelează de obicei după ce poza e verificată de `/api/classify`.
    """
    point = WKTElement(f"SRID=4326;POINT({report.lon} {report.lat})")
    debris = PlasticDebris(
        geom=point,
        size_category="beach",
        detected_at=datetime.now(timezone.utc),
        is_collected=False,
        is_verified=False,
        eco_points=10
    )
    db.add(debris)
    db.commit()
    db.refresh(debris)
    return {"message": "Deșeu raportat pe plajă. Așteaptă colectarea de personal autorizat.", "debris_id": debris.id}

@router.post("/{debris_id}/collect")
def collect_plastic_debris(
    debris_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Marchează un deșeu ca fiind colectat de către utilizatorul curent.
    - Pe plajă (beach): doar utilizatorii autorizați pot strânge, primesc puncte instant.
    - Ocean: oricine poate strânge, punctele se primesc DUPĂ verificarea prin satelit.
    """
    debris = db.query(PlasticDebris).filter(PlasticDebris.id == debris_id).first()
    if not debris:
        raise HTTPException(status_code=404, detail="Deșeul nu a fost găsit.")
    
    if debris.is_collected and debris.is_verified:
        raise HTTPException(status_code=400, detail="Acest deșeu a fost deja colectat și validat.")

    # 1. Reguli pentru Plajă
    if debris.size_category == "beach":
        if not current_user.is_authorized:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Doar personalul autorizat poate colecta deșeuri de pe plajă."
            )
        
        debris.is_collected = True
        debris.is_verified = True
        debris.collected_by = current_user.id
        debris.collected_at = datetime.now(timezone.utc)
        
        # Acordăm punctele instant
        current_user.eco_points += debris.eco_points
        db.commit()
        return {"message": f"Colectare reușită (personal autorizat)! Ai primit {debris.eco_points} puncte."}
    
    # 2. Reguli pentru Ocean
    else:
        debris.is_collected = True
        debris.collected_by = current_user.id
        debris.collected_at = datetime.now(timezone.utc)
        # NU setăm is_verified și NU acordăm punctele încă! Satelitul va decide.
        db.commit()
        return {
            "message": "Deșeu din ocean marcat ca și colectat. "
                       "Punctele se vor acorda DUPĂ verificarea independentă prin satelit."
        }
