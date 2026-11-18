# API contract — Phase 1

Base path: `/api/v1`

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/health` | public | service health |
| POST | `/auth/register` | public | citizen registration |
| POST | `/auth/login` | public | issue access token (OAuth2 form) |
| GET | `/users/me` | bearer token | current account profile |
| GET | `/admin/role-check` | admin or authority | demonstrate role gate |

### Register request
`{ "full_name": "Demo Citizen", "email": "citizen@example.com", "password": "StrongPass123!" }`

Response: user id, full name, email, role, active state and timestamps. The request schema intentionally has no `role` property.

### Login
Content type: `application/x-www-form-urlencoded`; fields: `username` (email) and `password`. Response: `access_token`, `token_type`.

### Error conventions
- `400`: duplicate email / invalid registration state.
- `401`: missing/invalid/expired token or invalid credentials.
- `403`: authenticated user lacks required role or is inactive.
- `422`: request validation failure.
