"""
Modelos de base de datos usando SQLAlchemy.

Este módulo define la estructura de las tablas en la base de datos SQLite.
"""

from sqlalchemy import Column, Integer, String, Date, Time, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Marca(Base):
    """
    Modelo para registrar las marcas de entrada/salida y artículos.
    
    Attributes:
        id: Identificador único autoincremental
        fecha: Fecha de la marca (YYYY-MM-DD)
        tipo: Tipo de marca - 'ENTRADA', 'SALIDA' o 'ART15'
        hora: Hora de la marca (HH:MM:SS) - Para Art.15 se usa para almacenar las horas
        horas_art15: Horas del artículo 15 (1.5, 2, 2.5, 3, 4) - Solo para tipo ART15
        observacion: Nota opcional sobre la marca
        created_at: Timestamp de creación del registro
        updated_at: Timestamp de última actualización
    """
    __tablename__ = "marcas"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    fecha = Column(Date, nullable=False, index=True)
    tipo = Column(String(10), nullable=False)  # 'ENTRADA', 'SALIDA' o 'ART15'
    hora = Column(Time, nullable=True)  # Nullable para Art.15
    horas_art15 = Column(Integer, nullable=True)  # Horas en minutos (90, 120, 150, 180, 240)
    observacion = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Marca(id={self.id}, fecha={self.fecha}, tipo={self.tipo}, hora={self.hora})>"


class Feriado(Base):
    """
    Modelo para registrar feriados nacionales y no laborables.
    
    Attributes:
        id: Identificador único autoincremental
        nombre: Nombre del feriado (ej: "Año Nuevo", "Navidad")
        fecha: Fecha del feriado (YYYY-MM-DD)
        tipo: Tipo de feriado - 'FIJO' o 'MOVIL'
        se_repite_anualmente: Si el feriado se repite cada año (True para fijos)
        observacion: Nota opcional
        created_at: Timestamp de creación del registro
        updated_at: Timestamp de última actualización
    """
    __tablename__ = "feriados"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(200), nullable=False)
    fecha = Column(Date, nullable=False, index=True)
    tipo = Column(String(10), nullable=False)  # 'FIJO' o 'MOVIL'
    se_repite_anualmente = Column(Boolean, default=False)
    observacion = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Feriado(id={self.id}, nombre={self.nombre}, fecha={self.fecha})>"
