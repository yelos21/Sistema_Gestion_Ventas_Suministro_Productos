-- 4.4 Creación completa de la base del proyecto (consola, psql)
-- Ejecutar conectado a practica_proyecto. Se puede repetir las veces que quieras:
-- empieza borrando el esquema public.

DROP SCHEMA public CASCADE;
CREATE SCHEMA public;

CREATE TABLE categoria (
    id     SERIAL PRIMARY KEY,
    nombre VARCHAR(80) NOT NULL UNIQUE
);

CREATE TABLE proveedor (
    id        SERIAL PRIMARY KEY,
    rfc       VARCHAR(13) UNIQUE,
    nombre    VARCHAR(120) NOT NULL,
    telefono  VARCHAR(20),
    direccion VARCHAR(200)
);

CREATE TABLE producto (
    id            SERIAL PRIMARY KEY,
    codigo        VARCHAR(30) NOT NULL UNIQUE,
    nombre        VARCHAR(120) NOT NULL,
    precio_compra NUMERIC(10,2) NOT NULL,
    precio_venta  NUMERIC(10,2) NOT NULL,
    stock         INTEGER NOT NULL DEFAULT 0,
    stock_minimo  INTEGER NOT NULL DEFAULT 0,
    categoria_id  INTEGER NOT NULL REFERENCES categoria(id),
    CONSTRAINT ck_producto_precios CHECK (precio_compra >= 0 AND precio_venta >= 0),
    CONSTRAINT ck_producto_stock   CHECK (stock >= 0 AND stock_minimo >= 0)
);
CREATE INDEX ix_producto_nombre ON producto (nombre);

CREATE TABLE cliente (
    id               SERIAL PRIMARY KEY,
    nombre           VARCHAR(80) NOT NULL,
    apellidos        VARCHAR(120) NOT NULL,
    telefono         VARCHAR(20),
    direccion        VARCHAR(200),
    fecha_nacimiento DATE
);

CREATE TABLE venta (
    id          SERIAL PRIMARY KEY,
    cliente_id  INTEGER REFERENCES cliente(id),
    fecha       TIMESTAMP NOT NULL DEFAULT now(),
    metodo_pago VARCHAR(20) NOT NULL DEFAULT 'efectivo',
    CONSTRAINT ck_venta_metodo CHECK (metodo_pago IN ('efectivo', 'tarjeta', 'transferencia'))
);

CREATE TABLE detalle_venta (
    id              SERIAL PRIMARY KEY,
    venta_id        INTEGER NOT NULL REFERENCES venta(id),
    producto_id     INTEGER NOT NULL REFERENCES producto(id),
    cantidad        INTEGER NOT NULL,
    precio_unitario NUMERIC(10,2) NOT NULL,
    CONSTRAINT ck_detalle_venta_cantidad CHECK (cantidad > 0)
);

CREATE TABLE suministro (
    id           SERIAL PRIMARY KEY,
    proveedor_id INTEGER NOT NULL REFERENCES proveedor(id),
    fecha        TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE detalle_suministro (
    id             SERIAL PRIMARY KEY,
    suministro_id  INTEGER NOT NULL REFERENCES suministro(id),
    producto_id    INTEGER NOT NULL REFERENCES producto(id),
    cantidad       INTEGER NOT NULL,
    costo_unitario NUMERIC(10,2) NOT NULL,
    CONSTRAINT ck_detalle_suministro_cantidad CHECK (cantidad > 0)
);

-- Datos de ejemplo
INSERT INTO categoria (nombre) VALUES ('Bebidas'), ('Papelería'), ('Cómputo y Electrónica');

INSERT INTO producto (codigo, nombre, precio_compra, precio_venta, stock, stock_minimo, categoria_id) VALUES
    ('7501',   'Refresco 600ml',  10,   15,     50, 10, 1),
    ('P00006', 'Resma de papel',  90,   129.90, 40,  5, 2),
    ('P00001', 'Teclado mecánico', 800, 1250,   16,  3, 3);

INSERT INTO cliente (nombre, apellidos, telefono) VALUES ('Ana', 'López', '5512345678');
INSERT INTO proveedor (rfc, nombre) VALUES ('ABC010101AB1', 'Distribuidora Central');

INSERT INTO venta (cliente_id, metodo_pago) VALUES (1, 'tarjeta');
INSERT INTO detalle_venta (venta_id, producto_id, cantidad, precio_unitario) VALUES
    (1, 1, 2, 15), (1, 3, 1, 1250);

INSERT INTO suministro (proveedor_id) VALUES (1);
INSERT INTO detalle_suministro (suministro_id, producto_id, cantidad, costo_unitario) VALUES (1, 1, 100, 10);

-- Resumen
\dt
SELECT 'categoria' AS tabla, count(*) FROM categoria
UNION ALL SELECT 'producto', count(*) FROM producto
UNION ALL SELECT 'venta', count(*) FROM venta
UNION ALL SELECT 'detalle_venta', count(*) FROM detalle_venta;
