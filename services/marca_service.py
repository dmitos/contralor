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
from typing import List, Optional, Dict, Tuple


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
    
    @staticmethod
    def obtener_inicio_semana(fecha: date) -> date:
        """
        Obtiene el lunes de la semana de la fecha dada.
        
        Args:
            fecha: Fecha de referencia
            
        Returns:
            Fecha del lunes de esa semana
        """
        # weekday(): Lunes=0, Domingo=6
        dias_desde_lunes = fecha.weekday()
        inicio_semana = fecha - timedelta(days=dias_desde_lunes)
        return inicio_semana
    
    @staticmethod
    def obtener_fin_semana(fecha: date) -> date:
        """
        Obtiene el domingo de la semana de la fecha dada.
        
        Args:
            fecha: Fecha de referencia
            
        Returns:
            Fecha del domingo de esa semana
        """
        inicio = MarcaService.obtener_inicio_semana(fecha)
        fin_semana = inicio + timedelta(days=6)
        return fin_semana
    
    @staticmethod
    def calcular_horas_semana(db: Session, fecha_referencia: Optional[date] = None) -> Dict:
        """
        Calcula las horas trabajadas en la semana de la fecha de referencia.
        
        Args:
            db: Sesión de base de datos
            fecha_referencia: Fecha de referencia (default: hoy)
            
        Returns:
            Diccionario con estadísticas de la semana:
            {
                'fecha_inicio': fecha del lunes,
                'fecha_fin': fecha del domingo,
                'horas_trabajadas': "HH:MM",
                'horas_trabajadas_decimal': float,
                'horas_requeridas': 43.0,
                'diferencia': "HH:MM" (positivo o negativo),
                'diferencia_decimal': float,
                'porcentaje_completado': float,
                'dias_trabajados': int
            }
        """
        if not fecha_referencia:
            fecha_referencia = date.today()
        
        inicio_semana = MarcaService.obtener_inicio_semana(fecha_referencia)
        fin_semana = MarcaService.obtener_fin_semana(fecha_referencia)
        
        # Obtener marcas de la semana
        marcas = MarcaService.obtener_marcas_rango_fechas(db, inicio_semana, fin_semana)
        
        # Agrupar por día y calcular horas
        marcas_por_dia = {}
        for marca in marcas:
            if marca.fecha not in marcas_por_dia:
                marcas_por_dia[marca.fecha] = []
            marcas_por_dia[marca.fecha].append(marca)
        
        # Calcular total de segundos trabajados
        total_segundos = 0
        dias_trabajados = 0
        
        for fecha, marcas_dia in marcas_por_dia.items():
            horas_dia = MarcaService.calcular_horas_dia(marcas_dia)
            if horas_dia != "00:00":
                dias_trabajados += 1
                # Convertir HH:MM a segundos
                partes = horas_dia.split(":")
                segundos_dia = int(partes[0]) * 3600 + int(partes[1]) * 60
                total_segundos += segundos_dia
        
        # Convertir a horas decimales
        horas_decimales = total_segundos / 3600
        
        # Convertir a formato HH:MM
        horas = int(total_segundos // 3600)
        minutos = int((total_segundos % 3600) // 60)
        horas_str = f"{horas:02d}:{minutos:02d}"
        
        # Calcular diferencia con las 43 horas requeridas
        horas_requeridas = 43.0
        diferencia_decimal = horas_decimales - horas_requeridas
        diferencia_segundos = total_segundos - (int(horas_requeridas * 3600))
        
        # Convertir diferencia a HH:MM
        signo = "+" if diferencia_segundos >= 0 else "-"
        diferencia_abs = abs(diferencia_segundos)
        diff_horas = int(diferencia_abs // 3600)
        diff_minutos = int((diferencia_abs % 3600) // 60)
        diferencia_str = f"{signo}{diff_horas:02d}:{diff_minutos:02d}"
        
        # Porcentaje completado
        porcentaje = (horas_decimales / horas_requeridas * 100) if horas_requeridas > 0 else 0
        
        return {
            'fecha_inicio': inicio_semana,
            'fecha_fin': fin_semana,
            'horas_trabajadas': horas_str,
            'horas_trabajadas_decimal': round(horas_decimales, 2),
            'horas_requeridas': horas_requeridas,
            'diferencia': diferencia_str,
            'diferencia_decimal': round(diferencia_decimal, 2),
            'porcentaje_completado': round(porcentaje, 1),
            'dias_trabajados': dias_trabajados
        }
    
    @staticmethod
    def calcular_horas_mes(db: Session, fecha_referencia: Optional[date] = None) -> Dict:
        """
        Calcula las horas trabajadas en el mes de la fecha de referencia.
        
        Args:
            db: Sesión de base de datos
            fecha_referencia: Fecha de referencia (default: hoy)
            
        Returns:
            Diccionario con estadísticas del mes
        """
        if not fecha_referencia:
            fecha_referencia = date.today()
        
        # Primer y último día del mes
        inicio_mes = fecha_referencia.replace(day=1)
        
        # Calcular último día del mes
        if fecha_referencia.month == 12:
            fin_mes = fecha_referencia.replace(year=fecha_referencia.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            fin_mes = fecha_referencia.replace(month=fecha_referencia.month + 1, day=1) - timedelta(days=1)
        
        # Obtener marcas del mes
        marcas = MarcaService.obtener_marcas_rango_fechas(db, inicio_mes, fin_mes)
        
        # Agrupar por día y calcular horas
        marcas_por_dia = {}
        for marca in marcas:
            if marca.fecha not in marcas_por_dia:
                marcas_por_dia[marca.fecha] = []
            marcas_por_dia[marca.fecha].append(marca)
        
        # Calcular total de segundos trabajados
        total_segundos = 0
        dias_trabajados = 0
        
        for fecha, marcas_dia in marcas_por_dia.items():
            horas_dia = MarcaService.calcular_horas_dia(marcas_dia)
            if horas_dia != "00:00":
                dias_trabajados += 1
                partes = horas_dia.split(":")
                segundos_dia = int(partes[0]) * 3600 + int(partes[1]) * 60
                total_segundos += segundos_dia
        
        # Convertir a horas decimales
        horas_decimales = total_segundos / 3600
        
        # Convertir a formato HH:MM
        horas = int(total_segundos // 3600)
        minutos = int((total_segundos % 3600) // 60)
        horas_str = f"{horas:02d}:{minutos:02d}"
        
        return {
            'mes': fecha_referencia.month,
            'año': fecha_referencia.year,
            'fecha_inicio': inicio_mes,
            'fecha_fin': fin_mes,
            'horas_trabajadas': horas_str,
            'horas_trabajadas_decimal': round(horas_decimales, 2),
            'dias_trabajados': dias_trabajados,
            'promedio_diario': round(horas_decimales / dias_trabajados, 2) if dias_trabajados > 0 else 0
        }

