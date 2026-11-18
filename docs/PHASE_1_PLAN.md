# Phase 1 — Foundation plan

## Goal
Create a reliable base on which the civic complaint lifecycle and AI modules can be implemented without restructuring the application.

## Work packages and acceptance criteria

| Work package | Deliverable | Acceptance criteria |
|---|---|---|
| P1.1 Product baseline | scope, actors, non-goals | roles and Phase 1 boundaries documented |
| P1.2 Architecture | modular monolith diagram | frontend, API, DB and future worker boundaries clear |
| P1.3 Repository | frontend/backend/docs layout | code grouped by responsibility |
| P1.4 Environment | env example and Docker Compose | services have health checks and persistent DB volume |
| P1.5 Data foundation | user model and migration | unique email, role, timestamps, safe password hash |
| P1.6 Authentication | register/login/me | JWT login works; public registration cannot set privileged roles |
| P1.7 Authorization | role dependency | protected endpoint denies wrong role |
| P1.8 Frontend shell | responsive landing page | app starts and links to API docs |
| P1.9 Quality | tests and instructions | automated API tests pass |

## Roles
- `citizen`: can eventually create and track their own reports. Public registration creates only this role.
- `authority`: verified department staff; provisioned by admin.
- `admin`: platform operator; provisioned securely, never via public signup.

## Phase 1 exit checklist
- [ ] Docker services start and become healthy.
- [ ] Alembic migration applies to PostGIS PostgreSQL.
- [ ] Citizen can register and login.
- [ ] Passwords are hashed; plaintext password is never returned.
- [ ] JWT-protected `/users/me` returns the signed-in user.
- [ ] Role-protected example rejects citizen and allows authority/admin.
- [ ] Backend automated tests pass.
- [ ] Frontend starts and can reach the API health endpoint.
- [ ] README and architecture/API/security docs are current.
