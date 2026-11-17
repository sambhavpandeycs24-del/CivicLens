# CivicLens AI — Phase 2: Core Complaint Platform

## Scope delivered in this iteration
- Complaint data model with category, status, priority, tracking code, address and coordinates.
- Authenticated citizen complaint creation and personal complaint history.
- Authority/Admin complaint queue.
- Authority/Admin complaint assignment and status/priority updates.
- Resolution requires a resolution note.
- Basic citizen reporting page wired to the API.
- Alembic migration `0002_create_complaints`.
- API and tests for creation, listing permissions and coordinate validation.

## API
- `POST /api/v1/complaints` — authenticated citizen creates a complaint.
- `GET /api/v1/complaints/mine` — current user's complaints.
- `GET /api/v1/complaints` — authority/admin queue; optional `?status=...`.
- `GET /api/v1/complaints/{id}` — authorized detail.
- `PATCH /api/v1/complaints/{id}` — authority/admin updates assignment, status, priority and resolution note.

## Roles and access
- Citizen: create complaints; list and read only own complaints.
- Authority: read unassigned or own assigned complaints; update complaint workflow.
- Admin: read and update all complaints.
- Public self-registration still creates citizen accounts only.

## Status values
`submitted`, `under_review`, `assigned`, `in_progress`, `resolved`, `rejected`.

## Important limitations
- Coordinates are stored as latitude/longitude scalar columns for this first workflow slice; PostGIS geometry and spatial indexing are a subsequent geospatial task.
- `image_url` is supported in the API model, but binary image upload/storage is not implemented yet.
- Notification delivery, immutable status history, department entities and admin UI remain follow-up work.
- The report page expects an access token in `localStorage` under `civiclens_access_token`; a complete login UI/token lifecycle is not included in this iteration.
- This iteration is a development build, not ready for public deployment.
