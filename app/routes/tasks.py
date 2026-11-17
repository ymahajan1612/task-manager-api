from fastapi import APIRouter, HTTPException, Depends, Query
import logging
from app.schemas import TaskCreate, TaskResponse, TaskUpdate, TaskStatus, TaskWithUserResponse


from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database import get_db
from app.dependencies import get_current_user
from app.database_models import Task, User  
from uuid import UUID
from app.services import task_service
from app.exceptions import TaskNotFoundError, TaskForbiddenError, InvalidTaskError
from datetime import date
router = APIRouter(tags=["tasks"])

@router.post("/tasks", status_code=201, response_model=TaskResponse)
def create_task(
    task: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Task:
    return task_service.create_task(current_user.id, db, task)
    

@router.get("/tasks", response_model=list[TaskWithUserResponse])
def list_tasks(
    status: TaskStatus | None = None,
    due_before: date | None = None,
    due_after: date | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = task_service.list_tasks(
        user_id=current_user.id,
        db=db,
        status=status,
        due_before=due_before,
        due_after=due_after,
        limit=limit,
        offset=offset
    )
    tasks = []
    for task, user_email in result:
        tasks.append(TaskWithUserResponse(
            id=task.id,
            title=task.title,
            description=task.description,
            status=task.status,
            due_date=task.due_date,
            user_email=user_email,
            completed_at=task.completed_at
        ))
    return tasks


@router.get("/tasks/{task_id}", status_code=200, response_model=TaskResponse)
def get_task(task_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Task:
    try:
        return task_service.get_task_by_id(current_user.id, db, task_id)
    except TaskNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TaskForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    try:
        task_service.delete_task(current_user.id, db, task_id)
    except TaskNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TaskForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))
    



@router.patch("/tasks/{task_id}", status_code=200, response_model=TaskResponse)
def update_task(task_id: UUID, updated_task: TaskUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Task:
    try:
        updated_task = task_service.update_task(current_user.id, db, task_id, updated_task)
        return updated_task
    except TaskNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TaskForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except InvalidTaskError as e:
        raise HTTPException(status_code=422, detail=str(e))
