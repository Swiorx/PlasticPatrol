# backend/app/api/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import User
from app.core.security import SECRET_KEY, ALGORITHM

# Aceasta linie spune FastAPI unde sa caute token-ul (in header-ul Authorization)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/users/login")

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Nu am putut valida credentialele",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decodam token-ul
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Cautam user-ul in DB
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    
    return user # Returnam obiectul user complet!