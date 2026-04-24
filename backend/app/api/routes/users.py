# Rute pentru profilul utilizatorilor (ex: GET /users/{user_id}/eco-points).
# backend/app/api/routes/users.py
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from uuid import uuid4

from app.db.session import get_db
from app.db.models import User
from app.schemas.user import UserCreate, UserLogin
from app.core.security import get_password_hash, verify_password, cookie, backend, SessionData, verifier

router = APIRouter()

@router.post("/register")
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email deja folosit")
    
    hashed_pwd = get_password_hash(user_data.password)
    new_user = User(email=user_data.email, hashed_password=hashed_pwd)
    
    db.add(new_user)
    db.commit()
    return {"message": "Utilizator inregistrat cu succes. Te rugam sa te loghezi."}

@router.post("/login")
async def login_user(user_data: UserLogin, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Email sau parola incorecte")

    # Creăm sesiunea (UUID)
    session_id = uuid4()
    data = SessionData(user_email=user.email)

    # Salvăm sesiunea în memorie și atașăm cookie-ul pe răspuns
    await backend.create(session_id, data)
    cookie.attach_to_response(response, session_id)

    return {"message": f"Login reusit pentru {user.email}"}

@router.post("/logout")
async def logout(response: Response, session_id: uuid4 = Depends(cookie)):
    # Ștergem sesiunea din memorie și din browser
    await backend.delete(session_id)
    cookie.delete_from_response(response)
    return {"message": "Delogat cu succes"}

# Exemplu de rută protejată:
@router.get("/me")
async def get_current_user_profile(session_data: SessionData = Depends(verifier), db: Session = Depends(get_db)):
    # Această rută funcționează DOAR dacă utilizatorul are un cookie valid
    user = db.query(User).filter(User.email == session_data.user_email).first()
    return {"email": user.email, "eco_points": user.eco_points}