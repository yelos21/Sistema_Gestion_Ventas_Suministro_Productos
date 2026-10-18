-- 4.2 Creación y gestión de tablas y registros

DROP TABLE IF EXISTS detalle_suministro, detalle_venta, suministro, venta,
                     cliente, producto, proveedor, categoria CASCADE;

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
    categoria_id  INTEGER NOT NULL REFERENCES categoria(id)
);

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
    cliente_id  INTEGER REFERENCES cliente(id),      -- NULL = venta al público
    fecha       TIMESTAMP NOT NULL DEFAULT now(),
    metodo_pago VARCHAR(20) NOT NULL DEFAULT 'efectivo'
);

CREATE TABLE detalle_venta (
    id              SERIAL PRIMARY KEY,
    venta_id        INTEGER NOT NULL REFERENCES venta(id),
    producto_id     INTEGER NOT NULL REFERENCES producto(id),
    cantidad        INTEGER NOT NULL,
    precio_unitario NUMERIC(10,2) NOT NULL
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
    costo_unitario NUMERIC(10,2) NOT NULL
);

\dt

-- Gestión de la estructura (ALTER TABLE)
ALTER TABLE cliente ADD COLUMN correo VARCHAR(120);
ALTER TABLE cliente RENAME COLUMN correo TO email;
ALTER TABLE cliente DROP COLUMN email;

-- Registros (CRUD)
INSERT INTO categoria (nombre) VALUES ('Bebidas'), ('Papelería');

INSERT INTO producto (codigo, nombre, precio_compra, precio_venta, stock, stock_minimo, categoria_id)
VALUES ('7501',   'Refresco 600ml', 10, 15,     5, 2, 1),
       ('P00006', 'Resma de papel', 90, 129.90, 40, 5, 2);

INSERT INTO cliente (nombre, apellidos) VALUES ('Ana', 'López');
INSERT INTO venta (cliente_id, metodo_pago) VALUES (1, 'efectivo');
INSERT INTO detalle_venta (venta_id, producto_id, cantidad, precio_unitario) VALUES (1, 1, 2, 15);

-- SELECT
SELECT p.codigo, p.nombre, c.nombre AS categoria, p.stock
FROM producto p JOIN categoria c ON c.id = p.categoria_id;

-- UPDATE
UPDATE producto SET stock = stock - 2 WHERE id = 1;
SELECT nombre, stock FROM producto ORDER BY id;

-- DELETE 
DELETE FROM producto WHERE id = 2;
SELECT nombre FROM producto;
