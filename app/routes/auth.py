from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database import get_db
from app.exceptions import InvalidCredentialsError, UserExistsError
from app.schemas import UserCreate, UserResponse, TokenResponse, LoginRequest
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=201, response_model=UserResponse)
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    try:
        return auth_service.register_user(user_data, db)
    except UserExistsError:
        raise HTTPException(status_code=400, detail="Email already registered")




@router.post("/login", status_code=200, response_model=TokenResponse)
def login_user(
    login_request: LoginRequest,
    db: Session = Depends(get_db),
):
    try:
        access_token = auth_service.login_user(login_request, db)
        return TokenResponse(access_token=access_token)
    except InvalidCredentialsError:
        raise HTTPException(status_code=400, detail="Invalid email or password")