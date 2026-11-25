# SmartAttend

## A Secure Web-Based Class Attendance Verification System

SmartAttend is a hardware-independent web-based class attendance verification system for university environments. It is designed to reduce opportunities for proxy attendance through rotating, time-bound verification values, attendance-session controls, enrolment validation and lecturer review.

> **Important limitation:** SmartAttend reduces opportunities for proxy attendance; it does not claim to prove that a student is physically present in the classroom.

## Technology Stack

- Frontend: Next.js 15 + TypeScript
- Backend: FastAPI + Python 3.12
- Database: PostgreSQL 16
- Database migrations: Alembic
- Deployment: Docker / Docker Compose
- Authentication: JWT + role-based access control
- Password hashing: bcrypt via Passlib

## Repository Structure

```text
SmartAttend/
├── README.md
├── .env.example
├── .gitignore
├── docker-compose.yml
├── frontend/
│   ├── app/
│   │   ├── login/
│   │   ├── student/
│   │   ├── lecturer/
│   │   └── admin/
│   ├── components/
│   ├── lib/
│   └── services/
├── backend/
│   ├── app/
│   │   ├── api/routes/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── security/
│   │   └── services/
│   ├── migrations/
│   │   └── versions/
│   ├── scripts/
│   └── tests/
├── database/
├── docs/
├── scripts/
└── .github/
    └── workflows/
```

## Milestone 1: Runnable Foundation

The current milestone provides:

- Alembic-managed PostgreSQL schema creation and rollback.
- A single initial migration for users, courses, enrolments, attendance sessions, attendance records and audit logs.
- Idempotent demo seed data for admin, lecturer and student roles.
- A backend startup script that applies migrations before starting FastAPI.
- Optional automatic demo seeding in Docker Compose development mode.
- A proper frontend login form using the existing JWT API.
- Role-aware redirects to student, lecturer or administrator workspaces.
- Session-scoped browser token storage and sign-out.
- Login success/failure audit events.
- Backend authentication and rotating-code tests.

## Run with Docker Compose

1. Copy the environment file:

```bash
cp .env.example .env
```

2. Start the stack:

```bash
docker compose up --build
```

The backend waits for PostgreSQL, runs `alembic upgrade head`, loads demo data when `SEED_DEMO_DATA=true`, then starts FastAPI.

Open:

- Frontend: http://localhost:3000
- API: http://localhost:8000
- API health: http://localhost:8000/api/health

### Demo accounts

All demo accounts use the password `ChangeMe123!`:

| Role | University ID |
|---|---|
| Administrator | `ADMIN001` |
| Lecturer | `LECT001` |
| Student | `STU001` |

The seeded demo course is `SMART101` and `STU001` is enrolled in it.

> Demo credentials are for local development only. Replace them before any deployment outside the prototype environment.

## Database Commands

From the repository root, with `DATABASE_URL` configured:

```bash
cd backend
alembic upgrade head
```

To rebuild the schema from the migration history:

```bash
cd backend
alembic downgrade base
alembic upgrade head
```

To seed demo data from the repository root:

```bash
python scripts/seed_demo.py
```

To reset and rebuild the schema:

```bash
python scripts/reset_db.py
```

For a Docker database that already contains the pre-Alembic prototype schema, remove the development volume before starting the new migration history:

```bash
docker compose down -v
docker compose up --build
```

## Authentication Flow

1. A user opens `/login`.
2. The frontend sends `university_id` and password to `POST /api/auth/login`.
3. FastAPI verifies the bcrypt password hash and issues a short-lived JWT.
4. The frontend stores the access token in `sessionStorage` for the current browser session.
5. The frontend calls `GET /api/auth/me` to retrieve the authoritative user role.
6. The user is redirected to `/student`, `/lecturer` or `/admin`.
7. Protected role pages validate the token again and redirect on invalid or mismatched roles.
8. The user can sign out, which clears the browser token.

The backend remains authoritative: the frontend role is never trusted for authorization.

## Core Attendance Workflow

1. Lecturer authenticates and starts a time-limited attendance session.
2. The server generates the current rotating verification values.
3. The lecturer dashboard displays the verification value and, in later milestones, the QR code.
4. An authenticated student submits attendance.
5. The backend verifies identity, enrolment, session validity, freshness and duplicate status.
6. Valid attendance is recorded.
7. Failed or suspicious attempts can be reviewed by the lecturer.

## Security Priorities

- Keep attendance validation server-side.
- Prevent replay of expired or already-used verification values.
- Enforce session expiry on the server.
- Apply RBAC to protected backend operations.
- Hash passwords; never store plaintext passwords.
- Validate JWT expiry and claims.
- Use database constraints for integrity and duplicate protection.
- Maintain audit logs for security-sensitive actions.
- Validate all client input.
- Keep secrets in environment variables, never source control.
- Use HTTPS/TLS in deployed environments.
- Minimize and protect personally identifiable information.

## Testing

Run the backend tests with:

```bash
cd backend
PYTHONPATH=. pytest tests -q
```

The current foundation tests cover:

- successful JWT login;
- invalid-password rejection;
- authenticated `/api/auth/me`;
- missing-token rejection;
- six-digit rotating verification code behavior.

Later milestones will add attendance integration, review-queue, security, end-to-end and load tests.

## Development Status

**Milestone 1 — Foundation and authentication implemented.**

The repository now has a migration-backed database lifecycle, repeatable demo data, a proper login flow and role-aware authentication UI. Lecturer session management, QR rendering/scanning, standards-based TOTP, review queues, attendance reporting and performance evaluation remain subsequent milestones.

## Requirements Mapping

- **FR1:** authentication with hashed credentials and role-based JWT access.
- **FR2:** database foundation supports lecturer-owned courses and attendance sessions.
- **NFR1:** bcrypt password hashing, JWT expiry and server-side authorization are established.
- **NFR5:** role separation and audit logging are established as the foundation for privacy/security controls.
- **NFR6:** Alembic migrations and modular services improve maintainability.

## License

No license has been selected yet. Add the approved project license before public distribution.
