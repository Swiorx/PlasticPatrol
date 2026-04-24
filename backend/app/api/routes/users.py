# Rute pentru profilul utilizatorilor (ex: GET /users/{user_id}/eco-points).
# backend/app/api/routes/users.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User
from app.schemas.user import UserCreate, UserOut
from app.core.security import get_password_hash, verify_password, create_access_token
from app.api.deps import get_current_user
from typing import List

router = APIRouter()

@router.get("/", response_model=List[UserOut])
def get_all_users(db: Session = Depends(get_db)):
    """
    Returnează toți utilizatorii din baza de date pentru a-i putea vedea în Swagger.
    Parolele nu vor fi afișate, deoarece folosim schema UserOut.
    """
    return db.query(User).all()

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email-ul este deja folosit")
        
    existing_username = db.query(User).filter(User.username == user_data.username).first()
    if existing_username:
        raise HTTPException(status_code=400, detail="Username-ul este deja folosit")
    
    hashed_pwd = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email, 
        hashed_password=hashed_pwd
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login")
async def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Permitem logarea FIE cu adresa de email, FIE cu username-ul
    user = db.query(User).filter(
        (User.email == form_data.username) | (User.username == form_data.username)
    ).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Email/Username sau parolă incorecte",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generăm JWT Token
    access_token = create_access_token(subject=user.email)

    return {"access_token": access_token, "token_type": "bearer"}

# Exemplu de rută protejată

@router.get("/me", response_model=UserOut)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    # Această rută funcționează DOAR dacă utilizatorul are un token valid
    return current_user
