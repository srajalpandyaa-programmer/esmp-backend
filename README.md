# ESMP API

Enterprise Service Management Platform backend built with FastAPI, SQLAlchemy,
Alembic, and PostgreSQL.

## Requirements

- Python 3.12 or newer
- PostgreSQL 14 or newer

## Windows setup

Open PowerShell in this directory:

```powershell
cd "C:\Users\DELL\Major Project\esmp"
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and set a real database URL and a long random JWT secret:

```dotenv
DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/esmp
JWT_SECRET_KEY=replace-with-a-long-random-secret
```

Create the `esmp` PostgreSQL database, then apply migrations:

```powershell
alembic upgrade head
```

Start the development server:

```powershell
python -m uvicorn app.main:app --reload
```

Open:

- API: http://127.0.0.1:8000
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc
- Health: http://127.0.0.1:8000/health
- Readiness: http://127.0.0.1:8000/health/ready

## Test and validation

```powershell
python -m compileall -q app alembic
python -m pytest -q
alembic heads
```

Public registration always creates an Employee account. Admins can create
elevated accounts through `POST /api/v1/users`.

## Main endpoints

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`
- `GET /api/v1/dashboard/me`
- `POST /api/v1/tickets`
- `GET /api/v1/tickets`
- `GET /api/v1/tickets/{ticket_id}/history`
- `POST /api/v1/assets`
- `POST /api/v1/assets/{asset_id}/assign`
- `POST /api/v1/assets/{asset_id}/return`
- `PATCH /api/v1/assets/{asset_id}/retire`
- `GET /api/v1/notifications`
- `PATCH /api/v1/notifications/read-all`
- `GET /api/v1/audit-logs`

Use the `Authorize` button in Swagger UI with:

```text
Bearer <access_token>
```
