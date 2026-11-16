
from app.services import task_service 
from app.schemas import TaskUpdate
from app.database_models import Task
from datetime import datetime, timezone
from uuid import uuid4
import pytest

def test_update_task_not_found(db_session):
    task_id = uuid4()
    user_id = uuid4()

    updated_task = TaskUpdate(title="Updated Title", description="Updated Description", due_date="2026-10-01")
    with pytest.raises(task_service.TaskNotFoundError):
            task_service.update_task(user_id, db_session, task_id, updated_task)


def test_update_task_forbidden(test_user, second_user, db_session, sample_task):
    task = Task(
        title=sample_task["title"],
        description=sample_task["description"],
        due_date=sample_task["due_date"],
        user_id=test_user.id
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    updated_task = TaskUpdate(title="Updated Title", description="Updated Description", due_date="2026-10-01")
    with pytest.raises(task_service.TaskForbiddenError):
        task_service.update_task(second_user.id, db_session, task.id, updated_task)

    db_session.refresh(task)

    assert task.title == "Test Title"
    assert task.description == "Test Description"

def test_update_task_invalid_title(db_session, sample_task, test_user):
    task = Task(
        title=sample_task["title"],
        description=sample_task["description"],
        due_date=sample_task["due_date"],
        user_id=test_user.id
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    updated_task = TaskUpdate(title="   ", description="Updated Description", due_date="2026-10-01")
    with pytest.raises(task_service.InvalidTaskError):
        task_service.update_task(test_user.id, db_session, task.id, updated_task)

    db_session.refresh(task)

    assert task.title == "Test Title"
    assert task.description == "Test Description"

def test_update_task_success(db_session, sample_task, test_user):
    task = Task(
        title=sample_task["title"],
        description=sample_task["description"],
        due_date=sample_task["due_date"],
        user_id=test_user.id
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    updated_task = TaskUpdate(title="Updated Title", description="Updated Description", due_date="2026-10-01")
    result = task_service.update_task(test_user.id, db_session, task.id, updated_task)

    assert result.title == "Updated Title"
    assert result.description == "Updated Description"

def test_update_task_preserves_unset_fields(db_session, sample_task, test_user):
    task = Task(
        title=sample_task["title"],
        description=sample_task["description"],
        due_date=sample_task["due_date"],
        user_id=test_user.id
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    updated_task = TaskUpdate(description="Updated Description")
    result = task_service.update_task(test_user.id, db_session, task.id, updated_task)

    assert result.title == "Test Title"
    assert result.description == "Updated Description"
       
@pytest.mark.parametrize(
    "initial_status, new_status, expected_completed_at",
    [
        ("not_started", "not_started", None),
        ("not_started", "in_progress", None),
        ("not_started", "done", "set"),
        ("in_progress", "done", "set"),
        ("done", "in_progress", None),
        ("done", "not_started", None),
        ("done", "done", "set"),
    ]
)
def test_update_task_status_transitions(initial_status, new_status, expected_completed_at, db_session, sample_task, test_user):
    task = Task(
        title=sample_task["title"],
        description=sample_task["description"],
        due_date=sample_task["due_date"],
        user_id=test_user.id,
        status=initial_status
    )
    if initial_status == "done":
        task.completed_at = datetime(
            2026, 1, 1, tzinfo=timezone.utc
        )


    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    updated_task = TaskUpdate(status=new_status)
    result = task_service.update_task(test_user.id, db_session, task.id, updated_task)

    assert result.status == new_status
    if expected_completed_at == "set":
        assert result.completed_at is not None
    else:
        assert result.completed_at is None


def test_task_update_invalid_field_keeps_task_unchanged(db_session, sample_task, test_user):
    task = Task(
        title=sample_task["title"],
        description=sample_task["description"],
        due_date=sample_task["due_date"],
        user_id=test_user.id
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    updated_task = TaskUpdate(description="Updated Description", status=None)
    with pytest.raises(task_service.InvalidTaskError):
        task_service.update_task(test_user.id, db_session, task.id, updated_task)

    db_session.flush()
    db_session.refresh(task)

    assert task.title == "Test Title"
    assert task.description == "Test Description"