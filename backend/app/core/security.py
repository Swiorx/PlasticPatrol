from jose import jwt, JWTError, ExpiredSignatureError
from datetime import datetime, timedelta, timezone
from typing import Any, Union
import bcrypt
from fastapi import HTTPException, status
from pydantic import ValidationError
from app.core.config import settings

# 2. Configurația JWT folosind cheia secretă din mediul de rulare (.env)
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 # Token-uri scurte = Securitate mai mare

def get_password_hash(password: str) -> str:
    """
    Transformă parola într-un hash securizat folosind bcrypt direct.
    Acest algoritm previne atacurile de tip Rainbow Table prin adăugarea unui salt generat aleatoriu.
    """
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_password.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifică dacă parola introdusă se potrivește cu hash-ul bcrypt din baza de date.
    """
    password_byte_enc = plain_password.encode('utf-8')
    hashed_password_byte_enc = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_byte_enc, hashed_password_byte_enc)

def create_access_token(subject: Union[str, Any]) -> str:
    """
    Generează un JWT (Json Web Token) semnat digital.
    'sub' (subject) conține de obicei email-ul sau ID-ul utilizatorului.
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> str:
    """
    Verifică validitatea token-ului și extrage subiectul (email-ul).
    Aruncă eroare dacă token-ul e expirat sau invalid.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email: str = payload.get("sub")
        if user_email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalid: lipsă subiect",
            )
        return user_email
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesiune expirată. Te rugăm să te loghezi din nou.",
        )
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de acces invalid",
        )