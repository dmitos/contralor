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
    def trasladar_feriado(fecha_original: date) -> date:
        """
        Aplica la regla de traslado uruguaya para feriados no-fijos.

        Regla oficial:
        - Lunes          → se mantiene
        - Martes–Viernes → se traslada al lunes ANTERIOR
        - Sábado–Domingo → se traslada al lunes SIGUIENTE

        Esta regla garantiza que el feriado siempre quede en un lunes,
        minimizando el impacto sobre la semana laboral.

        Args:
            fecha_original: Fecha canónica del feriado (ej: 19 de abril)

        Returns:
            Fecha efectiva del feriado (siempre un lunes)
        """
        wd = fecha_original.weekday()  # 0=lun, 1=mar, ..., 5=sab, 6=dom
        if wd == 0:
            # Ya es lunes
            return fecha_original
        elif 1 <= wd <= 4:
            # Martes a viernes → lunes anterior
            return fecha_original - timedelta(days=wd)
        else:
            # Sábado (5) o domingo (6) → lunes siguiente
            return fecha_original + timedelta(days=7 - wd)

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
        Calcula las fechas de Carnaval (48 días antes del lunes de Pascua).
        
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

        Los feriados FIJOS se guardan con su fecha canónica (no se trasladan).
        Los feriados MÓVILES trasladables se guardan con la fecha efectiva
        (resultado de aplicar la regla de traslado), ya que esa es la fecha
        que impacta en el cálculo de horas requeridas.

        Args:
            año: Año para generar los feriados
            
        Returns:
            Lista de diccionarios con los feriados listos para persistir
        """
        feriados = []
        
        # ── Feriados FIJOS ────────────────────────────────────────────────────
        # Se repiten cada año en la misma fecha. No se trasladan.
        feriados_fijos = [
            {"nombre": "Año Nuevo",               "mes": 1,  "dia": 1},
            {"nombre": "Día de los Trabajadores", "mes": 5,  "dia": 1},
            {"nombre": "Día de la Independencia", "mes": 8,  "dia": 25},
            {"nombre": "Día de Navidad",          "mes": 12, "dia": 25},
        ]
        
        for f in feriados_fijos:
            feriados.append({
                "nombre": f["nombre"],
                "fecha": date(año, f["mes"], f["dia"]),
                "tipo": "FIJO",
                "se_repite_anualmente": True,
                "observacion": "Feriado nacional"
            })
        
        # ── Carnaval (MÓVIL, calculado) ───────────────────────────────────────
        # Carnaval no se traslada; siempre cae en lunes y martes.
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
        
        # ── Semana de Turismo / Semana Santa (MÓVIL, calculado) ───────────────
        # Jueves y Viernes Santo no se trasladan; son días fijos de la semana.
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
        
        # ── Feriados MÓVILES trasladables ─────────────────────────────────────
        # Se guardan con la fecha efectiva (lunes resultante del traslado).
        # La observación registra la fecha canónica para trazabilidad.
        feriados_trasladables = [
            {
                "nombre": "Desembarco de los 33 Orientales",
                "fecha_canonica": date(año, 4, 19),
            },
            {
                "nombre": "Batalla de Las Piedras",
                "fecha_canonica": date(año, 5, 18),
            },
            {
                "nombre": "Natalicio de Artigas",
                "fecha_canonica": date(año, 6, 19),
            },
            {
                "nombre": "Día de la Raza",
                "fecha_canonica": date(año, 10, 12),
            },
            {
                "nombre": "Día de los Difuntos",
                "fecha_canonica": date(año, 11, 2),
            },
        ]
        
        for f in feriados_trasladables:
            fecha_canonica = f["fecha_canonica"]
            fecha_efectiva = FeriadoService.trasladar_feriado(fecha_canonica)
            feriados.append({
                "nombre": f["nombre"],
                "fecha": fecha_efectiva,
                "tipo": "MOVIL",
                "se_repite_anualmente": False,
                "observacion": f"Fecha canónica: {fecha_canonica.strftime('%d/%m')} — trasladado al lunes"
            })
        
        return sorted(feriados, key=lambda x: x['fecha'])
    
    @staticmethod
    def precargar_feriados_año(db: Session, año: int) -> int:
        """
        Precarga los feriados de Uruguay para un año específico.
        No duplica feriados ya existentes (verifica por fecha + nombre).
        
        Args:
            db: Sesión de base de datos
            año: Año para precargar
            
        Returns:
            Cantidad de feriados nuevos agregados
        """
        feriados_predefinidos = FeriadoService.obtener_feriados_predefinidos_uruguay(año)
        
        count = 0
        for f_data in feriados_predefinidos:
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
