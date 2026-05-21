"""add direccion_snapshot to pedido

Revision ID: 2c8f9e3a7d01
Revises: 4f52322ba7f8
Create Date: 2026-05-21 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = "2c8f9e3a7d01"
down_revision = "4f52322ba7f8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "pedido",
        sa.Column("direccion_snapshot", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("pedido", "direccion_snapshot")
