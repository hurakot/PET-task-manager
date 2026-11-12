# Задача: рефактор структуры FastAPI-проекта под конвенции

## Контекст
Это учебный пет-проект — **Task Manager API** на FastAPI + SQLModel + PostgreSQL.
Автор — начинающий backend-разработчик, учится, поэтому важно не просто сделать,
а коротко объяснять каждое изменение. Комментарии в коде веду на русском — сохрани этот стиль.

Сейчас почти весь код лежит в одном `main.py` (создание приложения, подключение к БД,
сессии, настройки через `os.environ`, все CRUD-ручки, обработчики). Модель и схемы —
в отдельных файлах `models.py` и `schemas.py`.

## Цель
Привести проект к общепринятой раскладке FastAPI-проекта (по духу
https://github.com/zhanymkanov/fastapi-best-practices), **не меняя поведение**.
Это чистый рефакторинг: те же эндпоинты, те же ответы — меняется только организация кода.

## Что сделать (пошагово)
1. **Сначала прочитай текущие файлы** проекта (`main.py`, `models.py`, `schemas.py`,
   `database.py` если есть, `.env`, `alembic/` если есть) и покажи мне короткий план
   рефактора ДО внесения изменений. Дождись моего «ок».
2. Приведи структуру к такой раскладке:
   ```
   app/
   ├── main.py          # ТОЛЬКО: создание FastAPI(), lifespan, подключение роутеров
   ├── config.py        # настройки (DATABASE_URL, SECRET_KEY) через pydantic-settings
   ├── database.py      # engine, get_session, SessionDep, create_db_and_tables
   ├── models.py        # таблица Task (table=True)
   ├── schemas.py       # TaskBase / TaskCreate / TaskRead / TaskUpdate
   └── routers/
       ├── __init__.py
       └── tasks.py     # APIRouter со всеми ручками /tasks
   ```
3. **Вынеси все ручки в роутер**: в `routers/tasks.py` создай
   `router = APIRouter(prefix="/tasks", tags=["tasks"])` и перевесь ручки на него
   (`@router.get("/")`, `@router.get("/{task_id}")`, POST, PATCH, DELETE). Благодаря
   `prefix` пути внутри станут короче (`"/"` вместо `"/tasks/"`).
4. **Сделай `main.py` тонким**: там остаётся только создание `app`, `lifespan` и
   `app.include_router(tasks.router)`. Ни одной бизнес-ручки в `main.py` быть не должно.
5. **Вынеси настройки в `config.py`**: класс на `pydantic-settings` (`BaseSettings`),
   который читает `.env`; в коде обращение через `settings.DATABASE_URL`.
   Убери разбросанные `os.environ[...]`.
6. **Обнови все импорты** на доменные (`from app.database import SessionDep`,
   `from app.models import Task`, `from app.schemas import ...`, `from app.config import settings`).

## Ограничения (важно)
- **Не переусложняй.** Проект из одной сущности. НЕ добавляй слои `service.py`,
  `repository.py`, `dependencies.py` — для одной модели это избыточно. Только раскладка
  по файлам + роутер + конфиг.
- Поведение не меняем: те же пути, статусы и тела ответов, что сейчас.
- `.env` не трогай, секреты в код не хардкодь.
- Если проект запускается как `uvicorn app.main:app`, следи, чтобы импорты были
  пакетные (`from app. ...`) и `app/__init__.py`, `app/routers/__init__.py` существовали.
- По ходу коротко поясняй, что и зачем переносишь (я учусь).

## Критерии готовности
- `main.py` короткий: создание app + lifespan + `include_router`, без ручек.
- Все ручки `/tasks` живут в `routers/tasks.py` на `APIRouter`.
- Настройки читаются из `config.py` (не `os.environ` по всему коду).
- Приложение запускается, и в `/docs` те же эндпоинты, что были до рефактора.
- В конце прогони проверку: запусти приложение (или тесты через TestClient) и покажи,
  что основные сценарии (создание задачи, получение списка, получение по id,
  обновление, удаление, 404 на несуществующем id) работают как раньше.
