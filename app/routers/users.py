
# APIRouter со всеми ручками /users

from sqlmodel import Field, Session, SQLModel, create_engine, select
from fastapi import HTTPException, Depends, FastAPI, Query, APIRouter

from contextlib import asynccontextmanager
from typing import Annotated

from app.models import Task
from app.schemas import TaskUpdate, TaskRead, TaskCreate
from app.database import SessionDep




from datetime import datetime, timedelta, timezone
from typing import Annotated

import bcrypt
import jwt                                   # библиотека PyJWT
from jwt.exceptions import InvalidTokenError
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Field, Session, SQLModel, create_engine, select

from app.schemas import UserRead, UserCreate, Token
from app.models import User, Task
from app.security import hash_password, verify_password, create_access_token
from app.dependencies import CurrentUser

from fastapi.concurrency import run_in_threadpool

# Ручки API, связанные с tasks

router_users = APIRouter(prefix="/users", tags = ["users"]) 

# Регистрация пользователя

@router_users.post("/register", response_model=UserRead)
async def register(data: UserCreate, session: SessionDep):
    result = await session.exec(select(User).where(User.username == data.username))
    if result.first():
        raise HTTPException(status_code=400, detail="Username already taken")
    user = User(username=data.username, hashed_password=await run_in_threadpool(hash_password, data.password))
    session.add(user); await session.commit(); await session.refresh(user)
    return user

# Логин => JWT
@router_users.post("/token", response_model=Token)
async def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], session: SessionDep):
    result = await session.exec(select(User).where(User.username == form.username))
    user = result.first()
    if not user or not await run_in_threadpool(verify_password, form.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    token = create_access_token({"sub": user.username})
    return Token(access_token=token, token_type="bearer")

