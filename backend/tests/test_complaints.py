from app.models.user import User, UserRole
from app.core.security import hash_password

def register_and_token(client, email="citizen2@example.com"):
    client.post("/api/v1/auth/register", json={"full_name":"Citizen Two","email":email,"password":"StrongPass123!"})
    response = client.post("/api/v1/auth/login", data={"username":email,"password":"StrongPass123!"})
    return response.json()["access_token"]

def test_citizen_can_create_and_list_own_complaint(client):
    token = register_and_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "title":"Large pothole near school",
        "description":"A deep pothole is creating danger for two-wheelers.",
        "category":"pothole",
        "address":"Near Main Road, Mathura",
        "latitude":27.4924,
        "longitude":77.6737
    }
    created = client.post("/api/v1/complaints", json=payload, headers=headers)
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["status"] == "submitted"
    assert body["tracking_code"].startswith("CL-")
    assert client.get("/api/v1/complaints/mine", headers=headers).json()[0]["id"] == body["id"]

def test_citizen_cannot_access_authority_queue(client):
    token = register_and_token(client, "citizen3@example.com")
    response = client.get("/api/v1/complaints", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403

def test_complaint_coordinates_validated(client):
    token = register_and_token(client, "citizen4@example.com")
    payload = {"title":"Broken street light","description":"Street light has not worked for days.","category":"streetlight","address":"Ward 4, Mathura","latitude":120,"longitude":77}
    response = client.post("/api/v1/complaints", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 422


def test_citizen_can_upload_and_retrieve_valid_png(client, tmp_path, monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "complaint_upload_dir", str(tmp_path))

    token = register_and_token(client, "image-citizen@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "title": "Damaged public bench",
        "description": "The public bench has a broken and sharp section.",
        "category": "other",
        "address": "Central park gate",
        "latitude": 27.4924,
        "longitude": 77.6737,
    }
    created = client.post("/api/v1/complaints", json=payload, headers=headers)
    assert created.status_code == 201
    complaint_id = created.json()["id"]

    png = b"\x89PNG\r\n\x1a\n" + (b"\x00" * 32)
    uploaded = client.post(
        f"/api/v1/complaints/{complaint_id}/image",
        headers=headers,
        files={"file": ("proof.PNG", png, "image/png")},
    )
    assert uploaded.status_code == 200, uploaded.text
    assert uploaded.json()["image_storage_key"]

    retrieved = client.get(f"/api/v1/complaints/{complaint_id}/image", headers=headers)
    assert retrieved.status_code == 200
    assert retrieved.content.startswith(b"\x89PNG")


def test_image_upload_rejects_signature_mismatch(client, tmp_path, monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "complaint_upload_dir", str(tmp_path))

    token = register_and_token(client, "image-mismatch@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "title": "Blocked roadside drain",
        "description": "A roadside drain is blocked and overflowing.",
        "category": "drainage",
        "address": "Ward 2 junction",
        "latitude": 27.4924,
        "longitude": 77.6737,
    }
    complaint_id = client.post("/api/v1/complaints", json=payload, headers=headers).json()["id"]
    response = client.post(
        f"/api/v1/complaints/{complaint_id}/image",
        headers=headers,
        files={"file": ("fake.jpg", b"not-a-real-jpeg", "image/jpeg")},
    )
    assert response.status_code == 415


def test_image_upload_rejects_oversized_file(client, tmp_path, monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "complaint_upload_dir", str(tmp_path))
    monkeypatch.setattr(settings, "complaint_upload_max_bytes", 16)

    token = register_and_token(client, "image-large@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "title": "Garbage at market",
        "description": "Garbage is accumulating beside the market entrance.",
        "category": "garbage",
        "address": "Main market",
        "latitude": 27.4924,
        "longitude": 77.6737,
    }
    complaint_id = client.post("/api/v1/complaints", json=payload, headers=headers).json()["id"]
    response = client.post(
        f"/api/v1/complaints/{complaint_id}/image",
        headers=headers,
        files={"file": ("large.png", b"\x89PNG\r\n\x1a\n" + (b"0" * 32), "image/png")},
    )
    assert response.status_code == 413, response.text
