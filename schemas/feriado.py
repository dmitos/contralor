"""
Schemas Pydantic para feriados.

Define los modelos de validación para la gestión de feriados.
"""

from pydantic import BaseModel, Field, field_validator
from datetime import date, datetime
from typing import Optional


class FeriadoCreate(BaseModel):
    """
    Schema para crear un nuevo feriado.
    
    Attributes:
        nombre: Nombre del feriado
        fecha: Fecha del feriado
        tipo: FIJO o MOVIL
        se_repite_anualmente: Si se repite cada año
        observacion: Nota opcional
    """
    nombre: str = Field(..., min_length=1, max_length=200, description="Nombre del feriado")
    fecha: date = Field(..., description="Fecha del feriado")
    tipo: str = Field(..., description="Tipo: FIJO o MOVIL")
    se_repite_anualmente: bool = Field(False, description="Se repite cada año")
    observacion: Optional[str] = Field(None, max_length=500, description="Observación opcional")
    
    @field_validator('tipo')
    @classmethod
    def validar_tipo(cls, v: str) -> str:
        """Valida que el tipo sea FIJO o MOVIL"""
        v_upper = v.upper()
        if v_upper not in ['FIJO', 'MOVIL']:
            raise ValueError('El tipo debe ser FIJO o MOVIL')
        return v_upper
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "nombre": "Año Nuevo",
                    "fecha": "2026-01-01",
                    "tipo": "FIJO",
                    "se_repite_anualmente": True,
                    "observacion": "Feriado nacional"
                }
            ]
        }
    }


class FeriadoUpdate(BaseModel):
    """
    Schema para actualizar un feriado existente.
    Todos los campos son opcionales.
    """
    nombre: Optional[str] = Field(None, min_length=1, max_length=200)
    fecha: Optional[date] = None
    tipo: Optional[str] = None
    se_repite_anualmente: Optional[bool] = None
    observacion: Optional[str] = Field(None, max_length=500)
    
    @field_validator('tipo')
    @classmethod
    def validar_tipo(cls, v: Optional[str]) -> Optional[str]:
        """Valida que el tipo sea FIJO o MOVIL si se proporciona"""
        if v is not None:
            v_upper = v.upper()
            if v_upper not in ['FIJO', 'MOVIL']:
                raise ValueError('El tipo debe ser FIJO o MOVIL')
            return v_upper
        return v


class FeriadoResponse(BaseModel):
    """
    Schema de respuesta al consultar un feriado.
    """
    id: int
    nombre: str
    fecha: date
    tipo: str
    se_repite_anualmente: bool
    observacion: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "from_attributes": True
    }
