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
