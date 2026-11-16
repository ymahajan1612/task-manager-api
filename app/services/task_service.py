
from datetime import datetime, timezone

from app.database_models import Task
from app.exceptions import TaskNotFoundError, TaskForbiddenError, InvalidTaskError
from app.schemas import TaskStatus


def update_task(user_id, db, task_id, updated_task):
    task = db.get(Task, task_id)

    if not task:
        raise TaskNotFoundError("Task not found")

    if task.user_id != user_id:
        raise TaskForbiddenError("You are not allowed to update this task")

    updated_data = updated_task.model_dump(exclude_unset=True)

    # Validate all supplied fields before modifying the ORM object
    if "title" in updated_data:
        title = updated_data["title"]
        if title is None or not title.strip():
            raise InvalidTaskError("A task title must be a non-empty string")

    if "status" in updated_data:
        if updated_data["status"] is None:
            raise InvalidTaskError("A task status cannot be null")

    # Apply changes
    if "title" in updated_data:
        task.title = updated_data["title"]

    if "description" in updated_data:
        task.description = updated_data["description"]

    if "due_date" in updated_data:
        task.due_date = updated_data["due_date"]

    if "status" in updated_data:
        old_status = task.status
        new_status = updated_data["status"]

        task.status = new_status

        if old_status != TaskStatus.DONE and new_status == TaskStatus.DONE:
            task.completed_at = datetime.now(timezone.utc)

        elif old_status == TaskStatus.DONE and new_status != TaskStatus.DONE:
            task.completed_at = None

    task.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(task)

    return task


def create_task(user_id, db, task):
    new_task = Task(
        title=task.title,
        description=task.description,
        user_id=user_id,
        due_date=task.due_date
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return new_task

def get_task_by_id(user_id, db, task_id):
    task = db.get(Task, task_id)

    if not task:
        raise TaskNotFoundError("Task not found")

    if task.user_id != user_id:
        raise TaskForbiddenError("You are not allowed to access this task")

    return task


def delete_task(user_id, db, task_id):
    task = db.get(Task, task_id)

    if not task:
        raise TaskNotFoundError("Task not found")

    if task.user_id != user_id:
        raise TaskForbiddenError("You are not allowed to delete this task")

    db.delete(task)
    db.commit()