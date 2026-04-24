from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from geoalchemy2.functions import ST_AsText

from app.db.session import get_db
from app.db.models import PlasticDebris, User
from app.api.deps import get_current_user

router = APIRouter()

@router.get("/")
def get_all_plastic_debris(db: Session = Depends(get_db)):
    """
    Returnează toate deșeurile de plastic (inclusiv coordonatele extrase de Sentinel) 
    din baza de date pentru a le vizualiza în Swagger.
    """
    # Folosim ST_AsText pentru a converti formatul binar PostGIS (WKB) 
    # într-un text lizibil de tipul "POINT(lon lat)"
    results = db.query(
        PlasticDebris.id,
        ST_AsText(PlasticDebris.geom).label("coordinates"),
        PlasticDebris.size_category,
        PlasticDebris.detected_at,
        PlasticDebris.is_collected,
        PlasticDebris.eco_points
    ).all()
    
    return [
        {
            "id": r.id,
            "coordinates": r.coordinates,
            "size_category": r.size_category,
            "detected_at": r.detected_at,
            "is_collected": r.is_collected,
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
