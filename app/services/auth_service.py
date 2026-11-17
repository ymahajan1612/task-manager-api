
from app.database_models import User
from sqlalchemy import select

from app.exceptions import InvalidCredentialsError, UserExistsError
from app.security import hash_password, verify_password, create_access_token

def register_user(
    user_data,
    db
):
    # Check if user already exists
    stmt = select(User).where(User.email == user_data.email)
    existing_user = db.execute(stmt).scalar_one_or_none()

    if existing_user:
        raise UserExistsError("Email already registered")

    # Create new user
    hashed_password = hash_password(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

def login_user(
    login_request,
    db
):
    # Check if user exists
    stmt = select(User).where(User.email == login_request.email)
    user = db.execute(stmt).scalar_one_or_none()

    if not user:
        raise InvalidCredentialsError("Invalid email or password")

    # Verify password
    if not verify_password(login_request.password, user.hashed_password):
        raise InvalidCredentialsError("Invalid email or password")

    return create_access_token(user_id=str(user.id))