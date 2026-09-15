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

app = FastAPI(
    title="SchoolGuard API",
    version="1.0.0",
    description="School attendance, parent notification and Telegram integration API.",
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
