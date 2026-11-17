# CivicLens AI — Phase 2

Phase 2 adds the first end-to-end complaint workflow to the Phase 1 foundation.

## Run
1. Copy `.env.example` to `.env` and set a strong `JWT_SECRET_KEY` and matching database credentials.
2. From project root: `docker compose up --build`.
3. API docs: http://localhost:8000/docs
4. Frontend: http://localhost:3000
5. Citizen report page: http://localhost:3000/report

The backend container applies Alembic migrations before starting.

## Local backend tests
From `backend/`:
```bash
pip install -r requirements.txt
pytest -q
```

## Citizen test flow
1. Register through `POST /api/v1/auth/register`.
2. Login through `POST /api/v1/auth/login` using form fields `username` and `password`.
3. Store returned `access_token` in browser localStorage as `civiclens_access_token`.
4. Open `/report` and submit an issue.

For authority workflow, provision an authority account securely in the database for development; public registration cannot grant privileged roles.
