# API Design

Current MVP endpoints:

- GET `/api/health` — service health check.
- POST `/api/auth/login` — issue a JWT from a university ID and password.
- GET `/api/auth/me` — return the authenticated user's role and identity.
- POST `/api/attendance/sessions` — lecturer/admin creates a time-limited attendance session.
- GET `/api/attendance/sessions/{session_id}/code` — lecturer/admin obtains the current 30-second verification code.
- POST `/api/attendance/verify` — an authenticated student submits a session ID and current verification code.

All protected endpoints use bearer JWT authentication. Role checks occur in the backend.

Planned domains:
- users
- courses
- enrolments
- attendance reports
- audit

Production API work should add consistent error envelopes, request correlation IDs, rate limiting and OpenAPI examples.
