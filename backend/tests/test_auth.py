def register(client, email="citizen@example.com"):
    return client.post("/api/v1/auth/register", json={"full_name": "Test Citizen", "email": email, "password": "StrongPass123!"})

def login(client, email="citizen@example.com"):
    return client.post("/api/v1/auth/login", data={"username": email, "password": "StrongPass123!"})

def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_register_assigns_citizen_and_never_returns_hash(client):
    response = register(client)
    assert response.status_code == 201
    body = response.json()
    assert body["role"] == "citizen"
    assert "hashed_password" not in body
    assert "password" not in body

def test_public_registration_cannot_escalate_role(client):
    response = client.post("/api/v1/auth/register", json={"full_name": "Attacker", "email": "attacker@example.com", "password": "StrongPass123!", "role": "admin"})
    assert response.status_code == 201
    assert response.json()["role"] == "citizen"

def test_duplicate_email_rejected(client):
    assert register(client).status_code == 201
    assert register(client).status_code == 400

def test_login_and_current_user(client):
    assert register(client).status_code == 201
    token_response = login(client)
    assert token_response.status_code == 200
    token = token_response.json()["access_token"]
    profile = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert profile.status_code == 200
    assert profile.json()["email"] == "citizen@example.com"

def test_invalid_credentials_rejected(client):
    register(client)
    response = client.post("/api/v1/auth/login", data={"username": "citizen@example.com", "password": "wrong-password"})
    assert response.status_code == 401

def test_role_gate_rejects_citizen(client):
    register(client)
    token = login(client).json()["access_token"]
    response = client.get("/api/v1/admin/role-check", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403

def test_profile_requires_authentication(client):
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401
