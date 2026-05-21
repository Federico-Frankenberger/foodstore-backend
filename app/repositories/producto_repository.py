from datetime import datetime, timezone
from typing import List, Optional

from sqlmodel import Session, select

from app.models.producto import Producto
from app.models.producto_categoria import ProductoCategoria
from app.models.producto_ingrediente import ProductoIngrediente
from app.repositories.base import BaseRepository
from app.schemas.producto import ProductoCreate


class ProductoRepository(BaseRepository[Producto]):
    def __init__(self, sesion: Session):
        super().__init__(Producto, sesion)

    def crear(self, datos: ProductoCreate) -> Producto:
        producto = Producto(
            nombre=datos.nombre,
            descripcion=datos.descripcion,
            margen_ganancia=datos.margen_ganancia,
            imagenes_url=datos.imagenes_url,
            disponible=datos.disponible,
            unidad_venta_id=datos.unidad_venta_id,
            stock_directo=datos.stock_directo,
            precio_base=datos.precio_base,
        )
        self.sesion.add(producto)
        self.sesion.flush()

        for asignacion in datos.categorias:
            self.sesion.add(ProductoCategoria(
                producto_id=producto.id,
                categoria_id=asignacion.categoria_id,
                es_principal=asignacion.es_principal,
            ))

        for asignacion in datos.ingredientes:
            self.sesion.add(ProductoIngrediente(
                producto_id=producto.id,
                ingrediente_id=asignacion.ingrediente_id,
                cantidad=asignacion.cantidad,
                unidad_medida_id=asignacion.unidad_medida_id,
                es_removible=asignacion.es_removible,
            ))

        self.sesion.flush()
        self.sesion.refresh(producto)
        return producto

    def obtener_por_id(self, id: int) -> Optional[Producto]:
        producto = self.sesion.get(Producto, id)
        if producto and producto.deleted_at is not None:
            return None
        return producto

    def obtener_todos(
        self,
        skip: int = 0,
        limit: int = 10,
        nombre: Optional[str] = None,
        disponible: Optional[bool] = None,
        categoria_id: Optional[int] = None,
    ) -> List[Producto]:
        consulta = select(Producto).where(Producto.deleted_at == None)
        if nombre:
            consulta = consulta.where(Producto.nombre.icontains(nombre))
        if disponible is not None:
            consulta = consulta.where(Producto.disponible == disponible)
        if categoria_id is not None:
            consulta = (
                consulta
                .join(ProductoCategoria, ProductoCategoria.producto_id == Producto.id)
                .where(ProductoCategoria.categoria_id == categoria_id)
                .distinct()
            )
        consulta = consulta.offset(skip).limit(limit)
        return list(self.sesion.exec(consulta).all())

    def actualizar(self, producto: Producto, campos: dict) -> Producto:
        for campo, valor in campos.items():
            setattr(producto, campo, valor)
        self.sesion.add(producto)
        self.sesion.flush()
        self.sesion.refresh(producto)
        return producto

    def eliminar(self, producto: Producto) -> None:
        producto.deleted_at = datetime.now(timezone.utc)
        self.sesion.add(producto)
        self.sesion.flush()

    def agregar_categoria(self, producto_id: int, categoria_id: int, es_principal: bool = False) -> Producto:
        self.sesion.add(ProductoCategoria(
            producto_id=producto_id,
            categoria_id=categoria_id,
            es_principal=es_principal,
        ))
        self.sesion.flush()
        producto = self.sesion.get(Producto, producto_id)
        self.sesion.refresh(producto)
        return producto

    def quitar_categoria(self, producto_id: int, categoria_id: int) -> bool:
        vinculo = self.sesion.get(ProductoCategoria, (producto_id, categoria_id))
        if not vinculo:
            return False
        self.sesion.delete(vinculo)
        self.sesion.flush()
        return True

    def agregar_ingrediente(
        self,
        producto_id: int,
        ingrediente_id: int,
        cantidad,
        unidad_medida_id: int,
        es_removible: bool,
    ) -> Producto:
        self.sesion.add(ProductoIngrediente(
            producto_id=producto_id,
            ingrediente_id=ingrediente_id,
            cantidad=cantidad,
            unidad_medida_id=unidad_medida_id,
            es_removible=es_removible,
        ))
        self.sesion.flush()
        producto = self.sesion.get(Producto, producto_id)
        self.sesion.refresh(producto)
        return producto

    def quitar_ingrediente(self, producto_id: int, ingrediente_id: int) -> bool:
        vinculo = self.sesion.get(ProductoIngrediente, (producto_id, ingrediente_id))
        if not vinculo:
            return False
        self.sesion.delete(vinculo)
        self.sesion.flush()
        return True
