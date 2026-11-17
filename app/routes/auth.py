from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database import get_db
from app.database_models import User
from app.exceptions import UserExistsError
from app.schemas import UserCreate, UserResponse, TokenResponse, LoginRequest
from app.security import verify_password, create_access_token

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

    return new_user



@router.post("/login", status_code=200, response_model=TokenResponse)
def login_user(
    login_request: LoginRequest,
    db: Session = Depends(get_db),
):
    # Check if user exists
    stmt = select(User).where(User.email == login_request.email)
    user = db.execute(stmt).scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid email or password")

    # Verify password
    if not verify_password(login_request.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    access_token = create_access_token(user_id=str(user.id))

    return TokenResponse(access_token=access_token)