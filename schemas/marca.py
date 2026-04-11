"""
Schemas Pydantic para validación de datos.

Define los modelos de entrada y salida de la API, asegurando
que los datos recibidos y enviados cumplan con el formato esperado.
"""

from pydantic import BaseModel, Field, field_validator
from datetime import date, time, datetime
from typing import Optional


class MarcaCreate(BaseModel):
    """
    Schema para crear una nueva marca.
    Validación de datos de entrada cuando se registra una marca.
    
    Attributes:
        fecha: Fecha de la marca (formato YYYY-MM-DD)
        tipo: Tipo de marca, debe ser 'ENTRADA' o 'SALIDA'
        hora: Hora de la marca (formato HH:MM o HH:MM:SS)
        observacion: Nota opcional (máximo 500 caracteres)
    """
    fecha: date = Field(..., description="Fecha de la marca")
    tipo: str = Field(..., description="Tipo: ENTRADA o SALIDA")
    hora: time = Field(..., description="Hora de la marca")
    observacion: Optional[str] = Field(None, max_length=500, description="Observación opcional")
    
    @field_validator('tipo')
    @classmethod
    def validar_tipo(cls, v: str) -> str:
        """Valida que el tipo sea ENTRADA o SALIDA (case insensitive)"""
        v_upper = v.upper()
        if v_upper not in ['ENTRADA', 'SALIDA']:
            raise ValueError('El tipo debe ser ENTRADA o SALIDA')
        return v_upper
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "fecha": "2026-04-10",
                    "tipo": "ENTRADA",
                    "hora": "08:30:00",
                    "observacion": "Llegada normal"
                }
            ]
        }
    }


class MarcaUpdate(BaseModel):
    """
    Schema para actualizar una marca existente.
    Todos los campos son opcionales.
    
    Attributes:
        fecha: Nueva fecha (opcional)
        tipo: Nuevo tipo (opcional)
        hora: Nueva hora (opcional)
        observacion: Nueva observación (opcional)
    """
    fecha: Optional[date] = None
    tipo: Optional[str] = None
    hora: Optional[time] = None
    observacion: Optional[str] = Field(None, max_length=500)
    
    @field_validator('tipo')
    @classmethod
    def validar_tipo(cls, v: Optional[str]) -> Optional[str]:
        """Valida que el tipo sea ENTRADA o SALIDA si se proporciona"""
        if v is not None:
            v_upper = v.upper()
            if v_upper not in ['ENTRADA', 'SALIDA']:
                raise ValueError('El tipo debe ser ENTRADA o SALIDA')
            return v_upper
        return v


class MarcaResponse(BaseModel):
    """
    Schema de respuesta al consultar una marca.
    Incluye todos los campos del modelo, incluyendo ID y timestamps.
    
    Attributes:
        id: Identificador único
        fecha: Fecha de la marca
        tipo: ENTRADA o SALIDA
        hora: Hora de la marca
        observacion: Observación (puede ser None)
        created_at: Fecha y hora de creación del registro
        updated_at: Fecha y hora de última actualización
    """
    id: int
    fecha: date
    tipo: str
    hora: time
    observacion: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "from_attributes": True  # Permite crear desde objetos SQLAlchemy
    }


class MarcasPorDia(BaseModel):
    """
    Schema para agrupar marcas por día.
    Útil para mostrar un resumen diario.
    
    Attributes:
        fecha: Fecha del día
        marcas: Lista de marcas de ese día
        total_horas: Horas trabajadas ese día (calculado)
    """
    fecha: date
    marcas: list[MarcaResponse]
    total_horas: Optional[str] = None  # Formato "HH:MM"
