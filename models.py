from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class Categoria(SQLModel, table=True):
    __tablename__ = "categoria"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=80, unique=True)

    productos: list["Producto"] = Relationship(back_populates="categoria")


class Proveedor(SQLModel, table=True):
    __tablename__ = "proveedor"

    id: Optional[int] = Field(default=None, primary_key=True)
    rfc: Optional[str] = Field(default=None, max_length=13, unique=True)
    nombre: str = Field(max_length=120)
    telefono: Optional[str] = Field(default=None, max_length=20)
    direccion: Optional[str] = Field(default=None, max_length=200)

    suministros: list["Suministro"] = Relationship(back_populates="proveedor")


class Producto(SQLModel, table=True):
    __tablename__ = "producto"

    id: Optional[int] = Field(default=None, primary_key=True)
    codigo: str = Field(max_length=30, unique=True, index=True)  # código de barras
    nombre: str = Field(max_length=120)
    precio_compra: Decimal = Field(max_digits=10, decimal_places=2)
    precio_venta: Decimal = Field(max_digits=10, decimal_places=2)
    stock: int = Field(default=0)
    stock_minimo: int = Field(default=0)
    categoria_id: int = Field(foreign_key="categoria.id")

    categoria: Optional[Categoria] = Relationship(back_populates="productos")
    detalles_venta: list["DetalleVenta"] = Relationship(back_populates="producto")
    detalles_suministro: list["DetalleSuministro"] = Relationship(back_populates="producto")


class Cliente(SQLModel, table=True):
    __tablename__ = "cliente"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=80)
    apellidos: str = Field(max_length=120)
    telefono: Optional[str] = Field(default=None, max_length=20)
    direccion: Optional[str] = Field(default=None, max_length=200)
    fecha_nacimiento: Optional[date] = None

    ventas: list["Venta"] = Relationship(back_populates="cliente")


class Venta(SQLModel, table=True):
    __tablename__ = "venta"

    id: Optional[int] = Field(default=None, primary_key=True)
    cliente_id: Optional[int] = Field(default=None, foreign_key="cliente.id")  # NULL = venta al público
    fecha: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metodo_pago: str = Field(default="efectivo", max_length=20)

    cliente: Optional[Cliente] = Relationship(back_populates="ventas")
    detalles: list["DetalleVenta"] = Relationship(back_populates="venta")


class DetalleVenta(SQLModel, table=True):
    __tablename__ = "detalle_venta"

    id: Optional[int] = Field(default=None, primary_key=True)
    venta_id: int = Field(foreign_key="venta.id")
    producto_id: int = Field(foreign_key="producto.id")
    cantidad: int
    precio_unitario: Decimal = Field(max_digits=10, decimal_places=2)  # precio al momento de la venta

    venta: Optional[Venta] = Relationship(back_populates="detalles")
    producto: Optional[Producto] = Relationship(back_populates="detalles_venta")


class Suministro(SQLModel, table=True):
    __tablename__ = "suministro"

    id: Optional[int] = Field(default=None, primary_key=True)
    proveedor_id: int = Field(foreign_key="proveedor.id")
    fecha: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    proveedor: Optional[Proveedor] = Relationship(back_populates="suministros")
    detalles: list["DetalleSuministro"] = Relationship(back_populates="suministro")


class DetalleSuministro(SQLModel, table=True):
    __tablename__ = "detalle_suministro"

    id: Optional[int] = Field(default=None, primary_key=True)
    suministro_id: int = Field(foreign_key="suministro.id")
    producto_id: int = Field(foreign_key="producto.id")
    cantidad: int
    costo_unitario: Decimal = Field(max_digits=10, decimal_places=2)

    suministro: Optional[Suministro] = Relationship(back_populates="detalles")
    producto: Optional[Producto] = Relationship(back_populates="detalles_suministro")