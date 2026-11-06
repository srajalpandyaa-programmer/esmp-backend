# ESMP Frontend

React and TypeScript frontend for the ESMP FastAPI backend.

## Run locally

```powershell
cd "C:\Users\DELL\Major Project\frontend"
npm install
Copy-Item .env.example .env
npm run dev
```

Open `http://localhost:5173`.

The backend must be running at `http://127.0.0.1:8000`. If it is hosted
elsewhere, change `VITE_API_URL` in `.env`.

The backend `.env` must allow the Vite origin:

```dotenv
CORS_ORIGINS=http://localhost:5173
```

## Production build

```powershell
npm run build
npm run preview
```

The application includes login/registration, dashboard metrics, ticket
creation and listing, assets, approvals, notifications, and API error states.
