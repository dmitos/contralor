"""
Módulo de base de datos.
Exporta las funciones y clases principales para facilitar imports.
"""

from .connection import get_db, init_db, engine
from .models import Base, Marca, Feriado

__all__ = ["get_db", "init_db", "engine", "Base", "Marca", "Feriado"]
