"""
Módulo de schemas Pydantic.
Define los modelos de validación de datos.
"""

from .marca import MarcaCreate, MarcaUpdate, MarcaResponse, MarcasPorDia
from .feriado import FeriadoCreate, FeriadoUpdate, FeriadoResponse

__all__ = [
    "MarcaCreate", "MarcaUpdate", "MarcaResponse", "MarcasPorDia",
    "FeriadoCreate", "FeriadoUpdate", "FeriadoResponse"
]
