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

~~~text
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
~~~

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

## Milestone 2: Lecturer Attendance Session

The lecturer workflow now provides:

1. **Assigned course selection:** lecturers can only list and select courses assigned to their account.
2. **Session creation:** the lecturer selects a course, session duration, and QR/TOTP refresh interval.
3. **Explicit session ending:** the lecturer can end an active session at any time.
4. **Server-side expiry:** session status is derived from server timestamps and the explicit end state; expired sessions cannot issue live verification credentials.
5. **Proper TOTP:** the backend generates a six-digit RFC 6238-compatible TOTP using HMAC-SHA1.
6. **Rotating verification window:** the refresh interval is configurable from 5–15 seconds, with the proposal-aligned default of 10 seconds.
7. **QR generation:** every verification window receives an HMAC-signed QR token rendered as an SVG data URI.
8. **Short grace period:** the immediately previous window is accepted for 2 seconds after rotation to accommodate network latency; older windows are rejected.
9. **Live lecturer display:** the lecturer dashboard shows the current QR, six-digit TOTP, QR countdown and overall session countdown.
10. **Verification foundation:** students submit both QR token and TOTP; the server checks session state, freshness, enrolment and duplicate attendance before recording a successful entry.
11. **Audit trail:** session start/end and failed verification attempts are written to the audit log without storing OTP values.

## Run with Docker Compose

1. Copy the environment file:

~~~bash
cp .env.example .env
~~~

2. Start the stack:

~~~bash
docker compose up --build
~~~

The backend waits for PostgreSQL, runs the Alembic migration history, loads demo data when SEED_DEMO_DATA=true, then starts FastAPI.

Open:

- Frontend: http://localhost:3000
- API: http://localhost:8000
- API health: http://localhost:8000/api/health
- API documentation: http://localhost:8000/docs

### Demo accounts

All demo accounts use the password ChangeMe123!:

| Role | University ID |
|---|---|
| Administrator | ADMIN001 |
| Lecturer | LECT001 |
| Student | STU001 |

The seeded demo course is SMART101 and STU001 is enrolled in it.

> Demo credentials are for local development only. Replace them before any deployment outside the prototype environment.

## Database Commands

From the repository root, with DATABASE_URL configured:

~~~bash
cd backend
alembic upgrade head
~~~

To rebuild the schema from the migration history:

~~~bash
cd backend
alembic downgrade base
alembic upgrade head
~~~

To seed demo data:

~~~bash
python scripts/seed_demo.py
~~~

To reset and rebuild the schema:

~~~bash
python scripts/reset_db.py
~~~

For a Docker database that already contains the pre-Alembic prototype schema, remove the development volume before starting the new migration history:

~~~bash
docker compose down -v
docker compose up --build
~~~

## Authentication Flow

1. A user opens /login.
2. The frontend sends university_id and password to POST /api/auth/login.
3. FastAPI verifies the bcrypt password hash and issues a short-lived JWT.
4. The frontend stores the access token in sessionStorage for the current browser session.
5. The frontend calls GET /api/auth/me to retrieve the authoritative user role.
6. The user is redirected to /student, /lecturer or /admin.
7. Protected role pages validate the token again and redirect on invalid or mismatched roles.
8. The user can sign out, which clears the browser token.

The backend remains authoritative: the frontend role is never trusted for authorization.

## Core Attendance Workflow

1. Lecturer authenticates and selects one of the courses assigned to the lecturer account.
2. Lecturer starts a time-limited attendance session.
3. The server generates the current six-digit TOTP and signed rotating QR token.
4. The lecturer dashboard displays both values with their remaining validity time.
5. An authenticated student submits the QR token and TOTP.
6. The backend verifies session state, QR freshness, TOTP validity, enrolment and duplicate status.
7. Valid attendance is timestamped in the database.
8. Failed verification attempts are audited and are not automatically converted into an absence decision.
9. Review-queue handling remains a later milestone.

## Security Priorities

- Keep attendance validation server-side.
- Prevent replay of expired verification windows.
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
- Do not claim that a rotating code proves physical presence.

## Testing

Run the backend tests with:

~~~bash
PYTHONPATH=backend python -m pytest backend/tests -q
~~~

Milestone 2 tests cover:

- assigned-course isolation;
- unauthorized lecturer access;
- six-digit TOTP and QR generation;
- enforcement of the 5–15 second refresh range;
- server-side session expiry;
- explicit session ending;
- wrong-TOTP rejection;
- stale QR replay rejection after the grace period;
- RFC 6238 SHA-1 reference-vector compatibility.

Later milestones will add student QR scanning, review-queue workflows, end-to-end testing, security testing and load/performance evaluation.

## Development Status

**Milestone 2 — Lecturer Attendance Session implemented.**

The repository now has a migration-backed database lifecycle, repeatable demo data, role-aware authentication, lecturer course isolation, time-limited attendance sessions, standards-based six-digit TOTP generation, signed rotating QR generation and a live lecturer presentation screen.

Remaining milestones include the student scanning/verification UI, lecturer review queue, attendance reporting, manual overrides, broader security controls, end-to-end tests and the proposal's performance/usability evaluation.

## Requirements Mapping

- **FR1:** authentication with hashed credentials and role-based JWT access.
- **FR2:** lecturer selects an assigned unit/course and starts a time-windowed session.
- **FR3:** rotating QR refreshes at a configurable 5–15 second interval, default 10 seconds.
- **FR4:** short-lived six-digit TOTP is displayed during an active session.
- **FR7:** server rejects expired sessions and stale verification windows.
- **FR8:** successful attendance remains timestamped.
- **FR13:** enrolment validation and duplicate detection remain server-side.
- **NFR1:** bcrypt/JWT foundation, HMAC-signed QR tokens, constant-time comparisons and short-lived verification values.
- **NFR5:** lecturer access is limited to assigned courses and owned sessions.
- **NFR6:** Alembic migrations and modular backend services support maintainability.

## Important Security Limitation

The proposal itself notes that SmartAttend does not prove physical presence. A determined real-time relay of a currently valid QR/TOTP remains possible. The rotating window is intended to reduce casual or delayed proxy sharing without requiring biometric or RFID hardware.

## License

No license has been selected yet. Add the approved project license before public distribution.
