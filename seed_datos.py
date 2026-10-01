"""
Inserta los datos de ejemplo (Cliente, Proveedor, Producto, Compra)
en la base de datos, adaptados al esquema normalizado del proyecto.

Cómo se adaptó cada tabla del ejercicio a este esquema:

- CLIENTE      -> tabla `cliente` (nombre, apellidos, direccion, fecha_nacimiento).
                  El DNI del ejercicio se usa solo aquí, en el script, para
                  saber a qué cliente pertenece cada compra; la tabla no
                  guarda el DNI porque el modelo usa un id autonumérico.

- PROVEEDOR    -> tabla `proveedor`. El NIF del ejercicio se guarda en la
                  columna `rfc`, que ya existía para ese propósito.

- PRODUCTO     -> tabla `producto`. El Codigo_Producto se guarda tal cual en
                  la columna `codigo`. Como el modelo pide una `categoria_id`
                  obligatoria (el ejercicio no trae categorías), se crearon
                  3 categorías razonables según el tipo de producto.
                  precio_venta = Precio_Unitario del ejercicio.
                  precio_compra = 75% del precio de venta (el ejercicio no
                  trae precio de compra; ajusta este porcentaje si tienes
                  el dato real).

- PRODUCTO-PROVEEDOR -> en el ejercicio, cada producto tenía UN proveedor
                  fijo (columna NIF_Proveedor en PRODUCTO). En este esquema
                  normalizado esa relación se guarda como una entrega real:
                  se crea un `suministro` por proveedor con su
                  `detalle_suministro` (cantidad = stock inicial que se les
                  dio a los productos, costo_unitario = precio_compra).

- COMPRA       -> tabla `venta` + `detalle_venta`. Las filas de COMPRA con
                  el mismo cliente y la misma fecha se agrupan en una sola
                  venta (así quedó dos veces en tus datos: 45120378K el
                  2026-08-14 con 2 productos, y 29845173P el 2026-08-20 con
                  2 productos). precio_unitario = Precio_Unitario del
                  producto al momento de la compra.
"""

from datetime import date, datetime, timezone
from decimal import Decimal

import models
from database import create_db_and_tables, engine
from sqlmodel import Session

# ---------------------------------------------------------------------
# 1. Datos tal cual como en el ejercicio
# ---------------------------------------------------------------------

CLIENTES = [
    ("45120378K", "Laura", "Ramírez Gómez", "Av. Hidalgo 245, Tonalá", date(1998, 3, 14)),
    ("38294011T", "Miguel Ángel", "Torres Vega", "Calle Juárez 87, Guadalajara", date(1995, 11, 2)),
    ("51003467M", "Ana Sofía", "Delgado Ruiz", "Priv. Colón 12, Zapopan", date(2001, 7, 23)),
    ("29845173P", "Roberto", "Núñez Salas", "Av. Tonaltecas 310, Tonalá", date(1987, 1, 30)),
    ("60712394D", "Carmen", "Ibarra Luna", "Calle Morelos 58, Tlaquepaque", date(1993, 5, 19)),
    ("47038261H", "Javier", "Peña Castro", "Av. Patria 1204, Zapopan", date(1990, 9, 8)),
    ("55901728B", "Daniela", "Fuentes Mora", "Calle Reforma 76, Guadalajara", date(2000, 12, 11)),
    ("31674508R", "Óscar", "Beltrán Ríos", "Av. Río Nilo 902, Tonalá", date(1984, 4, 27)),
    ("62185043W", "Silvia", "Aguilar Pérez", "Calle Allende 33, Tlajomulco", date(1997, 8, 5)),
    ("40536912G", "Héctor", "Villaseñor Cruz", "Av. López Mateos 640, Zapopan", date(1992, 2, 16)),
]

PROVEEDORES = [
    ("B78451236", "Distribuidora Bajío", "Calle Industria 40, León"),
    ("A15630298", "Tecno Import S.A.", "Av. Central 118, Querétaro"),
    ("C49207531", "Papelera del Norte", "Blvd. Norte 77, Monterrey"),
    ("B60918342", "Muebles Occidente", "Calle Pino 205, Guadalajara"),
    ("A27364159", "Electro Mayoreo", "Av. Revolución 890, CDMX"),
    ("D83015674", "Insumos del Centro", "Calle Sur 14, Puebla"),
    ("B39826470", "Global Cómputo", "Av. Tecnológico 55, Tijuana"),
    ("C71204983", "Suministros Jalisco", "Calle Obreros 61, Tonalá"),
    ("A94517820", "Comercial Andina", "Av. Hidalgo 1500, Morelia"),
    ("D52678134", "Almacenes Pacífico", "Blvd. Costero 9, Mazatlán"),
]

# categoria asignada según el tipo de producto (el ejercicio no traía categorías)
CATEGORIAS = ["Cómputo y Electrónica", "Mobiliario", "Papelería"]

PRODUCTOS = [
    # codigo, nombre, precio_venta, nif_proveedor, categoria, stock_inicial
    ("P00001", "Teclado mecánico", Decimal("1250.00"), "B39826470", "Cómputo y Electrónica", 20),
    ("P00002", "Mouse inalámbrico", Decimal("380.50"), "B39826470", "Cómputo y Electrónica", 20),
    ("P00003", "Monitor 24 pulgadas", Decimal("3499.00"), "A15630298", "Cómputo y Electrónica", 15),
    ("P00004", "Silla ergonómica", Decimal("2890.00"), "B60918342", "Mobiliario", 15),
    ("P00005", "Escritorio de madera", Decimal("4150.00"), "B60918342", "Mobiliario", 15),
    ("P00006", "Resma de papel", Decimal("129.90"), "C49207531", "Papelería", 50),
    ("P00007", "Multifuncional láser", Decimal("5299.00"), "A27364159", "Cómputo y Electrónica", 10),
    ("P00008", "Memoria USB 64 GB", Decimal("215.00"), "B78451236", "Cómputo y Electrónica", 30),
    ("P00009", "Audífonos diadema", Decimal("899.00"), "D52678134", "Cómputo y Electrónica", 20),
    ("P00010", "Regulador de voltaje", Decimal("640.00"), "C71204983", "Cómputo y Electrónica", 20),
]

# (DNI_Cliente, Codigo_Producto, Fecha_Compra, Cantidad)
COMPRAS = [
    ("45120378K", "P00001", date(2026, 8, 14), 2),
    ("45120378K", "P00002", date(2026, 8, 14), 1),
    ("38294011T", "P00003", date(2026, 8, 15), 1),
    ("51003467M", "P00006", date(2026, 8, 18), 10),
    ("29845173P", "P00004", date(2026, 8, 20), 4),
    ("29845173P", "P00005", date(2026, 8, 20), 2),
    ("60712394D", "P00008", date(2026, 8, 21), 3),
    ("47038261H", "P00007", date(2026, 8, 24), 1),
    ("55901728B", "P00009", date(2026, 8, 26), 2),
    ("31674508R", "P00010", date(2026, 8, 28), 1),
    ("62185043W", "P00001", date(2026, 9, 1), 1),
    ("45120378K", "P00001", date(2026, 9, 3), 1),
]

# ---------------------------------------------------------------------
# 2. Inserción
# ---------------------------------------------------------------------

create_db_and_tables()

with Session(engine) as session:

    # -- Categorías --
    categoria_por_nombre = {}
    for nombre in CATEGORIAS:
        cat = models.Categoria(nombre=nombre)
        session.add(cat)
        session.flush()  # asigna el id sin cerrar la transacción
        categoria_por_nombre[nombre] = cat

    # -- Clientes: DNI -> objeto Cliente (el DNI solo se usa aquí, no se guarda) --
    cliente_por_dni = {}
    for dni, nombre, apellidos, direccion, nacimiento in CLIENTES:
        c = models.Cliente(nombre=nombre, apellidos=apellidos, direccion=direccion, fecha_nacimiento=nacimiento)
        session.add(c)
        session.flush()
        cliente_por_dni[dni] = c

    # -- Proveedores: NIF -> objeto Proveedor --
    proveedor_por_nif = {}
    for nif, nombre, direccion in PROVEEDORES:
        p = models.Proveedor(rfc=nif, nombre=nombre, direccion=direccion)
        session.add(p)
        session.flush()
        proveedor_por_nif[nif] = p

    # -- Productos: Codigo_Producto -> objeto Producto --
    producto_por_codigo = {}
    for codigo, nombre, precio_venta, nif_proveedor, categoria, stock_inicial in PRODUCTOS:
        precio_compra = (precio_venta * Decimal("0.75")).quantize(Decimal("0.01"))
        prod = models.Producto(
            codigo=codigo,
            nombre=nombre,
            precio_compra=precio_compra,
            precio_venta=precio_venta,
            stock=stock_inicial,
            stock_minimo=5,
            categoria_id=categoria_por_nombre[categoria].id,
        )
        session.add(prod)
        session.flush()
        producto_por_codigo[codigo] = prod

    # -- Suministros: un envío inicial por proveedor, con sus productos --
    productos_por_proveedor = {}
    for codigo, _, _, nif_proveedor, _, _ in PRODUCTOS:
        productos_por_proveedor.setdefault(nif_proveedor, []).append(codigo)

    for nif, codigos in productos_por_proveedor.items():
        suministro = models.Suministro(
            proveedor_id=proveedor_por_nif[nif].id,
            fecha=datetime(2026, 8, 1, tzinfo=timezone.utc),
        )
        session.add(suministro)
        session.flush()
        for codigo in codigos:
            prod = producto_por_codigo[codigo]
            session.add(models.DetalleSuministro(
                suministro_id=suministro.id,
                producto_id=prod.id,
                cantidad=prod.stock,
                costo_unitario=prod.precio_compra,
            ))

    # -- Ventas: agrupar COMPRA por (cliente, fecha) --
    ventas_agrupadas = {}
    for dni, codigo, fecha, cantidad in COMPRAS:
        ventas_agrupadas.setdefault((dni, fecha), []).append((codigo, cantidad))

    for (dni, fecha), items in ventas_agrupadas.items():
        venta = models.Venta(
            cliente_id=cliente_por_dni[dni].id,
            fecha=datetime(fecha.year, fecha.month, fecha.day, tzinfo=timezone.utc),
            metodo_pago="efectivo",
        )
        session.add(venta)
        session.flush()
        for codigo, cantidad in items:
            prod = producto_por_codigo[codigo]
            session.add(models.DetalleVenta(
                venta_id=venta.id,
                producto_id=prod.id,
                cantidad=cantidad,
                precio_unitario=prod.precio_venta,
            ))
            prod.stock -= cantidad  # refleja la venta en el inventario
            session.add(prod)

    session.commit()

print("Datos insertados: 10 clientes, 10 proveedores, 10 productos, "
      f"{len(productos_por_proveedor)} suministros, {len(ventas_agrupadas)} ventas "
      f"({len(COMPRAS)} líneas de compra).")