import pytest 
from uuid import uuid4, UUID
import jwt
from datetime import datetime, timedelta, timezone

from app.security import (
    create_access_token,
    SECRET_KEY,
    ALGORITHM,
)

def test_register_user_success(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "securepassword"
        })

    assert response.status_code == 201
    UUID(response.json()["id"])
    assert response.json()["email"] == "test@example.com"


def test_register_duplicate_email(client, test_user):
    response = client.post(
        "/auth/register",
        json={
            "email": test_user.email,
            "password": "anotherpassword",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"



def test_register_missing_password(client):
    response = client.post(
        "/auth/register",
        json={"email": "newuser@example.com"},
    )

    assert response.status_code == 422


def test_login_success(client, test_user):
    response = client.post(
        "/auth/login",
        json={
            "email": test_user.email,
            "password": "testpassword",
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert isinstance(data["access_token"], str)
    assert data["token_type"] == "bearer"

    payload = jwt.decode(
        data["access_token"],
        SECRET_KEY,
        algorithms=[ALGORITHM],
    )
    assert payload["sub"] == str(test_user.id)


def test_login_wrong_password(client, test_user):
    response = client.post(
        "/auth/login",
        json={
            "email": test_user.email,
            "password": "wrongpassword",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid email or password"


def test_login_unknown_user(client):
    response = client.post(
        "/auth/login",
        json={
            "email": "unknown@example.com",
            "password": "testpassword",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid email or password"




def test_missing_token(client):
    response = client.get("/tasks")

    # FastAPI's HTTPBearer behaviour can vary by version.
    assert response.status_code in (401, 403)


def test_invalid_token(client):
    response = client.get(
        "/tasks",
        headers={"Authorization": "Bearer invalid.token.here"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"


def test_expired_token(client, test_user):
    expired_payload = {
        "sub": str(test_user.id),
        "exp": datetime.now(timezone.utc) - timedelta(minutes=5),
    }

    expired_token = jwt.encode(
        expired_payload,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    response = client.get(
        "/tasks",
        headers={"Authorization": f"Bearer {expired_token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"


def test_token_for_nonexistent_user(client):
    token = create_access_token(user_id=str(uuid4()))

    response = client.get(
        "/tasks",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid authentication credentials"


def test_valid_token(client, auth_headers):
    response = client.get("/tasks", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == []



@pytest.fixture
def second_user_headers(second_user):
    token = create_access_token(user_id=str(second_user.id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def first_user_task(client, auth_headers):
    response = client.post(
        "/tasks",
        json={"title": "Private task"},
        headers=auth_headers,
    )

    assert response.status_code == 201
    return response.json()


def test_cannot_read_another_users_task(
    client, first_user_task, second_user_headers
):
    task_id = first_user_task["id"]

    response = client.get(
        f"/tasks/{task_id}",
        headers=second_user_headers,
    )

    assert response.status_code == 403


def test_cannot_update_another_users_task(
    client, first_user_task, second_user_headers, auth_headers
):
    task_id = first_user_task["id"]

    response = client.patch(
        f"/tasks/{task_id}",
        json={"title": "Hacked title"},
        headers=second_user_headers,
    )

    assert response.status_code == 403

    original = client.get(
        f"/tasks/{task_id}",
        headers=auth_headers,
    )
    assert original.json()["title"] == "Private task"


def test_cannot_delete_another_users_task(
    client, first_user_task, second_user_headers, auth_headers
):
    task_id = first_user_task["id"]

    response = client.delete(
        f"/tasks/{task_id}",
        headers=second_user_headers,
    )

    assert response.status_code == 403

    original = client.get(
        f"/tasks/{task_id}",
        headers=auth_headers,
    )
    assert original.status_code == 200


def test_cannot_list_another_users_tasks(
    client, first_user_task, second_user_headers
):
    response = client.get(
        "/tasks",
        headers=second_user_headers,
    )

    assert response.status_code == 200
    assert response.json() == []