from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.infra.db import get_db
from app.routes.dependencies import get_current_user
from app.schemas import TokenResponse, UserCreate, UserLogin, UserOut
from app.services.auth_service import authenticate_user, create_access_token, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    try:
        user = register_user(db, payload.email, payload.password, payload.role)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return UserOut(id=user.id, email=user.email, role=user.role)


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return TokenResponse(access_token=create_access_token(user.id, user.email, user.role))


@router.get("/me", response_model=UserOut)
def me(user=Depends(get_current_user)):
    return UserOut(id=user.id, email=user.email, role=user.role)
