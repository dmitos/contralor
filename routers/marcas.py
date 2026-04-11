"""
Router de endpoints para marcas horarias.

Define todos los endpoints REST de la API relacionados con marcas:
- POST /api/marcas - Crear marca
- GET /api/marcas - Listar marcas
- GET /api/marcas/{id} - Obtener marca específica
- PUT /api/marcas/{id} - Actualizar marca
- DELETE /api/marcas/{id} - Eliminar marca
- GET /api/marcas/fecha/{fecha} - Marcas de una fecha
- GET /api/marcas/agrupadas - Marcas agrupadas por día
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from database import get_db
from schemas.marca import MarcaCreate, MarcaUpdate, MarcaResponse, MarcasPorDia
from services.marca_service import MarcaService

router = APIRouter(
    prefix="/api/marcas",
    tags=["marcas"]
)


@router.post("/", response_model=MarcaResponse, status_code=201)
def crear_marca(
    marca: MarcaCreate,
    db: Session = Depends(get_db)
):
    """
    Crea una nueva marca horaria.
    
    Args:
        marca: Datos de la marca a crear
        db: Sesión de base de datos (inyectada)
        
    Returns:
        Marca creada con su ID asignado
        
    Example request body:
        {
            "fecha": "2026-04-10",
            "tipo": "ENTRADA",
            "hora": "08:30:00",
            "observacion": "Llegada normal"
        }
    """
    nueva_marca = MarcaService.crear_marca(db, marca)
    return nueva_marca


@router.get("/", response_model=List[MarcaResponse])
def listar_marcas(
    limit: int = Query(100, ge=1, le=1000, description="Límite de registros"),
    db: Session = Depends(get_db)
):
    """
    Lista todas las marcas (ordenadas por fecha/hora desc).
    
    Args:
        limit: Número máximo de registros a retornar (default: 100)
        db: Sesión de base de datos (inyectada)
        
    Returns:
        Lista de marcas
    """
    marcas = MarcaService.obtener_todas_marcas(db, limit)
    return marcas


@router.get("/agrupadas", response_model=List[MarcasPorDia])
def listar_marcas_agrupadas(
    fecha_desde: Optional[date] = Query(None, description="Fecha inicial (YYYY-MM-DD)"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha final (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Lista marcas agrupadas por día con cálculo de horas trabajadas.
    Si no se especifican fechas, retorna los últimos 30 días.
    
    Args:
        fecha_desde: Fecha inicial del rango (opcional)
        fecha_hasta: Fecha final del rango (opcional)
        db: Sesión de base de datos (inyectada)
        
    Returns:
        Lista de objetos con fecha, marcas del día y total de horas
    """
    marcas_agrupadas = MarcaService.obtener_marcas_agrupadas_por_dia(
        db, fecha_desde, fecha_hasta
    )
    return marcas_agrupadas


@router.get("/fecha/{fecha}", response_model=List[MarcaResponse])
def obtener_marcas_por_fecha(
    fecha: date,
    db: Session = Depends(get_db)
):
    """
    Obtiene todas las marcas de una fecha específica.
    
    Args:
        fecha: Fecha en formato YYYY-MM-DD
        db: Sesión de base de datos (inyectada)
        
    Returns:
        Lista de marcas del día (ordenadas por hora)
    """
    marcas = MarcaService.obtener_marcas_por_fecha(db, fecha)
    return marcas


@router.get("/{marca_id}", response_model=MarcaResponse)
def obtener_marca(
    marca_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene una marca específica por su ID.
    
    Args:
        marca_id: ID de la marca
        db: Sesión de base de datos (inyectada)
        
    Returns:
        Marca encontrada
        
    Raises:
        HTTPException 404: Si la marca no existe
    """
    marca = MarcaService.obtener_marca_por_id(db, marca_id)
    
    if not marca:
        raise HTTPException(status_code=404, detail=f"Marca con ID {marca_id} no encontrada")
    
    return marca


@router.put("/{marca_id}", response_model=MarcaResponse)
def actualizar_marca(
    marca_id: int,
    marca_data: MarcaUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualiza una marca existente.
    Solo se actualizan los campos proporcionados (no nulos).
    
    Args:
        marca_id: ID de la marca a actualizar
        marca_data: Datos a actualizar
        db: Sesión de base de datos (inyectada)
        
    Returns:
        Marca actualizada
        
    Raises:
        HTTPException 404: Si la marca no existe
    """
    marca = MarcaService.actualizar_marca(db, marca_id, marca_data)
    
    if not marca:
        raise HTTPException(status_code=404, detail=f"Marca con ID {marca_id} no encontrada")
    
    return marca


@router.delete("/{marca_id}", status_code=204)
def eliminar_marca(
    marca_id: int,
    db: Session = Depends(get_db)
):
    """
    Elimina una marca por su ID.
    
    Args:
        marca_id: ID de la marca a eliminar
        db: Sesión de base de datos (inyectada)
        
    Returns:
        No retorna contenido (204 No Content)
        
    Raises:
        HTTPException 404: Si la marca no existe
    """
    eliminada = MarcaService.eliminar_marca(db, marca_id)
    
    if not eliminada:
        raise HTTPException(status_code=404, detail=f"Marca con ID {marca_id} no encontrada")
    
    return None
