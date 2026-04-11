"""
Servicio de lógica de negocio para marcas.

Contiene toda la lógica de manipulación de datos, cálculos y 
operaciones complejas sobre las marcas horarias.
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from database.models import Marca
from schemas.marca import MarcaCreate, MarcaUpdate, MarcasPorDia
from datetime import date, datetime, time, timedelta
from typing import List, Optional


class MarcaService:
    """
    Servicio para gestionar operaciones sobre marcas horarias.
    Encapsula toda la lógica de negocio relacionada con marcas.
    """
    
    @staticmethod
    def crear_marca(db: Session, marca_data: MarcaCreate) -> Marca:
        """
        Crea una nueva marca en la base de datos.
        
        Args:
            db: Sesión de base de datos
            marca_data: Datos de la marca a crear
            
        Returns:
            Marca creada con su ID asignado
        """
        nueva_marca = Marca(
            fecha=marca_data.fecha,
            tipo=marca_data.tipo,
            hora=marca_data.hora,
            observacion=marca_data.observacion
        )
        db.add(nueva_marca)
        db.commit()
        db.refresh(nueva_marca)
        return nueva_marca
    
    @staticmethod
    def obtener_marca_por_id(db: Session, marca_id: int) -> Optional[Marca]:
        """
        Obtiene una marca por su ID.
        
        Args:
            db: Sesión de base de datos
            marca_id: ID de la marca a buscar
            
        Returns:
            Marca encontrada o None si no existe
        """
        return db.query(Marca).filter(Marca.id == marca_id).first()
    
    @staticmethod
    def obtener_todas_marcas(db: Session, limit: int = 100) -> List[Marca]:
        """
        Obtiene todas las marcas ordenadas por fecha y hora descendente.
        
        Args:
            db: Sesión de base de datos
            limit: Número máximo de registros a retornar
            
        Returns:
            Lista de marcas
        """
        return db.query(Marca)\
            .order_by(Marca.fecha.desc(), Marca.hora.desc())\
            .limit(limit)\
            .all()
    
    @staticmethod
    def obtener_marcas_por_fecha(db: Session, fecha: date) -> List[Marca]:
        """
        Obtiene todas las marcas de una fecha específica.
        
        Args:
            db: Sesión de base de datos
            fecha: Fecha a consultar
            
        Returns:
            Lista de marcas ordenadas por hora
        """
        return db.query(Marca)\
            .filter(Marca.fecha == fecha)\
            .order_by(Marca.hora)\
            .all()
    
    @staticmethod
    def obtener_marcas_rango_fechas(
        db: Session, 
        fecha_desde: date, 
        fecha_hasta: date
    ) -> List[Marca]:
        """
        Obtiene marcas en un rango de fechas.
        
        Args:
            db: Sesión de base de datos
            fecha_desde: Fecha inicial (inclusive)
            fecha_hasta: Fecha final (inclusive)
            
        Returns:
            Lista de marcas en el rango
        """
        return db.query(Marca)\
            .filter(and_(Marca.fecha >= fecha_desde, Marca.fecha <= fecha_hasta))\
            .order_by(Marca.fecha, Marca.hora)\
            .all()
    
    @staticmethod
    def actualizar_marca(
        db: Session, 
        marca_id: int, 
        marca_data: MarcaUpdate
    ) -> Optional[Marca]:
        """
        Actualiza una marca existente.
        
        Args:
            db: Sesión de base de datos
            marca_id: ID de la marca a actualizar
            marca_data: Datos a actualizar (solo campos no nulos)
            
        Returns:
            Marca actualizada o None si no existe
        """
        marca = db.query(Marca).filter(Marca.id == marca_id).first()
        
        if not marca:
            return None
        
        # Actualizar solo campos que no sean None
        update_data = marca_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(marca, field, value)
        
        marca.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(marca)
        return marca
    
    @staticmethod
    def eliminar_marca(db: Session, marca_id: int) -> bool:
        """
        Elimina una marca por su ID.
        
        Args:
            db: Sesión de base de datos
            marca_id: ID de la marca a eliminar
            
        Returns:
            True si se eliminó, False si no existía
        """
        marca = db.query(Marca).filter(Marca.id == marca_id).first()
        
        if not marca:
            return False
        
        db.delete(marca)
        db.commit()
        return True
    
    @staticmethod
    def calcular_horas_dia(marcas: List[Marca]) -> str:
        """
        Calcula las horas trabajadas en un día a partir de las marcas.
        Asume que las marcas están ordenadas cronológicamente y alterna
        entre ENTRADA y SALIDA.
        
        Args:
            marcas: Lista de marcas del día (ordenadas por hora)
            
        Returns:
            String con formato "HH:MM" representando horas trabajadas
        """
        if not marcas:
            return "00:00"
        
        total_segundos = 0
        entrada_actual = None
        
        for marca in marcas:
            if marca.tipo == "ENTRADA":
                entrada_actual = marca.hora
            elif marca.tipo == "SALIDA" and entrada_actual:
                # Convertir time a datetime para poder restar
                dt_entrada = datetime.combine(date.today(), entrada_actual)
                dt_salida = datetime.combine(date.today(), marca.hora)
                
                diferencia = dt_salida - dt_entrada
                total_segundos += diferencia.total_seconds()
                entrada_actual = None
        
        # Convertir segundos a formato HH:MM
        horas = int(total_segundos // 3600)
        minutos = int((total_segundos % 3600) // 60)
        
        return f"{horas:02d}:{minutos:02d}"
    
    @staticmethod
    def obtener_marcas_agrupadas_por_dia(
        db: Session,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None
    ) -> List[MarcasPorDia]:
        """
        Obtiene marcas agrupadas por día con cálculo de horas trabajadas.
        
        Args:
            db: Sesión de base de datos
            fecha_desde: Fecha inicial (opcional, default: hace 30 días)
            fecha_hasta: Fecha final (opcional, default: hoy)
            
        Returns:
            Lista de objetos MarcasPorDia
        """
        if not fecha_hasta:
            fecha_hasta = date.today()
        if not fecha_desde:
            fecha_desde = fecha_hasta - timedelta(days=30)
        
        marcas = MarcaService.obtener_marcas_rango_fechas(db, fecha_desde, fecha_hasta)
        
        # Agrupar por fecha
        marcas_por_fecha = {}
        for marca in marcas:
            if marca.fecha not in marcas_por_fecha:
                marcas_por_fecha[marca.fecha] = []
            marcas_por_fecha[marca.fecha].append(marca)
        
        # Crear objetos MarcasPorDia
        resultado = []
        for fecha, marcas_dia in sorted(marcas_por_fecha.items(), reverse=True):
            total_horas = MarcaService.calcular_horas_dia(marcas_dia)
            resultado.append(MarcasPorDia(
                fecha=fecha,
                marcas=marcas_dia,
                total_horas=total_horas
            ))
        
        return resultado
