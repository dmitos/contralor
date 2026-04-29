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


# Límite de horas trabajadas por día (regla de negocio)
MAX_HORAS_DIA_SEGUNDOS = 10 * 3600  # 10 horas en segundos


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
        # Convertir horas_art15 de decimal a minutos para almacenar
        horas_art15_minutos = None
        if marca_data.horas_art15 is not None:
            horas_art15_minutos = int(marca_data.horas_art15 * 60)
        
        nueva_marca = Marca(
            fecha=marca_data.fecha,
            tipo=marca_data.tipo,
            hora=marca_data.hora,
            horas_art15=horas_art15_minutos,
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
        
        Aplica la misma conversión de horas_art15 (decimal → minutos) que crear_marca,
        para mantener consistencia en el almacenamiento.
        
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
        
        # Obtener campos a actualizar (solo los que fueron enviados)
        update_data = marca_data.model_dump(exclude_unset=True)

        # FIX: convertir horas_art15 de decimal a minutos antes de persistir,
        # igual que en crear_marca. Sin esto, editar un Art.15 guardaba el valor
        # decimal directamente (ej: 1.5) en vez de minutos (90).
        if "horas_art15" in update_data and update_data["horas_art15"] is not None:
            update_data["horas_art15"] = int(update_data["horas_art15"] * 60)

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
        Incluye horas de Art.15.
        Asume que las marcas ENTRADA/SALIDA están ordenadas cronológicamente.

        El total diario está limitado a MAX_HORAS_DIA_SEGUNDOS (10 horas).
        Esto previene acumulaciones incorrectas por marcas mal cargadas.
        
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
                # Ignorar intervalos negativos (salida antes que entrada — dato corrupto)
                if diferencia.total_seconds() > 0:
                    total_segundos += diferencia.total_seconds()
                entrada_actual = None
            elif marca.tipo == "ART15" and marca.horas_art15:
                # Agregar las horas del artículo (almacenadas en minutos)
                total_segundos += marca.horas_art15 * 60

        # FIX: aplicar límite de 10 horas diarias.
        # Previene que marcas incorrectas inflen el total semanal.
        total_segundos = min(total_segundos, MAX_HORAS_DIA_SEGUNDOS)
        
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
        Considera feriados para ajustar las horas requeridas.
        
        Args:
            db: Sesión de base de datos
            fecha_referencia: Fecha de referencia (default: hoy)
            
        Returns:
            Diccionario con estadísticas de la semana incluyendo ajuste por feriados
        """
        from database.models import Feriado
        
        if not fecha_referencia:
            fecha_referencia = date.today()
        
        inicio_semana = MarcaService.obtener_inicio_semana(fecha_referencia)
        fin_semana = MarcaService.obtener_fin_semana(fecha_referencia)
        
        # Obtener marcas de la semana
        marcas = MarcaService.obtener_marcas_rango_fechas(db, inicio_semana, fin_semana)
        
        # Obtener feriados de la semana (solo lunes a viernes)
        feriados_semana = db.query(Feriado)\
            .filter(
                Feriado.fecha >= inicio_semana,
                Feriado.fecha <= fin_semana
            )\
            .all()
        
        # Filtrar solo feriados que caen en días laborables (lunes=0 a viernes=4)
        feriados_laborables = [f for f in feriados_semana if f.fecha.weekday() < 5]
        cantidad_feriados = len(feriados_laborables)
        
        # Agrupar por día y calcular horas
        marcas_por_dia = {}
        for marca in marcas:
            if marca.fecha not in marcas_por_dia:
                marcas_por_dia[marca.fecha] = []
            marcas_por_dia[marca.fecha].append(marca)
        
        # Calcular total de segundos trabajados y minutos de Art.15 en la semana
        total_segundos = 0
        dias_trabajados = 0
        art15_semana_minutos = 0

        for fecha, marcas_dia in marcas_por_dia.items():
            horas_dia = MarcaService.calcular_horas_dia(marcas_dia)
            if horas_dia != "00:00":
                dias_trabajados += 1
                partes = horas_dia.split(":")
                segundos_dia = int(partes[0]) * 3600 + int(partes[1]) * 60
                total_segundos += segundos_dia
            for marca in marcas_dia:
                if marca.tipo == "ART15" and marca.horas_art15:
                    art15_semana_minutos += marca.horas_art15  # almacenado en minutos
        
        # Convertir a horas decimales
        horas_decimales = total_segundos / 3600
        
        # Convertir a formato HH:MM
        horas = int(total_segundos // 3600)
        minutos = int((total_segundos % 3600) // 60)
        horas_str = f"{horas:02d}:{minutos:02d}"
        
        # Calcular horas requeridas ajustadas por feriados
        # Cada feriado resta 8 horas 36 minutos (516 minutos)
        horas_requeridas_base = 43.0
        minutos_por_feriado = 516  # 8h 36min
        ajuste_feriados_minutos = cantidad_feriados * minutos_por_feriado
        
        horas_requeridas_minutos = int(horas_requeridas_base * 60) - ajuste_feriados_minutos
        horas_requeridas = horas_requeridas_minutos / 60
        
        # Formato HH:MM de horas requeridas
        hrs_req = int(horas_requeridas_minutos // 60)
        min_req = int(horas_requeridas_minutos % 60)
        horas_requeridas_str = f"{hrs_req:02d}:{min_req:02d}"
        
        # Calcular diferencia con las horas requeridas ajustadas
        diferencia_decimal = horas_decimales - horas_requeridas
        diferencia_segundos = total_segundos - (horas_requeridas_minutos * 60)
        
        # Convertir diferencia a HH:MM
        signo = "+" if diferencia_segundos >= 0 else "-"
        diferencia_abs = abs(diferencia_segundos)
        diff_horas = int(diferencia_abs // 3600)
        diff_minutos = int((diferencia_abs % 3600) // 60)
        diferencia_str = f"{signo}{diff_horas:02d}:{diff_minutos:02d}"
        
        # Porcentaje completado
        porcentaje = (horas_decimales / horas_requeridas * 100) if horas_requeridas > 0 else 0
        
        # Calcular saldo Art.15 del mes
        año_ref = fecha_referencia.year
        mes_ref = fecha_referencia.month
        saldo_art15 = MarcaService.calcular_saldo_art15_mes(db, año_ref, mes_ref)
        
        return {
            'fecha_inicio': inicio_semana,
            'fecha_fin': fin_semana,
            'horas_trabajadas': horas_str,
            'horas_trabajadas_decimal': round(horas_decimales, 2),
            'horas_requeridas': horas_requeridas,
            'horas_requeridas_str': horas_requeridas_str,
            'diferencia': diferencia_str,
            'diferencia_decimal': round(diferencia_decimal, 2),
            'porcentaje_completado': round(porcentaje, 1),
            'dias_trabajados': dias_trabajados,
            'feriados': {
                'cantidad': cantidad_feriados,
                'fechas': [{'fecha': f.fecha, 'nombre': f.nombre} for f in feriados_laborables],
                'ajuste_horas': round(ajuste_feriados_minutos / 60, 2)
            },
            'art15': saldo_art15,
            'art15_semana_minutos': art15_semana_minutos
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
        
        if fecha_referencia.month == 12:
            fin_mes = fecha_referencia.replace(year=fecha_referencia.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            fin_mes = fecha_referencia.replace(month=fecha_referencia.month + 1, day=1) - timedelta(days=1)
        
        marcas = MarcaService.obtener_marcas_rango_fechas(db, inicio_mes, fin_mes)
        
        marcas_por_dia = {}
        for marca in marcas:
            if marca.fecha not in marcas_por_dia:
                marcas_por_dia[marca.fecha] = []
            marcas_por_dia[marca.fecha].append(marca)
        
        total_segundos = 0
        dias_trabajados = 0
        
        for fecha, marcas_dia in marcas_por_dia.items():
            horas_dia = MarcaService.calcular_horas_dia(marcas_dia)
            if horas_dia != "00:00":
                dias_trabajados += 1
                partes = horas_dia.split(":")
                segundos_dia = int(partes[0]) * 3600 + int(partes[1]) * 60
                total_segundos += segundos_dia
        
        horas_decimales = total_segundos / 3600
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
    
    @staticmethod
    def calcular_saldo_art15_mes(db: Session, año: int, mes: int) -> Dict:
        """
        Calcula el saldo de Art.15 para un mes específico.
        
        Args:
            db: Sesión de base de datos
            año: Año a consultar
            mes: Mes a consultar (1-12)
            
        Returns:
            Diccionario con:
            - total_horas: 4.0 (cuota mensual)
            - horas_usadas: Horas ya usadas en el mes
            - horas_disponibles: Horas restantes
            - usos: Lista de usos (fecha, horas)
        """
        primer_dia = date(año, mes, 1)
        if mes == 12:
            ultimo_dia = date(año + 1, 1, 1) - timedelta(days=1)
        else:
            ultimo_dia = date(año, mes + 1, 1) - timedelta(days=1)
        
        art15_mes = db.query(Marca)\
            .filter(
                and_(
                    Marca.tipo == "ART15",
                    Marca.fecha >= primer_dia,
                    Marca.fecha <= ultimo_dia
                )
            )\
            .order_by(Marca.fecha)\
            .all()
        
        horas_usadas = sum(marca.horas_art15 / 60 for marca in art15_mes if marca.horas_art15)
        horas_disponibles = 4.0 - horas_usadas
        
        usos = [
            {
                'id': marca.id,
                'fecha': marca.fecha,
                'horas': marca.horas_art15 / 60 if marca.horas_art15 else 0,
                'observacion': marca.observacion
            }
            for marca in art15_mes
        ]
        
        return {
            'año': año,
            'mes': mes,
            'total_horas': 4.0,
            'horas_usadas': round(horas_usadas, 1),
            'horas_disponibles': round(horas_disponibles, 1),
            'usos': usos
        }
