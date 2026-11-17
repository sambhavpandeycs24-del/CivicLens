# Database design — Phase 1

## `users`

| Column | Type | Rules |
|---|---|---|
| id | UUID | primary key |
| full_name | VARCHAR(120) | required |
| email | VARCHAR(255) | required, unique, normalized lowercase |
| hashed_password | VARCHAR(255) | required, never returned by API |
| role | VARCHAR(20) | citizen / authority / admin; default citizen |
| is_active | BOOLEAN | default true |
| created_at | TIMESTAMPTZ | UTC, server generated |
| updated_at | TIMESTAMPTZ | UTC, server generated |

## Future entities (not migrated in Phase 1)
- `departments`: civic departments and service categories.
- `complaints`: reporter, title, description, category, status, priority, location and timestamps.
- `complaint_media`: object-storage keys and file metadata.
- `assignments`: authority/team assignment and SLA.
- `status_history`: immutable lifecycle events.
- `ai_predictions`: model/version, score, explanation and review state.

## Data integrity principles
Use foreign keys, unique constraints and explicit status transitions. Store original report facts separately from AI predictions. Keep an audit trail for authority actions. Location data should be collected only when needed and protected by access controls.
