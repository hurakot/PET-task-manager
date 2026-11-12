
# APIRouter со всеми ручками /tasks

from sqlmodel import Field, Session, SQLModel, create_engine, select
from fastapi import HTTPException, Depends, FastAPI, Query, APIRouter

from contextlib import asynccontextmanager
from typing import Annotated

from app.models import Task
from app.schemas import TaskUpdate, TaskRead, TaskCreate
from app.database import SessionDep
from app.dependencies import CurrentUser

# Ручки API, связанные с tasks

router = APIRouter(prefix="/tasks", tags = ["tasks"]) 

# CRUD - операция CREATE

@router.post("/", response_model=TaskRead)
async def create_task(task: TaskCreate, user:CurrentUser, session: SessionDep):
    db_task = Task.model_validate(task, update={"owner_id": user.id})
    session.add(db_task)
    await session.commit()
    await session.refresh(db_task)
    return db_task

# CRUD - операция READ (все объекты)
@router.get("/", response_model=list[TaskRead])
async def read_task(
    user: CurrentUser,
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
):
    tasks = await session.exec(
        select(Task).where(Task.owner_id == user.id)
        .offset(offset).limit(limit)
    )
    return tasks.all()

# CRUD - операция READ (1 объект)
@router.get("/{task_id}", response_model=TaskRead)
async def read_task_by_id(task_id: int, user: CurrentUser, session: SessionDep):
    task = await session.get(Task, task_id)
    if not task or task.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

# CRUD - операция UPDATE
@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(task_id: int, task: TaskUpdate, user: CurrentUser, session: SessionDep):
    task_db = await session.get(Task, task_id)
    if not task_db or task_db.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Task not found")
    task_data = task.model_dump(exclude_unset=True)
    task_db.sqlmodel_update(task_data)
    session.add(task_db)
    await session.commit()
    await session.refresh(task_db)
    return task_db

# CRUD операция DELETE
@router.delete("/{task_id}")
async def delete_task(task_id: int, user: CurrentUser, session: SessionDep):
    task = await session.get(Task, task_id)
    if not task or task.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Task not found")
    await session.delete(task)
    await session.commit()
    return {"ok": True}