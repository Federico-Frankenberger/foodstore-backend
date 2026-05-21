"""initial_schema

Revision ID: 4f52322ba7f8
Revises:
Create Date: 2026-05-21 00:53:05.763667

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '4f52322ba7f8'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── unidad_medida ─────────────────────────────────────────────────────────
    op.create_table(
        'unidad_medida',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('nombre', sa.String(50), nullable=False),
        sa.Column('simbolo', sa.String(10), nullable=False),
        sa.Column('tipo', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nombre'),
        sa.UniqueConstraint('simbolo'),
    )

    # ── rol ───────────────────────────────────────────────────────────────────
    op.create_table(
        'rol',
        sa.Column('codigo', sa.String(20), nullable=False),
        sa.Column('nombre', sa.String(50), nullable=False),
        sa.Column('descripcion', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('codigo'),
        sa.UniqueConstraint('nombre'),
    )

    # ── estado_pedido ─────────────────────────────────────────────────────────
    op.create_table(
        'estado_pedido',
        sa.Column('codigo', sa.String(20), nullable=False),
        sa.Column('descripcion', sa.String(80), nullable=False),
        sa.Column('orden', sa.SmallInteger(), nullable=False),
        sa.Column('es_terminal', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.PrimaryKeyConstraint('codigo'),
    )

    # ── forma_pago ────────────────────────────────────────────────────────────
    op.create_table(
        'forma_pago',
        sa.Column('codigo', sa.String(20), nullable=False),
        sa.Column('descripcion', sa.String(80), nullable=False),
        sa.Column('habilitado', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.PrimaryKeyConstraint('codigo'),
    )

    # ── usuario ───────────────────────────────────────────────────────────────
    op.create_table(
        'usuario',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('nombre', sa.String(80), nullable=False),
        sa.Column('apellido', sa.String(80), nullable=False),
        sa.Column('email', sa.String(254), nullable=False),
        sa.Column('celular', sa.String(20), nullable=True),
        sa.Column('password_hash', sa.String(60), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index('ix_usuario_email', 'usuario', ['email'], unique=False)

    # ── categoria ─────────────────────────────────────────────────────────────
    # parent_id deliberadamente sin FK — la jerarquía se valida en la capa de servicio
    op.create_table(
        'categoria',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('parent_id', sa.BigInteger(), nullable=True),
        sa.Column('nombre', sa.String(100), nullable=False),
        sa.Column('descripcion', sa.String(), nullable=True),
        sa.Column('imagen_url', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nombre'),
    )

    # ── ingrediente ───────────────────────────────────────────────────────────
    op.create_table(
        'ingrediente',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('nombre', sa.String(100), nullable=False),
        sa.Column('descripcion', sa.String(), nullable=True),
        sa.Column('es_alergeno', sa.Boolean(), nullable=False),
        sa.Column('unidad_medida_id', sa.BigInteger(), nullable=True),
        sa.Column('stock_total', sa.Numeric(10, 3), server_default=sa.text('0'), nullable=False),
        sa.Column('precio_costo', sa.Numeric(10, 2), server_default=sa.text('0'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('stock_total >= 0', name='ck_ingrediente_stock_total_positivo'),
        sa.CheckConstraint('precio_costo >= 0', name='ck_ingrediente_precio_costo_positivo'),
        sa.ForeignKeyConstraint(['unidad_medida_id'], ['unidad_medida.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nombre'),
    )

    # ── producto ──────────────────────────────────────────────────────────────
    op.create_table(
        'producto',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('unidad_venta_id', sa.BigInteger(), nullable=True),
        sa.Column('nombre', sa.String(150), nullable=False),
        sa.Column('descripcion', sa.String(), nullable=True),
        sa.Column('margen_ganancia', sa.Numeric(5, 2), server_default=sa.text('0'), nullable=False),
        sa.Column('imagenes_url', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('disponible', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('stock_directo', sa.BigInteger(), nullable=True),
        sa.Column('precio_base', sa.Numeric(10, 2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['unidad_venta_id'], ['unidad_medida.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    # ── refresh_token ─────────────────────────────────────────────────────────
    op.create_table(
        'refresh_token',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('usuario_id', sa.BigInteger(), nullable=False),
        sa.Column('token_hash', sa.String(64), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuario.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash'),
    )

    # ── usuario_rol ───────────────────────────────────────────────────────────
    op.create_table(
        'usuario_rol',
        sa.Column('usuario_id', sa.BigInteger(), nullable=False),
        sa.Column('rol_codigo', sa.String(20), nullable=False),
        sa.Column('asignado_por_id', sa.BigInteger(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['asignado_por_id'], ['usuario.id']),
        sa.ForeignKeyConstraint(['rol_codigo'], ['rol.codigo']),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuario.id']),
        sa.PrimaryKeyConstraint('usuario_id', 'rol_codigo'),
    )

    # ── producto_categoria ────────────────────────────────────────────────────
    op.create_table(
        'producto_categoria',
        sa.Column('producto_id', sa.BigInteger(), nullable=False),
        sa.Column('categoria_id', sa.BigInteger(), nullable=False),
        sa.Column('es_principal', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['categoria_id'], ['categoria.id']),
        sa.ForeignKeyConstraint(['producto_id'], ['producto.id']),
        sa.PrimaryKeyConstraint('producto_id', 'categoria_id'),
    )

    # ── producto_ingrediente ──────────────────────────────────────────────────
    op.create_table(
        'producto_ingrediente',
        sa.Column('producto_id', sa.BigInteger(), nullable=False),
        sa.Column('ingrediente_id', sa.BigInteger(), nullable=False),
        sa.Column('cantidad', sa.Numeric(10, 3), nullable=False),
        sa.Column('unidad_medida_id', sa.BigInteger(), nullable=False),
        sa.Column('es_removible', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.ForeignKeyConstraint(['ingrediente_id'], ['ingrediente.id']),
        sa.ForeignKeyConstraint(['producto_id'], ['producto.id']),
        sa.ForeignKeyConstraint(['unidad_medida_id'], ['unidad_medida.id']),
        sa.PrimaryKeyConstraint('producto_id', 'ingrediente_id'),
    )

    # ── direccion_entrega ─────────────────────────────────────────────────────
    op.create_table(
        'direccion_entrega',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('usuario_id', sa.BigInteger(), nullable=False),
        sa.Column('alias', sa.String(50), nullable=True),
        sa.Column('linea1', sa.Text(), nullable=False),
        sa.Column('linea2', sa.Text(), nullable=True),
        sa.Column('ciudad', sa.String(100), nullable=False),
        sa.Column('provincia', sa.Text(), nullable=True),
        sa.Column('codigo_postal', sa.String(10), nullable=True),
        sa.Column('latitud', sa.Numeric(9, 6), nullable=True),
        sa.Column('longitud', sa.Numeric(9, 6), nullable=True),
        sa.Column('es_principal', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuario.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    # ── pedido ────────────────────────────────────────────────────────────────
    op.create_table(
        'pedido',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('usuario_id', sa.BigInteger(), nullable=False),
        sa.Column('direccion_id', sa.BigInteger(), nullable=True),
        sa.Column('estado_codigo', sa.String(20), nullable=False),
        sa.Column('forma_pago_codigo', sa.String(20), nullable=False),
        sa.Column('subtotal', sa.Numeric(10, 2), nullable=False),
        sa.Column('descuento', sa.Numeric(10, 2), server_default=sa.text('0'), nullable=False),
        sa.Column('costo_envio', sa.Numeric(10, 2), server_default=sa.text('50'), nullable=False),
        sa.Column('total', sa.Numeric(10, 2), nullable=False),
        sa.Column('notas', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('total >= 0', name='ck_pedido_total_positivo'),
        sa.CheckConstraint('subtotal >= 0', name='ck_pedido_subtotal_positivo'),
        sa.CheckConstraint('descuento >= 0', name='ck_pedido_descuento_positivo'),
        sa.CheckConstraint('costo_envio >= 0', name='ck_pedido_costo_envio_positivo'),
        sa.ForeignKeyConstraint(['direccion_id'], ['direccion_entrega.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['estado_codigo'], ['estado_pedido.codigo']),
        sa.ForeignKeyConstraint(['forma_pago_codigo'], ['forma_pago.codigo']),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuario.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    # ── detalle_pedido ────────────────────────────────────────────────────────
    op.create_table(
        'detalle_pedido',
        sa.Column('pedido_id', sa.BigInteger(), nullable=False),
        sa.Column('producto_id', sa.BigInteger(), nullable=False),
        sa.Column('cantidad', sa.SmallInteger(), nullable=False),
        sa.Column('nombre_snapshot', sa.String(200), nullable=False),
        sa.Column('precio_snapshot', sa.Numeric(10, 2), nullable=False),
        sa.Column('subtotal_snap', sa.Numeric(10, 2), nullable=False),
        sa.Column('personalizacion', postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('cantidad >= 1', name='ck_detalle_cantidad_positiva'),
        sa.CheckConstraint('precio_snapshot >= 0', name='ck_detalle_precio_positivo'),
        sa.CheckConstraint('subtotal_snap >= 0', name='ck_detalle_subtotal_positivo'),
        sa.ForeignKeyConstraint(['pedido_id'], ['pedido.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['producto_id'], ['producto.id']),
        sa.PrimaryKeyConstraint('pedido_id', 'producto_id'),
    )

    # ── historial_estado_pedido ───────────────────────────────────────────────
    op.create_table(
        'historial_estado_pedido',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('pedido_id', sa.BigInteger(), nullable=False),
        sa.Column('estado_desde', sa.String(20), nullable=True),
        sa.Column('estado_hasta', sa.String(20), nullable=False),
        sa.Column('usuario_id', sa.BigInteger(), nullable=False),
        sa.Column('motivo', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['estado_desde'], ['estado_pedido.codigo']),
        sa.ForeignKeyConstraint(['estado_hasta'], ['estado_pedido.codigo']),
        sa.ForeignKeyConstraint(['pedido_id'], ['pedido.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuario.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('historial_estado_pedido')
    op.drop_table('detalle_pedido')
    op.drop_table('pedido')
    op.drop_table('direccion_entrega')
    op.drop_table('producto_ingrediente')
    op.drop_table('producto_categoria')
    op.drop_table('usuario_rol')
    op.drop_table('refresh_token')
    op.drop_table('producto')
    op.drop_table('ingrediente')
    op.drop_table('categoria')
    op.drop_index('ix_usuario_email', table_name='usuario')
    op.drop_table('usuario')
    op.drop_table('forma_pago')
    op.drop_table('estado_pedido')
    op.drop_table('rol')
    op.drop_table('unidad_medida')
