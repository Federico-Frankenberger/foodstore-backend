"""rename estado EN_PREP to EN_PREPARACION

Revision ID: a1b2c3d4e5f6
Revises: 2c8f9e3a7d01
Create Date: 2026-05-21 00:01:00.000000

"""
from alembic import op

revision = "a1b2c3d4e5f6"
down_revision = "2c8f9e3a7d01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Insert the new state (the old one may still be referenced by FKs)
    op.execute(
        "INSERT INTO estado_pedido (codigo, descripcion, orden, es_terminal) "
        "VALUES ('EN_PREPARACION', 'En preparación', 3, false) "
        "ON CONFLICT DO NOTHING"
    )
    # 2. Update all FK references before removing the old code
    op.execute(
        "UPDATE pedido SET estado_codigo = 'EN_PREPARACION' "
        "WHERE estado_codigo = 'EN_PREP'"
    )
    op.execute(
        "UPDATE historial_estado_pedido SET estado_desde = 'EN_PREPARACION' "
        "WHERE estado_desde = 'EN_PREP'"
    )
    op.execute(
        "UPDATE historial_estado_pedido SET estado_hasta = 'EN_PREPARACION' "
        "WHERE estado_hasta = 'EN_PREP'"
    )
    # 3. Remove the old state now that no FKs point to it
    op.execute("DELETE FROM estado_pedido WHERE codigo = 'EN_PREP'")


def downgrade() -> None:
    op.execute(
        "INSERT INTO estado_pedido (codigo, descripcion, orden, es_terminal) "
        "VALUES ('EN_PREP', 'En preparación', 3, false) "
        "ON CONFLICT DO NOTHING"
    )
    op.execute(
        "UPDATE pedido SET estado_codigo = 'EN_PREP' "
        "WHERE estado_codigo = 'EN_PREPARACION'"
    )
    op.execute(
        "UPDATE historial_estado_pedido SET estado_desde = 'EN_PREP' "
        "WHERE estado_desde = 'EN_PREPARACION'"
    )
    op.execute(
        "UPDATE historial_estado_pedido SET estado_hasta = 'EN_PREP' "
        "WHERE estado_hasta = 'EN_PREPARACION'"
    )
    op.execute("DELETE FROM estado_pedido WHERE codigo = 'EN_PREPARACION'")
