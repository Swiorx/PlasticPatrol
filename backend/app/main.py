from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.session import engine
from app.db import models

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

@app.get("/")
def read_root():
    return {"message": "Welcome to PlasticPatrol API!"}
