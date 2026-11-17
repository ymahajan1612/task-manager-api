from app.services import auth_service
from app.schemas import UserCreate, LoginRequest
from app.database_models import User
from app.exceptions import UserExistsError, InvalidCredentialsError
from app.security import verify_password, verify_token

import pytest


def test_register_user_success(db_session):
    user_data = UserCreate(
        email="newuser@example.com",
        password="SecurePassword123!"
    )

    result = auth_service.register_user(user_data, db_session)

    # Check returned user
    assert result.email == user_data.email
    assert result.id is not None

    # Verify user was persisted
    saved_user = db_session.get(User, result.id)

    assert saved_user is not None
    assert saved_user.email == user_data.email

    # Verify password was hashed correctly
    assert saved_user.hashed_password != user_data.password
    assert verify_password(
        user_data.password,
        saved_user.hashed_password
    )


def test_register_user_duplicate_email(db_session):
    user_data = UserCreate(
        email="duplicate@example.com",
        password="SecurePassword123!"
    )

    # Register first user
    auth_service.register_user(user_data, db_session)

    # Attempt to register again with the same email
    with pytest.raises(UserExistsError):
        auth_service.register_user(user_data, db_session)


def test_login_user_success(db_session):
    user_data = UserCreate(
        email="login@example.com",
        password="SecurePassword123!"
    )

    user = auth_service.register_user(user_data, db_session)

    login_request = LoginRequest(
        email=user_data.email,
        password=user_data.password
    )

    access_token = auth_service.login_user(
        login_request,
        db_session
    )

    assert isinstance(access_token, str)
    assert access_token

    # Decode and validate the JWT
    token_user_id = verify_token(access_token)

    assert token_user_id == user.id


def test_login_user_email_not_found(db_session):
    login_request = LoginRequest(
        email="nonexistent@example.com",
        password="SecurePassword123!"
    )

    with pytest.raises(
        InvalidCredentialsError,
        match="Invalid email or password"
    ):
        auth_service.login_user(login_request, db_session)


def test_login_user_incorrect_password(db_session):
    user_data = UserCreate(
        email="login@example.com",
        password="SecurePassword123!"
    )

    auth_service.register_user(user_data, db_session)

    login_request = LoginRequest(
        email=user_data.email,
        password="WrongPassword123!"
    )

    with pytest.raises(
        InvalidCredentialsError,
        match="Invalid email or password"
    ):
        auth_service.login_user(login_request, db_session)
