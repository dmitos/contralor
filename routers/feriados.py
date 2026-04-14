"""
Router de endpoints para feriados.

Define todos los endpoints REST de la API relacionados con feriados.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from database import get_db
from schemas.feriado import FeriadoCreate, FeriadoUpdate, FeriadoResponse
from services.feriado_service import FeriadoService

router = APIRouter(
    prefix="/api/feriados",
    tags=["feriados"]
)


@router.post("/", response_model=FeriadoResponse, status_code=201)
def crear_feriado(
    feriado: FeriadoCreate,
    db: Session = Depends(get_db)
):
    """
    Crea un nuevo feriado.
    
    Args:
        feriado: Datos del feriado a crear
        db: Sesión de base de datos
        
    Returns:
        Feriado creado con su ID asignado
    """
    nuevo_feriado = FeriadoService.crear_feriado(db, feriado)
    return nuevo_feriado


@router.get("/", response_model=List[FeriadoResponse])
def listar_feriados(
    año: Optional[int] = Query(None, description="Filtrar por año"),
    db: Session = Depends(get_db)
):
    """
    Lista todos los feriados, opcionalmente filtrados por año.
    
    Args:
        año: Año para filtrar (opcional)
        db: Sesión de base de datos
        
    Returns:
        Lista de feriados
    """
    if año:
        feriados = FeriadoService.obtener_feriados_año(db, año)
    else:
        # Si no se especifica año, traer del año actual
        año_actual = date.today().year
        feriados = FeriadoService.obtener_feriados_año(db, año_actual)
    
    return feriados


@router.get("/año/{año}", response_model=List[FeriadoResponse])
def obtener_feriados_por_año(
    año: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene todos los feriados de un año específico.
    
    Args:
        año: Año a consultar
        db: Sesión de base de datos
        
    Returns:
        Lista de feriados del año
    """
    feriados = FeriadoService.obtener_feriados_año(db, año)
    return feriados


@router.get("/{feriado_id}", response_model=FeriadoResponse)
def obtener_feriado(
    feriado_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene un feriado específico por su ID.
    
    Args:
        feriado_id: ID del feriado
        db: Sesión de base de datos
        
    Returns:
        Feriado encontrado
    """
    feriado = FeriadoService.obtener_feriado_por_id(db, feriado_id)
    
    if not feriado:
        raise HTTPException(status_code=404, detail=f"Feriado con ID {feriado_id} no encontrado")
    
    return feriado


@router.put("/{feriado_id}", response_model=FeriadoResponse)
def actualizar_feriado(
    feriado_id: int,
    feriado_data: FeriadoUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualiza un feriado existente.
    
    Args:
        feriado_id: ID del feriado a actualizar
        feriado_data: Datos a actualizar
        db: Sesión de base de datos
        
    Returns:
        Feriado actualizado
    """
    feriado = FeriadoService.actualizar_feriado(db, feriado_id, feriado_data)
    
    if not feriado:
        raise HTTPException(status_code=404, detail=f"Feriado con ID {feriado_id} no encontrado")
    
    return feriado


@router.delete("/{feriado_id}", status_code=204)
def eliminar_feriado(
    feriado_id: int,
    db: Session = Depends(get_db)
):
    """
    Elimina un feriado.
    
    Args:
        feriado_id: ID del feriado a eliminar
        db: Sesión de base de datos
        
    Returns:
        204 No Content
    """
    eliminado = FeriadoService.eliminar_feriado(db, feriado_id)
    
    if not eliminado:
        raise HTTPException(status_code=404, detail=f"Feriado con ID {feriado_id} no encontrado")
    
    return None


@router.post("/precargar/{año}", response_model=dict)
def precargar_feriados_año(
    año: int,
    db: Session = Depends(get_db)
):
    """
    Precarga los feriados nacionales de Uruguay para un año específico.
    
    Args:
        año: Año para precargar feriados
        db: Sesión de base de datos
        
    Returns:
        Diccionario con la cantidad de feriados agregados
    """
    count = FeriadoService.precargar_feriados_año(db, año)
    
    return {
        "año": año,
        "feriados_agregados": count,
        "mensaje": f"Se agregaron {count} feriados para el año {año}"
    }


@router.get("/verificar/{fecha}", response_model=dict)
def verificar_si_es_feriado(
    fecha: date,
    db: Session = Depends(get_db)
):
    """
    Verifica si una fecha específica es feriado.
    
    Args:
        fecha: Fecha a verificar (formato YYYY-MM-DD)
        db: Sesión de base de datos
        
    Returns:
        Diccionario indicando si es feriado y detalles
    """
    feriado = FeriadoService.obtener_feriado_por_fecha(db, fecha)
    
    if feriado:
        return {
            "es_feriado": True,
            "nombre": feriado.nombre,
            "tipo": feriado.tipo,
            "fecha": feriado.fecha
        }
    else:
        return {
            "es_feriado": False,
            "fecha": fecha
        }
