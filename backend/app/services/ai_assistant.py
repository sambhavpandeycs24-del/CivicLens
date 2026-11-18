"""Explainable baseline assistant. This is rules-based, not a trained ML model."""
import math
import re
from difflib import SequenceMatcher
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.complaint import Complaint, ComplaintCategory, ComplaintStatus

CATEGORY_TERMS = {
    ComplaintCategory.POTHOLE: {"pothole", "road hole", "crater", "road damaged", "road damage", "road broken", "gaddha", "sadak"},
    ComplaintCategory.GARBAGE: {"garbage", "trash", "rubbish", "waste", "kachra", "dump", "litter"},
    ComplaintCategory.STREETLIGHT: {"streetlight", "street light", "lamp post", "light not working", "dark street", "light broken"},
    ComplaintCategory.WATER_LEAKAGE: {"water leakage", "pipe leak", "leaking pipe", "water leak", "pipeline", "pani leak"},
    ComplaintCategory.DRAINAGE: {"drain", "drainage", "sewage", "sewer", "blocked drain", "naali", "nala", "overflow"},
}
URGENT_TERMS = {"accident", "injury", "injured", "electric shock", "live wire", "fire", "flood", "flooding", "open manhole", "collapse", "dangerous", "emergency"}
HIGH_TERMS = {"overflow", "blocked", "school", "hospital", "main road", "heavy traffic", "contamination", "contaminated"}


def classify_category(title: str, description: str, supplied: ComplaintCategory | None = None):
    text = f"{title} {description}".lower()
    scores = {cat: sum(1 for term in terms if term in text) for cat, terms in CATEGORY_TERMS.items()}
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return (supplied.value if supplied else ComplaintCategory.OTHER.value, 0.35,
                "No strong category keywords were found; this is a low-confidence fallback.")
    total = sum(scores.values())
    confidence = min(0.95, 0.55 + 0.4 * scores[best] / max(total, 1))
    if supplied and supplied != best:
        return (supplied.value, round(confidence, 2),
                f"Text suggests {best.value}, but the citizen-selected category {supplied.value} is retained for review.")
    return (best.value, round(confidence, 2), f"Matched issue terms for {best.value}.")


def priority_suggestion(title: str, description: str):
    text = f"{title} {description}".lower()
    urgent = sorted(term for term in URGENT_TERMS if term in text)
    high = sorted(term for term in HIGH_TERMS if term in text)
    if urgent:
        return "urgent", 90, [f"Potential safety term detected: {term}" for term in urgent]
    if high:
        return "high", 70, [f"Potential impact term detected: {term}" for term in high]
    if any(term in text for term in ("not working", "broken", "leak", "blocked")):
        return "medium", 50, ["Issue-impact keyword detected; human review is recommended."]
    return "low", 25, ["No predefined high-risk terms detected; this does not prove the issue is low risk."]


def _normalise(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


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
        similarity = SequenceMatcher(None, target, candidate).ratio()
        same_category = bool(category and item.category == category)
        if same_category:
            similarity = min(1.0, similarity + 0.08)
        distance = None
        nearby = False
        if latitude is not None and longitude is not None:
            distance = _distance_meters(latitude, longitude, item.latitude, item.longitude)
            nearby = distance <= 500
        if similarity >= 0.52 and (nearby or distance is None):
            reasons = []
            if same_category: reasons.append("same category")
            if nearby: reasons.append(f"within {round(distance)} metres")
            reasons.append("similar wording")
            found.append({
                "complaint_id": str(item.id), "tracking_code": item.tracking_code,
                "title": item.title, "category": item.category.value,
                "status": item.status.value,
                "distance_meters": round(distance, 1) if distance is not None else None,
                "similarity": round(similarity, 2), "reason": ", ".join(reasons)
            })
    found.sort(key=lambda x: (x["similarity"], -(x["distance_meters"] or 0)), reverse=True)
    return found[:limit]
