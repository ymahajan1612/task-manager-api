from app.services import auth_service
from app.schemas import UserCreate
from app.database_models import User
from app.exceptions import UserExistsError
from app.security import verify_password

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