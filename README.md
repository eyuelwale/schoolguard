# SchoolGuard  School Attendance & Parent Notification Platform

A scalable starter implementation with:

- FastAPI backend
- MySQL database
- Telegram parent/teacher bot
- React + Vite frontend
- JWT authentication
- Role-based access control
- Student/parent/teacher/class management
- QR attendance-ready API
- Arrival/departure tracking
- Parent Telegram notifications
- Timetable and class-end notification hooks
- Docker Compose for local development

## Architecture

React UI -> FastAPI -> MySQL
Telegram Bot -> FastAPI service layer -> MySQL
QR/Scanner -> FastAPI -> Attendance service -> Notification service -> Telegram

## Quick start

### 1. Environment

Copy `.env.example` to `.env` and change secrets.

### 2. Start MySQL + backend

```bash
docker compose up --build
```

Backend:
- API: http://localhost:8000
- Swagger: http://localhost:8000/docs

Frontend:
- http://localhost:5173

### 3. Database

The MySQL container automatically runs `database/init/001_schema.sql`.

### 4. Create an admin

```bash
curl -X POST http://localhost:8000/api/auth/bootstrap-admin \
  -H "Content-Type: application/json" \
  -d '{"full_name":"System Admin","email":"admin@schoolguard.local","password":"ChangeMe123!"}'
```

### 5. Telegram bot

Create a bot with BotFather, put its token in `.env`, then:

```bash
python -m bot.main
```

For Docker, the `telegram_bot` service is included in `docker-compose.yml`.

## Important production notes

This repository is a strong MVP/reference implementation, not a claim of production certification. Before deployment with real student data:

- change every default secret
- use HTTPS
- restrict CORS to your real frontend domain
- use Alembic migrations instead of schema bootstrapping
- configure Telegram webhook instead of polling where appropriate
- add a background queue such as Redis/Celery or RQ for notifications
- add backups, monitoring, rate limiting and structured audit retention
- enforce school/tenant isolation if supporting multiple schools
- review local privacy/data-protection requirements
- use a real QR token strategy rather than exposing student IDs
