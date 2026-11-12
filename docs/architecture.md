# Архитектура

## Структура проекта

```
PET-task-manager/
├── app/
│   ├── main.py          # создание FastAPI(), lifespan, подключение роутеров
│   ├── config.py        # настройки из переменных окружения / .env (pydantic-settings)
│   ├── database.py      # async engine, фабрика сессий, get_session, SessionDep
│   ├── models.py        # таблицы БД: User, Task (SQLModel, table=True)
│   ├── schemas.py       # схемы запросов/ответов: TaskCreate, TaskRead, UserCreate, Token...
│   ├── security.py      # хэширование паролей (bcrypt) и выпуск JWT
│   ├── dependencies.py  # get_current_user / CurrentUser — проверка JWT
│   └── routers/
│       ├── users.py     # /users/register, /users/token
│       └── tasks.py     # CRUD /tasks
├── docs/                # документация
├── test_app.py          # тесты (pytest + TestClient)
├── Dockerfile           # образ приложения
├── docker-compose.yaml  # приложение + PostgreSQL
├── requirements.txt     # зависимости для работы приложения
├── requirements-dev.txt # + зависимости для тестов
└── .env.example         # шаблон настроек
```

## Слои и их ответственность

| Слой | Файл | Что делает |
|---|---|---|
| Точка входа | `main.py` | Создаёт приложение, при старте создаёт таблицы, при остановке закрывает пул соединений |
| Настройки | `config.py` | Читает `DATABASE_URL`, `SECRET_KEY` и др. Переменные окружения важнее значений из `.env` |
| БД | `database.py` | Один `AsyncEngine` на всё приложение; на каждый запрос — своя `AsyncSession` |
| Модели | `models.py` | Описание таблиц `users` и `tasks` |
| Схемы | `schemas.py` | Что API принимает и что отдаёт (например, `hashed_password` наружу не уходит) |
| Безопасность | `security.py` | `hash_password`, `verify_password`, `create_access_token` |
| Авторизация | `dependencies.py` | Достаёт токен из заголовка, проверяет подпись и срок, находит пользователя |
| Ручки | `routers/` | HTTP-эндпоинты |

## Модель данных

```
users                          tasks
─────────────────────          ──────────────────────────────
id              PK             id           PK
username        UNIQUE, index  owner_id     FK → users.id, index
hashed_password                title        index
                               description  NULL
                               is_done      default false
```

Один пользователь → много задач. Каждая задача принадлежит ровно одному пользователю.

## Как проходит запрос

Пример: `GET /tasks/` с заголовком `Authorization: Bearer <token>`.

1. FastAPI видит в ручке зависимости `CurrentUser` и `SessionDep`.
2. `get_session` открывает `AsyncSession`.
3. `get_current_user` берёт токен из заголовка, проверяет подпись (`SECRET_KEY`) и срок (`exp`), достаёт `username` из поля `sub` и ищет пользователя в БД. Нет токена / он неверный / пользователя нет → `401`.
4. Ручка выбирает задачи с `owner_id == user.id`.
5. Ответ фильтруется схемой `TaskRead`, сессия закрывается.

## Изоляция данных пользователей

Все операции с задачами фильтруются по `owner_id`. Чужая задача возвращает **`404 Task not found`**, а не `403` — так нельзя узнать, существует ли задача с таким `id`. Поведение проверяется тестом `test_user_isolation`.

`id` задач сквозные для всей таблицы, поэтому у одного пользователя могут быть задачи `3, 7, 8` — это нормально.

## Асинхронность

- Драйверы: `asyncpg` (PostgreSQL) и `aiosqlite` (SQLite в тестах). Схема в `DATABASE_URL` обязана указывать async-драйвер: `postgresql+asyncpg://`, `sqlite+aiosqlite://`.
- SQLAlchemy использует `greenlet` для async-режима — пакет обязателен.
- `expire_on_commit=False` — объекты остаются читаемыми после `commit()`, без лишнего похода в БД.
- bcrypt специально медленный, поэтому `hash_password` / `verify_password` вызываются через `run_in_threadpool`, чтобы не блокировать event loop.
- Правило для запросов: сначала `await`, потом метод результата:
  ```python
  result = await session.exec(select(...))
  rows = result.all()
  ```

## Создание таблиц

Таблицы создаются при старте через `SQLModel.metadata.create_all` (в `lifespan`). Это создаёт **только отсутствующие** таблицы и **не меняет** существующие. Подробнее — в [known-issues.md](known-issues.md).
