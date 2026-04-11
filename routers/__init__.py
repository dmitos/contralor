"""
Módulo de routers.
Contiene los endpoints de la API REST.
"""

from .marcas import router as marcas_router

__all__ = ["marcas_router"]
