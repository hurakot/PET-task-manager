# Разработка и тесты

## Локальный запуск без Docker

Нужны Python 3.13 и запущенный PostgreSQL.

```bash
python3.13 -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt

cp .env.example .env        # заполнить DATABASE_URL (хост localhost), SECRET_KEY
uvicorn app.main:app --reload
```

`--reload` перезапускает сервер при изменении кода — только для разработки.

Открыть: http://localhost:8000/docs

## Локальный запуск в Docker

```bash
cp .env.example .env        # заполнить POSTGRES_PASSWORD, SECRET_KEY
docker compose up --build
```

Postgres в контейнере — отдельная база, не та, что установлена на компьютере.

## Тесты

```bash
python -m pytest -q
```

- Тесты не трогают PostgreSQL: до импорта приложения `DATABASE_URL` подменяется на `sqlite+aiosqlite:///./test.db`.
- `TestClient` запускает `lifespan`, поэтому таблицы создаются автоматически; после каждого теста файл `test.db` удаляется.
- Покрыто: регистрация, дубль имени, логин, защита ручек, CRUD, изоляция пользователей.

## Зависимости

| Файл | Что внутри | Где используется |
|---|---|---|
| `requirements.txt` | Только то, что нужно для работы приложения | Docker-образ, сервер |
| `requirements-dev.txt` | `-r requirements.txt` + pytest, httpx2, aiosqlite | Локальная разработка |

Добавить пакет:
1. `pip install <пакет>`
2. Вписать его с версией (`pip freeze | grep -i <пакет>`) в нужный файл.
3. Проверить: `python -m pytest -q` и `docker compose up --build`.

`pip freeze > requirements.txt` не используй — в файл попадёт всё из venv, включая тестовые пакеты.

## Полезные команды Docker

| Команда | Что делает |
|---|---|
| `docker compose up -d --build` | Собрать и запустить в фоне |
| `docker compose logs -f api` | Логи приложения |
| `docker compose ps` | Статус контейнеров (`db` должен быть `healthy`) |
| `docker compose down` | Остановить (данные сохраняются) |
| `docker compose down -v` | Остановить и **удалить данные БД** |
| `docker compose exec db psql -U postgres -d pet1fastapidb` | Консоль PostgreSQL |
