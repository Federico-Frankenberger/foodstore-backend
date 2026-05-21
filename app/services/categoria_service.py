from typing import List, Optional

from sqlalchemy.exc import IntegrityError

from app.schemas.categoria import CategoriaNodo, CategoriaCreate, CategoriaRead, CategoriaUpdate
from app.uow.uow import UnidadDeTrabajo


def _armar_arbol(filas: list[dict]) -> list[CategoriaNodo]:
    nodos: dict[int, CategoriaNodo] = {}
    for fila in filas:
        nodos[fila["id"]] = CategoriaNodo(
            id=fila["id"],
            nombre=fila["nombre"],
            descripcion=fila.get("descripcion"),
            imagen_url=fila.get("imagen_url"),
            parent_id=fila.get("parent_id"),
        )
    raices: list[CategoriaNodo] = []
    for fila in filas:
        nodo = nodos[fila["id"]]
        pid = fila.get("parent_id")
        if pid and pid in nodos:
            nodos[pid].hijos.append(nodo)
        else:
            raices.append(nodo)
    return raices


def obtener_arbol() -> list[CategoriaNodo]:
    with UnidadDeTrabajo() as uow:
        filas = uow.categorias.get_tree()
        return _armar_arbol(filas)


def crear_categoria(datos: CategoriaCreate) -> CategoriaRead:
    try:
        with UnidadDeTrabajo() as uow:
            if datos.parent_id is not None and not uow.categorias.obtener_por_id(datos.parent_id):
                raise ValueError(f"No existe una categoría con id '{datos.parent_id}'")
            categoria = uow.categorias.crear(datos)
            return CategoriaRead.model_validate(categoria)
    except IntegrityError:
        raise ValueError(f"Ya existe una categoría con el nombre '{datos.nombre}'")


def obtener_categorias(
    skip: int = 0,
    limit: int = 10,
    nombre: Optional[str] = None,
    parent_id: Optional[int] = None,
) -> List[CategoriaRead]:
    with UnidadDeTrabajo() as uow:
        categorias = uow.categorias.obtener_todos(skip, limit, nombre, parent_id)
        return [CategoriaRead.model_validate(c) for c in categorias]


def obtener_categoria(id: int) -> Optional[CategoriaRead]:
    with UnidadDeTrabajo() as uow:
        categoria = uow.categorias.obtener_por_id(id)
        if not categoria:
            return None
        return CategoriaRead.model_validate(categoria)


def actualizar_categoria(id: int, datos: CategoriaUpdate) -> Optional[CategoriaRead]:
    with UnidadDeTrabajo() as uow:
        categoria = uow.categorias.obtener_por_id(id)
        if not categoria:
            return None
        campos = datos.model_dump(exclude_unset=True)
        if "parent_id" in campos and campos["parent_id"] is not None:
            if not uow.categorias.obtener_por_id(campos["parent_id"]):
                raise ValueError(f"No existe una categoría con id '{campos['parent_id']}'")
            if uow.categorias.would_create_cycle(id, campos["parent_id"]):
                raise ValueError("La asignación crearía un ciclo en la jerarquía")
        categoria = uow.categorias.actualizar(categoria, campos)
        return CategoriaRead.model_validate(categoria)


def eliminar_categoria(id: int) -> bool:
    with UnidadDeTrabajo() as uow:
        categoria = uow.categorias.obtener_por_id(id)
        if not categoria:
            return False
        if uow.categorias.obtener_hijos_activos(id):
            raise ValueError("No se puede eliminar: la categoría tiene subcategorías activas")
        if uow.categorias.tiene_productos_activos(id):
            raise ValueError("No se puede eliminar: la categoría tiene productos activos")
        uow.categorias.eliminar(categoria)
        return True
