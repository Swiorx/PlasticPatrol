# Clase Pydantic pentru validarea datelor despre marinari.

from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    eco_points: int

    class Config:
        from_attributes = True
