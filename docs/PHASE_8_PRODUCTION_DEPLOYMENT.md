# Phase 8 - Production Deployment

## Architecture

The production topology adds an Nginx reverse proxy in front of the Next.js frontend and FastAPI backend. PostgreSQL/PostGIS and Redis remain private Docker services. Complaint images use a persistent Docker volume by default or optional S3-compatible object storage. The category model uses a separate persistent volume.

```text
Internet -> HTTPS Nginx -> Next.js /static and pages
                         -> /api/v1 and /health -> FastAPI
PostgreSQL/PostGIS <- FastAPI
Redis <- FastAPI (deployment support)
Local volume or S3 <- complaint images
category_models volume <- JSON ML model
```

## Deployment model

Use Docker Compose on a Linux VPS (2 vCPU, 4 GB RAM minimum) or a small VM platform. This is the least-cost practical option and does not require a managed database. TLS certificates can come from a commercial provider or Let's Encrypt. Public DNS must point to the host.

Typical costs are usage-based and may include:

- VPS: approximately US$6-$20/month; always check provider pricing.
- DNS/domain: approximately US$10-$20/year.
- Object storage (optional): only if local volumes are insufficient.
- Backups: local or object-storage transfer costs.

Docker Desktop or the host Docker engine is required. The provided production compose is not a claim of a deployed server.

## Environment

Copy `.env.production.example` to `.env.production` and replace every secret. Never commit `.env.production`.

Important variables:

| Variable | Purpose |
| --- | --- |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | PostgreSQL bootstrap credentials |
| `DATABASE_URL` | SQLAlchemy PostgreSQL URL |
| `JWT_SECRET_KEY` | 32+ character production signing secret |
| `CORS_ORIGINS` | Exact HTTPS frontend origins, comma separated |
| `ALLOWED_HOSTS` | Exact public hostnames |
| `NEXT_PUBLIC_API_URL` | Browser API base; `/api/v1` through the reverse proxy |
| `COMPLAINT_IMAGE_STORAGE` | `local` or `s3` |
| `S3_BUCKET`, `S3_REGION`, `S3_ENDPOINT_URL` | S3-compatible object storage |
| `COMPLAINT_UPLOAD_MAX_BYTES` | Maximum upload size |
| `CATEGORY_MODEL_PATH` | Persistent JSON model path |

Generate a secret with `openssl rand -hex 32`. The backend refuses unsafe JWT defaults and wildcard CORS in production.

## TLS and reverse proxy

Place certificates at `deploy/certs/fullchain.pem` and `deploy/certs/privkey.pem`. Nginx redirects HTTP to HTTPS and proxies `/api`, `/health`, WebSockets, and frontend routes. Renew certificates according to the certificate provider. For a hosted load balancer, TLS can terminate there and this Nginx TLS block can be replaced with a proxy-only configuration.

## Docker commands

Development:

```powershell
docker compose config
docker compose up --build
docker compose ps
docker compose logs -f backend
```

Production:

```powershell
docker compose -f docker-compose.prod.yml --env-file .env.production config
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs --tail=200 backend
```

Use `docker compose down` for a normal stop. Never use volume removal or `down -v` on a deployment.

## Migration procedure

Before migration, make a database backup and confirm migration state:

```powershell
docker compose -f docker-compose.prod.yml exec backend alembic current
docker compose -f docker-compose.prod.yml exec backend alembic heads
```

The startup command runs `alembic upgrade head`. The migration set is `0001` through `0005`; each migration is additive and does not reset existing data. Before first production release:

1. Stop or quiesce writers.
2. Back up PostgreSQL.
3. Deploy the new backend image.
4. Confirm Alembic reaches `0005_phase7_intelligence`.
5. Run readiness and smoke tests.
6. Resume traffic.

## Database backup and restore

From the repository root:

```powershell
$env:POSTGRES_USER = "civiclens"
$env:POSTGRES_DB = "civiclens"
.\scripts\backup-postgres.ps1 -ComposeFile docker-compose.prod.yml -OutputDir backups
```

Restore only to the intended service and database:

```powershell
$env:POSTGRES_USER = "civiclens"
$env:POSTGRES_DB = "civiclens"
.\scripts\restore-postgres.ps1 -ComposeFile docker-compose.prod.yml -BackupFile "backups\civiclens-YYYYMMDD-HHMMSS.dump"
```

Test restores regularly in an isolated environment. Store backups outside the Docker host and encrypt them. Do not use `dropdb`, `drop database`, or volume deletion.

## Persistent storage

Docker volumes preserve complaint images and trained model JSON:

- `complaint_uploads`
- `category_models`
- `postgres_data`

Include these volumes in host-level backup procedures. Complaint image backups contain personal data and must be encrypted and access controlled.

For S3-compatible storage set `COMPLAINT_IMAGE_STORAGE=s3` and S3 credentials. Use a private bucket, server-side encryption, and short presigned URL expiry. The application currently returns a presigned URL for 300 seconds. If credentials are not present, use a workload role or equivalent credential provider where the host supports it.

## Monitoring and logs

- Liveness: `GET /health`
- Readiness: `GET /health/ready`
- Structured JSON request logs include request ID, method, path, status, and duration only.
- Request bodies, emails, passwords, tokens, and complaint descriptions are not logged.
- Monitor container restarts, readiness failures, HTTP 5xx rates, database connections, disk use, backup age, and upload failures.
- Forward Nginx/container stdout and PostgreSQL logs to a production log platform or host journal.

The in-process WebSocket connection manager is suitable for one backend replica. Multiple replicas require a Redis pub/sub notifier before horizontal scaling.

## Security

- Public registration always creates citizens.
- Authority and Admin roles remain server-enforced.
- Citizens can only view/update their own complaint data.
- JWTs expire at 30 minutes by default.
- Passwords use Argon2.
- CORS uses exact origins.
- Uploads require signature and extension validation and a 5 MB default limit.
- Security headers include CSP, frame denial, nosniff, referrer, permissions, HSTS in production, and request IDs.
- IP-based rate limiting is in-process and resets on restart.
- Never put secrets in browser variables, Git, images, or request logs.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Backend exits at startup | `JWT_SECRET_KEY`, CORS, database URL, and migration logs |
| 503 on readiness | PostgreSQL health and network; inspect database logs |
| Frontend cannot call API | `NEXT_PUBLIC_API_URL`, proxy location, CORS and browser console |
| WebSocket rejected | JWT validity and `/api/v1/notifications/ws` proxy upgrade |
| Upload 413/415 | Size limit and JPEG/PNG/WebP content |
| Image missing after redeploy | Verify `complaint_uploads` volume or S3 key and bucket |
| Model missing | Verify `category_models` volume and `CATEGORY_MODEL_PATH` |
| Migration state mismatch | Run Alembic current/heads and restore only from a known backup |

## Known limitations

- Docker Compose has no automated failover or multi-region replication.
- PostgreSQL, Redis, and persistent volumes are on one host unless moved to managed services.
- Rate limiting and WebSocket fan-out are process-local; Redis-backed implementations are required for multi-replica production.
- No password reset, email verification, refresh-token revocation, MFA, or SIEM integration is included.
- The ML model remains advisory and is not trained until sufficient valid complaint labels exist.
- Public tracking is account-bound and does not disclose private complaint details.
