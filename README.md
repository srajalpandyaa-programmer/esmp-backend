# ESMP

Integrated Enterprise Service Management Platform:

- FastAPI backend
- PostgreSQL database
- React + TypeScript frontend

## Requirements

- Python 3.12+
- Node.js 20+
- PostgreSQL 14+

## First-time setup

Open PowerShell:

```powershell
cd "C:\Users\DELL\Major Project\esmp"
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
cd frontend
npm install
cd ..
```

Configure `.env` with a real PostgreSQL URL and secret:

```dotenv
DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/esmp
JWT_SECRET_KEY=your-long-random-secret
CORS_ORIGINS=http://localhost:5173
```

Create the database if needed, then apply migrations:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\createdb.exe" -U postgres esmp
alembic upgrade head
```

## Run the complete project locally

Use two PowerShell windows.

### Terminal 1 - backend

```powershell
cd "C:\Users\DELL\Major Project\esmp"
.\venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend: http://127.0.0.1:8000
Swagger: http://127.0.0.1:8000/docs

### Terminal 2 - frontend

```powershell
cd "C:\Users\DELL\Major Project\esmp\frontend"
npm run dev
```

Frontend: http://localhost:5173

The frontend uses `VITE_API_URL` from `frontend/.env`, defaulting to
`http://127.0.0.1:8000/api/v1`. To override it:

```powershell
Copy-Item frontend\.env.example frontend\.env
```

## Test and build

```powershell
python -m compileall -q app alembic
python -m pytest -q
alembic heads
cd frontend
npm run build
```

## Main flow

1. Open the frontend.
2. Register an Employee account or log in.
3. Use the dashboard to create tickets and view records.
4. Use Swagger for administrative endpoints and asset/approval setup.

The frontend is in [frontend/](./frontend), and the backend API is in
[app/](./app).

## Deploy to GitHub and Render

Commit and push from the repository root:

```powershell
git add .
git status
git commit -m "Integrate ESMP frontend and Render deployment"
git push origin main
```

Confirm `.env` is not shown by `git status`. It is excluded by `.gitignore`.

On Render:

1. Open https://dashboard.render.com.
2. Select **New +** and **Blueprint**.
3. Connect the GitHub repository `srajalpandyaa-programmer/esmp-backend`.
4. Select the `main` branch.
5. Render detects `render.yaml`.
6. Apply the blueprint.
7. Wait for the PostgreSQL database and web service to finish deploying.

The Render service automatically:

- Builds the React frontend.
- Builds the Python backend.
- Runs `alembic upgrade head`.
- Starts Uvicorn on Render's `$PORT`.
- Serves the frontend and API from one URL.

After deployment, open the generated Render URL. Swagger is available at
`https://YOUR-SERVICE.onrender.com/docs`.
