"""add complaint image storage key

Revision ID: 0004_add_complaint_image_storage
Revises: 0003_create_notifications
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_add_complaint_image_storage"
down_revision = "0003_create_notifications"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "complaints",
        sa.Column("image_storage_key", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("complaints", "image_storage_key")
