# Internship Tracker

A full-stack web app for tracking internship applications through the whole pipeline — from a saved posting to an offer — with deadlines, notes, and a label for which tailored resume version was sent to each company.

Built as a portfolio project: a FastAPI + SQLAlchemy backend with JWT auth, and a React + TypeScript single-page frontend.

## Features

- **Accounts & auth** — register / log in with JWT bearer tokens; every application is private to its owner
- **Application CRUD** — company, role, location, job URL, deadline, notes, and tailored resume version
- **Status pipeline** — `saved → applied → oa (online assessment) → interview → offer / rejected`, with a status filter on the list
- **Dashboard stats** — counts by status, total count, and upcoming deadlines in the next 30 days
- **Two database modes** — SQLite by default for zero-setup local dev, PostgreSQL via `DATABASE_URL` (wired up in Docker Compose)

## Tech Stack

| Layer    | Tech |
|----------|------|
| Backend  | Python, FastAPI, SQLAlchemy 2.0, Pydantic, PyJWT, pytest |
| Frontend | React 18, TypeScript, Vite |
| Database | SQLite (local) / PostgreSQL 16 (Docker) |
| DevOps   | Docker Compose, GitHub Actions CI |

## Architecture

```
internship-tracker/
├── backend/
│   ├── app/
│   │   ├── main.py       # FastAPI app: auth, applications, and stats routes
│   │   ├── models.py     # SQLAlchemy models (User, Application, status enum)
│   │   ├── schemas.py    # Pydantic request/response schemas
│   │   ├── security.py   # PBKDF2 password hashing + JWT issue/verify
│   │   └── database.py   # Engine/session; DATABASE_URL selects SQLite or Postgres
│   ├── tests/            # pytest suite (auth, CRUD, ownership, stats)
│   └── seed.py           # Optional demo data (clearly labeled examples)
├── frontend/
│   └── src/
│       ├── App.tsx       # Auth page + dashboard (stats, form, list)
│       ├── api.ts        # Typed API client
│       └── styles.css
└── docker-compose.yml    # Postgres + backend + frontend
```

The frontend talks to the backend over a small REST API. In dev, Vite proxies `/api` to `http://localhost:8000`, so no CORS configuration is needed beyond the backend defaults.

## Local Setup

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload   # http://localhost:8000, docs at /docs
```

Optional demo data (example companies only — not real applications):

```bash
python seed.py   # creates demo@example.com / demo-password-123
```

Run the tests:

```bash
pytest -q
```

### Frontend

```bash
cd frontend
npm install
npm run dev   # http://localhost:5173
```

### Docker Compose (full stack with PostgreSQL)

```bash
docker compose up --build
# Frontend: http://localhost:5173   Backend: http://localhost:8000/docs
```

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET    | `/health` | No | Health check |
| POST   | `/auth/register` | No | Create an account |
| POST   | `/auth/login` | No | Log in (OAuth2 form), returns a JWT |
| GET    | `/auth/me` | Yes | Current user |
| POST   | `/applications` | Yes | Create an application |
| GET    | `/applications?status=applied` | Yes | List my applications, optional status filter |
| GET    | `/applications/{id}` | Yes | Get one application |
| PUT    | `/applications/{id}` | Yes | Update an application |
| DELETE | `/applications/{id}` | Yes | Delete an application |
| GET    | `/stats` | Yes | Counts by status + upcoming deadlines (30 days) |


