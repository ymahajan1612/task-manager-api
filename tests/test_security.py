import pytest 
from uuid import uuid4, UUID
import jwt

from app.security import ALGORITHM, SECRET_KEY, create_access_token, verify_password, verify_token
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException

def test_create_access(test_user):
    user_id = str(test_user.id)
    before = datetime.now(tz=timezone.utc)
    token = create_access_token(user_id=user_id)
    after = datetime.now(tz=timezone.utc)

    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    expiry = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)

    expected_expiry = before + timedelta(minutes=30)
    elapsed = after - before

    assert (
        expected_expiry - timedelta(seconds=1)
        <= expiry
        <= expected_expiry + elapsed
    )

    assert isinstance(token, str)

    assert payload["sub"] == user_id

def test_verify_token_valid(test_user):
    user_id = str(test_user.id)
    token = create_access_token(user_id=user_id)

    result = verify_token(token)

    assert result == UUID(user_id)

def test_verify_token_invalid():
    invalid_token = "invalid.token.here"

    with pytest.raises(HTTPException) as exc_info:
        verify_token(invalid_token)

    assert exc_info.value.status_code == 401


def test_verify_password_correct(test_user):
    result = verify_password(
        "testpassword",
        test_user.hashed_password
    )

    assert result is True


def test_verify_password_incorrect(test_user):
    result = verify_password(
        "wrongpassword",
        test_user.hashed_password
    )

    assert result is False