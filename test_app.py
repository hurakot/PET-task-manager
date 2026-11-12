import os
# Отдельная БД ТОЛЬКО для тестов: временный файл SQLite через async-драйвер aiosqlite.
# Переменную ставим ДО импорта app — иначе engine создастся с адресом из .env (Postgres).
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"

import pytest
from fastapi.testclient import TestClient

from app.main import app   # твоё приложение (lifespan сам создаст таблицы)


@pytest.fixture(name="client")
def client_fixture():
    # with TestClient -> запускается lifespan: create_db_and_tables() при старте,
    # engine.dispose() при остановке. Подменять get_session больше не нужно.
    with TestClient(app) as client:
        yield client
    # чистая база для следующего теста
    if os.path.exists("test.db"):
        os.remove("test.db")


# Помощник: зарегистрировать + залогинить, вернуть заголовок с токеном
def auth_headers(client, username, password):
    client.post("/users/register", json={"username": username, "password": password})
    token = client.post("/users/token", data={"username": username, "password": password}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ---------- Регистрация ----------
def test_register_ok(client):
    r = client.post("/users/register", json={"username": "alice", "password": "secret1"})
    assert r.status_code == 200
    body = r.json()
    assert body["username"] == "alice"
    assert "password" not in body and "hashed_password" not in body

def test_register_duplicate(client):
    client.post("/users/register", json={"username": "alice", "password": "secret1"})
    r = client.post("/users/register", json={"username": "alice", "password": "other"})
    assert r.status_code == 400


# ---------- Логин ----------
def test_login_wrong_password(client):
    client.post("/users/register", json={"username": "alice", "password": "secret1"})
    r = client.post("/users/token", data={"username": "alice", "password": "WRONG"})
    assert r.status_code == 400

def test_login_ok(client):
    client.post("/users/register", json={"username": "alice", "password": "secret1"})
    r = client.post("/users/token", data={"username": "alice", "password": "secret1"})
    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer"
    assert r.json()["access_token"]


# ---------- Защита ----------
def test_tasks_require_auth(client):
    assert client.get("/tasks/").status_code == 401

def test_tasks_bad_token(client):
    assert client.get("/tasks/", headers={"Authorization": "Bearer garbage"}).status_code == 401


# ---------- CRUD под своим пользователем ----------
def test_crud_flow(client):
    h = auth_headers(client, "alice", "secret1")

    created = client.post("/tasks/", headers=h, json={"title": "task 1"})
    assert created.status_code == 200
    task_id = created.json()["id"]

    assert len(client.get("/tasks/", headers=h).json()) == 1
    assert client.get(f"/tasks/{task_id}", headers=h).status_code == 200

    upd = client.patch(f"/tasks/{task_id}", headers=h, json={"is_done": True})
    assert upd.status_code == 200 and upd.json()["is_done"] is True

    assert client.delete(f"/tasks/{task_id}", headers=h).status_code == 200
    assert client.get(f"/tasks/{task_id}", headers=h).status_code == 404


# ---------- Изоляция per-user ----------
def test_user_isolation(client):
    ah = auth_headers(client, "alice", "secret1")
    bh = auth_headers(client, "bob", "secret2")

    a_task = client.post("/tasks/", headers=ah, json={"title": "alice task"}).json()
    client.post("/tasks/", headers=bh, json={"title": "bob task"})

    assert len(client.get("/tasks/", headers=ah).json()) == 1
    assert len(client.get("/tasks/", headers=bh).json()) == 1

    assert client.get(f"/tasks/{a_task['id']}", headers=bh).status_code == 404
    assert client.patch(f"/tasks/{a_task['id']}", headers=bh, json={"is_done": True}).status_code == 404
    assert client.delete(f"/tasks/{a_task['id']}", headers=bh).status_code == 404