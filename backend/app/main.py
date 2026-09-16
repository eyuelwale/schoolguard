import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .routers import (
    auth,
    users,
    classes,
    students,
    parents,
    attendance,
    notifications,
    dashboard,
    telegram,
    schools
)

bot_app_instance = None
bot_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global bot_app_instance, bot_task
    # Startup: Start Telegram bot background worker if token is configured
    if settings.TELEGRAM_BOT_TOKEN:
        try:
            try:
                from backend.bot.main import build_bot_app, start_bot_polling, stop_bot_polling
            except ModuleNotFoundError:
                from bot.main import build_bot_app, start_bot_polling, stop_bot_polling

            bot_app_instance = build_bot_app(settings.TELEGRAM_BOT_TOKEN)
            bot_task = asyncio.create_task(start_bot_polling(bot_app_instance))
            print("Telegram Bot: Cloud background task launched.")
        except Exception as e:
            print(f"Telegram Bot Startup Warning: Could not start bot worker: {e}")

    yield

    # Shutdown: Stop Telegram bot background worker
    if bot_app_instance:
        try:
            try:
                from backend.bot.main import stop_bot_polling
            except ModuleNotFoundError:
                from bot.main import stop_bot_polling
            await stop_bot_polling(bot_app_instance)
        except Exception as e:
            print(f"Telegram Bot Shutdown Warning: {e}")
    if bot_task and not bot_task.done():
        bot_task.cancel()


app = FastAPI(
    title="SchoolGuard API",
    version="1.0.0",
    description="School attendance, parent notification and Telegram integration API.",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_origin_regex=r"^https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in [
    auth.router,
    users.router,
    classes.router,
    students.router,
    parents.router,
    attendance.router,
    notifications.router,
    dashboard.router,
    telegram.router,
    schools.router
]:
    app.include_router(router)


@app.get("/")
def root():
    return {
        "name": settings.APP_NAME,
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


if __name__ == "__main__":
    import os
    import uvicorn

    port = int(os.environ.get("PORT", 8000))

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )
