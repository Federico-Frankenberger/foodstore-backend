from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import text
from sqlmodel import Session, select
from app.models.categoria import Categoria
from app.models.producto import Producto
from app.models.producto_categoria import ProductoCategoria
from app.repositories.base import BaseRepository
from app.schemas.categoria import CategoriaCreate


class CategoriaRepository(BaseRepository[Categoria]):
    def __init__(self, sesion: Session):
        super().__init__(Categoria, sesion)

    def crear(self, datos: CategoriaCreate) -> Categoria:
        categoria = Categoria(**datos.model_dump())
        self.sesion.add(categoria)
        self.sesion.flush()
        self.sesion.refresh(categoria)
        return categoria

    def obtener_por_id(self, id: int) -> Optional[Categoria]:
        categoria = self.sesion.get(Categoria, id)
        if categoria and categoria.deleted_at is not None:
            return None
        return categoria

    def obtener_todos(
        self,
        skip: int = 0,
        limit: int = 10,
        nombre: Optional[str] = None,
        parent_id: Optional[int] = None,
    ) -> List[Categoria]:
        consulta = select(Categoria).where(Categoria.deleted_at == None)
        if nombre:
            consulta = consulta.where(Categoria.nombre.icontains(nombre))
        if parent_id is not None:
            consulta = consulta.where(Categoria.parent_id == parent_id)
        consulta = consulta.offset(skip).limit(limit)
        return self.sesion.exec(consulta).all()

    def tiene_productos_activos(self, id: int) -> bool:
        resultado = self.sesion.exec(
            select(ProductoCategoria.categoria_id)
            .join(Producto, ProductoCategoria.producto_id == Producto.id)
            .where(
                ProductoCategoria.categoria_id == id,
                Producto.deleted_at == None,
            )
            .limit(1)
        ).first()
        return resultado is not None

    def obtener_hijos_activos(self, id: int) -> List[Categoria]:
        consulta = select(Categoria).where(
            Categoria.parent_id == id,
            Categoria.deleted_at == None,
        )
        return self.sesion.exec(consulta).all()

    def actualizar(self, categoria: Categoria, campos: dict) -> Categoria:
        for campo, valor in campos.items():
            setattr(categoria, campo, valor)
        self.sesion.add(categoria)
        self.sesion.flush()
        self.sesion.refresh(categoria)
        return categoria

    def get_tree(self) -> list[dict]:
        resultado = self.sesion.execute(
            text("""
                WITH RECURSIVE arbol AS (
                    SELECT id, parent_id, nombre, descripcion, imagen_url, 0 AS profundidad
                    FROM categoria
                    WHERE parent_id IS NULL
                      AND deleted_at IS NULL

                    UNION ALL

                    SELECT c.id, c.parent_id, c.nombre, c.descripcion, c.imagen_url,
                           a.profundidad + 1
                    FROM categoria c
                    JOIN arbol a ON c.parent_id = a.id
                    WHERE c.deleted_at IS NULL
                )
                SELECT * FROM arbol
                ORDER BY profundidad, nombre
            """)
        ).all()
        return [dict(row._mapping) for row in resultado]

    def would_create_cycle(self, categoria_id: int, nuevo_parent_id: int) -> bool:
        if categoria_id == nuevo_parent_id:
            return True
        resultado = self.sesion.execute(
            text("""
                WITH RECURSIVE ancestros AS (
                    SELECT id, parent_id
                    FROM categoria
                    WHERE id = :parent_id

                    UNION ALL

                    SELECT c.id, c.parent_id
                    FROM categoria c
                    JOIN ancestros a ON c.id = a.parent_id
                )
                SELECT id FROM ancestros WHERE id = :categoria_id
            """).bindparams(parent_id=nuevo_parent_id, categoria_id=categoria_id)
        ).first()
        return resultado is not None

    def eliminar(self, categoria: Categoria) -> None:
        categoria.deleted_at = datetime.now(timezone.utc)
        self.sesion.add(categoria)
        self.sesion.flush()
