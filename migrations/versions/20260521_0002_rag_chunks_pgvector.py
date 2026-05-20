"""extend documents chunks for rag

Revision ID: 20260521_0002
Revises: 20260521_0001
Create Date: 2026-05-21
"""
from alembic import op
import sqlalchemy as sa


revision = "20260521_0002"
down_revision = "20260521_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.add_column("documents", sa.Column("source_type", sa.String(length=50), nullable=True))
    op.add_column("documents", sa.Column("source_id", sa.String(length=500), nullable=True))
    op.execute("UPDATE documents SET source_type = COALESCE(source, 'docs') WHERE source_type IS NULL")
    op.execute("UPDATE documents SET source_id = title WHERE source_id IS NULL")
    op.alter_column("documents", "source_type", nullable=False)
    op.alter_column("documents", "source_id", nullable=False)
    op.create_unique_constraint("uq_documents_source", "documents", ["source_type", "source_id"])

    op.add_column("chunks", sa.Column("chunk_id", sa.String(length=700), nullable=True))
    op.add_column("chunks", sa.Column("char_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("chunks", sa.Column("embedding_json", sa.JSON(), nullable=True))
    op.execute("UPDATE chunks SET chunk_id = document_id || ':' || chunk_index WHERE chunk_id IS NULL")
    op.alter_column("chunks", "chunk_id", nullable=False)
    op.create_unique_constraint("uq_chunks_chunk_id", "chunks", ["chunk_id"])
    op.execute("ALTER TABLE chunks ADD COLUMN IF NOT EXISTS embedding vector(384)")


def downgrade() -> None:
    op.execute("ALTER TABLE chunks DROP COLUMN IF EXISTS embedding")
    op.drop_constraint("uq_chunks_chunk_id", "chunks", type_="unique")
    op.drop_column("chunks", "embedding_json")
    op.drop_column("chunks", "char_count")
    op.drop_column("chunks", "chunk_id")
    op.drop_constraint("uq_documents_source", "documents", type_="unique")
    op.drop_column("documents", "source_id")
    op.drop_column("documents", "source_type")
