# Task Manager API

**Демо:** https://pet-task-manager.onrender.com/docs

> Демо работает на бесплатном тарифе Render: после ~15 минут простоя сервис засыпает, и первый запрос может идти до минуты. База демо периодически очищается — не храните там ничего важного.

REST API для личного списка задач с регистрацией и JWT-авторизацией. Каждый пользователь видит и меняет только свои задачи.

## Идея проекта

Учебный backend-проект на FastAPI, собранный по общепринятой структуре:

- регистрация и вход по логину/паролю, пароли хранятся только как bcrypt-хэши;
- выдача JWT-токена и защита всех ручек `/tasks` по нему;
- CRUD задач с изоляцией данных между пользователями;
- полностью асинхронная работа с PostgreSQL;
- запуск одной командой через Docker Compose, тесты на pytest.

## Стек технологий

| Область | Технологии |
|---|---|
| Язык | Python 3.13 |
| Веб-фреймворк | FastAPI, Uvicorn (uvloop, httptools) |
| ORM и валидация | SQLModel (SQLAlchemy 2.0 + Pydantic 2) |
| База данных | PostgreSQL 17, async-драйвер asyncpg |
| Настройки | pydantic-settings, `.env` |
| Авторизация | OAuth2 Password + JWT (PyJWT), bcrypt |
| Тесты | pytest, FastAPI TestClient, SQLite (aiosqlite) |
| Инфраструктура | Docker, Docker Compose (локально) |
| Деплой | Render: Web Service (Docker) + Render PostgreSQL |

## Документация

| Файл | Содержание |
|---|---|
| [docs/architecture.md](docs/architecture.md) | Структура проекта, слои, модель данных, путь запроса, асинхронность |
| [docs/api.md](docs/api.md) | Все эндпоинты, авторизация, коды ответов, примеры на curl |
| [docs/configuration.md](docs/configuration.md) | Переменные окружения, `.env`, генерация секретов |
| [docs/development.md](docs/development.md) | Локальный запуск, тесты, работа с зависимостями, команды Docker |
| [docs/deployment.md](docs/deployment.md) | Альтернатива Render — деплой на собственный VPS: SSH, firewall, Docker, nginx, HTTPS, бэкапы |
| [docs/known-issues.md](docs/known-issues.md) | Ограничения текущей версии и планы улучшений |

## Быстрый старт (локально, Docker)

Нужен установленный и запущенный Docker Desktop.

```bash
git clone https://github.com/hurakot/PET-task-manager/ PET-task-manager
cd PET-task-manager

cp .env.example .env
# в .env заполнить POSTGRES_PASSWORD и SECRET_KEY:
#   python3 -c "import secrets; print(secrets.token_hex(32))"

docker compose up --build
```

Открыть http://localhost:8000/docs:

1. `POST /users/register` — создать пользователя.
2. **Authorize** — ввести логин и пароль.
3. Работать с `/tasks`.

Остановить: `Ctrl+C`, затем `docker compose down` (данные сохранятся).

Запуск без Docker и тесты — в [docs/development.md](docs/development.md).

## Тесты

```bash
python3.13 -m venv venv && source venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest -q
```

## Деплой на Render

Так развёрнуто демо. Docker-compose на Render не используется: приложение и база — два отдельных сервиса.

**1. База:** New → **Postgres**, тариф Free. Запомнить регион, скопировать **Internal Database URL**.

**2. Приложение:** New → **Web Service** → репозиторий с GitHub, **Language: Docker**, регион тот же, что у базы. Health Check Path: `/`.

**3. Environment Variables веб-сервиса:**

| Key | Value |
|---|---|
| `DATABASE_URL` | Internal Database URL, в котором `postgresql://` заменено на **`postgresql+asyncpg://`** |
| `SECRET_KEY` | `python3 -c "import secrets; print(secrets.token_hex(32))"` |
| `ALGORITHM` | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` |

Порт задавать не нужно: Render передаёт его в переменной `PORT`, Dockerfile её подхватывает.

Без `+asyncpg` приложение не стартует (`The asyncio extension requires an async driver`). Пароли в код и в репозиторий не вписываются — только в Environment.

**Обновление:** `git push` в `main` — Render пересоберёт и перезапустит сервис сам.

## Запуск на собственном сервере (VPS)

Альтернатива Render, если нужен свой сервер под полным контролем. Демо развёрнуто не так — это инструкция для самостоятельного деплоя.

Кратко. Подробно, с объяснениями и решением проблем — [docs/deployment.md](docs/deployment.md).

Сервер: Ubuntu 22.04/24.04. Наружу открыты только SSH, 80 и 443; приложение слушает `127.0.0.1:8000`, к нему проксирует nginx.

**1. Подготовка сервера** (под пользователем с sudo, не root; SSH только по ключам — см. шаги 1–2 в deployment.md):
```bash
sudo ufw allow OpenSSH && sudo ufw allow 80/tcp && sudo ufw allow 443/tcp && sudo ufw enable

curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh
sudo usermod -aG docker $USER      # затем перелогиниться
```

**2. Код и настройки:**
```bash
git clone https://github.com/hurakot/PET-task-manager/ ~/PET-task-manager && cd ~/PET-task-manager
cp .env.example .env && chmod 600 .env
nano .env                          # НОВЫЕ POSTGRES_PASSWORD и SECRET_KEY
```

**3. Запуск:**
```bash
docker compose up -d --build
curl http://127.0.0.1:8000/        # {"message":"ok"}
```

**4. Доступ из интернета — nginx:**
```bash
sudo apt install -y nginx
sudo nano /etc/nginx/sites-available/taskmanager
```
```nginx
server {
    listen 80;
    server_name example.com;       # домен или IP сервера
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
```bash
sudo ln -s /etc/nginx/sites-available/taskmanager /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

**5. HTTPS** (нужен домен, указывающий на IP сервера):
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d example.com
```

Готово: **https://example.com/docs**

**Обновление:** `git pull && docker compose up -d --build`. Данные БД сохраняются. Не используй `docker compose down -v` — это удалит базу.

## Безопасность

- `.env` с секретами не попадает ни в git, ни в Docker-образ; в репозитории только `.env.example`.
- Приложение в контейнере работает от непривилегированного пользователя, без `--reload`.
- На Render секреты хранятся в Environment веб-сервиса, база подключается по внутреннему адресу и из интернета недоступна.
- На своём сервере: PostgreSQL не публикует порт наружу, API доступно только через nginx. Не меняй `127.0.0.1:8000:8000` в `docker-compose.yaml` на `8000:8000`: Docker обходит ufw, и порт окажется открыт в интернет.
