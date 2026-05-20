"""add auth memory widget tables

Revision ID: 20260521_0003
Revises: 20260521_0002
Create Date: 2026-05-21
"""
from alembic import op
import sqlalchemy as sa


revision = "20260521_0003"
down_revision = "20260521_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "memories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("memory_type", sa.String(length=50), nullable=False, server_default="semantic"),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("embedding_json", sa.JSON(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_memories_user_id", "memories", ["user_id"])
    op.execute("ALTER TABLE memories ADD COLUMN IF NOT EXISTS embedding vector(384)")

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("target_type", sa.String(length=100), nullable=False),
        sa.Column("target_id", sa.String(length=255)),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "widget_configs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("widget_id", sa.String(length=100), nullable=False),
        sa.Column("allowed_origins", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("theme", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("greeting", sa.String(length=500), nullable=False, server_default="Hi! How can I help?"),
        sa.Column("enabled_tools", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_widget_configs_widget_id", "widget_configs", ["widget_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_widget_configs_widget_id", table_name="widget_configs")
    op.drop_table("widget_configs")
    op.drop_table("audit_logs")
    op.execute("ALTER TABLE memories DROP COLUMN IF EXISTS embedding")
    op.drop_index("ix_memories_user_id", table_name="memories")
    op.drop_table("memories")
