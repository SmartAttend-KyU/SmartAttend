# SmartAttend

SmartAttend is a secure, web-first class attendance verification prototype for Kirinyaga University. It combines role-based authentication, lecturer-controlled attendance sessions, rotating QR codes, short-lived 6-digit TOTP verification, enrolment checks, duplicate detection, and auditable workflows.

## Stack

- Frontend: Next.js + TypeScript
- Backend: FastAPI on Python 3.11+
- Database: PostgreSQL
- Infrastructure: Docker / Docker Compose
- Authentication: bcrypt password hashing + JWT
- Security: server-side validation, short-lived verification windows, audit logging, TLS-ready deployment

## Milestone 2 — Lecturer Attendance Session

The lecturer workflow now covers:

1. Lecturer course selection limited to courses assigned to the authenticated lecturer.
2. Session creation with configurable duration and a 5–15 second QR/TOTP refresh interval, defaulting to 10 seconds.
3. Explicit session ending.
4. Server-authoritative expiry derived from session timestamps and end state.
5. RFC 6238-compatible 6-digit TOTP generation using SHA-1.
6. HMAC-signed rotating QR tokens rendered as SVG data URIs.
7. A 2-second grace period after a rotation boundary for network latency; older windows are rejected.
8. A live lecturer display showing the QR code, TOTP, QR countdown, and session countdown.
9. A student verification endpoint that validates session state, QR signature/window, TOTP, enrolment, and duplicate attendance.
10. Audit events for session start/end and failed verification attempts.

## Proposal requirement mapping

| Requirement | Implementation |
|---|---|
| FR2 | Lecturer selects an assigned course and starts/ends a time-limited session. |
| FR3 | QR refresh interval is configurable from 5–15 seconds; default is 10 seconds. |
| FR4 | Six-digit TOTP is displayed alongside the QR during an active session. |
| FR7 | Server rejects expired/inactive sessions and stale QR/TOTP windows. |
| FR8 | Successful attendance remains timestamped in attendance_records. |
| FR13 | Existing enrolment validation and duplicate detection remain server-side. |
| NFR1 | bcrypt/JWT foundation, HMAC-signed QR tokens, constant-time comparisons, and short-lived credentials. |
| NFR5 | Lecturer endpoints expose only assigned courses and owned attendance sessions. |

## Run

~~~text
cp .env.example .env
docker compose up --build
~~~

Open http://localhost:3000 and sign in with the demo lecturer account LECT001 / ChangeMe123!.

Backend tests:

~~~text
PYTHONPATH=backend python -m pytest backend/tests -q
~~~

The test suite includes assigned-course isolation, unauthorized lecturer access, 5–15 second interval validation, six-digit TOTP and QR generation, server-side expiry, explicit ending, wrong-TOTP rejection, QR replay rejection after grace, and an RFC 6238 SHA-1 reference vector.

## Security boundary

The browser is only a presentation layer. The FastAPI server remains authoritative for role, course ownership, session state, QR freshness, TOTP validity, enrolment, and duplicate checks.

SmartAttend reduces opportunities for proxy attendance but does not claim to prove physical presence or eliminate determined real-time relay attacks.
