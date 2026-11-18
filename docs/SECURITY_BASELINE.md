# Security baseline

Implemented in Phase 1:
- Password hashing using Argon2 via `pwdlib`.
- JWT signature and expiry validation.
- Public registration hardcodes the citizen role.
- Role checks are enforced on the server.
- Password hashes are excluded from response schemas.
- CORS origins are configured via environment.
- Database credentials and JWT secret are environment-based.

Required before production:
- Replace all example secrets; use a secrets manager.
- Add rate limiting and abuse protection to registration/login.
- Add email verification, password reset and session/token revocation.
- Add upload validation, malware scanning and private object storage before accepting evidence images.
- Add audit events, security headers, HTTPS, backups and monitoring.
- Review privacy notice, retention policy and access to precise location data.
- Conduct dependency, API and penetration testing.
