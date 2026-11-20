# Security Design

Implemented in the MVP:

- Password hashes are stored instead of plaintext passwords.
- JWT expiry is enforced by the token decoder.
- Protected endpoints use backend RBAC.
- Attendance verification codes are HMAC-derived and rotate every 30 seconds.
- Attendance sessions have server-side start and expiry checks.
- Course enrolment is verified server-side before a record is created.
- A unique database constraint prevents a student from recording attendance twice in the same session.
- Secrets are read from environment variables.

Still required before production:

- HTTPS/TLS at the deployment edge.
- Login and verification rate limiting.
- Centralized audit logging for security-sensitive events.
- Stronger account lifecycle controls and password reset.
- Secure refresh-token/session strategy if long-lived sessions are introduced.
- Database migrations instead of startup `create_all`.
- Monitoring and alerting.
- Automated dependency and container vulnerability scanning.
- QR presentation/scanning with the same server-side validation rules.
- Privacy/data-retention rules appropriate for student records.

SmartAttend should continue to be described as reducing opportunities for proxy attendance, not proving physical presence.
