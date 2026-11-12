# Конфигурация

Настройки читаются классом `Settings` в `app/config.py` (pydantic-settings).
Источники по приоритету:

1. **Переменные окружения** (в Docker их задаёт `docker-compose.yaml`).
2. Файл **`.env`** в текущей папке (для локального запуска).

Файл `.env` содержит секреты — он в `.gitignore` и `.dockerignore`. В git хранится только шаблон `.env.example`:

```bash
cp .env.example .env
```

## Переменные

| Переменная | Кто использует | Пример | Описание |
|---|---|---|---|
| `POSTGRES_USER` | контейнер `db`, compose | `postgres` | Пользователь PostgreSQL |
| `POSTGRES_PASSWORD` | контейнер `db`, compose | — | Пароль PostgreSQL. **Секрет** |
| `POSTGRES_DB` | контейнер `db`, compose | `pet1fastapidb` | Имя базы |
| `DATABASE_URL` | приложение | `postgresql+asyncpg://postgres:pass@localhost:5432/pet1fastapidb` | Строка подключения. Только async-драйверы |
| `SECRET_KEY` | приложение | — | Ключ подписи JWT. **Секрет** |
| `ALGORITHM` | приложение | `HS256` | Алгоритм подписи JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | приложение | `30` | Время жизни токена |

## DATABASE_URL: локально и в Docker

- **Локально** (uvicorn из venv) берётся значение из `.env`, хост — `localhost`.
- **В Docker** compose собирает строку сам из `POSTGRES_*` с хостом `db` (имя сервиса в сети compose) и передаёт как переменную окружения — она перебивает `.env`. Поэтому `DATABASE_URL` в `.env` на сервере не используется, но пароль в нём лучше держать в соответствии с `POSTGRES_PASSWORD`.

Схема строки обязательно с async-драйвером:

| БД | Схема |
|---|---|
| PostgreSQL | `postgresql+asyncpg://` |
| SQLite (тесты) | `sqlite+aiosqlite://` |

С `postgresql://` без драйвера приложение упадёт при старте: `The asyncio extension requires an async driver`.

## Генерация секретов

```bash
# SECRET_KEY
python3 -c "import secrets; print(secrets.token_hex(32))"

# POSTGRES_PASSWORD (без символов, ломающих URL: @ : / ?)
python3 -c "import secrets; print(secrets.token_urlsafe(24))"
```

Правила:
- На сервере — **свои** значения, не те, что на ноутбуке.
- Пустой `SECRET_KEY` приложение сейчас примет — это опасно (токены можно подделать). Заполняй всегда.
- Смена `SECRET_KEY` делает все выданные токены недействительными — пользователям нужно залогиниться заново.
- Пароль Postgres задаётся **только при первом создании** volume. Если поменять `POSTGRES_PASSWORD` позже, контейнер `db` продолжит ждать старый пароль. Сменить: `ALTER USER` внутри БД, либо (с потерей данных) `docker compose down -v`.
