from app.services.ai_assistant import classify_category, priority_suggestion
from app.models.complaint import ComplaintCategory


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
