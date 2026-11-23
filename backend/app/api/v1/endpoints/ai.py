from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.ai import (
    AIAnalysisRequest,
    AIAnalysisResponse,
    ComplaintSummaryRequest,
    ComplaintSummaryResponse,
)
from app.services.ai_assistant import classify_category, priority_suggestion, find_duplicates
from app.services.complaint_summary import summarize_complaint
from app.services.ml_classifier import load_model, predict
from app.core.config import settings

router = APIRouter(prefix="/ai", tags=["AI Assistance"])

@router.post("/analyze", response_model=AIAnalysisResponse)
def analyze_complaint(payload: AIAnalysisRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    category, confidence, category_reason = classify_category(payload.title, payload.description, payload.category)
    classification_method = "rules"
    model = load_model(settings.category_model_path)
    if model is not None:
        predicted_category, model_confidence = predict(
            f"{payload.title} {payload.description}", model
        )
        if model_confidence >= 0.4:
            category = predicted_category
            confidence = model_confidence
            category_reason = "Trained TF-IDF/logistic model prediction; human review is required."
            classification_method = "tfidf_logistic_regression"
        else:
            category_reason = (
                "The trained model confidence was low; the existing rules-based suggestion is shown."
            )
            classification_method = "rules_fallback"
    priority, score, reasons = priority_suggestion(payload.title, payload.description)
    duplicates = find_duplicates(db, payload.title, payload.description, payload.category,
                                 payload.latitude, payload.longitude)
    return AIAnalysisResponse(
        suggested_category=category, category_confidence=confidence,
        category_reason=category_reason, classification_method=classification_method,
        suggested_priority=priority,
        priority_score=score, priority_reasons=reasons,
        duplicate_candidates=duplicates,
        duplicate_check_note="Only up to 300 recent non-rejected reports are checked. A match is a suggestion, not proof of duplication.",
        decision_notice="AI assistance only. A human authority must review category, priority and possible duplicates."
    )


@router.post("/summarize", response_model=ComplaintSummaryResponse)
def summarize(payload: ComplaintSummaryRequest, user: User = Depends(get_current_user)):
    return summarize_complaint(
        payload.title,
        payload.description,
        payload.address,
        payload.category,
        payload.priority,
    )
