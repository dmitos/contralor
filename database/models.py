"""
Modelos de base de datos usando SQLAlchemy.

Este módulo define la estructura de las tablas en la base de datos SQLite.
"""

from sqlalchemy import Column, Integer, String, Date, Time, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Marca(Base):
    """
    Modelo para registrar las marcas de entrada/salida.
    
    Attributes:
        id: Identificador único autoincremental
        fecha: Fecha de la marca (YYYY-MM-DD)
        tipo: Tipo de marca - 'ENTRADA' o 'SALIDA'
        hora: Hora de la marca (HH:MM:SS)
        observacion: Nota opcional sobre la marca
        created_at: Timestamp de creación del registro
        updated_at: Timestamp de última actualización
    """
    __tablename__ = "marcas"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    fecha = Column(Date, nullable=False, index=True)
    tipo = Column(String(10), nullable=False)  # 'ENTRADA' o 'SALIDA'
    hora = Column(Time, nullable=False)
    observacion = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Marca(id={self.id}, fecha={self.fecha}, tipo={self.tipo}, hora={self.hora})>"
