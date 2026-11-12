# Схемы БД - модификации для оригинальной таблицы и для изменения оригинальной таблицы

# TaskBase / TaskCreate / TaskRead / TaskUpdate

from sqlmodel import Field, SQLModel


class TaskBase(SQLModel):
    title: str
    description: str | None = None


class TaskCreate(TaskBase):
    title: str
    description: str | None = None


class TaskRead(TaskBase):
    id: int
    title: str
    description: str | None = None
    is_done: bool = Field(default=False)


class TaskUpdate(TaskBase):
    title: str | None = None
    description: str | None = None
    is_done: bool | None = None


# Схемы, связанные с пользователями
class UserCreate(SQLModel):
    username: str
    password: str


class UserRead(SQLModel):
    id: int
    username: str


# Схемы, связанная с токеном
class Token(SQLModel):
    access_token: str
    token_type: str
