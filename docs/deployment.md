# Деплой на сервер

Пошаговая инструкция: чистый VPS на Ubuntu → API доступно из интернета по HTTPS.

Итоговая схема:

```
Интернет ──443/80──▶ nginx (на сервере) ──▶ 127.0.0.1:8000 ──▶ контейнер api ──▶ контейнер db
                     HTTPS, Let's Encrypt     порт закрыт снаружи                 порт не публикуется
```

Наружу открыты только 22 (SSH), 80 и 443. PostgreSQL и сам uvicorn из интернета недоступны.

## 0. Что нужно

- VPS с Ubuntu 22.04 или 24.04, от 1 ГБ RAM.
- IP-адрес сервера и доступ по SSH.
- Желательно домен (для HTTPS). Без домена API будет работать по `http://IP`, но пароли и токены пойдут открытым текстом — только для проверки.

Ниже `SERVER_IP` — IP сервера, `example.com` — твой домен. Подставляй свои значения.

## 1. Пользователь для работы (не root)

С Mac, если ещё нет SSH-ключа:
```bash
ssh-keygen -t ed25519
```

Первый вход:
```bash
ssh root@SERVER_IP
```

На сервере:
```bash
adduser deploy                      # задать пароль (нужен для sudo)
usermod -aG sudo deploy
# скопировать SSH-ключи root'а новому пользователю
rsync --archive --chown=deploy:deploy ~/.ssh /home/deploy
```

Если хостер выдал доступ по паролю, а не по ключу — с Mac:
```bash
ssh-copy-id deploy@SERVER_IP
```

**В новом окне терминала** проверь, что вход работает: `ssh deploy@SERVER_IP`. Дальше всё — под `deploy`.

## 2. SSH только по ключам

```bash
sudo tee /etc/ssh/sshd_config.d/00-hardening.conf > /dev/null <<'EOF'
PasswordAuthentication no
PermitRootLogin no
EOF
sudo sshd -t && sudo systemctl restart ssh
```

Имя файла начинается с `00-`: sshd берёт **первое** найденное значение, а в облачных образах есть `50-cloud-init.conf`, который может включать пароли.

Не закрывая текущую сессию, проверь вход в новом окне: `ssh deploy@SERVER_IP`.

## 3. Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status
```

> **Важно.** Docker обходит ufw для опубликованных портов. Поэтому в `docker-compose.yaml` порт api привязан к `127.0.0.1:8000:8000`. Не меняй на `"8000:8000"` — порт станет открыт в интернет, и ufw этому не помешает.

## 4. Docker

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker deploy
```

Перелогинься (`exit`, затем снова `ssh`), чтобы группа применилась. Проверка:
```bash
docker run --rm hello-world
docker compose version
```

Группа `docker` по правам равна root — не добавляй в неё посторонних.

## 5. Код на сервере

**Вариант А — git (рекомендуется):**
```bash
cd ~
git clone https://github.com/<user>/<repo>.git PET-task-manager
cd PET-task-manager
```
Для приватного репозитория нужен deploy key (GitHub → Settings → Deploy keys).

**Вариант Б — копирование с Mac** (из папки проекта):
```bash
rsync -av --exclude venv --exclude .env --exclude '__pycache__' \
  --exclude '*.db' --exclude .pytest_cache \
  ./ deploy@SERVER_IP:~/PET-task-manager/
```

## 6. Настройки (.env)

```bash
cd ~/PET-task-manager
cp .env.example .env
chmod 600 .env                     # читать может только владелец

# сгенерировать секреты
python3 -c "import secrets; print(secrets.token_hex(32))"      # → SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(24))"  # → POSTGRES_PASSWORD

nano .env
```

Заполни `POSTGRES_PASSWORD` и `SECRET_KEY` **новыми** значениями (не теми, что на Mac). Подробно о переменных — [configuration.md](configuration.md).

## 7. Запуск

```bash
docker compose up -d --build
docker compose ps                  # db: healthy, api: running
curl http://127.0.0.1:8000/        # {"message":"ok"}
```

Если не стартует — `docker compose logs api`.

**Проверка без nginx** (через SSH-туннель, с Mac):
```bash
ssh -L 8000:127.0.0.1:8000 deploy@SERVER_IP
```
Пока сессия открыта, http://localhost:8000/docs на Mac открывает API с сервера.

## 8. nginx — доступ из интернета

```bash
sudo apt update && sudo apt install -y nginx
sudo tee /etc/nginx/sites-available/taskmanager > /dev/null <<'EOF'
server {
    listen 80;
    server_name example.com;          # домен, или IP сервера если домена нет

    server_tokens off;                # не показывать версию nginx
    client_max_body_size 1m;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
sudo ln -s /etc/nginx/sites-available/taskmanager /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

Теперь `http://example.com/docs` (или `http://SERVER_IP/docs`) открывается из браузера.

## 9. HTTPS (Let's Encrypt)

Нужен домен, у которого A-запись указывает на `SERVER_IP` (проверка: `dig +short example.com`).

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d example.com
sudo certbot renew --dry-run       # проверка автопродления
```

certbot сам допишет конфиг nginx и включит редирект с http на https. Сертификат продлевается автоматически.

Итог: **https://example.com/docs**

## 10. Обновление приложения

```bash
cd ~/PET-task-manager
git pull                           # или rsync с Mac (вариант Б)
docker compose up -d --build
docker image prune -f              # удалить старые образы
```

Данные БД сохраняются. **Никогда не используй `docker compose down -v` на сервере** — `-v` удаляет базу.

Если поменялись поля моделей — см. [known-issues.md](known-issues.md#нет-миграций-бд).

## 11. Перезагрузка сервера

У сервисов `restart: unless-stopped`, Docker запускается вместе с системой — после `sudo reboot` всё поднимется само. Проверь один раз: `sudo reboot`, затем `docker compose ps`.

## 12. Бэкап БД

```bash
cd ~/PET-task-manager
docker compose exec -T db pg_dump -U postgres pet1fastapidb > backup_$(date +%F).sql
```

Скачать на Mac:
```bash
scp deploy@SERVER_IP:~/PET-task-manager/backup_*.sql .
```

Восстановить:
```bash
docker compose exec -T db psql -U postgres -d pet1fastapidb < backup_2026-01-01.sql
```

Файлы бэкапа содержат хэши паролей — не коммить их и не храни в публичных местах.

## Частые проблемы

| Симптом | Причина | Что делать |
|---|---|---|
| `502 Bad Gateway` | Контейнер api не запущен | `docker compose ps`, `docker compose logs api` |
| `password authentication failed` в логах | `POSTGRES_PASSWORD` поменяли после первого запуска | Вернуть старый пароль или сменить через `ALTER USER` |
| `The asyncio extension requires an async driver` | В `DATABASE_URL` нет `+asyncpg` | Исправить схему в compose/`.env` |
| `ModuleNotFoundError` | Пакета нет в `requirements.txt` | Добавить, `docker compose up -d --build` |
| `/docs` открывается, Authorize не работает | Запрос `/users/token` упал | Смотреть ответ в Swagger и логи api |
| `permission denied ... docker.sock` | Не перелогинился после `usermod -aG docker` | `exit` и зайти снова |

## Чек-лист безопасности

- [ ] Приложение работает не от root (в образе — `appuser`), на сервере — пользователь `deploy`
- [ ] SSH только по ключам, root-вход запрещён
- [ ] ufw: открыты только 22, 80, 443
- [ ] PostgreSQL не публикует порт; api слушает только `127.0.0.1`
- [ ] `.env` с новыми секретами, `chmod 600`, не в git
- [ ] Нет `--reload` и debug-режима
- [ ] HTTPS включён
