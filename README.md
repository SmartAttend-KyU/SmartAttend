# SmartAttend

## A Secure Web-Based Class Attendance Verification System

SmartAttend is a hardware-independent web-based class attendance verification system for university environments. It is designed to reduce opportunities for proxy attendance through rotating, time-bound QR codes, short-lived verification codes, attendance-session controls, enrolment validation and lecturer review.

> **Important limitation:** SmartAttend reduces opportunities for proxy attendance; it does not claim to prove that a student is physically present in the classroom.

## Technology Stack

- Frontend: Next.js + TypeScript
- Backend: FastAPI + Python
- Database: PostgreSQL
- Deployment: Docker / Docker Compose
- Authentication: JWT + role-based access control

## Repository Structure

```text
SmartAttend/
├── README.md
├── .env.example
├── .gitignore
├── docker-compose.yml
├── frontend/
│   ├── app/
│   ├── components/
│   ├── hooks/
│   ├── lib/
│   ├── services/
│   ├── types/
│   ├── public/
│   └── tests/
├── backend/
│   ├── app/
│   │   ├── api/routes/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   ├── security/
│   │   └── services/
│   └── tests/
├── database/
│   ├── migrations/
│   └── seed/
├── docs/
│   ├── architecture/
│   ├── api/
│   ├── security/
│   ├── setup/
│   └── testing/
├── scripts/
├── tests/e2e/
└── .github/
    ├── workflows/
    ├── ISSUE_TEMPLATE/
    └── pull_request_template.md
```

## Core Attendance Workflow

1. Lecturer authenticates and starts a time-limited attendance session.
2. The server generates the current rotating verification values.
3. The lecturer dashboard displays the QR code and short-lived verification code.
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

The project should include unit, integration, end-to-end, security and usability testing. Important cases include expired codes, replay attempts, duplicate submissions, expired sessions, wrong-course submissions, unregistered students and unauthorized roles.

## Documentation

Technical documentation is maintained under docs/ for architecture, database design, API design, security, development setup and testing.

## Development Status

**Repository initialization / architectural scaffolding.**

The repository is structured so frontend, backend, database, security, testing and documentation responsibilities remain separated as implementation grows.

## License

No license has been selected yet. Add the approved project license before public distribution.
