from app.exceptions import TaskNotFoundError, TaskForbiddenError, InvalidTaskError
from app.database_models import Task
from app.schemas import TaskStatus
from datetime import datetime, timezone


def update_task(user_id, db, task_id, updated_task):
    task = db.get(Task, task_id)
    if not task:
        raise TaskNotFoundError("Task not found")

    if task.user_id != user_id:
        raise TaskForbiddenError("You are not allowed to update this task")

    updated_data = updated_task.model_dump(exclude_unset=True)

    if "title" in updated_data:
        if updated_data["title"] is None or updated_data["title"].strip() == "":
            raise InvalidTaskError("A task title must be a non-empty string")
        task.title = updated_data["title"]

    if "description" in updated_data:
        task.description = updated_data["description"]

    if "due_date" in updated_data:
        task.due_date = updated_data["due_date"]

    if "status" in updated_data:
        if updated_data["status"] is None:
            raise InvalidTaskError("A task status cannot be null")

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