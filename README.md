# CivicLens AI — Civic Issue Reporting and Intelligence

A modular civic issue reporting and resolution platform built with Next.js, FastAPI, PostgreSQL/PostGIS, SQLAlchemy, Alembic, Redis, and Docker Compose. Phases 1–7 provide authentication, complaint workflows, advisory AI, maps and analytics, notifications, image uploads, authority tools, and advanced civic intelligence.

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
CivicLens/
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

The backend tests cover authentication, complaint workflows, AI behavior, uploads, notifications, and Phase 7 intelligence. Run `pytest -q` from `backend/`; frontend checks are `npm run lint` and `npm run build` from `frontend/`.

## Important implementation notes

- This is a development scaffold, not a production-ready deployment. Before public launch add email verification, password reset, rate limiting, refresh-token rotation/revocation, audit logging, secrets management, backups, and security review.
- JWT secret in `.env.example` is a placeholder. Generate a unique secret before running.
- PostGIS is enabled in the Docker database image. Complaint locations are stored as latitude/longitude values; the Phase 7 hotspot query derives PostGIS points for analysis without altering existing complaint data.
- Redis is provisioned now for later queues/caching; no background worker is enabled in Phase 1.


## Phase 3 — AI assistance baseline

Phase 3 adds an authenticated `POST /api/v1/ai/analyze` endpoint for explainable category suggestions, rule-based priority suggestions and similar-complaint candidates. This is a rules-based baseline, not a trained ML model. It does not automatically change saved complaint data. See `docs/PHASE_3_AI_INTELLIGENCE.md` for request examples, limitations and test instructions.

## Phase 4 — Location, Analytics and Notifications

Phase 4 adds authorised complaint location endpoints, coordinate-cell heatmap data, database-backed civic analytics, and in-app notifications. New frontend pages are available at `/dashboard/analytics`, `/dashboard/map`, and `/dashboard/notifications`. See `docs/PHASE_4_LOCATION_ANALYTICS_NOTIFICATIONS.md` for endpoints, access rules, migration details and limitations.


## Phase 5 — Production Readiness Baseline

Added database readiness endpoint (`/health/ready`), baseline HTTP security headers, and health/security tests. See `docs/PHASE_5_PRODUCTION_READINESS.md` for verification and remaining deployment requirements.

## Phase 6 — Advanced Features and Real-World Integration

Phase 6 adds signature-validated complaint image uploads, improved advisory AI priority/category suggestions, conservative duplicate detection, authenticated notification WebSockets, and an authority workflow dashboard with filters. See `docs/PHASE_6_ADVANCED_FEATURES.md` for API details, migration `0004_add_complaint_image_storage`, environment variables, testing, and limitations.

## Phase 7 — Advanced AI and Smart Civic Intelligence

Phase 7 adds an optional TF-IDF/logistic complaint classifier, deterministic complaint briefs, PostGIS category/week hotspots, SLA risk baselines, department performance metrics, and responsive AI/map/analytics dashboards. Everything is advisory; status and priority are not automatically changed.

### Model and data limitations

No labeled complaint dataset is included in this repository, so no trained model or real-world accuracy metric is currently available. The existing rules classifier remains the default until enough real, labeled complaints are present and operators train the local model. Training requires at least 30 reports and four examples per category. See [docs/PHASE_7_AI_INTELLIGENCE.md](docs/PHASE_7_AI_INTELLIGENCE.md) for the evaluation method, safe JSON artifact format, and full limitations.

### Phase 7 setup

Continue using the existing Compose setup and data volumes:

```powershell
docker compose up --build
```

Migration `0005_phase7_intelligence` is applied by the backend container startup. Optional SLA targets are configured with `SLA_TARGET_HOURS_JSON` (defaults: urgent 24h, high 72h, medium 168h, low 336h). Set optional category overrides as JSON, e.g. `{"priority:urgent":24,"pothole:high":48}`. Do not replace or delete existing Docker volumes. Train the model from `backend/` with `python -m app.services.train_classifier`; the Compose `category_models` volume persists its JSON artifact.

### Phase 7 API quick reference

All endpoints are under `/api/v1` and documented in FastAPI OpenAPI at `/docs`.

| Method | Endpoint | Access |
| --- | --- | --- |
| `POST` | `/ai/analyze` | Authenticated; ML when available, rules fallback otherwise |
| `POST` | `/ai/summarize` | Authenticated; deterministic local summary |
| `GET` | `/geo/hotspots?days=30&radius_meters=500&min_complaints=2` | Authority/Admin |
| `GET` | `/analytics/sla` | Authority/Admin |
| `GET` | `/analytics/departments` | Authority/Admin |
| `PATCH` | `/admin/users/{user_id}/department` | Admin |

The database stores coordinates as numeric latitude/longitude, not a PostGIS geometry column; PostgreSQL derives geometry for clustering at query time. Department reporting requires Admin assignment to Authority users. Resolution-time reporting starts with timestamps recorded after migration 0005; older resolved rows are not assigned fabricated durations. Full request behavior and setup details are in [docs/PHASE_7_AI_INTELLIGENCE.md](docs/PHASE_7_AI_INTELLIGENCE.md).

## Phase 8 — Production Deployment

Phase 8 adds a production Compose topology, HTTPS-ready Nginx reverse proxy, restart and health policies, persistent storage settings, structured JSON request logs, secret/CORS validation, in-process rate limiting, citizen auth/report/track screens, and database backup/restore scripts.

Start with [docs/PHASE_8_PRODUCTION_DEPLOYMENT.md](docs/PHASE_8_PRODUCTION_DEPLOYMENT.md) for environment setup, TLS, migration, backup, restore, monitoring, and limitations. Copy `.env.production.example` to `.env.production`; never commit that file. Keep PostgreSQL and persistent volumes intact during normal deployments.
