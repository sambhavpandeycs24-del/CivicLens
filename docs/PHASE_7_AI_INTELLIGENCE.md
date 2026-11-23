# Phase 7 — Advanced AI and Smart Civic Intelligence

Phase 7 adds advisory ML classification, complaint summaries, protected hotspot/SLA/department analytics, and the matching dashboards. All predictions and aggregates are read-only decision support; this phase does not automatically change complaint status, priority, or assignment.

## Complaint classification

`POST /api/v1/ai/analyze` first looks for a locally trained TF-IDF + logistic regression model at `CATEGORY_MODEL_PATH` (default: `data/complaint_category_model.json`). When a valid model is present and its prediction confidence is at least 0.4, the response includes the predicted category and `classification_method: "tfidf_logistic_regression"`. If the file is absent, the existing rules-based classifier is used. A low-confidence ML result uses the rules fallback. A malformed model is an explicit server error, not a silent fallback.

Train from the backend directory after the database contains labeled complaints:

```powershell
python -m app.services.train_classifier
```

Only complaint title, description, and persisted category labels are read. Training requires at least 30 reports, at least two categories, and at least four reports in each category. The command performs a stratified 80/20 (or class-count-adjusted) holdout evaluation, prints accuracy and a per-class report, then fits the artifact on the full eligible dataset. If the threshold is not met, it reports the observed label counts and writes no model. Do not treat a small holdout score as evidence of general performance.

The artifact is a validated, bounded-size JSON file containing vectorizer and logistic-regression numeric parameters. Inference never deserializes Python pickle/joblib files, and model writes use an atomic replacement. Docker persists the artifact in the `category_models` volume mounted at `/app/data`. Retrain deliberately when labels or complaint data change.

There is no checked-in or otherwise supplied labeled training dataset in this repository. Therefore no real model has been trained and no model accuracy is claimed. Until enough labeled reports are present and the training command is run, the current rules-based classifier remains active.

## Summaries

`POST /api/v1/ai/summarize` produces a short extractive summary, issue, address, priority context, and category-based recommended action. It is deterministic local logic (`generated_by: "extractive_rules"`), not an external generative model. No provider credentials or network calls are used; the feature remains available offline.

## Geographical hotspots

`GET /api/v1/geo/hotspots?days=30&radius_meters=500&min_complaints=2` requires an Authority or Admin JWT. PostgreSQL uses PostGIS `ST_ClusterDBSCAN` on points constructed from the existing latitude/longitude columns, in projected metres, partitioned by category and calendar week. It excludes rejected reports and applies the same authority visibility scope as other analytics. Query bounds are 7–365 days, 100–5000 metres, and 2–100 minimum reports.

The complaint schema has numeric latitude/longitude fields rather than a stored PostGIS geometry column. The Docker PostgreSQL service provides PostGIS, and the endpoint derives geometry during analysis; it does not add or backfill spatial columns. SQLite tests/development use a rounded-coordinate grid fallback, which is not an equivalent clustering algorithm and is identified as such in the response.

## SLA and department analytics

- `GET /api/v1/analytics/sla` returns active complaint risk levels, transparent elapsed-time explanations, and historical resolution timing where `resolved_at` is available. The baseline marks a report at risk at 80% of its target and overdue at/after the target.
- `GET /api/v1/analytics/departments` returns workload, overdue count, resolution rate, and average recorded resolution time. It does not rank departments. Groups with fewer than five complaints are marked descriptive-only.
- `PATCH /api/v1/admin/users/{user_id}/department` lets an Admin assign or clear a department on an existing Authority account. Public citizen registration cannot set a department.

Targets are configured with `SLA_TARGET_HOURS_JSON`. Defaults are 24/72/168/336 hours for urgent/high/medium/low priority. Optional JSON keys override in this order: `<category>:<priority>` (for example `pothole:high`), `category:<category>`, then `priority:<priority>`. Values must be positive finite hours. An invalid configuration is reported rather than silently replaced.

Migration `0005_phase7_intelligence` adds nullable `users.department` and `complaints.resolved_at`; existing rows are preserved. Resolution time is recorded when an authority changes a complaint to resolved and cleared if it is reopened. Pre-migration resolved reports have no reliable resolution timestamp and are excluded from timing averages.

## Frontend

- `/dashboard/ai`: protected analysis, explainable classification/priority/duplicate signals, and complaint brief.
- `/dashboard/map`: individual report locations and category/week hotspot cards with map links.
- `/dashboard/analytics`: overview, department performance, and per-complaint SLA risk indicators.

All pages follow the existing responsive CivicLens palette and require a valid Authority/Admin JWT where the backend endpoint does.

## API reference and verification

OpenAPI remains available at `/docs` when the API is running. Phase 7 endpoints are:

| Method | Path | Access |
| --- | --- | --- |
| `POST` | `/api/v1/ai/analyze` | Authenticated |
| `POST` | `/api/v1/ai/summarize` | Authenticated |
| `GET` | `/api/v1/geo/hotspots` | Authority/Admin |
| `GET` | `/api/v1/analytics/sla` | Authority/Admin |
| `GET` | `/api/v1/analytics/departments` | Authority/Admin |
| `PATCH` | `/api/v1/admin/users/{user_id}/department` | Admin |

Run backend tests with `pytest -q` from `backend/`; frontend checks are `npm run lint` and `npm run build` from `frontend/`. Check migration metadata with `alembic heads` and apply with `alembic upgrade head`.

## Limitations

- No supplied labeled corpus means no trained classifier or real-world model metrics are available until operators train from their own persisted labels.
- `resolved_at` cannot be reconstructed for complaints resolved before migration 0005.
- Department metrics require an Admin to assign departments to Authority accounts.
- SQLite hotspot fallback groups rounded coordinates and is only for local/test usage; PostGIS clustering is used with PostgreSQL.
- Summary and priority signals are deterministic, explainable baselines and require human review.
- The SLA result list is capped at 5,000 and indicates truncation; the existing complaint-points map endpoint is capped at 1,000 reports.
