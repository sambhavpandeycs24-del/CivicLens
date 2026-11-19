# Phase 5 - Production Readiness Baseline

## Included

- API liveness endpoint: `GET /health`
- Database readiness endpoint: `GET /health/ready` (executes `SELECT 1`)
- Baseline HTTP security headers: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, and `Permissions-Policy`.
- Automated tests for liveness, readiness, and security headers.

## Verify with Docker

From the project root:

```powershell
docker compose up --build -d
docker compose ps
docker compose exec backend pytest -v
docker compose exec frontend npm run build
```

Check `http://localhost:8000/health`, `http://localhost:8000/health/ready`, and `http://localhost:8000/docs`.

## Remaining production tasks

This is a production-readiness baseline, not production certification. Before public deployment:

1. Replace development credentials and generate a unique JWT secret of at least 32 random characters.
2. Set CORS origins to exact deployed frontend origins.
3. Use HTTPS behind a trusted reverse proxy.
4. Configure backups, monitoring, log retention and alerting.
5. Add upload scanning and strict file size/type controls before enabling real uploads.
6. Perform role-based API security tests and dependency vulnerability review.
7. Restrict database and Redis ports from public access.

The readiness endpoint checks database connectivity only. Redis readiness, external AI provider availability, and end-to-end browser workflows are not included.
