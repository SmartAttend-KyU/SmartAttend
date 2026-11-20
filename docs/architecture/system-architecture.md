# System Architecture

Use a layered architecture: Next.js presentation, FastAPI application/API, PostgreSQL persistence and Docker-based infrastructure.

The backend is the trust boundary for attendance verification. Client-provided values must be treated as untrusted input.
