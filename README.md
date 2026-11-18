# CivicLens AI — Phase 1 Foundation

A modular foundation for an AI-assisted civic issue reporting and resolution platform. Phase 1 establishes the application structure, authentication, role-based access control, database baseline, API documentation, local containers, and automated backend tests.

## Phase 1 boundaries

**Included:** citizen registration/login, JWT authentication, current-user endpoint, Citizen/Authority/Admin roles, protected role example, SQLAlchemy persistence, Alembic migration baseline, PostGIS-enabled PostgreSQL container, Redis service placeholder, Next.js landing page, environment configuration, Docker Compose, and tests.

**Not included yet:** complaint submission/workflows, image classification, duplicate detection, priority prediction, maps/heatmaps, notifications, authority assignment workflow, and production deployment. Those belong to later phases.

## Architecture

```text
Browser (Next.js / TypeScript :3000)
          | HTTP / JSON
          v
FastAPI API (:8000) ---- Redis (:6379, future background jobs)
          |
          v
PostgreSQL + PostGIS (:5432)

Backend modules: core / db / models / schemas / api / services
```

The backend is a modular monolith. Keep business logic in services and route handlers thin. AI workloads can later run in a separate worker without splitting the core API into microservices.

## Repository structure

```text
CivicLensAI_Phase1/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   ├── alembic/versions/
│   ├── tests/
│   ├── alembic.ini
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── public/
│   ├── Dockerfile
│   └── package.json
├── docs/
│   ├── PHASE_1_PLAN.md
│   ├── ARCHITECTURE.md
│   ├── DATABASE_DESIGN.md
│   ├── API_CONTRACT.md
│   └── SECURITY_BASELINE.md
├── docker-compose.yml
└── .env.example
```

## Run with Docker (recommended)

1. Install Docker Desktop and ensure its engine is running.
2. Copy `.env.example` to `.env`. Change the local database password and JWT secret. The `DATABASE_URL` password must match `POSTGRES_PASSWORD`.
3. From this directory run:

```bash
docker compose up --build
```

4. Open the frontend at http://localhost:3000 and API docs at http://localhost:8000/docs.
5. Health endpoint: http://localhost:8000/health.

The API container runs Alembic migrations before starting Uvicorn.

## Run backend locally (without Docker)

Requires Python 3.11+ and a PostgreSQL instance with PostGIS available. From `backend/`:

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
# Set DATABASE_URL, JWT_SECRET_KEY and CORS_ORIGINS in your shell or .env
alembic upgrade head
uvicorn app.main:app --reload
```

For the automated tests, SQLite is used in-memory, so no PostgreSQL server is required:

```bash
pytest -q
```

## Run frontend locally

Requires Node.js 20+. From `frontend/`:

```bash
npm install
# Copy ../.env.example values as needed; NEXT_PUBLIC_API_URL defaults to localhost:8000
npm run dev
```

## Authentication API quick check

Register a citizen (public self-registration always assigns `citizen`):

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"full_name":"Demo Citizen","email":"citizen@example.com","password":"StrongPass123!"}'
```

Login using OAuth2 form fields (`username` is the email):

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=citizen@example.com&password=StrongPass123!"
```

Use the returned access token as `Authorization: Bearer <token>` for `GET /api/v1/users/me`. Authority/Admin accounts must be provisioned by an administrator; never accept a privileged role from public registration.

## Test status

The backend test suite covers health, citizen registration, password non-disclosure, login, authenticated profile access, duplicate-email rejection, and role-protected access. Run `pytest -q` from `backend/`.

## Important implementation notes

- This is a development scaffold, not a production-ready deployment. Before public launch add email verification, password reset, rate limiting, refresh-token rotation/revocation, audit logging, secrets management, backups, and security review.
- JWT secret in `.env.example` is a placeholder. Generate a unique secret before running.
- PostGIS is enabled in the Docker database image. The initial user schema does not store location. Spatial complaint geometry and indexes will be introduced alongside the Phase 2 complaint-location model.
- Redis is provisioned now for later queues/caching; no background worker is enabled in Phase 1.


## Phase 3 — AI assistance baseline

Phase 3 adds an authenticated `POST /api/v1/ai/analyze` endpoint for explainable category suggestions, rule-based priority suggestions and similar-complaint candidates. This is a rules-based baseline, not a trained ML model. It does not automatically change saved complaint data. See `docs/PHASE_3_AI_INTELLIGENCE.md` for request examples, limitations and test instructions.

## Phase 4 — Location, Analytics and Notifications

Phase 4 adds authorised complaint location endpoints, coordinate-cell heatmap data, database-backed civic analytics, and in-app notifications. New frontend pages are available at `/dashboard/analytics`, `/dashboard/map`, and `/dashboard/notifications`. See `docs/PHASE_4_LOCATION_ANALYTICS_NOTIFICATIONS.md` for endpoints, access rules, migration details and limitations.
