"""add enrichment columns to products

Revision ID: 0002_enrich_product_columns
Revises: 0001_initial_schema
Create Date: 2026-05-19
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_enrich_product_columns"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("products", sa.Column("semantic_text", postgresql.JSONB()))
    op.add_column("products", sa.Column("shape", postgresql.JSONB()))
    op.add_column("products", sa.Column("visual_features", postgresql.ARRAY(sa.Text())))
    op.add_column("products", sa.Column("design_tags", postgresql.ARRAY(sa.Text())))
    op.add_column("products", sa.Column("visual_weight", sa.Text()))
    op.add_column("products", sa.Column("spatial_feel", sa.Text()))
    op.add_column("products", sa.Column("usage_intent", postgresql.ARRAY(sa.Text())))
    op.add_column("products", sa.Column("quality_tier", sa.Text()))


def downgrade() -> None:
    op.drop_column("products", "quality_tier")
    op.drop_column("products", "usage_intent")
    op.drop_column("products", "spatial_feel")
    op.drop_column("products", "visual_weight")
    op.drop_column("products", "design_tags")
    op.drop_column("products", "visual_features")
    op.drop_column("products", "shape")
    op.drop_column("products", "semantic_text")
