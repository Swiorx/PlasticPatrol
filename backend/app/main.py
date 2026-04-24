import sys
from pathlib import Path

# Add project root to path so ml_classifier (sibling of backend/) is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.session import engine
from app.db import models
from app.api.routes import users, plastic
from app.api.routes.classifier import router as classifier_router

# Creăm tabelele în baza de date pe baza modelelor definite anterior
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="PlasticPatrol API", version="1.0.0")

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

@app.get("/")
def read_root():
    return {"message": "Welcome to PlasticPatrol API!"}
