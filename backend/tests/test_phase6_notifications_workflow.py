from conftest import TestingSessionLocal
from app.core.security import hash_password
from app.models.user import User, UserRole
from starlette.websockets import WebSocketDisconnect


def register(client, email):
    response = client.post("/api/v1/auth/register", json={
        "full_name": "Phase 6 Citizen",
        "email": email,
        "password": "StrongPass123!",
    })
    assert response.status_code == 201
    login = client.post("/api/v1/auth/login", data={
        "username": email,
        "password": "StrongPass123!",
    })
    assert login.status_code == 200
    return login.json()["access_token"]


def test_status_update_persists_notification_and_authority_assignment(client):
    citizen_token = register(client, "phase6-citizen@example.com")
    citizen_headers = {"Authorization": f"Bearer {citizen_token}"}
    complaint = client.post("/api/v1/complaints", headers=citizen_headers, json={
        "title": "Live wire near crossing",
        "description": "A live electrical wire is dangling near a busy crossing.",
        "category": "streetlight",
        "address": "Central crossing",
        "latitude": 27.4924,
        "longitude": 77.6737,
    })
    assert complaint.status_code == 201
    complaint_id = complaint.json()["id"]

    db = TestingSessionLocal()
    authority = User(
        full_name="Phase 6 Authority",
        email="phase6-authority@example.com",
        hashed_password=hash_password("StrongPass123!"),
        role=UserRole.AUTHORITY,
    )
    db.add(authority)
    db.commit()
    db.refresh(authority)
    db.close()

    login = client.post("/api/v1/auth/login", data={
        "username": "phase6-authority@example.com",
        "password": "StrongPass123!",
    })
    if login.status_code == 401:
        client.post("/api/v1/auth/register", json={
            "full_name": "Phase 6 Authority",
            "email": "phase6-authority@example.com",
            "password": "StrongPass123!",
        })
        db = TestingSessionLocal()
        authority = db.scalar(__import__("sqlalchemy").select(User).where(User.email == "phase6-authority@example.com"))
        authority.role = UserRole.AUTHORITY
        db.commit()
        db.refresh(authority)
        db.close()
        login = client.post("/api/v1/auth/login", data={
            "username": "phase6-authority@example.com",
            "password": "StrongPass123!",
        })
    authority_token = login.json()["access_token"]
    authority_headers = {"Authorization": f"Bearer {authority_token}"}

    db = TestingSessionLocal()
    authority = db.scalar(__import__("sqlalchemy").select(User).where(User.email == "phase6-authority@example.com"))
    authority_id = authority.id
    db.close()

    updated = client.patch(
        f"/api/v1/complaints/{complaint_id}",
        headers=authority_headers,
        json={"assigned_to_id": str(authority_id), "status": "in_progress"},
    )
    assert updated.status_code == 200, updated.text

    citizen_notifications = client.get("/api/v1/notifications/mine", headers=citizen_headers)
    assert citizen_notifications.status_code == 200
    assert any("status updated" in item["title"].lower() for item in citizen_notifications.json())

    authority_notifications = client.get("/api/v1/notifications/mine", headers=authority_headers)
    assert authority_notifications.status_code == 200
    assert any("assigned" in item["title"].lower() for item in authority_notifications.json())


def test_websocket_rejects_invalid_token(client):
    register(client, "phase6-websocket@example.com")
    try:
        with client.websocket_connect("/api/v1/notifications/ws?token=invalid"):
            pass
    except WebSocketDisconnect as exc:
        assert exc.code == 1008
