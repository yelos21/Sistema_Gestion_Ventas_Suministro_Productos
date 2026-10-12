from contextlib import asynccontextmanager
from sqlite3 import IntegrityError
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select
from fastapi.middleware.cors import CORSMiddleware
import models
from database import create_db_and_tables, get_session

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="Sistema de Gestión de Ventas y Suministro", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)




@app.get("/api/categorias", response_model=list[models.Categoria])
def listar_categorias(session: Session = Depends(get_session)):
    return session.exec(select(models.Categoria)).all()


@app.post("/api/categorias", response_model=models.Categoria, status_code=201)
def crear_categoria(categoria: models.Categoria, session: Session = Depends(get_session)):
    categoria.id = None
    session.add(categoria)
    session.commit()
    session.refresh(categoria)
    return categoria


@app.delete("/api/categorias/{categoria_id}", status_code=204)
def borrar_categoria(categoria_id: int, session: Session = Depends(get_session)):
    obj = session.get(models.Categoria, categoria_id)
    if not obj:
        raise HTTPException(404, "Categoría no encontrada")
    session.delete(obj)
    session.commit()



@app.get("/api/proveedores", response_model=list[models.Proveedor])
def listar_proveedores(session: Session = Depends(get_session)):
    return session.exec(select(models.Proveedor)).all()


@app.post("/api/proveedores", response_model=models.Proveedor, status_code=201)
def crear_proveedor(proveedor: models.Proveedor, session: Session = Depends(get_session)):
    proveedor.id = None
    session.add(proveedor)
    session.commit()
    session.refresh(proveedor)
    return proveedor


@app.delete("/api/proveedores/{proveedor_id}", status_code=204)
def borrar_proveedor(proveedor_id: int, session: Session = Depends(get_session)):
    obj = session.get(models.Proveedor, proveedor_id)
    if not obj:
        raise HTTPException(404, "Proveedor no encontrado")
    session.delete(obj)
    session.commit()



@app.get("/api/productos", response_model=list[models.Producto])
def listar_productos(categoria_id: Optional[int] = None, session: Session = Depends(get_session)):
    query = select(models.Producto)
    if categoria_id is not None:
        query = query.where(models.Producto.categoria_id == categoria_id)
    return session.exec(query).all()


@app.post("/api/productos", response_model=models.Producto, status_code=201)
def crear_producto(producto: models.Producto, session: Session = Depends(get_session)):
    producto.id = None
    session.add(producto)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(409, "Ya existe un producto con ese código, o la categoría no existe")
    session.refresh(producto)
    return producto

@app.put("/api/productos/{producto_id}", response_model=models.Producto)
def actualizar_producto(producto_id: int, datos: models.Producto, session: Session = Depends(get_session)):
    producto = session.get(models.Producto, producto_id)
    if not producto:
        raise HTTPException(404, "Producto no encontrado")
    datos_dict = datos.model_dump(exclude_unset=True, exclude={"id"})
    for campo, valor in datos_dict.items():
        setattr(producto, campo, valor)
    session.add(producto)
    session.commit()
    session.refresh(producto)
    return producto


@app.delete("/api/productos/{producto_id}", status_code=204)
def borrar_producto(producto_id: int, session: Session = Depends(get_session)):
    obj = session.get(models.Producto, producto_id)
    if not obj:
        raise HTTPException(404, "Producto no encontrado")
    session.delete(obj)
    session.commit()



@app.get("/api/clientes", response_model=list[models.Cliente])
def listar_clientes(session: Session = Depends(get_session)):
    return session.exec(select(models.Cliente)).all()


@app.post("/api/clientes", response_model=models.Cliente, status_code=201)
def crear_cliente(cliente: models.Cliente, session: Session = Depends(get_session)):
    cliente.id = None
    session.add(cliente)
    session.commit()
    session.refresh(cliente)
    return cliente


@app.delete("/api/clientes/{cliente_id}", status_code=204)
def borrar_cliente(cliente_id: int, session: Session = Depends(get_session)):
    obj = session.get(models.Cliente, cliente_id)
    if not obj:
        raise HTTPException(404, "Cliente no encontrado")
    session.delete(obj)
    session.commit()



class ItemVenta(models.SQLModel):
    producto_id: int
    cantidad: int


class VentaEntrada(models.SQLModel):
    cliente_id: Optional[int] = None
    metodo_pago: str = "efectivo"
    items: list[ItemVenta]


@app.get("/api/ventas", response_model=list[models.Venta])
def listar_ventas(session: Session = Depends(get_session)):
    return session.exec(select(models.Venta)).all()


@app.get("/api/ventas/resumen")
def resumen_ventas(session: Session = Depends(get_session)):
    ventas = session.exec(
        select(models.Venta).order_by(models.Venta.id.desc())
    ).all()
    resultado = []
    for v in ventas:
        detalles = session.exec(
            select(models.DetalleVenta).where(models.DetalleVenta.venta_id == v.id)
        ).all()
        total = sum(d.precio_unitario * d.cantidad for d in detalles)
        resultado.append({
            "id": v.id,
            "fecha": v.fecha,
            "metodo_pago": v.metodo_pago,
            "articulos": sum(d.cantidad for d in detalles),
            "total": total,
        })
    return resultado

@app.post("/api/ventas", status_code=201)
def crear_venta(entrada: VentaEntrada, session: Session = Depends(get_session)):
    if not entrada.items:
        raise HTTPException(400, "La venta no tiene productos")

    venta = models.Venta(cliente_id=entrada.cliente_id, metodo_pago=entrada.metodo_pago)
    session.add(venta)
    session.flush()  

    total = 0
    for item in entrada.items:
        if item.cantidad <= 0:
            raise HTTPException(400, "La cantidad debe ser mayor a 0")

        producto = session.get(models.Producto, item.producto_id)
        if not producto:
            raise HTTPException(404, f"Producto {item.producto_id} no encontrado")
        if producto.stock < item.cantidad:
            raise HTTPException(400, f"Stock insuficiente de {producto.nombre}")

        detalle = models.DetalleVenta(
            venta_id=venta.id,
            producto_id=producto.id,
            cantidad=item.cantidad,
            precio_unitario=producto.precio_venta,
        )
        producto.stock -= item.cantidad
        total += producto.precio_venta * item.cantidad
        session.add(detalle)
        session.add(producto)

    session.commit() 
    return {"venta_id": venta.id, "total": total, "mensaje": "Venta registrada"}


