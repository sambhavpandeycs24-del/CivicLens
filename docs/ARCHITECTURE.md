# System architecture

## Architectural style
Use a modular monolith for the first release. It reduces deployment and debugging overhead for a solo developer while preserving clear module boundaries. AI inference and scheduled work can later be moved to a separate worker process using the same service/domain contracts.

## Components
- **Next.js web client:** citizen, authority and admin interfaces.
- **FastAPI application:** REST API, validation, authentication, authorization and domain services.
- **PostgreSQL/PostGIS:** relational source of truth and future spatial queries.
- **Redis:** future cache, rate-limit store and Celery broker.
- **AI worker (future):** image classification, duplicate detection and prioritization; not part of Phase 1 runtime.

## Request flow
1. Browser sends JSON request to `/api/v1`.
2. FastAPI validates request schema and access token.
3. Endpoint calls a service; service applies domain rules.
4. SQLAlchemy persists data in PostgreSQL.
5. Response schema controls which fields are exposed.

## Design rules
- Route handlers should remain thin.
- Do not trust a role supplied by a public client.
- Keep secrets in environment variables.
- Store timestamps in UTC.
- Use database constraints for uniqueness/integrity, not only frontend validation.
- Keep AI outputs advisory and explainable; humans remain accountable for civic decisions.
