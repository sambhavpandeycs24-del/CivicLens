from app.services.ai_assistant import classify_category, priority_suggestion, find_duplicates
from app.models.complaint import Complaint, ComplaintCategory, ComplaintStatus
from app.models.user import User, UserRole
from app.core.security import hash_password


def test_classifies_garbage_from_keywords():
    category, confidence, reason = classify_category("Garbage on road", "Large garbage dump near market")
    assert category == ComplaintCategory.GARBAGE.value
    assert 0 <= confidence <= 1
    assert "garbage" in reason


def test_uses_other_when_no_category_keywords():
    category, confidence, _ = classify_category("Problem reported", "Please inspect this location")
    assert category == ComplaintCategory.OTHER.value
    assert confidence < 0.5


def test_suggests_urgent_for_safety_keyword():
    priority, score, reasons = priority_suggestion("Live wire on road", "People may get electric shock")
    assert priority == "urgent"
    assert score >= 90
    assert reasons


def test_low_priority_is_not_claimed_as_safe():
    priority, score, reasons = priority_suggestion("Broken bench", "A bench needs repair")
    assert priority == "low"
    assert "does not prove" in reasons[0]


def test_category_suggestion_can_be_consistent_with_supplied_category():
    category, confidence, reason = classify_category(
        "Water pipe leaking",
        "A leaking water pipeline is flooding the pavement",
        ComplaintCategory.WATER_LEAKAGE,
    )
    assert category == "water_leakage"
    assert confidence >= 0.5
    assert "consistent" in reason


def test_priority_uses_public_impact_indicators():
    priority, score, reasons = priority_suggestion(
        "Blocked drain outside hospital",
        "Sewage overflow is blocking access for ambulances and contaminating the road",
    )
    assert priority in {"high", "urgent"}
    assert score >= 70
    assert any("impact" in reason.lower() or "indicator" in reason.lower() for reason in reasons)


def test_duplicate_and_unrelated_complaints(client):
    client.post("/api/v1/auth/register", json={
        "full_name": "Duplicate Citizen",
        "email": "duplicate-citizen@example.com",
        "password": "StrongPass123!",
    })
    login = client.post("/api/v1/auth/login", data={
        "username": "duplicate-citizen@example.com",
        "password": "StrongPass123!",
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    first = {
        "title": "Large pothole near school",
        "description": "A deep pothole on the main road is dangerous for school children.",
        "category": "pothole",
        "address": "School Road",
        "latitude": 27.4924,
        "longitude": 77.6737,
    }
    assert client.post("/api/v1/complaints", json=first, headers=headers).status_code == 201

    duplicate_analysis = client.post("/api/v1/ai/analyze", headers=headers, json={
        "title": "Pothole outside school",
        "description": "Deep road hole on school road is dangerous for children.",
        "category": "pothole",
        "latitude": 27.4925,
        "longitude": 77.6738,
    })
    assert duplicate_analysis.status_code == 200
    duplicate_candidates = duplicate_analysis.json()["duplicate_candidates"]
    assert duplicate_candidates
    assert duplicate_candidates[0]["tracking_code"].startswith("CL-")
    assert duplicate_candidates[0]["similarity"] >= 0.58
    assert "same category" in duplicate_candidates[0]["reason"]

    unrelated = client.post("/api/v1/ai/analyze", headers=headers, json={
        "title": "Streetlight replaced",
        "description": "The public park needs a new bench and drinking fountain.",
        "category": "streetlight",
        "latitude": 28.7041,
        "longitude": 77.1025,
    })
    assert unrelated.status_code == 200
    assert unrelated.json()["duplicate_candidates"] == []
