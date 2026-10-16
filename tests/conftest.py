import pytest
from sqlalchemy import delete

from app.main import app
from app.database import get_db, get_test_db, SessionLocalTest
from app.database_models import Task, User
from app.security import hash_password
from app.security import create_access_token

from fastapi.testclient import TestClient



app.dependency_overrides[get_db] = get_test_db

@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture(autouse=True)
def reset_database():
    db = SessionLocalTest()

    try:
        db.execute(delete(Task))
        db.execute(delete(User))
        db.commit()

        yield

        db.execute(delete(Task))
        db.execute(delete(User))
        db.commit()
    finally:
        db.close()


@pytest.fixture()
def test_user():
    db = SessionLocalTest()
    password = "testpassword"
    hashed_password = hash_password(password)
    user = User(email="testuser@gmail.com" , hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


@pytest.fixture
def auth_headers(test_user):
    user_id = str(test_user.id)
    token = create_access_token(
        user_id=user_id
    )

    return {"Authorization": f"Bearer {token}"}
