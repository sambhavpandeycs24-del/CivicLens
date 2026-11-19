import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, Text, Index, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class ComplaintCategory(str, enum.Enum):
    POTHOLE = "pothole"
    GARBAGE = "garbage"
    STREETLIGHT = "streetlight"
    WATER_LEAKAGE = "water_leakage"
    DRAINAGE = "drainage"
    OTHER = "other"

class ComplaintStatus(str, enum.Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    REJECTED = "rejected"

class ComplaintPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class Complaint(Base):
    __tablename__ = "complaints"
    __table_args__ = (
        Index("ix_complaints_status_created", "status", "created_at"),
        Index("ix_complaints_location", "latitude", "longitude"),
    )
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tracking_code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[ComplaintCategory] = mapped_column(Enum(ComplaintCategory, native_enum=False, values_callable=lambda c: [x.value for x in c]), nullable=False)
    status: Mapped[ComplaintStatus] = mapped_column(Enum(ComplaintStatus, native_enum=False, values_callable=lambda c: [x.value for x in c]), default=ComplaintStatus.SUBMITTED, nullable=False)
    priority: Mapped[ComplaintPriority] = mapped_column(Enum(ComplaintPriority, native_enum=False, values_callable=lambda c: [x.value for x in c]), default=ComplaintPriority.MEDIUM, nullable=False)
    address: Mapped[str] = mapped_column(String(300), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    reporter_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    assigned_to_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
