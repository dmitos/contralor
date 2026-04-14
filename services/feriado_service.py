"""
Servicio de lógica de negocio para feriados.

Incluye precarga de feriados nacionales de Uruguay y cálculo de feriados móviles.
"""

from sqlalchemy.orm import Session
from database.models import Feriado
from schemas.feriado import FeriadoCreate, FeriadoUpdate
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict


class FeriadoService:
    """
    Servicio para gestionar feriados y calcular feriados móviles.
    """
    
    @staticmethod
    def calcular_semana_santa(año: int) -> Dict[str, date]:
        """
        Calcula las fechas de Semana Santa usando el algoritmo de Meeus/Jones/Butcher.
        
        Args:
            año: Año para calcular
            
        Returns:
            Diccionario con fechas de Jueves Santo, Viernes Santo, etc.
        """
        a = año % 19
        b = año // 100
        c = año % 100
        d = b // 4
        e = b % 4
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19 * a + b - d - g + 15) % 30
        i = c // 4
        k = c % 4
        l = (32 + 2 * e + 2 * i - h - k) % 7
        m = (a + 11 * h + 22 * l) // 451
        mes = (h + l - 7 * m + 114) // 31
        dia = ((h + l - 7 * m + 114) % 31) + 1
        
        domingo_pascua = date(año, mes, dia)
        
        return {
            'jueves_santo': domingo_pascua - timedelta(days=3),
            'viernes_santo': domingo_pascua - timedelta(days=2),
            'sabado_santo': domingo_pascua - timedelta(days=1),
            'domingo_pascua': domingo_pascua
        }
    
    @staticmethod
    def calcular_carnaval(año: int) -> Dict[str, date]:
        """
        Calcula las fechas de Carnaval (47 días antes de Pascua).
        
        Args:
            año: Año para calcular
            
        Returns:
            Diccionario con fechas de Carnaval
        """
        semana_santa = FeriadoService.calcular_semana_santa(año)
        lunes_carnaval = semana_santa['domingo_pascua'] - timedelta(days=48)
        martes_carnaval = lunes_carnaval + timedelta(days=1)
        
        return {
            'lunes_carnaval': lunes_carnaval,
            'martes_carnaval': martes_carnaval
        }
    
    @staticmethod
    def obtener_feriados_predefinidos_uruguay(año: int) -> List[Dict]:
        """
        Retorna la lista de feriados nacionales de Uruguay para un año específico.
        
        Args:
            año: Año para generar los feriados
            
        Returns:
            Lista de diccionarios con los feriados
        """
        feriados = []
        
        # Feriados FIJOS que se repiten anualmente
        feriados_fijos = [
            {"nombre": "Año Nuevo", "mes": 1, "dia": 1},
            {"nombre": "Día de los Trabajadores", "mes": 5, "dia": 1},
            {"nombre": "Día de la Independencia", "mes": 8, "dia": 25},
            {"nombre": "Día de Navidad", "mes": 12, "dia": 25},
        ]
        
        for f in feriados_fijos:
            feriados.append({
                "nombre": f["nombre"],
                "fecha": date(año, f["mes"], f["dia"]),
                "tipo": "FIJO",
                "se_repite_anualmente": True,
                "observacion": "Feriado nacional"
            })
        
        # Feriados MÓVILES - Carnaval
        carnaval = FeriadoService.calcular_carnaval(año)
        feriados.append({
            "nombre": "Lunes de Carnaval",
            "fecha": carnaval['lunes_carnaval'],
            "tipo": "MOVIL",
            "se_repite_anualmente": False,
            "observacion": "Calculado automáticamente"
        })
        feriados.append({
            "nombre": "Martes de Carnaval",
            "fecha": carnaval['martes_carnaval'],
            "tipo": "MOVIL",
            "se_repite_anualmente": False,
            "observacion": "Calculado automáticamente"
        })
        
        # Feriados MÓVILES - Semana Santa
        semana_santa = FeriadoService.calcular_semana_santa(año)
        feriados.append({
            "nombre": "Jueves Santo",
            "fecha": semana_santa['jueves_santo'],
            "tipo": "MOVIL",
            "se_repite_anualmente": False,
            "observacion": "Calculado automáticamente"
        })
        feriados.append({
            "nombre": "Viernes Santo",
            "fecha": semana_santa['viernes_santo'],
            "tipo": "MOVIL",
            "se_repite_anualmente": False,
            "observacion": "Calculado automáticamente"
        })
        
        # Feriados MÓVILES - Fechas trasladables
        # Batalla de Las Piedras (18 de mayo) → lunes siguiente si cae en semana
        batalla_piedras = date(año, 5, 18)
        if batalla_piedras.weekday() < 5:  # Si es lunes a viernes
            fecha_batalla = batalla_piedras
        else:
            # Trasladar al lunes siguiente
            dias_hasta_lunes = (7 - batalla_piedras.weekday()) % 7
            if dias_hasta_lunes == 0:
                dias_hasta_lunes = 1
            fecha_batalla = batalla_piedras + timedelta(days=dias_hasta_lunes)
        
        feriados.append({
            "nombre": "Batalla de Las Piedras",
            "fecha": fecha_batalla,
            "tipo": "MOVIL",
            "se_repite_anualmente": False,
            "observacion": "Trasladable al lunes"
        })
        
        # Desembarco de los 33 Orientales (19 de abril)
        desembarco = date(año, 4, 19)
        if desembarco.weekday() < 5:
            fecha_desembarco = desembarco
        else:
            dias_hasta_lunes = (7 - desembarco.weekday()) % 7
            if dias_hasta_lunes == 0:
                dias_hasta_lunes = 1
            fecha_desembarco = desembarco + timedelta(days=dias_hasta_lunes)
        
        feriados.append({
            "nombre": "Desembarco de los 33 Orientales",
            "fecha": fecha_desembarco,
            "tipo": "MOVIL",
            "se_repite_anualmente": False,
            "observacion": "Trasladable al lunes"
        })
        
        # Natalicio de Artigas (19 de junio)
        artigas = date(año, 6, 19)
        if artigas.weekday() < 5:
            fecha_artigas = artigas
        else:
            dias_hasta_lunes = (7 - artigas.weekday()) % 7
            if dias_hasta_lunes == 0:
                dias_hasta_lunes = 1
            fecha_artigas = artigas + timedelta(days=dias_hasta_lunes)
        
        feriados.append({
            "nombre": "Natalicio de Artigas",
            "fecha": fecha_artigas,
            "tipo": "MOVIL",
            "se_repite_anualmente": False,
            "observacion": "Trasladable al lunes"
        })
        
        # Día de la Raza (12 de octubre)
        dia_raza = date(año, 10, 12)
        if dia_raza.weekday() < 5:
            fecha_raza = dia_raza
        else:
            dias_hasta_lunes = (7 - dia_raza.weekday()) % 7
            if dias_hasta_lunes == 0:
                dias_hasta_lunes = 1
            fecha_raza = dia_raza + timedelta(days=dias_hasta_lunes)
        
        feriados.append({
            "nombre": "Día de la Raza",
            "fecha": fecha_raza,
            "tipo": "MOVIL",
            "se_repite_anualmente": False,
            "observacion": "Trasladable al lunes"
        })
        
        # Día de los Difuntos (2 de noviembre)
        difuntos = date(año, 11, 2)
        if difuntos.weekday() < 5:
            fecha_difuntos = difuntos
        else:
            dias_hasta_lunes = (7 - difuntos.weekday()) % 7
            if dias_hasta_lunes == 0:
                dias_hasta_lunes = 1
            fecha_difuntos = difuntos + timedelta(days=dias_hasta_lunes)
        
        feriados.append({
            "nombre": "Día de los Difuntos",
            "fecha": fecha_difuntos,
            "tipo": "MOVIL",
            "se_repite_anualmente": False,
            "observacion": "Trasladable al lunes"
        })
        
        return sorted(feriados, key=lambda x: x['fecha'])
    
    @staticmethod
    def precargar_feriados_año(db: Session, año: int) -> int:
        """
        Precarga los feriados de Uruguay para un año específico.
        
        Args:
            db: Sesión de base de datos
            año: Año para precargar
            
        Returns:
            Cantidad de feriados agregados
        """
        feriados_predefinidos = FeriadoService.obtener_feriados_predefinidos_uruguay(año)
        
        count = 0
        for f_data in feriados_predefinidos:
            # Verificar si ya existe
            existe = db.query(Feriado).filter(
                Feriado.fecha == f_data['fecha'],
                Feriado.nombre == f_data['nombre']
            ).first()
            
            if not existe:
                feriado = Feriado(**f_data)
                db.add(feriado)
                count += 1
        
        db.commit()
        return count
    
    @staticmethod
    def crear_feriado(db: Session, feriado_data: FeriadoCreate) -> Feriado:
        """Crea un nuevo feriado."""
        nuevo_feriado = Feriado(
            nombre=feriado_data.nombre,
            fecha=feriado_data.fecha,
            tipo=feriado_data.tipo,
            se_repite_anualmente=feriado_data.se_repite_anualmente,
            observacion=feriado_data.observacion
        )
        db.add(nuevo_feriado)
        db.commit()
        db.refresh(nuevo_feriado)
        return nuevo_feriado
    
    @staticmethod
    def obtener_feriado_por_id(db: Session, feriado_id: int) -> Optional[Feriado]:
        """Obtiene un feriado por su ID."""
        return db.query(Feriado).filter(Feriado.id == feriado_id).first()
    
    @staticmethod
    def obtener_feriados_año(db: Session, año: int) -> List[Feriado]:
        """Obtiene todos los feriados de un año específico."""
        inicio = date(año, 1, 1)
        fin = date(año, 12, 31)
        return db.query(Feriado)\
            .filter(Feriado.fecha >= inicio, Feriado.fecha <= fin)\
            .order_by(Feriado.fecha)\
            .all()
    
    @staticmethod
    def obtener_feriado_por_fecha(db: Session, fecha: date) -> Optional[Feriado]:
        """Verifica si una fecha es feriado."""
        return db.query(Feriado).filter(Feriado.fecha == fecha).first()
    
    @staticmethod
    def actualizar_feriado(db: Session, feriado_id: int, feriado_data: FeriadoUpdate) -> Optional[Feriado]:
        """Actualiza un feriado existente."""
        feriado = db.query(Feriado).filter(Feriado.id == feriado_id).first()
        
        if not feriado:
            return None
        
        update_data = feriado_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(feriado, field, value)
        
        feriado.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(feriado)
        return feriado
    
    @staticmethod
    def eliminar_feriado(db: Session, feriado_id: int) -> bool:
        """Elimina un feriado."""
        feriado = db.query(Feriado).filter(Feriado.id == feriado_id).first()
        
        if not feriado:
            return False
        
        db.delete(feriado)
        db.commit()
        return True
