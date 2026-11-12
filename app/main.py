# ТОЛЬКО: создать FastAPI(), lifespan, подключить роутеры

# app/main.py - точка входа FastAPI


from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import create_db_and_tables, engine
from app.routers.tasks import router as router_tasks
from app.routers.users import router_users


@asynccontextmanager
async def lifespan(app: FastAPI):  
    # Выполняется один раз при запуске (до приёма запросов) и один раз при остановке.
    # --- код до yield: при СТАРТЕ ---
    await create_db_and_tables()
    yield
    # --- код после yield: выполнится один раз при ОСТАНОВКЕ ---
    await engine.dispose()
    

app = FastAPI(lifespan=lifespan)  # само приложение


app.include_router(router_users)
app.include_router(router_tasks)


@app.get("/")
def root():
    return {"message": "ok"}
