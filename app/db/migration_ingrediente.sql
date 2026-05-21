-- Migración manual para entornos donde las tablas ya existen.
-- En tests y desarrollo nuevo, SQLModel.metadata.create_all() las crea automáticamente.

ALTER TABLE ingrediente
    ADD COLUMN IF NOT EXISTS unidad_medida_id BIGINT REFERENCES unidad_medida(id),
    ADD COLUMN IF NOT EXISTS stock_total  NUMERIC(10,3) NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS precio_costo NUMERIC(10,2) NOT NULL DEFAULT 0;

ALTER TABLE ingrediente
    ADD CONSTRAINT IF NOT EXISTS ck_ingrediente_stock_total_positivo  CHECK (stock_total >= 0),
    ADD CONSTRAINT IF NOT EXISTS ck_ingrediente_precio_costo_positivo CHECK (precio_costo >= 0);

ALTER TABLE producto
    ADD COLUMN IF NOT EXISTS margen_ganancia NUMERIC(5,2) NOT NULL DEFAULT 0;

-- Las columnas producto.stock y producto.precio_base permanecen en BD pero el ORM las ignora.
-- No se necesita DROP COLUMN: tienen server_default y no afectan los nuevos inserts.
