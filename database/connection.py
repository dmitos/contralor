"""
Configuración de la conexión a la base de datos SQLite.

Gestiona la creación del engine, sesiones y la inicialización de tablas.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .models import Base

# URL de conexión a SQLite (archivo local)
# Usa variable de entorno si está disponible, sino usa default
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/control_horario.db")

# Crear engine de SQLAlchemy
# check_same_thread=False es necesario para SQLite con FastAPI
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False  # Cambiar a True para ver las queries SQL en consola
)

# Crear SessionLocal para manejar transacciones
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    Inicializa la base de datos creando todas las tablas definidas en models.py
    Solo crea las tablas si no existen.
    """
    Base.metadata.create_all(bind=engine)
    print("✓ Base de datos inicializada correctamente")


def get_db() -> Session:
    """
    Generador de dependencias para FastAPI.
    Proporciona una sesión de base de datos y asegura que se cierre después de usar.
    
    Yields:
        Session: Sesión de SQLAlchemy
    
    Example:
        @app.get("/marcas")
        def get_marcas(db: Session = Depends(get_db)):
            return db.query(Marca).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
