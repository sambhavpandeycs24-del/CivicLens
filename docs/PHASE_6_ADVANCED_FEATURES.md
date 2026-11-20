# Phase 6 - Advanced Features and Real-World Integration

## Implemented features

- JWT-protected complaint image upload and retrieval for JPEG, PNG and WebP.
- Signature, MIME type, extension and configurable size validation.
- Safe unique image filenames and dedicated local storage.
- Rule-based advisory category and priority suggestions with confidence/explanation fields.
- Normalized duplicate-text scoring with category and geographical proximity evidence.
- Persisted notification REST APIs plus JWT-authenticated notification WebSockets.
- Authority filters and an authority workflow dashboard with priority and duplicate visibility.

## Image uploads

Authorized complaint upload endpoint:

```text
POST /api/v1/complaints/{complaint_id}/image
Content-Type: multipart/form-data
```

Authorized retrieval endpoint:

```text
GET /api/v1/complaints/{complaint_id}/image
```

Existing `image_url` records remain compatible. The retrieval endpoint redirects to legacy URLs, while newly uploaded files are served only after complaint authorization checks.

## AI and duplicate detection

`POST /api/v1/ai/analyze` remains advisory. Suggestions do not modify category or priority fields.

Duplicate scoring combines normalized SequenceMatcher wording similarity and token overlap. Category matches and reports within 500 metres add evidence. Far-away reports require stronger wording similarity, and the threshold prevents category-only matches. Candidates include tracking codes, similarity scores and human-readable explanations.

## Notifications

WebSocket endpoint:

```text
WS /api/v1/notifications/ws?token=<JWT>
```

The connection validates the JWT and active user. Notifications are committed to the database before delivery. The frontend reconnects every three seconds after a disconnect.

The connection manager is in-process and is intended for single-Uvicorn-process deployments. Redis Pub/Sub is optional for future horizontal scaling and is not required for basic development.

## Authority workflow

`GET /api/v1/complaints` supports `status`, `category` and `priority` query parameters in addition to existing authority/admin authorization.

`GET /api/v1/complaints/{complaint_id}/duplicates` returns advisory possible duplicates to authority/admin users.

The dashboard is available at `/dashboard/authority`. Citizens cannot update complaints or access authority filters.

## Database migration

Revision `0004_add_complaint_image_storage` adds nullable `complaints.image_storage_key`. Existing rows retain their `image_url` values and require no file migration.

Apply migrations:

```bash
cd backend
py -3.13 -m alembic upgrade head
```

## Environment variables

```text
COMPLAINT_UPLOAD_DIR=./complaint_uploads
COMPLAINT_UPLOAD_MAX_BYTES=5242880
```

Docker Compose mounts a persistent `complaint_uploads` named volume.

## Testing

Backend:

```bash
cd backend
py -3.13 -m pytest -q
```

Frontend:

```bash
cd frontend
npm run lint
npm run build
```

## Known limitations

- The AI is rules-based; it is not a trained machine-learning model.
- Duplicate detection is advisory and may require tuning for larger datasets.
- The WebSocket connection registry is local to each application process; Redis Pub/Sub is not implemented for horizontal scaling.
- Legacy external `image_url` values are redirected rather than copied into local storage.
- No antivirus/content renderer validation is performed beyond signatures and supported types.
