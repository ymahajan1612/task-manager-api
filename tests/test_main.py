from fastapi.testclient import TestClient
import pytest

from app.main import app

from sqlalchemy import delete
from app.database import get_db, get_test_db, SessionLocalTest
from app.database_models import Task, User
from uuid import UUID, uuid4


client = TestClient(app)

TEST_USER_ID = UUID("203cc458-009f-41dc-bfba-28b9fe3c031c")

app.dependency_overrides[get_db] = get_test_db


@pytest.fixture(autouse=True)
def reset_database():
    db = SessionLocalTest()

    db.execute(delete(Task))
    db.execute(delete(User))
    db.commit()

    test_user = User(
        id=TEST_USER_ID,
        email="test@example.com",
    )

    db.add(test_user)
    db.commit()
    db.close()

    yield

    db = SessionLocalTest()

    db.execute(delete(Task))
    db.execute(delete(User))
    db.commit()

    db.close()


def test_root():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_task():
    response = client.post(
        "/tasks",
        json={
            "title": "Test Title",
            "description": "Test Description",
            "due_date": "2026-09-30",
        },
    )

    data = response.json()

    assert response.status_code == 201

    UUID(data["id"])

    assert data["title"] == "Test Title"
    assert data["description"] == "Test Description"
    assert data["due_date"] == "2026-09-30"
    assert data["status"] == "not_started"


def test_list_tasks():
    client.post(
        "/tasks",
        json={
            "title": "First Task",
            "description": "First Description",
            "due_date": "2026-09-30",
        },
    )

    client.post(
        "/tasks",
        json={
            "title": "Second Task",
            "description": "Second Description",
            "due_date": "2026-10-01",
        },
    )

    response = client.get("/tasks")
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 2

    UUID(data[0]["id"])
    UUID(data[1]["id"])

    titles = {task["title"] for task in data}
    descriptions = {task["description"] for task in data}
    dates = {task["due_date"] for task in data}
    statuses = {task["status"] for task in data}

    assert titles == {"First Task", "Second Task"}
    assert descriptions == {"First Description", "Second Description"}
    assert dates == {"2026-09-30", "2026-10-01"}
    assert statuses == {"not_started"}


def test_get_task():
    create_response = client.post(
        "/tasks",
        json={
            "title": "Test Title",
            "description": "Test Description",
            "due_date": "2026-09-30",
        },
    )

    task_id = create_response.json()["id"]

    response = client.get(f"/tasks/{task_id}")
    data = response.json()

    assert response.status_code == 200

    UUID(data["id"])

    assert data["id"] == task_id
    assert data["title"] == "Test Title"
    assert data["description"] == "Test Description"
    assert data["due_date"] == "2026-09-30"
    assert data["status"] == "not_started"


def test_get_task_not_found():
    missing_id = uuid4()

    response = client.get(f"/tasks/{missing_id}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}


def test_update_task():
    create_response = client.post(
        "/tasks",
        json={
            "title": "Original Title",
            "description": "Original Description",
            "due_date": "2026-09-30",
        },
    )

    task_id = create_response.json()["id"]

    response = client.patch(
        f"/tasks/{task_id}",
        json={
            "title": "Updated Title",
            "description": "Updated Description",
            "due_date": "2026-10-15",
            "status": "in_progress",
        },
    )

    data = response.json()

    assert response.status_code == 200

    UUID(data["id"])

    assert data["id"] == task_id
    assert data["title"] == "Updated Title"
    assert data["description"] == "Updated Description"
    assert data["due_date"] == "2026-10-15"
    assert data["status"] == "in_progress"


def test_update_task_preserves_fields_when_not_provided():
    create_response = client.post(
        "/tasks",
        json={
            "title": "Original Title",
            "description": "Original Description",
            "due_date": "2026-09-30",
        },
    )

    task_id = create_response.json()["id"]

    response = client.patch(
        f"/tasks/{task_id}",
        json={
            "title": "Updated Title",
        },
    )

    data = response.json()

    assert response.status_code == 200

    UUID(data["id"])

    assert data["id"] == task_id
    assert data["title"] == "Updated Title"
    assert data["description"] == "Original Description"
    assert data["due_date"] == "2026-09-30"
    assert data["status"] == "not_started"


def test_update_task_status():
    create_response = client.post(
        "/tasks",
        json={
            "title": "Status Test",
            "description": "Testing status updates",
            "due_date": "2026-09-30",
        },
    )

    task_id = create_response.json()["id"]

    response = client.patch(
        f"/tasks/{task_id}",
        json={
            "status": "done",
        },
    )

    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "done"


def test_invalid_task_status():
    create_response = client.post(
        "/tasks",
        json={
            "title": "Invalid Status Test",
        },
    )

    task_id = create_response.json()["id"]

    response = client.patch(
        f"/tasks/{task_id}",
        json={
            "status": "banana",
        },
    )

    assert response.status_code == 422


def test_update_task_not_found():
    missing_id = uuid4()

    response = client.patch(
        f"/tasks/{missing_id}",
        json={
            "title": "Updated title",
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}


def test_delete_task():
    create_response = client.post(
        "/tasks",
        json={
            "title": "Test Delete Task Title",
            "description": "Test Delete Task Description",
            "due_date": "2026-09-30",
        },
    )

    task_id = create_response.json()["id"]

    delete_response = client.delete(f"/tasks/{task_id}")

    assert delete_response.status_code == 204

    get_response = client.get(f"/tasks/{task_id}")

    assert get_response.status_code == 404
    assert get_response.json() == {"detail": "Task not found"}



def test_filter_tasks_by_status():
    first = client.post(
        "/tasks",
        json={
            "title": "First Task",
            "description": "First Description",
            "due_date": "2026-09-30",
        },
    ).json()

    second = client.post(
        "/tasks",
        json={
            "title": "Second Task",
            "description": "Second Description",
            "due_date": "2026-10-05",
        },
    ).json()

    client.patch(
        f"/tasks/{second['id']}",
        json={
            "status": "done",
        },
    )

    response = client.get("/tasks?status=done")
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 1
    assert data[0]["id"] == second["id"]
    assert data[0]["status"] == "done"


def test_filter_tasks_by_due_before():
    client.post(
        "/tasks",
        json={
            "title": "Earlier Task",
            "due_date": "2026-09-25",
        },
    )

    client.post(
        "/tasks",
        json={
            "title": "Later Task",
            "due_date": "2026-10-05",
        },
    )

    response = client.get("/tasks?due_before=2026-09-30")
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 1
    assert data[0]["title"] == "Earlier Task"


def test_filter_tasks_by_due_after():
    client.post(
        "/tasks",
        json={
            "title": "Earlier Task",
            "due_date": "2026-09-25",
        },
    )

    client.post(
        "/tasks",
        json={
            "title": "Later Task",
            "due_date": "2026-10-05",
        },
    )

    response = client.get("/tasks?due_after=2026-09-30")
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 1
    assert data[0]["title"] == "Later Task"