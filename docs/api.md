# API

Интерактивная документация доступна на запущенном сервере:

- Swagger UI — `/docs`
- ReDoc — `/redoc`
- OpenAPI-схема — `/openapi.json`

## Сводка эндпоинтов

| Метод | Путь | Авторизация | Описание |
|---|---|---|---|
| GET | `/` | — | Проверка, что сервис жив: `{"message": "ok"}` |
| POST | `/users/register` | — | Регистрация |
| POST | `/users/token` | — | Логин, выдаёт JWT |
| POST | `/tasks/` | Bearer | Создать задачу |
| GET | `/tasks/` | Bearer | Список своих задач |
| GET | `/tasks/{task_id}` | Bearer | Одна задача |
| PATCH | `/tasks/{task_id}` | Bearer | Частичное обновление |
| DELETE | `/tasks/{task_id}` | Bearer | Удаление |

## Авторизация

Схема OAuth2 Password + JWT (Bearer).

1. Зарегистрироваться: `POST /users/register`.
2. Получить токен: `POST /users/token` (данные формы, не JSON).
3. Передавать токен в каждом запросе к `/tasks`:
   ```
   Authorization: Bearer <access_token>
   ```

Токен живёт `ACCESS_TOKEN_EXPIRE_MINUTES` минут (по умолчанию 30). После этого — `401`, нужно залогиниться снова.

В Swagger UI: кнопка **Authorize** → ввести `username` и `password` (поля `client_id`/`client_secret` оставить пустыми).

## Пользователи

### POST /users/register

Тело (JSON):
```json
{ "username": "alice", "password": "secret1" }
```

| Код | Когда | Тело |
|---|---|---|
| 200 | Успех | `{"id": 1, "username": "alice"}` |
| 400 | Имя занято | `{"detail": "Username already taken"}` |
| 422 | Невалидное тело | ошибка валидации |

Пароль хранится только в виде bcrypt-хэша и в ответах не возвращается.

### POST /users/token

Тело — `application/x-www-form-urlencoded`: `username=alice&password=secret1`

| Код | Когда | Тело |
|---|---|---|
| 200 | Успех | `{"access_token": "eyJ...", "token_type": "bearer"}` |
| 400 | Неверное имя или пароль | `{"detail": "Incorrect username or password"}` |

## Задачи

Все ручки требуют токен. Без токена или с невалидным токеном — `401 Could not validate credentials`.
Чужая или несуществующая задача — `404 Task not found`.

Объект задачи (`TaskRead`):
```json
{ "id": 3, "title": "Купить хлеб", "description": null, "is_done": false }
```

### POST /tasks/
```json
{ "title": "Купить хлеб", "description": "бородинский" }
```
`title` обязателен, `description` — нет. Ответ `200` с созданной задачей. `owner_id` проставляется из токена.

### GET /tasks/
Query-параметры: `offset` (по умолчанию 0), `limit` (по умолчанию 100, максимум 100).
Ответ `200` — массив задач **текущего** пользователя.

### GET /tasks/{task_id}
Ответ `200` — задача, либо `404`.

### PATCH /tasks/{task_id}
Передаются только меняемые поля:
```json
{ "is_done": true }
```
Ответ `200` — обновлённая задача, либо `404`.

### DELETE /tasks/{task_id}
Ответ `200` — `{"ok": true}`, либо `404`.

## Примеры на curl

```bash
BASE=http://localhost:8000

curl -X POST $BASE/users/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"secret1"}'

TOKEN=$(curl -s -X POST $BASE/users/token \
  -d "username=alice&password=secret1" | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')

curl -X POST $BASE/tasks/ -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" -d '{"title":"Первая задача"}'

curl $BASE/tasks/ -H "Authorization: Bearer $TOKEN"

curl -X PATCH $BASE/tasks/1 -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" -d '{"is_done":true}'

curl -X DELETE $BASE/tasks/1 -H "Authorization: Bearer $TOKEN"
```
