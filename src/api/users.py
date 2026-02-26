from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from uuid import UUID

from src.database.deps import get_db
from src.models.user import User
from src.services.security import get_current_user

router = APIRouter(prefix="/users", tags=["users"])

class UserCreate(BaseModel):
    name: str
    email: EmailStr

class UserOut(BaseModel):
    id: UUID
    name: str
    email: EmailStr

    class Config:
        from_attributes = True

@router.post("", response_model=UserOut, status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    ...
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(name=payload.name, email=payload.email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.get("", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    ...
