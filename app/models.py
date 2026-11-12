# таблица Task (table=True)


from sqlmodel import Field, SQLModel

from app.schemas import TaskBase


class Task(TaskBase, table=True):
    # table=True - это настоящая таблица в БД (а не просто схема валидации)
    __tablename__ = "tasks"
    id: int | None = Field(
        default=None, primary_key=True
    )  # первичный ключ, БД заполнит сама
    owner_id: int = Field(foreign_key="users.id", index=True)
    title: str = Field(index=True)  # обязательное поле
    description: str | None = None  # необязательное (может быть NULL)
    is_done: bool = Field(default=False)  # по умолчанию False


class User(SQLModel, table=True):
    __tablename__ = "users"
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str  # Только хэш, не сам пароль
