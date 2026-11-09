import pytest

from uuid import UUID, uuid4


@pytest.fixture
def sample_task():
    return {
        "title": "Test Title",
        "description": "Test Description",
        "due_date": "2026-09-30",
    }

def test_root(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_task(client, sample_task, auth_headers):

    
    response = client.post(
        "/tasks",
        json=sample_task,
        headers=auth_headers,
    )

    data = response.json()

    assert response.status_code == 201

    UUID(data["id"])

    assert data["title"] == "Test Title"
    assert data["description"] == "Test Description"
    assert data["due_date"] == "2026-09-30"
    assert data["status"] == "not_started"


def test_list_tasks(client, auth_headers):
    client.post(
        "/tasks",
        json={
            "title": "First Task",
            "description": "First Description",
            "due_date": "2026-09-30",
        },
        headers=auth_headers,
    )

    client.post(
        "/tasks",
        json={
            "title": "Second Task",
            "description": "Second Description",
            "due_date": "2026-10-01",
        },
        headers=auth_headers,
    )

    response = client.get("/tasks", headers=auth_headers)
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


def test_get_task(client, auth_headers):
    create_response = client.post(
        "/tasks",
        json={
            "title": "Test Title",
            "description": "Test Description",
            "due_date": "2026-09-30",
        },
        headers=auth_headers,
    )

    task_id = create_response.json()["id"]

    response = client.get(f"/tasks/{task_id}", headers=auth_headers)
    data = response.json()

    assert response.status_code == 200

    UUID(data["id"])

    assert data["id"] == task_id
    assert data["title"] == "Test Title"
    assert data["description"] == "Test Description"
    assert data["due_date"] == "2026-09-30"
    assert data["status"] == "not_started"


def test_get_task_not_found(client, auth_headers):
    missing_id = uuid4()

    response = client.get(f"/tasks/{missing_id}", headers=auth_headers)

    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}


def test_update_task(client, auth_headers):
    create_response = client.post(
        "/tasks",
        json={
            "title": "Original Title",
            "description": "Original Description",
            "due_date": "2026-09-30",
        },
        headers=auth_headers,
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
        headers=auth_headers,
    )

    data = response.json()

    assert response.status_code == 200

    UUID(data["id"])

    assert data["id"] == task_id
    assert data["title"] == "Updated Title"
    assert data["description"] == "Updated Description"
    assert data["due_date"] == "2026-10-15"
    assert data["status"] == "in_progress"


def test_update_task_preserves_fields_when_not_provided(client, auth_headers):
    create_response = client.post(
        "/tasks",
        json={
            "title": "Original Title",
            "description": "Original Description",
            "due_date": "2026-09-30",
        },
        headers=auth_headers,
    )

    task_id = create_response.json()["id"]

    response = client.patch(
        f"/tasks/{task_id}",
        json={
            "title": "Updated Title",
        },
        headers=auth_headers,
    )

    data = response.json()

    assert response.status_code == 200

    UUID(data["id"])

    assert data["id"] == task_id
    assert data["title"] == "Updated Title"
    assert data["description"] == "Original Description"
    assert data["due_date"] == "2026-09-30"
    assert data["status"] == "not_started"


def test_update_task_status(client, auth_headers):
    create_response = client.post(
        "/tasks",
        json={
            "title": "Status Test",
            "description": "Testing status updates",
            "due_date": "2026-09-30",
        },
        headers=auth_headers,
    )

    task_id = create_response.json()["id"]

    response = client.patch(
        f"/tasks/{task_id}",
        json={
            "status": "done",
        },
        headers=auth_headers,
    )

    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "done"


@pytest.mark.parametrize(
    "status, expected_code",
    [
        ("not_started", 200),
        ("in_progress", 200),
        ("done", 200),
        ("banana", 422),
    ],
)
def test_task_status(client, status, expected_code, auth_headers):
    create_response = client.post(
        "/tasks",
        json={
            "title": "Status Test",
        },
        headers=auth_headers,
    
    )

    task_id = create_response.json()["id"]

    response = client.patch(
        f"/tasks/{task_id}",
        json={
            "status": status,
        },
        headers=auth_headers,
    )

    assert response.status_code == expected_code


def test_update_task_not_found(client, auth_headers):
    missing_id = uuid4()

    response = client.patch(
        f"/tasks/{missing_id}",
        json={
            "title": "Updated title",
        },
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}


def test_delete_task(client, auth_headers):
    create_response = client.post(
        "/tasks",
        json={
            "title": "Test Delete Task Title",
            "description": "Test Delete Task Description",
            "due_date": "2026-09-30",
        },
        headers=auth_headers,   
    )

    task_id = create_response.json()["id"]

    delete_response = client.delete(f"/tasks/{task_id}", headers=auth_headers)

    assert delete_response.status_code == 204

    get_response = client.get(f"/tasks/{task_id}", headers=auth_headers)

    assert get_response.status_code == 404
    assert get_response.json() == {"detail": "Task not found"}



def test_filter_tasks_by_status(client, auth_headers):
    first = client.post(
        "/tasks",
        json={
            "title": "First Task",
            "description": "First Description",
            "due_date": "2026-09-30",
        },
        headers=auth_headers,
    ).json()

    second = client.post(
        "/tasks",
        json={
            "title": "Second Task",
            "description": "Second Description",
            "due_date": "2026-10-05",
        },
        headers=auth_headers,
    ).json()

    client.patch(
        f"/tasks/{second['id']}",
        json={
            "status": "done",
        },
        headers=auth_headers,
    )

    response = client.get("/tasks?status=done", headers=auth_headers)
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 1
    assert data[0]["id"] == second["id"]
    assert data[0]["status"] == "done"


def test_filter_tasks_by_due_before(client, auth_headers):
    client.post(
        "/tasks",
        json={
            "title": "Earlier Task",
            "due_date": "2026-09-25",
        },
        headers=auth_headers,
    )

    client.post(
        "/tasks",
        json={
            "title": "Later Task",
            "due_date": "2026-10-05",
        },
        headers=auth_headers,
    )

    response = client.get("/tasks?due_before=2026-09-30", headers=auth_headers)
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 1
    assert data[0]["title"] == "Earlier Task"


def test_filter_tasks_by_due_after(client, auth_headers):
    client.post(
        "/tasks",
        json={
            "title": "Earlier Task",
            "due_date": "2026-09-25",
        },
        headers=auth_headers,
    )

    client.post(
        "/tasks",
        json={
            "title": "Later Task",
            "due_date": "2026-10-05",
        },
        headers=auth_headers,
    )

    response = client.get("/tasks?due_after=2026-09-30", headers=auth_headers)
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 1
    assert data[0]["title"] == "Later Task"


def test_status_complete(client, auth_headers):
    response = client.post(
        "/tasks",
        json={
            "title": "Task to be completed",
            "description": "This task is intended to be marked as done",
            "due_date": "2026-09-30",
        },
        headers=auth_headers,
    )

    task_id = response.json()["id"]
    patch_response = client.patch(
        f"/tasks/{task_id}",
        json={"status": "done"},
        headers=auth_headers,
    )

    assert patch_response.status_code == 200

    data = client.get(
        f"/tasks/{task_id}", headers=auth_headers
    ).json()

    assert data["completed_at"] is not None

    undo_response = client.patch(
        f"/tasks/{task_id}",
        json={"status": "in_progress"},
        headers=auth_headers,
    )

    assert undo_response.status_code == 200
    data = client.get(
        f"/tasks/{task_id}", headers=auth_headers
    ).json()
    assert data["completed_at"] is None


def test_pagination(client, auth_headers):
    for i in range(15):
        client.post(
            "/tasks",
            json={
                "title": f"Task {i+1}",
                "description": f"Description for task {i+1}",
                "due_date": "2026-09-30",
            },
            headers=auth_headers,
        )

    response = client.get("/tasks?offset=2&limit=5", headers=auth_headers)
    response_all = client.get("/tasks", headers=auth_headers)
    data = response.json()
    data_all = response_all.json()

    assert response.status_code == 200
    assert len(data) == 5
    assert data == data_all[2:7]


@pytest.mark.parametrize(
        "query" ,
        [
            "limit=0",
            "limit=101",
            "offset=-1",
        ]
)
def test_invalid_pagination(client, auth_headers, query):
    response = client.get(f"/tasks?{query}", headers=auth_headers)

    assert response.status_code == 422


def test_patch_clear_nullable_fields(client, auth_headers):
    response = client.post(
        "/tasks",
        json={
            "title": "Task with nullable fields",
            "description": "This task has a description and due date",
            "due_date": "2026-09-30",
        },
        headers=auth_headers,
    )

    task_id = response.json()["id"]

    json={"description": None, "due_date": None}
    patch_response = client.patch(
        f"/tasks/{task_id}",
        json=json,
        headers=auth_headers,
    )

    assert patch_response.status_code == 200

    data = client.get(
        f"/tasks/{task_id}", headers=auth_headers
    ).json()
    assert data["description"] is None
    assert data["due_date"] is None