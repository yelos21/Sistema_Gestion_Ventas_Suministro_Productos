-- 4.3 Creación de restricciones (consola, psql)
-- Ejecutar conectado a practica_proyecto, DESPUÉS de 4_2_tablas.sql.
-- Las líneas marcadas "ERROR esperado" deben fallar: eso demuestra que la restricción funciona.

DROP TABLE IF EXISTS producto_demo, categoria_demo CASCADE;

-- Tablas sin ninguna restricción
CREATE TABLE categoria_demo (id INTEGER, nombre VARCHAR(80));
CREATE TABLE producto_demo (
    id INTEGER, codigo VARCHAR(30), nombre VARCHAR(120),
    precio_venta NUMERIC(10,2), stock INTEGER, categoria_id INTEGER
);

-- PRIMARY KEY
ALTER TABLE categoria_demo ADD CONSTRAINT pk_categoria_demo PRIMARY KEY (id);
ALTER TABLE producto_demo  ADD CONSTRAINT pk_producto_demo  PRIMARY KEY (id);
-- NOT NULL
ALTER TABLE categoria_demo ALTER COLUMN nombre SET NOT NULL;
ALTER TABLE producto_demo  ALTER COLUMN nombre SET NOT NULL;
-- UNIQUE
ALTER TABLE categoria_demo ADD CONSTRAINT uq_categoria_demo_nombre UNIQUE (nombre);
ALTER TABLE producto_demo  ADD CONSTRAINT uq_producto_demo_codigo  UNIQUE (codigo);
-- FOREIGN KEY
ALTER TABLE producto_demo ADD CONSTRAINT fk_producto_demo_categoria
    FOREIGN KEY (categoria_id) REFERENCES categoria_demo(id);
-- CHECK
ALTER TABLE producto_demo ADD CONSTRAINT ck_producto_demo_precio CHECK (precio_venta >= 0);
ALTER TABLE producto_demo ADD CONSTRAINT ck_producto_demo_stock  CHECK (stock >= 0);
-- DEFAULT
ALTER TABLE producto_demo ALTER COLUMN stock SET DEFAULT 0;
-- INDEX
CREATE INDEX ix_producto_demo_nombre ON producto_demo (nombre);

-- Pruebas
INSERT INTO categoria_demo VALUES (1, 'Bebidas');                  -- OK
INSERT INTO categoria_demo VALUES (1, 'Otra');                     -- ERROR esperado: PRIMARY KEY
INSERT INTO categoria_demo VALUES (2, NULL);                       -- ERROR esperado: NOT NULL
INSERT INTO categoria_demo VALUES (3, 'Bebidas');                  -- ERROR esperado: UNIQUE
INSERT INTO producto_demo (id, codigo, nombre, precio_venta, categoria_id)
VALUES (1, '7501', 'Refresco', 15, 1);                             -- OK (stock = 0 por DEFAULT)
INSERT INTO producto_demo (id, codigo, nombre, precio_venta, categoria_id)
VALUES (2, '7502', 'Agua', 10, 99);                                -- ERROR esperado: FOREIGN KEY
INSERT INTO producto_demo (id, codigo, nombre, precio_venta, categoria_id)
VALUES (3, '7503', 'Dulce', -5, 1);                                -- ERROR esperado: CHECK

SELECT id, nombre, stock FROM producto_demo;                        -- stock = 0

SET enable_seqscan = off;
EXPLAIN SELECT * FROM producto_demo WHERE nombre = 'Refresco';      -- usa el INDEX
RESET enable_seqscan;

\d producto_demo

-- Mismas reglas aplicadas a las tablas reales del proyecto
ALTER TABLE producto DROP CONSTRAINT IF EXISTS ck_producto_precios;
ALTER TABLE producto ADD CONSTRAINT ck_producto_precios CHECK (precio_compra >= 0 AND precio_venta >= 0);
ALTER TABLE producto DROP CONSTRAINT IF EXISTS ck_producto_stock;
ALTER TABLE producto ADD CONSTRAINT ck_producto_stock CHECK (stock >= 0 AND stock_minimo >= 0);
ALTER TABLE detalle_venta DROP CONSTRAINT IF EXISTS ck_detalle_venta_cantidad;
ALTER TABLE detalle_venta ADD CONSTRAINT ck_detalle_venta_cantidad CHECK (cantidad > 0);
ALTER TABLE detalle_suministro DROP CONSTRAINT IF EXISTS ck_detalle_suministro_cantidad;
ALTER TABLE detalle_suministro ADD CONSTRAINT ck_detalle_suministro_cantidad CHECK (cantidad > 0);
ALTER TABLE venta DROP CONSTRAINT IF EXISTS ck_venta_metodo;
ALTER TABLE venta ADD CONSTRAINT ck_venta_metodo
    CHECK (metodo_pago IN ('efectivo', 'tarjeta', 'transferencia'));
CREATE INDEX IF NOT EXISTS ix_producto_nombre ON producto (nombre);

-- Prueba sobre la tabla real
INSERT INTO detalle_venta (venta_id, producto_id, cantidad, precio_unitario)
VALUES (1, 1, 0, 15);                                               -- ERROR esperado: CHECK cantidad > 0
