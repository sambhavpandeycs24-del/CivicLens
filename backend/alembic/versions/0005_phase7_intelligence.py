"""add department ownership and complaint resolution timestamps

Revision ID: 0005_phase7_intelligence
Revises: 0004_add_complaint_image_storage
"""
from alembic import op
import sqlalchemy as sa

revision = "0005_phase7_intelligence"
down_revision = "0004_add_complaint_image_storage"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("department", sa.String(length=120), nullable=True))
    op.add_column("complaints", sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("complaints", "resolved_at")
    op.drop_column("users", "department")
