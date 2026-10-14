from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import date
from enum import Enum


class TaskStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    DONE = "done"

class TaskCreate(BaseModel):

    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    due_date: date | None = None


class TaskResponse(TaskCreate):
    id: UUID
    status: TaskStatus


class TaskUpdate(BaseModel):
        title: str | None = Field(min_length=1, max_length=200, default=None)
        description: str | None = None
        status: TaskStatus | None = None
        due_date: date | None = None
        

class TaskWithUserResponse(TaskResponse):
    user_email: EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

    