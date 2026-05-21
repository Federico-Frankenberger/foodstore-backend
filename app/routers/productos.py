from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.core.deps import requerir_rol
from app.schemas.producto import (
    DisponibilidadUpdate,
    ProductoCategoriaCreate,
    ProductoCreate,
    ProductoIngredienteCreate,
    ProductoRead,
    ProductoUpdate,
    StockDirectoUpdate,
)
from app.services import producto_service

router = APIRouter(prefix="/productos", tags=["Productos"])

IdProducto = Annotated[int, Path(gt=0, description="ID del producto")]


@router.post("/", response_model=ProductoRead, status_code=status.HTTP_201_CREATED)
def crear_producto(
    datos: ProductoCreate,
    _: Annotated[object, Depends(requerir_rol(["ADMIN"]))],
):
    try:
        return producto_service.crear_producto(datos)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/", response_model=List[ProductoRead])
def listar_productos(
    skip: Annotated[int, Query(ge=0, description="Registros a omitir")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Máximo de resultados")] = 10,
    nombre: Annotated[Optional[str], Query(description="Filtrar por nombre")] = None,
    disponible: Annotated[Optional[bool], Query(description="Filtrar por disponibilidad")] = None,
    categoria_id: Annotated[Optional[int], Query(gt=0, description="Filtrar por categoría")] = None,
):
    return producto_service.obtener_productos(skip, limit, nombre, disponible, categoria_id)


@router.get("/{id}", response_model=ProductoRead)
def detalle_producto(id: IdProducto):
    producto = producto_service.obtener_producto(id)
    if not producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado",
        )
    return producto


@router.put("/{id}", response_model=ProductoRead)
def actualizar_producto(
    id: IdProducto,
    datos: ProductoUpdate,
    _: Annotated[object, Depends(requerir_rol(["ADMIN"]))],
):
    producto = producto_service.actualizar_producto(id, datos)
    if not producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado",
        )
    return producto


@router.patch("/{id}/stock", response_model=ProductoRead)
def actualizar_stock_directo(
    id: IdProducto,
    datos: StockDirectoUpdate,
    _: Annotated[object, Depends(requerir_rol(["ADMIN", "STOCK"]))],
):
    try:
        producto = producto_service.actualizar_stock_directo(id, datos)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    if not producto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
    return producto


@router.patch("/{id}/disponibilidad", response_model=ProductoRead)
def actualizar_disponibilidad(
    id: IdProducto,
    datos: DisponibilidadUpdate,
    _: Annotated[object, Depends(requerir_rol(["ADMIN", "STOCK"]))],
):
    producto = producto_service.actualizar_disponibilidad(id, datos.disponible)
    if not producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado",
        )
    return producto


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_producto(
    id: IdProducto,
    _: Annotated[object, Depends(requerir_rol(["ADMIN"]))],
):
    encontrado = producto_service.eliminar_producto(id)
    if not encontrado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado",
        )


@router.post(
    "/{id}/categorias",
    response_model=ProductoRead,
    status_code=status.HTTP_201_CREATED,
    summary="Agregar categoría a un producto",
)
def agregar_categoria(
    id: IdProducto,
    datos: ProductoCategoriaCreate,
    _: Annotated[object, Depends(requerir_rol(["ADMIN"]))],
):
    try:
        producto = producto_service.agregar_categoria(id, datos)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    if not producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto o categoría no encontrado",
        )
    return producto


@router.delete(
    "/{id}/categorias/{cat_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Quitar categoría de un producto",
)
def quitar_categoria(
    id: IdProducto,
    cat_id: Annotated[int, Path(gt=0, description="ID de la categoría a quitar")],
    _: Annotated[object, Depends(requerir_rol(["ADMIN"]))],
):
    encontrado = producto_service.quitar_categoria(id, cat_id)
    if not encontrado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vínculo producto-categoría no encontrado",
        )


@router.post(
    "/{id}/ingredientes",
    response_model=ProductoRead,
    status_code=status.HTTP_201_CREATED,
    summary="Agregar ingrediente a un producto",
)
def agregar_ingrediente(
    id: IdProducto,
    datos: ProductoIngredienteCreate,
    _: Annotated[object, Depends(requerir_rol(["ADMIN"]))],
):
    try:
        producto = producto_service.agregar_ingrediente(id, datos)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    if not producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto o ingrediente no encontrado",
        )
    return producto


@router.delete(
    "/{id}/ingredientes/{ing_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Quitar ingrediente de un producto",
)
def quitar_ingrediente(
    id: IdProducto,
    ing_id: Annotated[int, Path(gt=0, description="ID del ingrediente a quitar")],
    _: Annotated[object, Depends(requerir_rol(["ADMIN"]))],
):
    encontrado = producto_service.quitar_ingrediente(id, ing_id)
    if not encontrado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vínculo producto-ingrediente no encontrado",
        )
