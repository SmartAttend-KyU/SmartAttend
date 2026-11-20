# System Architecture

SmartAttend uses a layered architecture:

```text
Next.js frontend
      |
      v
FastAPI HTTP/API layer
      |
      v
Security + application services
      |
      v
SQLAlchemy persistence
      |
      v
PostgreSQL
```

The backend is the trust boundary for attendance verification. Browser input is untrusted.

Current implementation boundaries:
- `api/routes` — HTTP transport and authorization dependencies.
- `schemas` — request/response validation.
- `services` — attendance business rules.
- `models` — persistence entities.
- `db` — SQLAlchemy session and engine.
- `security` — JWT, password hashing and RBAC.
- `frontend/app` — Next.js presentation layer.

Before production, add repository classes consistently, database migrations, audit/event storage, structured logging and background jobs where needed. Avoid moving attendance verification rules into the browser.
