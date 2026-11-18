import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.models.complaint import ComplaintCategory, ComplaintStatus, ComplaintPriority

class ComplaintCreate(BaseModel):
    title: str = Field(min_length=5, max_length=160)
    description: str = Field(min_length=10, max_length=5000)
    category: ComplaintCategory
    address: str = Field(min_length=5, max_length=300)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    image_url: str | None = Field(default=None, max_length=500)

class ComplaintUpdate(BaseModel):
    status: ComplaintStatus | None = None
    priority: ComplaintPriority | None = None
    assigned_to_id: uuid.UUID | None = None
    resolution_note: str | None = Field(default=None, max_length=3000)

class ComplaintPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    tracking_code: str
    title: str
    description: str
    category: ComplaintCategory
    status: ComplaintStatus
    priority: ComplaintPriority
    address: str
    latitude: float
    longitude: float
    image_url: str | None
    resolution_note: str | None
    reporter_id: uuid.UUID
    assigned_to_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
