import jwt
from datetime import datetime, timedelta, timezone
from typing import Any, Union
from passlib.context import CryptContext
from fastapi import HTTPException, status
from pydantic import ValidationError

# 1. Configurația de Hashing (BCrypt)
# Folosim 'bcrypt' cu un 'round' automat pentru a fi rezistent la atacuri brute-force.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 2. Configurația JWT (Acestea ar trebui să stea în fișierul .env pe care îl ai deja)
SECRET_KEY = "CHEIE_SECRETĂ_FOARTE_LUNGĂ_ȘI_RANDOM" # Generează una cu 'openssl rand -hex 32'
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 # Token-uri scurte = Securitate mai mare

def get_password_hash(password: str) -> str:
    """
    Transformă parola în text clar într-un hash securizat.
    BCrypt adaugă automat 'salt' (sare), deci două parole identice vor avea hash-uri diferite.
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifică dacă parola introdusă se potrivește cu hash-ul din baza de date.
    """
    return pwd_context.verify(plain_password, hashed_password)

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
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesiune expirată. Te rugăm să te loghezi din nou.",
        )
    except (jwt.InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de acces invalid",
        )