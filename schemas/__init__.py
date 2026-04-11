"""
Módulo de schemas Pydantic.
Define los modelos de validación de datos.
"""

from .marca import MarcaCreate, MarcaUpdate, MarcaResponse, MarcasPorDia

__all__ = ["MarcaCreate", "MarcaUpdate", "MarcaResponse", "MarcasPorDia"]
