from fastapi import APIRouter, HTTPException, Depends, Query
import logging
from app.schemas import TaskCreate, TaskResponse, TaskUpdate, TaskStatus, TaskWithUserResponse
from typing import List 


from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database import get_db
from app.dependencies import get_current_user
from app.database_models import Task, User  
from uuid import UUID
from datetime import date, datetime, timezone

router = APIRouter(tags=["tasks"])

@router.post("/tasks", status_code=201, response_model=TaskResponse)
def create_task(
    task: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Task:
    new_task = Task(
        title = task.title,
        description = task.description,
        user_id = current_user.id,
        due_date = task.due_date
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return new_task

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
    stmt = (
    select(Task, User.email)
    .join(User, Task.user_id == User.id)
    .where(Task.user_id == current_user.id)
    )


    if status is not None:
        stmt = stmt.where(Task.status == status)

    if due_before is not None:
        stmt = stmt.where(Task.due_date <= due_before)

    if due_after is not None:
        stmt = stmt.where(Task.due_date >= due_after)

    stmt = (
        stmt
        .order_by(Task.created_at.desc(), Task.id.desc())
        .offset(offset)
        .limit(limit)
    )

    result = db.execute(stmt).all()
    tasks = []
    for task, user_email in result:
        tasks.append(TaskWithUserResponse(
            id=task.id,
            title=task.title,
            description=task.description,
            status=task.status,
            due_date=task.due_date,
            user_email=user_email
        ))
    return tasks


@router.get("/tasks/{task_id}", status_code=200, response_model=TaskResponse)
def get_task(task_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Task:
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this task")
    return task
    

@router.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this task")
    db.delete(task)
    db.commit()
    



@router.patch("/tasks/{task_id}", status_code=200, response_model=TaskResponse)
def update_task(task_id: UUID, updated_task: TaskUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Task:
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this task")
    
    if updated_task.title is not None:
        task.title = updated_task.title

    if updated_task.description is not None:
        task.description = updated_task.description

    if updated_task.due_date is not None:
        task.due_date = updated_task.due_date

    if updated_task.status is not None:
        old_status = task.status
        new_status = updated_task.status

        task.status = new_status

        if old_status != TaskStatus.DONE and new_status == TaskStatus.DONE:
            task.completed_at = datetime.now(timezone.utc)

        elif old_status == TaskStatus.DONE and new_status != TaskStatus.DONE:
            task.completed_at = None

    db.commit()
    db.refresh(task)
    return task
