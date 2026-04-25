from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status, Response, Body
from sqlalchemy.orm import Session
from sqlalchemy import func, cast
from geoalchemy2.functions import ST_AsText
from geoalchemy2.types import Geography
from geoalchemy2.elements import WKTElement
from typing import Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import subprocess
import sys
import json
import time
import os
from pathlib import Path

from app.db.session import get_db
from app.db.models import PlasticDebris, User, Notification
from app.api.deps import get_current_user
from app.schemas.plastic import PlasticReportCreate

# Rate limiting simplu in-memory (per user_id -> timestamp ultimei acțiuni)
_rate_limit_store: dict = {}
RATE_LIMIT_SECONDS = 5  # Minim 5 secunde între acțiuni critice

def check_rate_limit(user_id: int, action: str = "default"):
    key = f"{user_id}:{action}"
    now = time.time()
    last = _rate_limit_store.get(key, 0)
    if now - last < RATE_LIMIT_SECONDS:
        raise HTTPException(
            status_code=429,
            detail=f"Prea multe cereri. Așteaptă {RATE_LIMIT_SECONDS} secunde între acțiuni."
        )
    _rate_limit_store[key] = now

router = APIRouter()


class SatelliteScanOptions(BaseModel):
    use_preset_locations: bool = Field(
        default=True,
        description="Folosește preset-uri geografice (true) sau SENTINEL_BBOX custom (false).",
    )
    preset_location_set: str = Field(
        default="world_hotspots",
        description="Setul preset de locații. Exemple: world_hotspots, constanta_only.",
    )
    target_resolution_meters: float = Field(
        default=10,
        ge=1,
        le=1000,
        description="Rezoluția țintă în metri/pixel. 10 păstrează calitate mare.",
    )
    min_component_pixels: int = Field(
        default=12,
        ge=1,
        le=100000,
        description="Filtru anti-zgomot: elimină componentele prea mici.",
    )
    max_relevant_points: int = Field(
        default=1200,
        ge=1,
        le=1000000,
        description="Limită pentru punctele candidate trimise în DB.",
    )
    max_grid_dimension: int = Field(
        default=2500,
        ge=128,
        le=12000,
        description="Limită de siguranță pentru dimensiunea rasterului per regiune.",
    )
    use_mock_data: Optional[bool] = Field(
        default=None,
        description="Forțează mock data (true/false). Dacă e null, decide automat după credențiale.",
    )

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
    Validare: coordonatele trebuie să fie pe suprafața Pământului.
    """
    check_rate_limit(current_user.id, "report")

    # Validare coordonate
    if not (-90 <= report.lat <= 90):
        raise HTTPException(status_code=422, detail="Latitudinea trebuie să fie între -90 și 90.")
    if not (-180 <= report.lon <= 180):
        raise HTTPException(status_code=422, detail="Longitudinea trebuie să fie între -180 și 180.")

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
    check_rate_limit(current_user.id, "collect")

    debris = db.query(PlasticDebris).filter(PlasticDebris.id == debris_id).first()
    if not debris:
        raise HTTPException(status_code=404, detail="Deșeul nu a fost găsit.")
    
    if debris.is_collected and debris.is_verified:
        raise HTTPException(status_code=400, detail="Acest deșeu a fost deja colectat și validat.")

    # 1. Reguli pentru Plajă → DOAR personal autorizat
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
        
        # Acordăm punctele instant (personal autorizat = încredere imediată)
        current_user.eco_points += debris.eco_points

        # Notificăm utilizatorul
        notif = Notification(
            user_id=current_user.id,
            message=f"🏦 Colectare plajă confirmată! Ai primit {debris.eco_points} puncte eco."
        )
        db.add(notif)
        db.commit()
        return {"message": f"Colectare reușită (personal autorizat)! Ai primit {debris.eco_points} puncte."}
    
    # 2. Reguli pentru Ocean → ORICINE poate colecta
    else:
        debris.is_collected = True
        debris.collected_by = current_user.id
        debris.collected_at = datetime.now(timezone.utc)

        # Notificăm utilizatorul că așteaptă verificare
        notif = Notification(
            user_id=current_user.id,
            message=f"🛰️ Deșeul #{debris_id} a fost marcat ca și colectat. Așteaptă confirmarea satelitului pentru puncte."
        )
        db.add(notif)
        db.commit()
        return {
            "message": "Deșeu din ocean marcat ca și colectat. "
                       "Punctele se vor acorda DUPĂ verificarea independentă prin satelit."
        }

@router.delete("/all/clear", status_code=status.HTTP_204_NO_CONTENT)
def delete_all_plastic_debris(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    [BUTON ADMIN] Șterge ABSOLUT TOATE deșeurile de plastic din baza de date.
    Atenție: Acțiune ireversibilă! Doar utilizatorii autentificați o pot rula.
    """
    db.query(PlasticDebris).delete()
    db.commit()
    return None

@router.post("/scan/start", status_code=status.HTTP_202_ACCEPTED)
def trigger_satellite_scan(
    background_tasks: BackgroundTasks,
    scan_options: SatelliteScanOptions = Body(default_factory=SatelliteScanOptions),
    current_user: User = Depends(get_current_user)
):
    """
    [BUTON ADMIN] Pornește scanarea din satelit (sentinel_fetcher.py) ca sub-proces.
    Scriptul rulează în fundal, independent de serverul FastAPI.

    Dacă credențialele Sentinel Hub nu sunt configurate, se folosesc
    automat date mock (simulate) pentru testare.

    Parametrii de scanare se trimit din Swagger body și sunt mapați pe
    variabilele de mediu ale scriptului `sentinel_fetcher.py`.
    """
    check_rate_limit(current_user.id, "scan")

    project_root = Path(__file__).resolve().parents[4]
    script_path = project_root / "data_pipeline" / "sentinel_fetcher.py"
    log_path = project_root / "backend" / "logs" / "sentinel_scan.log"
    conda_prefix = os.getenv("SENTINEL_CONDA_PREFIX", str(project_root / ".conda"))
    conda_exe = os.getenv("SENTINEL_CONDA_EXE", "/home/rares/anaconda3/bin/conda")

    if not script_path.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Nu găsesc scriptul de scanare: {script_path}",
        )

    # Copiem env-ul curent și forțăm mock dacă nu avem credențiale SH
    env = {**os.environ}
    env.update(
        {
            "USE_PRESET_LOCATIONS": "true" if scan_options.use_preset_locations else "false",
            "PRESET_LOCATION_SET": scan_options.preset_location_set,
            "TARGET_RESOLUTION_METERS": str(scan_options.target_resolution_meters),
            "MIN_COMPONENT_PIXELS": str(scan_options.min_component_pixels),
            "MAX_RELEVANT_POINTS": str(scan_options.max_relevant_points),
            "MAX_GRID_DIMENSION": str(scan_options.max_grid_dimension),
        }
    )

    sh_id = os.getenv("SH_CLIENT_ID", os.getenv("SENTINEL_HUB_CLIENT_ID", ""))
    sh_secret = os.getenv("SH_CLIENT_SECRET", os.getenv("SENTINEL_HUB_CLIENT_SECRET", ""))
    if scan_options.use_mock_data is not None:
        env["USE_MOCK_DATA"] = "1" if scan_options.use_mock_data else "0"
    elif not sh_id or not sh_secret:
        env["USE_MOCK_DATA"] = "1"

    if Path(conda_exe).exists() and Path(conda_prefix).exists():
        command = [conda_exe, "run", "-p", conda_prefix, "python", str(script_path)]
    else:
        # Fallback la interpreterul curent dacă conda nu e disponibil.
        command = [sys.executable, str(script_path)]

    def run_scan():
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(
                f"\n[{datetime.now(timezone.utc).isoformat()}] Starting sentinel scan. "
                f"command={' '.join(command)}\n"
            )
            log_file.flush()
            subprocess.Popen(
                command,
                cwd=str(project_root),
                env=env,
                stdout=log_file,
                stderr=log_file,
            )

    background_tasks.add_task(run_scan)

    mock_note = " (MOD MOCK - fără credențiale Sentinel)" if env.get("USE_MOCK_DATA") == "1" else ""

    return {
        "message": f"Comanda a fost trimisă cu succes către satelit{mock_note}! "
                   "Scanarea rulează acum în fundal. Dă un refresh la lista de plastic "
                   "în câteva minute pentru a vedea noile rezultate.",
        "effective_scan_options": {
            "USE_PRESET_LOCATIONS": env["USE_PRESET_LOCATIONS"],
            "PRESET_LOCATION_SET": env["PRESET_LOCATION_SET"],
            "TARGET_RESOLUTION_METERS": env["TARGET_RESOLUTION_METERS"],
            "MIN_COMPONENT_PIXELS": env["MIN_COMPONENT_PIXELS"],
            "MAX_RELEVANT_POINTS": env["MAX_RELEVANT_POINTS"],
            "MAX_GRID_DIMENSION": env["MAX_GRID_DIMENSION"],
            "USE_MOCK_DATA": env.get("USE_MOCK_DATA", "0"),
            "runner": "conda" if command[0] == conda_exe else "python",
            "scan_log": str(log_path),
        }
    }

@router.get("/export/geojson")
def export_geojson(db: Session = Depends(get_db)):
    """
    Exportă toate deșeurile de plastic în format GeoJSON.
    Fișierul poate fi importat în QGIS, Google Earth, sau orice hartă interactivă.
    """
    results = db.query(
        PlasticDebris.id,
        func.ST_X(PlasticDebris.geom).label("lon"),
        func.ST_Y(PlasticDebris.geom).label("lat"),
        PlasticDebris.size_category,
        PlasticDebris.detected_at,
        PlasticDebris.is_collected,
        PlasticDebris.is_verified,
        PlasticDebris.eco_points
    ).all()

    features = []
    for r in results:
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [r.lon, r.lat]
            },
            "properties": {
                "id": r.id,
                "size_category": r.size_category,
                "detected_at": r.detected_at.isoformat() if r.detected_at else None,
                "is_collected": r.is_collected,
                "is_verified": r.is_verified,
                "eco_points": r.eco_points
            }
        }
        features.append(feature)

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    return Response(
        content=json.dumps(geojson, ensure_ascii=False),
        media_type="application/geo+json",
        headers={"Content-Disposition": "attachment; filename=plastic_debris.geojson"}
    )
