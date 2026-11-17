"""create complaints table

Revision ID: 0002_create_complaints
Revises: 0001_create_users
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_create_complaints"
down_revision = "0001_create_users"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "complaints",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tracking_code", sa.String(20), nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="submitted"),
        sa.Column("priority", sa.String(20), nullable=False, server_default="medium"),
        sa.Column("address", sa.String(300), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("image_url", sa.String(500), nullable=True),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.Column("reporter_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("assigned_to_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tracking_code", name="uq_complaints_tracking_code"),
        sa.CheckConstraint("latitude >= -90 AND latitude <= 90", name="ck_complaints_latitude"),
        sa.CheckConstraint("longitude >= -180 AND longitude <= 180", name="ck_complaints_longitude"),
    )
    op.create_index("ix_complaints_tracking_code", "complaints", ["tracking_code"], unique=True)
    op.create_index("ix_complaints_reporter_id", "complaints", ["reporter_id"])
    op.create_index("ix_complaints_assigned_to_id", "complaints", ["assigned_to_id"])
    op.create_index("ix_complaints_status_created", "complaints", ["status", "created_at"])
    op.create_index("ix_complaints_location", "complaints", ["latitude", "longitude"])

def downgrade() -> None:
    op.drop_table("complaints")
