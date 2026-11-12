# Образ для FastAPI-приложения Task Manager

# Та же версия Python, что и в локальном venv (3.13). slim — урезанный Debian, образ меньше.
FROM python:3.13-slim

# PYTHONDONTWRITEBYTECODE — не создавать .pyc файлы внутри контейнера
# PYTHONUNBUFFERED — логи (print, uvicorn) сразу видны в `docker compose logs`, без буфера
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Рабочая папка внутри контейнера — все следующие команды выполняются отсюда
WORKDIR /code

# Сначала копируем ТОЛЬКО requirements.txt и ставим зависимости.
# Docker кэширует слои: пока requirements.txt не меняется, этот шаг не повторяется
# при каждой правке кода — сборка идёт за секунды.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Отдельный непривилегированный пользователь — приложение НЕ работает от root
RUN useradd --create-home --uid 1000 appuser

# Теперь копируем сам код (то, что не исключено в .dockerignore)
COPY --chown=appuser:appuser ./app ./app

USER appuser

# Документируем порт, на котором слушает приложение
EXPOSE 8000

# Без --reload: это режим для разработки, в контейнере он не нужен.
# --host 0.0.0.0 — слушать все интерфейсы ВНУТРИ контейнера, иначе снаружи не достучаться.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
