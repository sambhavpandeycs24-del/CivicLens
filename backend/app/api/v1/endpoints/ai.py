from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.ai import AIAnalysisRequest, AIAnalysisResponse
from app.services.ai_assistant import classify_category, priority_suggestion, find_duplicates

router = APIRouter(prefix="/ai", tags=["AI Assistance"])

@router.post("/analyze", response_model=AIAnalysisResponse)
def analyze_complaint(payload: AIAnalysisRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    category, confidence, category_reason = classify_category(payload.title, payload.description, payload.category)
    priority, score, reasons = priority_suggestion(payload.title, payload.description)
    duplicates = find_duplicates(db, payload.title, payload.description, payload.category,
                                 payload.latitude, payload.longitude)
    return AIAnalysisResponse(
        suggested_category=category, category_confidence=confidence,
        category_reason=category_reason, suggested_priority=priority,
        priority_score=score, priority_reasons=reasons,
        duplicate_candidates=duplicates,
        duplicate_check_note="Only up to 300 recent non-rejected reports are checked. A match is a suggestion, not proof of duplication.",
        decision_notice="AI assistance only. A human authority must review category, priority and possible duplicates."
    )
