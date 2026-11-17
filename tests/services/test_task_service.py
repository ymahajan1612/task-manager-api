
from app.services import task_service 
from app.schemas import TaskUpdate, TaskCreate, TaskStatus
from app.database_models import Task
from datetime import datetime, timezone, date
from uuid import uuid4
import pytest

def test_create_task_success(db_session, sample_task, test_user):
    task_create = TaskCreate(**sample_task)
    result = task_service.create_task(test_user.id, db_session, task_create)

    assert result.title == sample_task["title"]
    assert result.description == sample_task["description"]
    assert result.due_date == datetime.strptime(sample_task["due_date"], "%Y-%m-%d").date()
    assert result.user_id == test_user.id
    assert result.status == "not_started"
    assert result.completed_at is None


def test_get_task_by_id_success(db_session, sample_task, test_user):
    task = Task(
        title=sample_task["title"],
        description=sample_task["description"],
        due_date=sample_task["due_date"],
        user_id=test_user.id
    )
    db_session.add(task)
    db_session.commit()

    result = task_service.get_task_by_id(test_user.id, db_session, task.id)

    assert result.id == task.id
    assert result.title == sample_task["title"]
    assert result.description == sample_task["description"]
    assert result.due_date == datetime.strptime(sample_task["due_date"], "%Y-%m-%d").date()
    assert result.user_id == test_user.id

def test_get_task_by_id_not_found(db_session):
    task_id = uuid4()
    user_id = uuid4()

    with pytest.raises(task_service.TaskNotFoundError):
        task_service.get_task_by_id(user_id, db_session, task_id)

def test_get_task_by_id_forbidden(test_user, second_user, db_session, sample_task):
    task = Task(
        title=sample_task["title"],
        description=sample_task["description"],
        due_date=sample_task["due_date"],
        user_id=test_user.id
    )
    db_session.add(task)
    db_session.commit()

    with pytest.raises(task_service.TaskForbiddenError):
        task_service.get_task_by_id(second_user.id, db_session, task.id)

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


def test_delete_task_success(db_session, sample_task, test_user):
    task = Task(
        title=sample_task["title"],
        description=sample_task["description"],
        due_date=sample_task["due_date"],
        user_id=test_user.id
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    task_service.delete_task(test_user.id, db_session, task.id)

    deleted_task = db_session.get(Task, task.id)
    assert deleted_task is None

def test_delete_task_not_found(db_session):
    task_id = uuid4()
    user_id = uuid4()

    with pytest.raises(task_service.TaskNotFoundError):
        task_service.delete_task(user_id, db_session, task_id)

def test_delete_task_forbidden(test_user, second_user, db_session, sample_task):
    task = Task(
        title=sample_task["title"],
        description=sample_task["description"],
        due_date=sample_task["due_date"],
        user_id=test_user.id
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    with pytest.raises(task_service.TaskForbiddenError):
        task_service.delete_task(second_user.id, db_session, task.id)

    existing_task = db_session.get(Task, task.id)
    assert existing_task is not None


def test_list_tasks_only_returns_current_users_tasks(test_user, second_user, db_session, sample_task):
    task1 = Task(
        title=sample_task["title"],
        description=sample_task["description"],
        due_date=sample_task["due_date"],
        user_id=test_user.id,
        status="not_started"
    )
    task2 = Task(
        title="Another Task",
        description="Another Description",
        due_date=sample_task["due_date"],
        user_id=second_user.id,
        status="in_progress"
    )
    db_session.add(task1)
    db_session.add(task2)
    db_session.commit()

    result = task_service.list_tasks(test_user.id, db_session)

    assert len(result) == 1

    task, user_email = result[0]

    assert task.id == task1.id
    assert user_email == test_user.email

def test_list_tasks_filters_by_status(test_user, db_session, sample_task):
    task1 = Task(
        title=sample_task["title"],
        description=sample_task["description"],
        due_date=sample_task["due_date"],
        user_id=test_user.id,
        status=TaskStatus.NOT_STARTED
    )
    task2 = Task(
        title="Another Task",
        description="Another Description",
        due_date=sample_task["due_date"],
        user_id=test_user.id,
        status=TaskStatus.IN_PROGRESS
    )
    db_session.add(task1)
    db_session.add(task2)
    db_session.commit()

    result = task_service.list_tasks(test_user.id, db_session, status=TaskStatus.NOT_STARTED)

    assert len(result) == 1

    task, user_email = result[0]

    assert task.id == task1.id
    assert user_email == test_user.email


def test_list_tasks_filters_by_due_date(test_user, db_session):
    task1 = Task(
        title="Task 1",
        description="First task",
        due_date=date(2026, 9, 30),
        user_id=test_user.id,
        status=TaskStatus.NOT_STARTED
    )
    task2 = Task(
        title="Task 2",
        description="Second task",
        due_date=date(2026, 10, 15),
        user_id=test_user.id,
        status=TaskStatus.IN_PROGRESS
    )

    db_session.add_all([task1, task2])
    db_session.commit()

    # 1. due_before excludes later tasks
    result = task_service.list_tasks(
        test_user.id,
        db_session,
        due_before=date(2026, 10, 1)
    )

    assert {task.id for task, _ in result} == {task1.id}

    # 2. due_before includes tasks on the boundary
    result = task_service.list_tasks(
        test_user.id,
        db_session,
        due_before=date(2026, 10, 15)
    )

    assert {task.id for task, _ in result} == {task1.id, task2.id}

    # 3. due_after excludes earlier tasks
    result = task_service.list_tasks(
        test_user.id,
        db_session,
        due_after=date(2026, 10, 1)
    )

    assert {task.id for task, _ in result} == {task2.id}

    # 4. due_after includes tasks on the boundary
    result = task_service.list_tasks(
        test_user.id,
        db_session,
        due_after=date(2026, 9, 30)
    )

    assert {task.id for task, _ in result} == {task1.id, task2.id}



from datetime import datetime, timezone, timedelta


def test_list_tasks_ordering(test_user, db_session):
    base_time = datetime(2026, 11, 1, tzinfo=timezone.utc)

    tasks = [
        Task(
            title=f"Task {i}",
            user_id=test_user.id,
            created_at=base_time + timedelta(days=i)
        )
        for i in range(3)
    ]

    db_session.add_all(tasks)
    db_session.commit()

    result = task_service.list_tasks(test_user.id, db_session)

    returned_ids = [task.id for task, _ in result]

    assert returned_ids == [
        tasks[2].id,
        tasks[1].id,
        tasks[0].id
    ]



def test_list_tasks_pagination(test_user, db_session):
    same_time = datetime(2026, 11, 1, tzinfo=timezone.utc)

    tasks = [
        Task(
            title=f"Task {i}",
            user_id=test_user.id,
            created_at=same_time
        )
        for i in range(5)
    ]

    db_session.add_all(tasks)
    db_session.commit()


    expected_ids = sorted(
        [task.id for task in tasks],
        reverse=True
    )

    first_page = task_service.list_tasks(
        test_user.id,
        db_session,
        limit=2,
        offset=0
    )

    second_page = task_service.list_tasks(
        test_user.id,
        db_session,
        limit=2,
        offset=2
    )

    third_page = task_service.list_tasks(
        test_user.id,
        db_session,
        limit=2,
        offset=4
    )

    assert [task.id for task, _ in first_page] == expected_ids[:2]
    assert [task.id for task, _ in second_page] == expected_ids[2:4]
    assert [task.id for task, _ in third_page] == expected_ids[4:]

    # No overlapping tasks between pages
    all_returned_ids = [
        task.id
        for page in (first_page, second_page, third_page)
        for task, _ in page
    ]

    assert len(all_returned_ids) == len(set(all_returned_ids)) == 5
