
# Работа с БД - engine, get_session, SessionDep, create_db_and_tables

from sqlmodel import SQLModel
from fastapi import Depends
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession


from typing import Annotated

from app.config import settings


# check_same_thread нужен только SQLite; Postgres такой аргумент не принимает
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_async_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session():
    # зависимость: выдаёт свежую сессию на каждый запрос
    async with SessionLocal() as session: # открывает сессию; по выходу из with закроет её сам,
        yield session # даже если внутри запроса случилась ошибка.
        # yield (а не return) - сессия "одолжена" на время запроса и вернётся обратно после

# Annotated[Session, Depends(get_session)] = "тип Session, который FastAPI"
# сам достанет через get_session." Дальше в ручках пищещь session: SessionDep
SessionDep = Annotated[AsyncSession, Depends(get_session)]

