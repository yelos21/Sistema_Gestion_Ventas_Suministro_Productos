

CREATE TABLE categoria{
    id_categoria INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(100) NOT NULL UNIQUE
} ;

CREATE TABLE proveedor{
    id_proveedor INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY AUTO_INCREMENT,
    nombre_proveedor VARCHAR(100) NOT NULL,
    telefono_proveedor VARCHAR(20) NOT NULL,
    rfc_proveedor VARCHAR(20) NOT NULL UNIQUE,
    correo_electronico_proveedor VARCHAR(100) NOT NULL,
    direccion_proveedor VARCHAR(200) NOT NULL
};

CREATE TABLE producto{
    id_producto INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY AUTO_INCREMENT,
    nombre_producto VARCHAR(100) NOT NULL,
    descripcion_producto VARCHAR(200) NOT NULL,
    precio_venta DECIMAL(10,2) NOT NULL CHECK (precio_venta >= 0),
    precio_compra DECIMAL(10,2) NOT NULL CHECK (precio_compra >= 0),
    id_categoria INT NOT NULL REFERENCES categoria(id_categoria),
    id_proveedor INT NOT NULL REFERENCES proveedor(id_proveedor),
    codigo_producto VARCHAR(50) NOT NULL UNIQUE,
    stock_producto INT NOT NULL CHECK (stock >= 0)
};

CREATE TABLE cliente{
    id_cliente INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY AUTO_INCREMENT,
    nombre_cliente VARCHAR(100) NOT NULL, 
    apellidos_cliente VARCHAR(100) NOT NULL,
    telefono_cliente VARCHAR(20),
    direccion_cliente VARCHAR(200) 
    fecha_nacimiento_cliente DATE
};

CREATE TABLE venta{
    id_venta INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY AUTO_INCREMENT,
    id_producto INT NOT NULL REFERENCES producto(id_producto),
    id_cliente INT REFERENCES cliente (id_cliente) ON DELETE SET NULL,  -- NULL = venta al público,
    fecha_venta TIMESTAMPTZ NOT NULL DEFAULT now(), 
    metodo_pago VARCHAR(20) NOT NULL DEFAULT "efectivo" CHECK (metodo_pago IN ('efectivo', 'tarjeta', 'transferencia'))
};

CREATE TABLE detalle_venta{
    id_detalle_venta INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY AUTO_INCREMENT 
    id_venta INT NOT NULL REFERENCES venta(id_venta) ON DELETE CASCADE,
    id_producto INT NOT NULL REFERENCES producto(id_producto), 
    precio_unitario  NUMERIC(10,2) NOT NULL CHECK (precio_unitario >= 0), 
    UNIQUE (id_venta, id_producto)
);
 
CREATE TABLE suministro (
    id_suministro INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_proveedor  INT NOT NULL REFERENCES proveedor(id_proveedor),
    fecha TIMESTAMPTZ NOT NULL DEFAULT now()
);
 
CREATE TABLE detalle_suministro (
    id_detalle_suministro   INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_suminsitro   INT NOT NULL REFERENCES suministro(id_suministro) ON DELETE CASCADE,
    id_producto INT NOT NULL REFERENCES producto(id_producto),
    cantidad_suministro    INT NOT NULL CHECK (cantidad > 0),
    costo_unitario  NUMERIC(10,2) NOT NULL CHECK (costo_unitario >= 0),
    UNIQUE (id_suministro, id_producto)
);
