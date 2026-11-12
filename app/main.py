
# ТОЛЬКО: создать FastAPI(), lifespan, подключить роутеры

# app/main.py - точка входа FastAPI


from fastapi import FastAPI
from contextlib import asynccontextmanager



from app.database import create_db_and_tables, engine
from app.routers.tasks import router as router_tasks
from app.routers.users import router_users as router_users


@asynccontextmanager
async def lifespan(app: FastAPI): # Занимается выполнением кода один раз при запуске приложения 
                                  #(до того, как оно начнёт принимать запросы) и один раз при остановке.
    # --- код до yield: выполнится один раз при СТАРТЕ ---
    await create_db_and_tables()
    yield
    await engine.dispose()
    # --- код после yield: выполнится один раз при ОСТАНОВКЕ ---
    # сюда позже можно положить закрытие соединений, если понадобится

app = FastAPI(lifespan=lifespan) # само приложение


app.include_router(router_users)
app.include_router(router_tasks)

@app.get("/")
def root():
    return {"message": "ok"}







