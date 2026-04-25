import sys
from pathlib import Path

# Add project root to path so ml_classifier (sibling of backend/) is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timezone
from geoalchemy2.elements import WKTElement
from app.db.session import engine, get_db, SessionLocal
from app.db import models
from app.db.models import User, PlasticDebris, Notification
from app.db.migrations import run_startup_migrations
from app.core.security import get_password_hash
from app.api.routes import users, plastic
from app.api.routes.classifier import router as classifier_router
from app.api.routes.stats import router as stats_router
from app.api.routes.notifications import router as notifications_router
from app.api.routes.clusters import router as clusters_router

# Creăm tabelele în baza de date pe baza modelelor definite anterior
models.Base.metadata.create_all(bind=engine)

with SessionLocal() as _db:
    run_startup_migrations(_db)

tags_metadata = [
    {"name": "root", "description": "Endpoint principal"},
    {"name": "health", "description": "Verificarea stării de sănătate a API-ului"},
    {"name": "users", "description": "Înregistrare, autentificare, leaderboard"},
    {"name": "plastics", "description": "CRUD deșeuri de plastic, colectare, scanare satelit, export"},
    {"name": "classifier", "description": "Clasificare imagini cu ML (plastic vs. apă curată)"},
    {"name": "statistics", "description": "Dashboard cu statistici globale"},
    {"name": "notifications", "description": "Sistem de notificări per utilizator"},
    {"name": "seed", "description": "Populare baza de date cu date de test (DEV ONLY)"},
]

app = FastAPI(
    title="PlasticPatrol API",
    version="1.0.0",
    description="API pentru detectarea și colectarea deșeurilor de plastic din oceane și de pe plaje, "
                "cu verificare prin satelit Sentinel-2 și gamificare ecologică.\n\n"
                "## Pași pentru testare în Swagger:\n"
                "1. **POST /api/seed** → creează utilizatori și date de test\n"
                "2. **POST /api/users/login** → username: `admin`, password: `admin123` → copiază token-ul\n"
                "3. **Authorize** (butonul verde 🔒 de sus) → lipește token-ul\n"
                "4. Testează orice endpoint protejat!\n",
    openapi_tags=tags_metadata
)

# Permitem frontend-ului (Angular) să comunice cu acest API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(plastic.router, prefix="/api/plastics", tags=["plastics"])
app.include_router(classifier_router, prefix="/api")
app.include_router(stats_router, prefix="/api/stats", tags=["statistics"])
app.include_router(notifications_router, prefix="/api/notifications", tags=["notifications"])
app.include_router(clusters_router, prefix="/api/clusters", tags=["clusters"])

@app.get("/", tags=["root"])
def read_root():
    return {"message": "Welcome to PlasticPatrol API!"}

@app.get("/api/health", tags=["health"])
def health_check(db: Session = Depends(get_db)):
    """
    Verifică starea de sănătate a API-ului și a bazei de date.
    Returnează: versiunea API, statusul DB, și un timestamp.
    """
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "unhealthy"

    return {
        "status": "ok",
        "api_version": "1.0.0",
        "database": db_status,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.post("/api/seed", tags=["seed"])
def seed_database(db: Session = Depends(get_db)):
    """
    **[DEV ONLY]** Populează baza de date cu date de test:

    - 2 utilizatori: `admin` (autorizat) și `testuser` (normal), parola: `admin123`
    - 5 deșeuri de plastic în ocean (necolectate)
    - 2 deșeuri pe plajă (necolectate)
    - 1 notificare de bun venit

    **⚠️ Nu rulați în producție!** Poate crea duplicate dacă e apelat de mai multe ori.
    """
    # Verificăm dacă utilizatorii deja există
    existing_admin = db.query(User).filter(User.username == "admin").first()
    existing_test = db.query(User).filter(User.username == "testuser").first()

    admin_user = existing_admin
    test_user = existing_test

    if not existing_admin:
        admin_user = User(
            username="admin",
            email="admin@plasticpatrol.com",
            hashed_password=get_password_hash("admin123"),
            is_authorized=True,
            eco_points=0
        )
        db.add(admin_user)
        db.flush()

    if not existing_test:
        test_user = User(
            username="testuser",
            email="test@plasticpatrol.com",
            hashed_password=get_password_hash("admin123"),
            is_authorized=False,
            eco_points=0
        )
        db.add(test_user)
        db.flush()

    # Deșeuri ocean (zona Lagos / Gulf of Guinea)
    ocean_points = [
        (3.45, 6.42), (3.52, 6.38), (3.61, 6.50),
        (3.70, 6.55), (3.80, 6.45)
    ]
    for lon, lat in ocean_points:
        point = WKTElement(f"SRID=4326;POINT({lon} {lat})")
        debris = PlasticDebris(
            geom=point,
            size_category="small",
            detected_at=datetime.now(timezone.utc),
            is_collected=False,
            is_verified=False,
            eco_points=5
        )
        db.add(debris)

    # Deșeuri plajă
    beach_points = [(3.40, 6.44), (3.55, 6.41)]
    for lon, lat in beach_points:
        point = WKTElement(f"SRID=4326;POINT({lon} {lat})")
        debris = PlasticDebris(
            geom=point,
            size_category="beach",
            detected_at=datetime.now(timezone.utc),
            is_collected=False,
            is_verified=False,
            eco_points=10
        )
        db.add(debris)

    # Notificare de bun venit
    target_user = admin_user or test_user
    if target_user and target_user.id:
        notif = Notification(
            user_id=target_user.id,
            message="🌊 Bine ai venit pe PlasticPatrol! Începe să colectezi deșeuri pentru puncte eco."
        )
        db.add(notif)

    db.commit()

    return {
        "message": "Date de test create cu succes!",
        "users_created": {
            "admin": "admin / admin123 (autorizat)",
            "testuser": "testuser / admin123 (normal)"
        },
        "debris_created": {
            "ocean": len(ocean_points),
            "beach": len(beach_points)
        },
        "instructions": [
            "1. Mergi la POST /api/users/login",
            "2. Username: admin, Password: admin123",
            "3. Copiază access_token din răspuns",
            "4. Click pe butonul 'Authorize' 🔒 de sus",
            "5. Lipește token-ul și apasă Authorize",
            "6. Acum poți testa toate endpoint-urile protejate!"
        ]
    }
