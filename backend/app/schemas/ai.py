from pydantic import BaseModel, Field
from app.models.complaint import ComplaintCategory

class AIAnalysisRequest(BaseModel):
    title: str = Field(min_length=5, max_length=160)
    description: str = Field(min_length=10, max_length=5000)
    category: ComplaintCategory | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)

class DuplicateCandidate(BaseModel):
    complaint_id: str
    tracking_code: str
    title: str
    category: str
    status: str
    distance_meters: float | None
    similarity: float
    reason: str

class AIAnalysisResponse(BaseModel):
    suggested_category: str
    category_confidence: float
    category_reason: str
    suggested_priority: str
    priority_score: int
    priority_reasons: list[str]
    duplicate_candidates: list[DuplicateCandidate]
    duplicate_check_note: str
    decision_notice: str
