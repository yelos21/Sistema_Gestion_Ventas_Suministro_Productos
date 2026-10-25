"""Práctica 4.4 a 4.6 con FastAPI + SQLAlchemy.

4.4 Respaldo y restauración (archivo JSON que se descarga y se vuelve a subir)
4.5 Usuarios (10 usuarios con permisos)
4.6 Importar y exportar (MySQL, SQLite, CSV, JSON)

Reutiliza la conexión y las validaciones de practica_bd.py. Solo toca bases 'practica_*'
y roles 'pr_*'. No usa pg_dump ni librerías nuevas: todo con SQLAlchemy.
"""
import csv
import io
import json
import re
import warnings
from datetime import date, datetime, time, timezone
from decimal import Decimal
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
from sqlalchemy import MetaData, create_engine, inspect, text
from sqlalchemy.dialects import mysql, postgresql
from sqlalchemy.exc import CompileError, SAWarning, SQLAlchemyError
from sqlalchemy.schema import CheckConstraint, CreateIndex, CreateTable

from practica_bd import admin, mensaje, motor_de, motor_existente, validar

warnings.filterwarnings("ignore", category=SAWarning)  # SQLite avisa que Decimal se guarda como float

router = APIRouter(prefix="/api/practica-admin", tags=["Práctica Admin"])

EXPORTACIONES = Path(__file__).resolve().parent / "exportaciones"
IDENT = re.compile(r"^\w+$")


def reflejar(eng) -> MetaData:
    meta = MetaData()
    meta.reflect(bind=eng)
    return meta


def validar_tabla(eng, tabla: str) -> str:
    if tabla not in inspect(eng).get_table_names():
        raise HTTPException(404, f"La tabla {tabla} no existe en esa base")
    return tabla


def ajustar_secuencias(eng):
    """Después de insertar ids a mano, deja cada secuencia en el máximo id."""
    with eng.begin() as c:
        cols = c.execute(text(
            "SELECT table_name, column_name FROM information_schema.columns "
            "WHERE table_schema = 'public' AND column_default LIKE 'nextval%'"
        )).all()
        for t, col in cols:
            c.execute(text(
                f"SELECT setval(pg_get_serial_sequence('\"{t}\"', '{col}'), "
                f"COALESCE((SELECT MAX(\"{col}\") FROM \"{t}\"), 1), "
                f"(SELECT MAX(\"{col}\") FROM \"{t}\") IS NOT NULL)"
            ))


def descarga(contenido: str, nombre: str, tipo: str) -> Response:
    return Response(
        contenido.encode("utf-8"),
        media_type=tipo,
        headers={"Content-Disposition": f'attachment; filename="{nombre}"'},
    )


# ============ 4.4 Respaldo y restauración ============

@router.get("/respaldo/{bd}")
def descargar_respaldo(bd: str):
    """Respaldo lógico: el CREATE TABLE de cada tabla y todos sus registros, en un JSON."""
    eng = motor_existente(bd)
    meta = reflejar(eng)
    for t in meta.tables.values():  # quita nextval(...) para que al restaurar se genere SERIAL
        for c in t.columns:
            if c.server_default is not None and "nextval(" in str(c.server_default.arg):
                c.server_default = None

    dialecto = postgresql.dialect()
    ddl, datos = [], {}
    with eng.connect() as c:
        for t in meta.sorted_tables:
            ddl.append(str(CreateTable(t).compile(dialect=dialecto)).strip())
            ddl.extend(str(CreateIndex(i).compile(dialect=dialecto)).strip() for i in t.indexes)
            datos[t.name] = [dict(f) for f in c.execute(t.select()).mappings()]

    contenido = {"base": bd, "fecha": datetime.now().isoformat(), "ddl": ddl, "datos": datos}
    return descarga(
        json.dumps(contenido, default=str, ensure_ascii=False, indent=1),
        f"{bd}_{datetime.now():%Y%m%d_%H%M%S}.json",
        "application/json",
    )


class Restaurar(BaseModel):
    destino: str
    respaldo: dict


@router.post("/restauracion", status_code=201)
def restaurar_respaldo(d: Restaurar):
    """Crea una base NUEVA a partir del archivo de respaldo: tablas, registros y secuencias."""
    destino = validar(d.destino)
    ddl, datos = d.respaldo.get("ddl"), d.respaldo.get("datos")
    if not isinstance(ddl, list) or not isinstance(datos, dict):
        raise HTTPException(400, "El archivo no parece un respaldo de esta práctica")
    for s in ddl:  # solo se aceptan CREATE TABLE / CREATE INDEX de una sola sentencia
        if not re.match(r"^CREATE (UNIQUE )?(TABLE|INDEX)\b", s) or ";" in s.strip().rstrip(";"):
            raise HTTPException(400, "El respaldo contiene sentencias no permitidas")
    for tabla, filas in datos.items():
        if not IDENT.match(tabla) or any(not IDENT.match(k) for f in filas for k in f):
            raise HTTPException(400, "El respaldo contiene nombres no válidos")

    try:
        with admin.connect() as c:
            c.execute(text(f'DROP DATABASE IF EXISTS "{destino}" WITH (FORCE)'))
            c.execute(text(f'CREATE DATABASE "{destino}"'))
        eng = motor_de(destino)
        with eng.begin() as c:
            for sentencia in ddl:
                c.execute(text(sentencia))
            for tabla, filas in datos.items():
                if not filas:
                    continue
                cols = list(filas[0].keys())
                lista = ", ".join(f'"{x}"' for x in cols)
                marcas = ", ".join(f":p{i}" for i in range(len(cols)))
                c.execute(
                    text(f'INSERT INTO "{tabla}" ({lista}) VALUES ({marcas})'),
                    [{f"p{i}": fila.get(col) for i, col in enumerate(cols)} for fila in filas],
                )
        ajustar_secuencias(eng)
        with eng.connect() as c:
            restaurados = {t: c.execute(text(f'SELECT count(*) FROM "{t}"')).scalar() for t in datos}
    except SQLAlchemyError as e:
        raise HTTPException(400, f"No se pudo restaurar: {mensaje(e)}")
    return {
        "mensaje": f"Respaldo restaurado en {destino}",
        "registros_en_el_archivo": {t: len(f) for t, f in datos.items()},
        "registros_restaurados": restaurados,
    }


# ============ 4.5 Usuarios: 10 usuarios con permisos ============
# Los roles pertenecen al servidor completo; los permisos (GRANT) a cada base.

NOMBRE_USUARIO = re.compile(r"^pr_[a-z0-9_]{2,40}$")
CLAVE_OK = re.compile(r"^[A-Za-z0-9_!@#%^*.-]{8,64}$")

GRUPOS = {
    "pr_rol_admin": [
        "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO pr_rol_admin",
        "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO pr_rol_admin",
    ],
    "pr_rol_ventas": [
        "GRANT SELECT ON categoria, producto, cliente, venta, detalle_venta TO pr_rol_ventas",
        "GRANT INSERT ON cliente, venta, detalle_venta TO pr_rol_ventas",
        "GRANT UPDATE (stock) ON producto TO pr_rol_ventas",
        "GRANT USAGE, SELECT ON SEQUENCE cliente_id_seq, venta_id_seq, detalle_venta_id_seq TO pr_rol_ventas",
    ],
    "pr_rol_inventario": [
        "GRANT SELECT, INSERT, UPDATE, DELETE ON categoria, producto, proveedor, suministro, detalle_suministro TO pr_rol_inventario",
        "GRANT SELECT ON cliente, venta, detalle_venta TO pr_rol_inventario",
        "GRANT USAGE, SELECT ON SEQUENCE categoria_id_seq, producto_id_seq, proveedor_id_seq, suministro_id_seq, detalle_suministro_id_seq TO pr_rol_inventario",
    ],
    "pr_rol_consulta": [
        "GRANT SELECT ON ALL TABLES IN SCHEMA public TO pr_rol_consulta",
    ],
    "pr_rol_contabilidad": [
        "GRANT SELECT ON venta, detalle_venta, suministro, detalle_suministro, proveedor TO pr_rol_contabilidad",
        "GRANT SELECT (id, codigo, nombre, precio_compra, precio_venta) ON producto TO pr_rol_contabilidad",
    ],
}

USUARIOS = [
    ("pr_admin_ana", ["pr_rol_admin"]),
    ("pr_gerente_luis", ["pr_rol_inventario", "pr_rol_ventas"]),
    ("pr_cajero_maria", ["pr_rol_ventas"]),
    ("pr_cajero_pedro", ["pr_rol_ventas"]),
    ("pr_cajero_sofia", ["pr_rol_ventas"]),
    ("pr_almacen_jose", ["pr_rol_inventario"]),
    ("pr_almacen_laura", ["pr_rol_inventario"]),
    ("pr_auditor_carlos", ["pr_rol_consulta"]),
    ("pr_auditor_diana", ["pr_rol_consulta"]),
    ("pr_contador_raul", ["pr_rol_contabilidad"]),
]


class CrearUsuarios(BaseModel):
    clave: str = "Temporal_123"  # contraseña temporal de práctica


@router.get("/usuarios/script")
def script_usuarios():
    """El mismo SQL que se ejecuta al crear los usuarios."""
    sql = ["-- Roles de grupo (no inician sesión)"]
    sql += [f"CREATE ROLE {r} NOLOGIN;" for r in GRUPOS]
    sql.append("\n-- Permisos de cada grupo")
    for sentencias in GRUPOS.values():
        sql += [s + ";" for s in sentencias]
    sql.append("\n-- Los 10 usuarios")
    sql += [f"CREATE USER {u} PASSWORD 'Temporal_123';" for u, _ in USUARIOS]
    sql.append("\n-- Pertenencia a grupos")
    sql += [f"GRANT {r} TO {u};" for u, roles in USUARIOS for r in roles]
    return {"script": "\n".join(sql)}


@router.post("/usuarios/{bd}", status_code=201)
def crear_usuarios(bd: str, d: CrearUsuarios = CrearUsuarios()):
    """Crea 5 roles de grupo y 10 usuarios, y les da permisos sobre las tablas de la base."""
    if not CLAVE_OK.match(d.clave):
        raise HTTPException(400, "La clave debe tener de 8 a 64 caracteres (letras, números y _!@#%^*.-)")
    eng = motor_existente(bd)

    def existe(c, rol):
        return c.execute(text("SELECT 1 FROM pg_roles WHERE rolname = :n"), {"n": rol}).scalar() is not None

    try:
        with admin.connect() as c:
            for rol in GRUPOS:
                if not existe(c, rol):
                    c.execute(text(f"CREATE ROLE {rol} NOLOGIN"))
            for usuario, roles in USUARIOS:
                if not existe(c, usuario):
                    c.execute(text(f"CREATE ROLE {usuario} LOGIN PASSWORD '{d.clave}'"))
                for rol in roles:
                    c.execute(text(f"GRANT {rol} TO {usuario}"))
        with eng.begin() as c:
            for sentencias in GRUPOS.values():
                for s in sentencias:
                    c.execute(text(s))
    except SQLAlchemyError as e:
        raise HTTPException(400, f"{mensaje(e)} (¿ya creaste las tablas en esa base?)")
    return {"mensaje": f"{len(USUARIOS)} usuarios y {len(GRUPOS)} roles de grupo listos en {bd}"}


@router.get("/usuarios/{bd}/permisos")
def ver_permisos(bd: str):
    """Matriz usuario x tabla. S=SELECT I=INSERT U=UPDATE D=DELETE; minúscula = solo algunas columnas."""
    eng = motor_existente(bd)
    tabla_sql = "('public.' || quote_ident(t.tablename))"
    partes = []
    for priv, letra in [("SELECT", "S"), ("INSERT", "I"), ("UPDATE", "U"), ("DELETE", "D")]:
        caso = f"CASE WHEN has_table_privilege(r.rolname, {tabla_sql}, '{priv}') THEN '{letra}' "
        if priv != "DELETE":  # DELETE no existe como permiso por columna
            caso += f"WHEN has_any_column_privilege(r.rolname, {tabla_sql}, '{priv}') THEN '{letra.lower()}' "
        partes.append(caso + "ELSE '-' END")
    consulta = f"""
        SELECT r.rolname, t.tablename, {' || '.join(partes)}
        FROM pg_roles r CROSS JOIN pg_tables t
        WHERE r.rolname LIKE 'pr\\_%' AND r.rolcanlogin AND t.schemaname = 'public'
        ORDER BY 1, 2
    """
    matriz: dict[str, dict[str, str]] = {}
    with eng.connect() as c:
        for usuario, tabla, permisos in c.execute(text(consulta)):
            matriz.setdefault(usuario, {})[tabla] = permisos
    if not matriz:
        raise HTTPException(404, "No hay usuarios pr_*. Pulsa «Crear 10 usuarios» primero")
    return matriz


# ============ 4.6 Importar y exportar ============

def copia_portable(origen: MetaData) -> MetaData:
    """Copia el esquema con tipos genéricos y sin DEFAULT/CHECK/índices de PostgreSQL."""
    nueva = MetaData()
    for t in origen.sorted_tables:
        t.to_metadata(nueva)
    for t in nueva.tables.values():
        for c in t.columns:
            try:
                c.type = c.type.as_generic()
            except NotImplementedError:
                pass
            c.server_default = None
        for k in [k for k in t.constraints if isinstance(k, CheckConstraint)]:
            t.constraints.discard(k)
        t.indexes.clear()
    return nueva


@router.get("/migracion/{bd}/sqlite")
def exportar_sqlite(bd: str):
    """PostgreSQL -> archivo .sqlite (otro motor)."""
    origen = motor_existente(bd)
    meta = reflejar(origen)
    portable = copia_portable(meta)
    EXPORTACIONES.mkdir(exist_ok=True)
    ruta = EXPORTACIONES / f"{bd}.sqlite"
    ruta.unlink(missing_ok=True)
    destino = create_engine(f"sqlite:///{ruta.as_posix()}")
    try:
        portable.create_all(destino)
        with origen.connect() as o, destino.begin() as d:
            for t in portable.sorted_tables:
                filas = [dict(f) for f in o.execute(meta.tables[t.name].select()).mappings()]
                if filas:
                    d.execute(t.insert(), filas)
    except SQLAlchemyError as e:
        raise HTTPException(400, f"No se pudo exportar: {mensaje(e)}")
    finally:
        destino.dispose()
    return FileResponse(ruta, filename=f"{bd}.sqlite", media_type="application/octet-stream")


def literal_mysql(v) -> str:
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, (int, float, Decimal)):
        return str(v)
    if isinstance(v, datetime):
        if v.tzinfo:
            v = v.astimezone(timezone.utc).replace(tzinfo=None)
        return "'" + v.strftime("%Y-%m-%d %H:%M:%S.%f") + "'"
    if isinstance(v, (date, time)):
        return "'" + v.isoformat() + "'"
    if isinstance(v, (dict, list)):
        v = json.dumps(v, ensure_ascii=False)
    return "'" + str(v).replace("\\", "\\\\").replace("'", "''") + "'"


@router.get("/migracion/{bd}/mysql")
def exportar_mysql(bd: str):
    """PostgreSQL -> script .sql con sintaxis de MySQL (se ejecuta con: mysql -u root -p < archivo.sql)."""
    origen = motor_existente(bd)
    meta = reflejar(origen)
    portable = copia_portable(meta)
    dialecto = mysql.dialect()
    try:
        sql = [
            f"-- Exportado de PostgreSQL ({bd}) a MySQL",
            "SET NAMES utf8mb4;",
            "SET FOREIGN_KEY_CHECKS = 0;",
            f"CREATE DATABASE IF NOT EXISTS `{bd}` CHARACTER SET utf8mb4;",
            f"USE `{bd}`;",
            "",
        ]
        sql += [f"DROP TABLE IF EXISTS `{t.name}`;" for t in portable.sorted_tables]
        sql.append("")
        sql += [str(CreateTable(t).compile(dialect=dialecto)).strip() + ";" for t in portable.sorted_tables]
        sql.append("")
        with origen.connect() as c:
            for t in portable.sorted_tables:
                cols = [col.name for col in t.columns]
                lista = ", ".join(f"`{x}`" for x in cols)
                for fila in c.execute(meta.tables[t.name].select()).mappings():
                    valores = ", ".join(literal_mysql(fila[x]) for x in cols)
                    sql.append(f"INSERT INTO `{t.name}` ({lista}) VALUES ({valores});")
        sql.append("SET FOREIGN_KEY_CHECKS = 1;")
    except CompileError as e:
        raise HTTPException(400, f"No se pudo convertir a MySQL: {e}")
    return descarga("\n".join(sql) + "\n", f"{bd}_mysql.sql", "application/sql")


def leer_tabla(bd: str, tabla: str):
    eng = motor_existente(bd)
    validar_tabla(eng, tabla)
    with eng.connect() as c:
        res = c.execute(text(f'SELECT * FROM "{tabla}" ORDER BY 1'))
        return list(res.keys()), [list(r) for r in res]


@router.get("/migracion/{bd}/tabla/{tabla}/csv")
def tabla_a_csv(bd: str, tabla: str):
    cols, filas = leer_tabla(bd, tabla)
    salida = io.StringIO()
    w = csv.writer(salida)
    w.writerow(cols)
    w.writerows([["" if v is None else v for v in fila] for fila in filas])
    return descarga("\ufeff" + salida.getvalue(), f"{tabla}.csv", "text/csv")  # BOM: Excel lee bien los acentos


@router.get("/migracion/{bd}/tabla/{tabla}/json")
def tabla_a_json(bd: str, tabla: str):
    cols, filas = leer_tabla(bd, tabla)
    datos = [dict(zip(cols, fila)) for fila in filas]
    return descarga(json.dumps(datos, default=str, ensure_ascii=False, indent=1), f"{tabla}.json", "application/json")


class ImportarTabla(BaseModel):
    formato: str  # "csv" o "json"
    contenido: str


@router.post("/migracion/{bd}/tabla/{tabla}/importar")
def importar_a_tabla(bd: str, tabla: str, d: ImportarTabla):
    """Inserta en la tabla los registros de un archivo CSV o JSON (todo o nada)."""
    eng = motor_existente(bd)
    validar_tabla(eng, tabla)
    try:
        if d.formato == "csv":
            lector = csv.DictReader(io.StringIO(d.contenido.lstrip("\ufeff")))
            filas = [{k: (v if v != "" else None) for k, v in f.items()} for f in lector]
        elif d.formato == "json":
            filas = json.loads(d.contenido)
        else:
            raise HTTPException(400, "El formato debe ser csv o json")
    except (json.JSONDecodeError, csv.Error) as e:
        raise HTTPException(400, f"No se pudo leer el archivo: {e}")
    if not isinstance(filas, list) or not filas or not all(isinstance(f, dict) for f in filas):
        raise HTTPException(400, "El archivo debe traer una lista de registros (JSON) o filas con encabezado (CSV)")

    cols = list(filas[0].keys())
    validas = {c["name"] for c in inspect(eng).get_columns(tabla)}
    malas = [c for c in cols if c not in validas]
    if malas:
        raise HTTPException(400, f"Columnas que no existen en {tabla}: {', '.join(map(str, malas))}")

    lista = ", ".join(f'"{c}"' for c in cols)
    marcas = ", ".join(f":p{i}" for i in range(len(cols)))
    try:
        with eng.begin() as c:
            c.execute(
                text(f'INSERT INTO "{tabla}" ({lista}) VALUES ({marcas})'),
                [{f"p{i}": f.get(col) for i, col in enumerate(cols)} for f in filas],
            )
        ajustar_secuencias(eng)
    except SQLAlchemyError as e:
        raise HTTPException(400, f"No se importó nada: {mensaje(e)}")
    return {"mensaje": f"{len(filas)} registros importados en {tabla}"}
