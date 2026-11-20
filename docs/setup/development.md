# Development Setup

## Prerequisites

- Docker Desktop
- Node.js 22+ for local frontend development
- Python 3.12+ for local backend development

## Docker development

1. Copy `.env.example` to `.env`.
2. Change `SECRET_KEY`, `JWT_SECRET_KEY` and the PostgreSQL password.
3. Start the stack:

```bash
docker compose up --build
```

The frontend is available at http://localhost:3000 and the API at http://localhost:8000.

## Demo data

After the database is available, run:

```bash
PYTHONPATH=backend python scripts/seed_demo.py
```

The seed script creates a lecturer, a student, a course and an enrolment. Its demo password must be changed before any real deployment.

## Local backend

```bash
python -m venv .venv
# activate the virtual environment
pip install -r backend/requirements.txt
```

Run the API from the repository root:

```bash
PYTHONPATH=backend uvicorn app.main:app --reload --port 8000
```

## Current MVP limitations

- Database tables are currently created by SQLAlchemy at startup; a proper migration tool should replace this before production.
- QR-code generation and scanning are not implemented yet.
- Rate limiting, centralized audit logging and production-grade monitoring are still required.
- The frontend currently exposes a minimal attendance verification flow rather than complete role-specific dashboards.

Never commit real secrets or production credentials.
