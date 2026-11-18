# Phase 4 — Location, Analytics and Notifications

## Goal
Add operational visibility for authorised civic staff: complaint location discovery, area concentration data, database-backed analytics, and in-app notifications.

## Included
- `GET /api/v1/geo/complaints`: authorised map-point data filtered by latitude/longitude bounds. Authority users see unassigned complaints and complaints assigned to themselves; Admin users can see all non-rejected complaints.
- `GET /api/v1/geo/heatmap`: aggregates complaint counts into rounded coordinate cells. This is a grid aggregation endpoint, not a rendered density heatmap or a PostGIS spatial query.
- `GET /api/v1/analytics/overview`: database-backed totals, resolution rate, status counts and category counts. Authority access is scoped to their queue; Admin sees all complaints.
- `GET /api/v1/notifications/mine`: current user's in-app notifications.
- `PATCH /api/v1/notifications/{id}/read`: marks only the caller's notification as read.
- Notification records are created when a citizen submits a complaint, when an assigned complaint's status changes, and when a complaint is newly assigned to an authority.
- Frontend pages: `/dashboard/analytics`, `/dashboard/map`, `/dashboard/notifications`.

## Migration
Alembic revision `0003_create_notifications` creates the notifications table and indexes. Existing data is not deleted. Run migrations through the normal backend startup or `alembic upgrade head`.

## Access and privacy
Analytics and geospatial endpoints require Authority or Admin role. Notification endpoints require authentication and enforce ownership. Map links open OpenStreetMap in a new tab. The map page currently displays a location list with map links; it is not yet an interactive embedded map.

## Known limitations
- Latitude/longitude filtering and rounded-cell aggregation are currently performed with SQL filters/Python aggregation; PostGIS geometry columns, spatial indexes, radius queries and true map tile rendering remain future improvements.
- Notifications are in-app only; no email, SMS, push delivery, background worker or realtime WebSocket delivery is configured.
- Analytics are aggregate counts; average resolution time, department performance and date-range comparisons are not included yet.
- Frontend pages read the existing `civiclens_access_token` localStorage key. A full login/token management UI is still required.
- Automated runtime integration testing must be performed in the user's Docker environment after applying migration 0003.
