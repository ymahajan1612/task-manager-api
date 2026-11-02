import pytest
from sqlalchemy import delete, create_engine
from sqlalchemy.orm import sessionmaker
from app.config import TEST_DATABASE_URL
from app.main import app
from app.database import get_db
from app.database_models import Task, User
from app.security import hash_password
from app.security import create_access_token

from fastapi.testclient import TestClient


test_engine = create_engine(TEST_DATABASE_URL)
SessionLocalTest = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def get_test_db():
    test_db = SessionLocalTest()
    try:
        yield test_db
    finally:
        test_db.close()



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


@pytest.fixture
def second_user():
    db = SessionLocalTest()

    try:
        user = User(
            email="seconduser@example.com",
            hashed_password=hash_password("testpassword"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()



