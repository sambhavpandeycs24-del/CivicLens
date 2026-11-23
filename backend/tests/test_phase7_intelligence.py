import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.core.config import settings
from app.models.complaint import Complaint, ComplaintCategory, ComplaintPriority, ComplaintStatus
from app.models.user import User, UserRole
from app.services.intelligence import complaint_sla
from app.services.ml_classifier import load_model, predict, save_model
from app.services.train_classifier import train_category_model
from conftest import TestingSessionLocal


def _account(client, email, role=UserRole.CITIZEN):
    registration = client.post("/api/v1/auth/register", json={
        "full_name": "Phase 7 Test User",
        "email": email,
        "password": "StrongPass123!",
    })
    assert registration.status_code == 201, registration.text
    db = TestingSessionLocal()
    user = db.scalar(select(User).where(User.email == email))
    user.role = role
    db.commit()
    user_id = str(user.id)
    db.close()
    login = client.post("/api/v1/auth/login", data={
        "username": email,
        "password": "StrongPass123!",
    })
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}, user_id


def test_ai_analysis_and_summary_are_protected_and_explainable(client, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "category_model_path", str(tmp_path / "missing-model.json"))
    headers, _ = _account(client, "phase7-ai@example.com")
    analysis = client.post("/api/v1/ai/analyze", headers=headers, json={
        "title": "Garbage beside market",
        "description": "Uncollected garbage is accumulating near the market entrance.",
        "category": "garbage",
    })
    assert analysis.status_code == 200, analysis.text
    assert analysis.json()["classification_method"] == "rules"
    assert analysis.json()["suggested_category"] == "garbage"

    summary = client.post("/api/v1/ai/summarize", headers=headers, json={
        "title": "Garbage beside market",
        "description": "Uncollected garbage is accumulating near the market entrance. It blocks the footpath.",
        "address": "Central market",
        "category": "garbage",
        "priority": "high",
    })
    assert summary.status_code == 200, summary.text
    assert summary.json()["generated_by"] == "extractive_rules"
    assert "Central market" == summary.json()["location"]
    assert "collection" in summary.json()["recommended_action"]


def test_classifier_uses_non_executable_json_model(client, tmp_path, monkeypatch):
    model_path = tmp_path / "category-model.json"
    monkeypatch.setattr(settings, "category_model_path", str(model_path))
    save_model({
        "format_version": 1,
        "algorithm": "tfidf_logistic_regression",
        "vocabulary": {"garbage": 0, "market": 1, "pothole": 2},
        "idf": [1.0, 1.0, 1.0],
        "sublinear_tf": True,
        "classes": ["garbage", "pothole"],
        "coefficients": [[0.0, 0.0, 2.0]],
        "intercepts": [0.0],
        "metrics": {},
    }, model_path)
    assert load_model(model_path)["algorithm"] == "tfidf_logistic_regression"
    assert predict("Pothole on road", load_model(model_path))[0] == "pothole"
    assert predict("unrecognized vocabulary terms", load_model(model_path))[1] == 0

    headers, _ = _account(client, "phase7-model@example.com")
    response = client.post("/api/v1/ai/analyze", headers=headers, json={
        "title": "Pothole on road",
        "description": "A pothole is creating a dangerous road surface.",
        "category": "other",
    })
    assert response.status_code == 200, response.text
    assert response.json()["classification_method"] == "tfidf_logistic_regression"
    assert response.json()["suggested_category"] == "pothole"
    assert 0.4 <= response.json()["category_confidence"] <= 1


def test_classifier_rejects_invalid_model_json(tmp_path):
    model_path = tmp_path / "invalid.json"
    model_path.write_text(json.dumps({"format_version": 99}), encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported or invalid"):
        load_model(model_path)


def test_training_does_not_claim_a_model_without_labeled_data(client, tmp_path):
    db = TestingSessionLocal()
    result = train_category_model(db, tmp_path / "must-not-exist.json")
    db.close()
    assert result["trained"] is False
    assert result["examples"] == 0
    assert "Insufficient" in result["message"]
    assert not (tmp_path / "must-not-exist.json").exists()


def test_training_pipeline_evaluates_only_database_labels(client, tmp_path):
    _, reporter_id = _account(client, "phase7-training-fixture@example.com")
    db = TestingSessionLocal()
    labels = [
        (ComplaintCategory.GARBAGE, "trash waste rubbish"),
        (ComplaintCategory.POTHOLE, "pothole damaged road surface"),
        (ComplaintCategory.DRAINAGE, "blocked drain sewage overflow"),
    ]
    for category, terms in labels:
        for index in range(10):
            db.add(Complaint(
                tracking_code=f"CL-TRAIN-{category.value}-{index}",
                title=f"{terms} report {index}",
                description=f"Report about {terms} near the local road.",
                category=category,
                address="Training fixture location",
                latitude=27.49,
                longitude=77.67,
                reporter_id=uuid.UUID(reporter_id),
            ))
    db.commit()
    result = train_category_model(db, tmp_path / "trained-test-fixture.json")
    db.close()
    assert result["trained"] is True
    assert result["examples"] == 30
    assert result["metrics"]["validation_examples"] > 0
    artifact = load_model(tmp_path / "trained-test-fixture.json")
    assert predict("blocked drain sewage", artifact)[0] in {
        ComplaintCategory.GARBAGE.value,
        ComplaintCategory.POTHOLE.value,
        ComplaintCategory.DRAINAGE.value,
    }


def test_sla_category_priority_override_is_explainable(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(
        settings,
        "sla_target_hours_json",
        '{"pothole:high":10,"priority:high":100}',
    )
    now = datetime.now(timezone.utc)
    complaint = Complaint(
        category=ComplaintCategory.POTHOLE,
        priority=ComplaintPriority.HIGH,
        status=ComplaintStatus.IN_PROGRESS,
        created_at=now - timedelta(hours=8),
    )
    result = complaint_sla(complaint, now)
    assert result["target_hours"] == 10
    assert result["risk_level"] == "at_risk"
    assert "8.0 of 10" in result["explanation"]


def test_department_sla_resolution_time_and_hotspots(client):
    citizen_headers, _ = _account(client, "phase7-citizen@example.com")
    authority_headers, authority_id = _account(
        client, "phase7-authority@example.com", UserRole.AUTHORITY
    )
    admin_headers, _ = _account(client, "phase7-admin@example.com", UserRole.ADMIN)
    department = client.patch(
        f"/api/v1/admin/users/{authority_id}/department",
        headers=admin_headers,
        json={"department": "Roads"},
    )
    assert department.status_code == 200, department.text

    complaint_ids = []
    for title in ("Pothole near school", "Road pothole near school"):
        response = client.post("/api/v1/complaints", headers=citizen_headers, json={
            "title": title,
            "description": "A deep pothole is damaging the road and risks nearby traffic.",
            "category": "pothole",
            "address": "School Road",
            "latitude": 27.4924,
            "longitude": 77.6737,
        })
        assert response.status_code == 201, response.text
        complaint_ids.append(response.json()["id"])

    for complaint_id in complaint_ids:
        assigned = client.patch(
            f"/api/v1/complaints/{complaint_id}",
            headers=authority_headers,
            json={"assigned_to_id": authority_id, "status": "in_progress"},
        )
        assert assigned.status_code == 200, assigned.text
    resolved = client.patch(
        f"/api/v1/complaints/{complaint_ids[0]}",
        headers=authority_headers,
        json={"status": "resolved", "resolution_note": "Repaired and inspected."},
    )
    assert resolved.status_code == 200, resolved.text

    db = TestingSessionLocal()
    record = db.get(Complaint, uuid.UUID(complaint_ids[0]))
    assert record.resolved_at is not None
    db.close()

    departments = client.get("/api/v1/analytics/departments", headers=authority_headers)
    assert departments.status_code == 200, departments.text
    roads = next(item for item in departments.json()["departments"] if item["department"] == "Roads")
    assert roads["total_complaints"] == 2
    assert roads["resolved_complaints"] == 1
    assert roads["average_resolution_hours"] is not None
    assert roads["sample_sufficient"] is False

    sla = client.get("/api/v1/analytics/sla", headers=authority_headers)
    assert sla.status_code == 200, sla.text
    assert sla.json()["resolution_counts"]["resolved_on_time"] == 1
    assert len(sla.json()["items"]) == 1
    assert sla.json()["items"][0]["risk_level"] in {"on_track", "at_risk"}

    hotspots = client.get(
        "/api/v1/geo/hotspots?days=30&min_complaints=2",
        headers=authority_headers,
    )
    assert hotspots.status_code == 200, hotspots.text
    assert hotspots.json()["method"] == "coordinate_grid_fallback"
    assert hotspots.json()["count"] == 1
    assert hotspots.json()["hotspots"][0]["category"] == "pothole"

    db = TestingSessionLocal()
    still_open = db.get(Complaint, uuid.UUID(complaint_ids[1]))
    assert still_open.status == ComplaintStatus.IN_PROGRESS
    db.close()


def test_citizens_cannot_access_protected_intelligence(client):
    headers, _ = _account(client, "phase7-unauthorized@example.com")
    assert client.get("/api/v1/analytics/departments", headers=headers).status_code == 403
    assert client.get("/api/v1/analytics/sla", headers=headers).status_code == 403
    assert client.get("/api/v1/geo/hotspots", headers=headers).status_code == 403
