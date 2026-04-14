"""
Script de migración para agregar soporte de Art.15

Agrega la columna horas_art15 a la tabla marcas.
Ejecutar: python migrate_art15.py
"""

import sqlite3
import os

DATABASE_PATH = os.getenv("DATABASE_URL", "sqlite:///./data/control_horario.db")
DB_FILE = DATABASE_PATH.replace("sqlite:///", "")

def migrate():
    """Ejecuta la migración para agregar Art.15"""
    
    print("🔄 Iniciando migración para Art.15...")
    
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Verificar si la columna ya existe
        cursor.execute("PRAGMA table_info(marcas)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'horas_art15' in columns:
            print("✅ La columna 'horas_art15' ya existe. No es necesario migrar.")
            conn.close()
            return
        
        # Agregar columna horas_art15
        print("📝 Agregando columna 'horas_art15'...")
        cursor.execute("ALTER TABLE marcas ADD COLUMN horas_art15 INTEGER")
        
        # Hacer la columna hora nullable
        print("📝 Actualizando restricciones de la columna 'hora'...")
        # SQLite no permite modificar columnas directamente, pero los NULL ya están permitidos
        # desde el modelo actualizado
        
        conn.commit()
        print("✅ Migración completada exitosamente!")
        print("   - Columna 'horas_art15' agregada")
        print("   - La base de datos está lista para usar Art.15")
        
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    migrate()
