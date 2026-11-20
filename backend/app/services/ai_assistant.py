"""Explainable baseline assistant. This is rules-based, not a trained ML model."""
import math
import re
from difflib import SequenceMatcher
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.complaint import Complaint, ComplaintCategory, ComplaintStatus

CATEGORY_TERMS = {
    ComplaintCategory.POTHOLE: {"pothole", "road hole", "crater", "road damaged", "road damage", "road broken", "gaddha", "sadak", "broken road", "road surface"},
    ComplaintCategory.GARBAGE: {"garbage", "trash", "rubbish", "waste", "kachra", "dump", "litter", "uncollected", "smelly", "rotting"},
    ComplaintCategory.STREETLIGHT: {"streetlight", "street light", "lamp post", "light not working", "dark street", "light broken", "bulb", "public lighting"},
    ComplaintCategory.WATER_LEAKAGE: {"water leakage", "pipe leak", "leaking pipe", "water leak", "pipeline", "pani leak", "tap leak", "water pipe"},
    ComplaintCategory.DRAINAGE: {"drain", "drainage", "sewage", "sewer", "blocked drain", "naali", "nala", "overflow", "manhole", "stagnant water"},
}
URGENT_TERMS = {"accident", "injury", "injured", "electric shock", "live wire", "fire", "flood", "flooding", "open manhole", "collapse", "dangerous", "emergency"}
HIGH_TERMS = {"overflow", "blocked", "school", "hospital", "main road", "heavy traffic", "contamination", "contaminated", "children", "traffic", "outbreak"}


def classify_category(title: str, description: str, supplied: ComplaintCategory | None = None):
    text = f"{title} {description}".lower()
    scores = {cat: sum(1 for term in terms if term in text) for cat, terms in CATEGORY_TERMS.items()}
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return (supplied.value if supplied else ComplaintCategory.OTHER.value, 0.35,
                "No strong category keywords were found; this is a low-confidence fallback.")
    total = sum(scores.values())
    confidence = min(0.95, 0.55 + 0.4 * scores[best] / max(total, 1))
    suggested = best.value
    if supplied and supplied.value == suggested:
        return (suggested, round(min(0.98, confidence + 0.08), 2),
                f"Rules matched multiple issue terms for {suggested}, consistent with the supplied category.")
    if supplied and supplied != best:
        return (supplied.value, round(confidence * 0.85, 2),
                f"Rules suggested {suggested}, but the citizen-selected category {supplied.value} is retained as the advisory suggestion.")
    return (suggested, round(confidence, 2), f"Rules matched issue terms for {suggested}; human review is required.")


def priority_suggestion(title: str, description: str):
    text = f"{title} {description}".lower()
    urgent = sorted(term for term in URGENT_TERMS if term in text)
    high = sorted(term for term in HIGH_TERMS if term in text)
    public_impact = sorted(term for term in HIGH_TERMS if term in text)
    if urgent:
        score = min(100, 90 + len(urgent) * 5)
        return "urgent", score, [f"Potential immediate safety or emergency indicator: {term}" for term in urgent]
    if public_impact:
        score = min(89, 70 + len(public_impact) * 4)
        reasons = [f"Potential public-impact indicator: {term}" for term in public_impact]
        reasons.append("Impact wording is advisory and requires authority review.")
        return "high", score, reasons
    if any(term in text for term in ("not working", "leak", "blocked")):
        return "medium", 50, ["Issue-impact keyword detected; human review is recommended."]
    return "low", 25, ["No predefined high-risk terms detected; this does not prove the issue is low risk."]


def _normalise(text: str) -> str:
    words = re.sub(r"[^a-z0-9]+", " ", text.lower()).strip().split()
    stop_words = {"the", "a", "an", "and", "or", "near", "please", "this", "that", "is", "are", "has", "have", "was", "for", "of", "at", "in", "to"}
    return " ".join(word for word in words if word not in stop_words)


def _text_similarity(first: str, second: str) -> float:
    if not first or not second:
        return 0.0
    sequence_score = SequenceMatcher(None, first, second).ratio()
    first_tokens = set(first.split())
    second_tokens = set(second.split())
    union = first_tokens | second_tokens
    token_score = len(first_tokens & second_tokens) / len(union) if union else 0.0
    return (0.55 * sequence_score) + (0.45 * token_score)


def _distance_meters(lat1, lon1, lat2, lon2):
    radius = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2-lat1)
    dl = math.radians(lon2-lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


def find_duplicates(db: Session, title: str, description: str, category: ComplaintCategory | None,
                    latitude: float | None, longitude: float | None, limit: int = 5):
    rows = db.scalars(select(Complaint).where(Complaint.status != ComplaintStatus.REJECTED).order_by(Complaint.created_at.desc()).limit(300)).all()
    target = _normalise(f"{title} {description}")
    found = []
    for item in rows:
        candidate = _normalise(f"{item.title} {item.description}")
        wording_similarity = _text_similarity(target, candidate)
        similarity = wording_similarity
        same_category = bool(category and item.category == category)
        distance = None
        nearby = False
        if latitude is not None and longitude is not None:
            distance = _distance_meters(latitude, longitude, item.latitude, item.longitude)
            nearby = distance <= 500
        category_match = same_category
        if category_match:
            similarity = min(1.0, similarity + 0.08)
        if nearby:
            similarity = min(1.0, similarity + 0.10)

        if distance is not None and distance > 2000 and wording_similarity < 0.82:
            continue
        if not nearby and distance is not None and not category_match and wording_similarity < 0.78:
            continue
        if similarity < 0.58:
            continue
        if not category_match and not nearby and wording_similarity < 0.78:
            continue

        reasons = []
        if same_category:
            reasons.append("same category")
        if nearby:
            reasons.append(f"location within {round(distance)} metres")
        elif distance is not None:
            reasons.append(f"location {round(distance)} metres away")
        reasons.append(f"text similarity {round(wording_similarity, 2)}")
        found.append({
            "complaint_id": str(item.id), "tracking_code": item.tracking_code,
            "title": item.title, "category": item.category.value,
            "status": item.status.value,
            "distance_meters": round(distance, 1) if distance is not None else None,
            "similarity": round(similarity, 2), "reason": "; ".join(reasons)
        })
    found.sort(key=lambda x: (x["similarity"], -(x["distance_meters"] or 0)), reverse=True)
    return found[:limit]
