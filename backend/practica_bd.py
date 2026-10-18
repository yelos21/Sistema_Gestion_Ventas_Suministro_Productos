"""Práctica 4: DDL (bases, tablas, restricciones) con FastAPI + SQLModel/SQLAlchemy.

Usa la misma conexión del proyecto (DATABASE_URL de database.py).
Solo toca bases cuyo nombre empiece con 'practica_': la base real nunca se modifica.
"""
import re
from decimal import Decimal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import NullPool
from sqlmodel import Session, SQLModel, select

import models  # registra las tablas del proyecto en SQLModel.metadata
from database import DATABASE_URL

router = APIRouter(prefix="/api/practica", tags=["Práctica BD"])

NOMBRE_OK = re.compile(r"^practica_[a-z0-9_]{1,50}$")

# CREATE/DROP DATABASE no pueden ir dentro de una transacción -> AUTOCOMMIT
admin = create_engine(DATABASE_URL, poolclass=NullPool, isolation_level="AUTOCOMMIT")


def mensaje(e: Exception) -> str:
    return str(getattr(e, "orig", e)).strip().splitlines()[0]


def validar(nombre: str) -> str:
    if not NOMBRE_OK.match(nombre):
        raise HTTPException(
            400, "El nombre debe empezar con 'practica_' y usar solo minúsculas, números y _"
        )
    if nombre == make_url(DATABASE_URL).database:
        raise HTTPException(400, "Esa es la base real del proyecto")
    return nombre


def motor_de(bd: str):
    return create_engine(make_url(DATABASE_URL).set(database=bd), poolclass=NullPool)


def existe(bd: str) -> bool:
    with admin.connect() as c:
        return c.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": bd}
        ).scalar() is not None


def motor_existente(bd: str):
    validar(bd)
    if not existe(bd):
        raise HTTPException(404, f"La base {bd} no existe. Créala en 4.1")
    return motor_de(bd)


# ============ 4.1 Bases de datos ============

class NombreBD(BaseModel):
    nombre: str


class RenombrarBD(BaseModel):
    nuevo: str


@router.get("/bases")
def listar_bases():
    with admin.connect() as c:
        return c.execute(
            text("SELECT datname FROM pg_database WHERE datname LIKE 'practica\\_%' ORDER BY 1")
        ).scalars().all()


@router.post("/bases", status_code=201)
def crear_base(d: NombreBD):
    n = validar(d.nombre)
    if existe(n):
        raise HTTPException(409, "La base ya existe")
    try:
        with admin.connect() as c:
            c.execute(text(f'CREATE DATABASE "{n}"'))
    except SQLAlchemyError as e:
        raise HTTPException(400, mensaje(e))
    return {"mensaje": f"Base {n} creada"}


@router.patch("/bases/{nombre}")
def renombrar_base(nombre: str, d: RenombrarBD):
    origen, destino = validar(nombre), validar(d.nuevo)
    try:
        with admin.connect() as c:
            c.execute(text(f'ALTER DATABASE "{origen}" RENAME TO "{destino}"'))
    except SQLAlchemyError as e:
        raise HTTPException(400, mensaje(e))
    return {"mensaje": f"{origen} ahora se llama {destino}"}


@router.delete("/bases/{nombre}")
def eliminar_base(nombre: str):
    n = validar(nombre)
    try:
        with admin.connect() as c:
            c.execute(text(f'DROP DATABASE IF EXISTS "{n}" WITH (FORCE)'))
    except SQLAlchemyError as e:
        raise HTTPException(400, mensaje(e))
    return {"mensaje": f"Base {n} eliminada"}


# ============ 4.2 Tablas y registros ============

@router.post("/{bd}/tablas", status_code=201)
def crear_tablas(bd: str):
    """create_all lee models.py y genera los CREATE TABLE."""
    SQLModel.metadata.create_all(motor_existente(bd))
    return {"mensaje": f"Tablas creadas en {bd}", "tablas": sorted(SQLModel.metadata.tables)}


@router.get("/{bd}/tablas")
def ver_tablas(bd: str):
    insp = inspect(motor_existente(bd))
    return [
        {
            "tabla": t,
            "columnas": [
                f'{c["name"]}  {c["type"]}  {"NULL" if c["nullable"] else "NOT NULL"}'
                for c in insp.get_columns(t)
            ],
        }
        for t in sorted(insp.get_table_names())
    ]


@router.post("/{bd}/alterar")
def alterar(bd: str):
    pasos = [
        "ALTER TABLE cliente ADD COLUMN correo VARCHAR(120)",
        "ALTER TABLE cliente RENAME COLUMN correo TO email",
        "ALTER TABLE cliente DROP COLUMN email",
    ]
    try:
        with motor_existente(bd).begin() as c:
            for p in pasos:
                c.execute(text(p))
    except SQLAlchemyError:
        raise HTTPException(400, "Primero crea las tablas")
    return {"mensaje": "ALTER TABLE ejecutado", "pasos": pasos}


@router.delete("/{bd}/tablas")
def borrar_tablas(bd: str):
    with motor_existente(bd).begin() as c:
        c.execute(text("DROP SCHEMA public CASCADE"))
        c.execute(text("CREATE SCHEMA public"))
    return {"mensaje": f"Tablas de {bd} eliminadas"}


@router.post("/{bd}/crud")
def crud(bd: str):
    """INSERT, SELECT, UPDATE y DELETE con SQLModel."""
    eng = motor_existente(bd)
    pasos = []
    try:
        with Session(eng) as s:
            # limpiar restos de una ejecución anterior
            prev = s.exec(select(models.Producto).where(models.Producto.codigo == "CRUD-001")).first()
            if prev:
                s.delete(prev)
                s.commit()
            prev_c = s.exec(
                select(models.Categoria).where(models.Categoria.nombre == "Categoría CRUD")
            ).first()
            if prev_c:
                s.delete(prev_c)
                s.commit()

            cat = models.Categoria(nombre="Categoría CRUD")  # INSERT
            s.add(cat)
            s.commit()
            s.refresh(cat)
            prod = models.Producto(
                codigo="CRUD-001", nombre="Producto de prueba",
                precio_compra=Decimal("10"), precio_venta=Decimal("15"),
                stock=5, stock_minimo=1, categoria_id=cat.id,
            )
            s.add(prod)
            s.commit()
            s.refresh(prod)
            pasos.append(f"INSERT: categoría {cat.id} y producto {prod.id} creados")

            leido = s.get(models.Producto, prod.id)  # SELECT
            pasos.append(f"SELECT: {leido.nombre}, stock = {leido.stock}")

            leido.stock = 20  # UPDATE
            s.add(leido)
            s.commit()
            s.refresh(leido)
            pasos.append(f"UPDATE: stock ahora = {leido.stock}")

            s.delete(leido)  # DELETE
            s.commit()
            pasos.append("DELETE: producto eliminado")
    except SQLAlchemyError as e:
        raise HTTPException(400, f"Primero crea las tablas ({mensaje(e)})")
    return {"mensaje": "CRUD completo", "pasos": pasos}


# ============ 4.3 Restricciones ============
# SQLModel genera PRIMARY KEY, FOREIGN KEY, UNIQUE, NOT NULL e INDEX (codigo),
# pero NO crea los DEFAULT en la base ni los CHECK: se agregan aquí con ALTER TABLE.

CHECKS = [
    ("producto", "ck_producto_precios", "precio_compra >= 0 AND precio_venta >= 0"),
    ("producto", "ck_producto_stock", "stock >= 0 AND stock_minimo >= 0"),
    ("detalle_venta", "ck_detalle_venta_cantidad", "cantidad > 0"),
    ("detalle_suministro", "ck_detalle_suministro_cantidad", "cantidad > 0"),
    ("venta", "ck_venta_metodo", "metodo_pago IN ('efectivo','tarjeta','transferencia')"),
]
DEFAULTS = [
    "ALTER TABLE producto ALTER COLUMN stock SET DEFAULT 0",
    "ALTER TABLE producto ALTER COLUMN stock_minimo SET DEFAULT 0",
    "ALTER TABLE venta ALTER COLUMN metodo_pago SET DEFAULT 'efectivo'",
    "ALTER TABLE venta ALTER COLUMN fecha SET DEFAULT now()",
    "ALTER TABLE suministro ALTER COLUMN fecha SET DEFAULT now()",
]


def aplicar(eng):
    with eng.begin() as c:
        for tabla, nombre, expr in CHECKS:
            c.execute(text(f"ALTER TABLE {tabla} DROP CONSTRAINT IF EXISTS {nombre}"))
            c.execute(text(f"ALTER TABLE {tabla} ADD CONSTRAINT {nombre} CHECK ({expr})"))
        for d in DEFAULTS:
            c.execute(text(d))
        c.execute(text("CREATE INDEX IF NOT EXISTS ix_producto_nombre ON producto (nombre)"))


@router.post("/{bd}/restricciones")
def aplicar_restricciones(bd: str):
    try:
        aplicar(motor_existente(bd))
    except SQLAlchemyError:
        raise HTTPException(400, "Primero crea las tablas")
    return {"mensaje": f"{len(CHECKS)} CHECK, {len(DEFAULTS)} DEFAULT y 1 INDEX aplicados"}


@router.get("/{bd}/restricciones")
def ver_restricciones(bd: str):
    eng = motor_existente(bd)
    with eng.connect() as c:
        restr = c.execute(text("""
            SELECT conrelid::regclass::text AS tabla, conname AS nombre,
                   CASE contype WHEN 'p' THEN 'PRIMARY KEY' WHEN 'f' THEN 'FOREIGN KEY'
                                WHEN 'u' THEN 'UNIQUE' WHEN 'c' THEN 'CHECK' END AS tipo,
                   pg_get_constraintdef(oid) AS definicion
            FROM pg_constraint
            WHERE connamespace = 'public'::regnamespace AND contype IN ('p','f','u','c')
            ORDER BY 1, 3, 2
        """)).mappings().all()
        indices = c.execute(text(
            "SELECT tablename, indexname FROM pg_indexes WHERE schemaname = 'public' ORDER BY 1, 2"
        )).mappings().all()
        cols = c.execute(text("""
            SELECT table_name, column_name, is_nullable, column_default
            FROM information_schema.columns WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position
        """)).mappings().all()
    return {
        "restricciones": [f'{r["tabla"]}: {r["tipo"]} {r["nombre"]} -> {r["definicion"]}' for r in restr],
        "indices": [f'{i["tablename"]}: {i["indexname"]}' for i in indices],
        "not_null": [f'{x["table_name"]}.{x["column_name"]}' for x in cols if x["is_nullable"] == "NO"],
        "default": [
            f'{x["table_name"]}.{x["column_name"]} = {x["column_default"]}'
            for x in cols
            if x["column_default"] and not x["column_default"].startswith("nextval")
        ],
    }


def intentar(eng, etiqueta: str, sql: str, params: dict | None = None):
    try:
        with eng.begin() as c:
            c.execute(text(sql), params or {})
        return f"ACEPTADO   {etiqueta}"
    except SQLAlchemyError as e:
        return f"RECHAZADO  {etiqueta}  ->  {mensaje(e)}"


@router.post("/{bd}/restricciones/probar")
def probar_restricciones(bd: str):
    eng = motor_existente(bd)
    try:
        aplicar(eng)
        with eng.begin() as c:
            cid = c.execute(text(
                "INSERT INTO categoria (nombre) VALUES ('Prueba restricciones') "
                "ON CONFLICT (nombre) DO UPDATE SET nombre = EXCLUDED.nombre RETURNING id"
            )).scalar()
    except SQLAlchemyError:
        raise HTTPException(400, "Primero crea las tablas")

    pruebas = [
        intentar(eng, "PRIMARY KEY: id repetido",
                 "INSERT INTO categoria (id, nombre) VALUES (:i, 'Otra')", {"i": cid}),
        intentar(eng, "NOT NULL: nombre vacío",
                 "INSERT INTO categoria (nombre) VALUES (NULL)"),
        intentar(eng, "UNIQUE: nombre repetido",
                 "INSERT INTO categoria (nombre) VALUES ('Prueba restricciones')"),
        intentar(eng, "FOREIGN KEY: categoría inexistente",
                 "INSERT INTO producto (codigo, nombre, precio_compra, precio_venta, categoria_id) "
                 "VALUES ('T-FK', 'Prueba', 1, 2, 999999)"),
        intentar(eng, "CHECK: precio negativo",
                 "INSERT INTO producto (codigo, nombre, precio_compra, precio_venta, categoria_id) "
                 "VALUES ('T-CK', 'Prueba', 1, -5, :c)", {"c": cid}),
        intentar(eng, "CHECK: método de pago inválido",
                 "INSERT INTO venta (metodo_pago) VALUES ('bitcoin')"),
        intentar(eng, "DEFAULT: producto sin indicar stock",
                 "INSERT INTO producto (codigo, nombre, precio_compra, precio_venta, categoria_id) "
                 "VALUES ('T-DEFAULT', 'Prueba default', 1, 2, :c) ON CONFLICT (codigo) DO NOTHING",
                 {"c": cid}),
    ]
    with eng.connect() as c:
        stock = c.execute(text("SELECT stock FROM producto WHERE codigo = 'T-DEFAULT'")).scalar()
        idx = c.execute(text(
            "SELECT indexname FROM pg_indexes WHERE tablename = 'producto' ORDER BY 1"
        )).scalars().all()
    return {
        "pruebas": pruebas,
        "default_stock": f"stock del producto sin indicar stock = {stock}",
        "indices_producto": idx,
    }


# ============ 4.4 Base del proyecto completa ============

@router.post("/{bd}/proyecto-completo", status_code=201)
def proyecto_completo(bd: str):
    """Borra y recrea la base, crea tablas, aplica restricciones y carga datos de ejemplo."""
    n = validar(bd)
    try:
        with admin.connect() as c:
            c.execute(text(f'DROP DATABASE IF EXISTS "{n}" WITH (FORCE)'))
            c.execute(text(f'CREATE DATABASE "{n}"'))
    except SQLAlchemyError as e:
        raise HTTPException(400, mensaje(e))

    eng = motor_de(n)
    SQLModel.metadata.create_all(eng)
    aplicar(eng)

    with Session(eng) as s:
        bebidas = models.Categoria(nombre="Bebidas")
        papeleria = models.Categoria(nombre="Papelería")
        compu = models.Categoria(nombre="Cómputo y Electrónica")
        s.add_all([bebidas, papeleria, compu])
        s.commit()

        refresco = models.Producto(codigo="7501", nombre="Refresco 600ml", precio_compra=Decimal("10"),
                                   precio_venta=Decimal("15"), stock=50, stock_minimo=10, categoria_id=bebidas.id)
        resma = models.Producto(codigo="P00006", nombre="Resma de papel", precio_compra=Decimal("90"),
                                precio_venta=Decimal("129.90"), stock=40, stock_minimo=5, categoria_id=papeleria.id)
        teclado = models.Producto(codigo="P00001", nombre="Teclado mecánico", precio_compra=Decimal("800"),
                                  precio_venta=Decimal("1250"), stock=16, stock_minimo=3, categoria_id=compu.id)
        cliente = models.Cliente(nombre="Ana", apellidos="López", telefono="5512345678")
        proveedor = models.Proveedor(rfc="ABC010101AB1", nombre="Distribuidora Central")
        s.add_all([refresco, resma, teclado, cliente, proveedor])
        s.commit()

        venta = models.Venta(cliente_id=cliente.id, metodo_pago="tarjeta")
        sumin = models.Suministro(proveedor_id=proveedor.id)
        s.add_all([venta, sumin])
        s.commit()
        s.add_all([
            models.DetalleVenta(venta_id=venta.id, producto_id=refresco.id, cantidad=2, precio_unitario=Decimal("15")),
            models.DetalleVenta(venta_id=venta.id, producto_id=teclado.id, cantidad=1, precio_unitario=Decimal("1250")),
            models.DetalleSuministro(suministro_id=sumin.id, producto_id=refresco.id, cantidad=100, costo_unitario=Decimal("10")),
        ])
        s.commit()

    with eng.connect() as c:
        conteos = {
            t: c.execute(text(f"SELECT count(*) FROM {t}")).scalar()
            for t in ["categoria", "producto", "cliente", "proveedor", "venta", "detalle_venta", "suministro", "detalle_suministro"]
        }
    return {"mensaje": f"Base {n} creada completa", "registros": conteos}
