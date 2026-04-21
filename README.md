# Control Horario UdelaR

Sistema de registro y control de marcas horarias (entradas y salidas) desarrollado con FastAPI y SQLite.

## Características

- Registro de marcas de entrada, salida y Art. 15
- Soporte para cualquier fecha (presente, pasado)
- Edición y eliminación de marcas
- Visualización del historial paginado por semana
- Navegación semana a semana con flechas, selector de fecha y botón "Hoy"
- Proyección de hora de salida: salida estándar y salida para cubrir las horas semanales
- Estadísticas semanales: horas trabajadas, requeridas, diferencia, días trabajados y saldo de Art. 15
- Gestión de feriados nacionales de Uruguay con precarga automática y ajuste de horas requeridas
- Base de datos SQLite con persistencia local
- Interfaz web responsive optimizada para móvil

## Instalación y ejecución

### Docker (recomendado)

```bash
docker-compose up -d
```

Acceso: http://localhost:8200

Ver [DOCKER.md](DOCKER.md) para guía completa de deployment.

### Desarrollo local con UV

```bash
uv sync
uv run uvicorn main:app --reload
```

Acceso: http://localhost:8000

### Con pip

```bash
pip install -r requirements.txt
python main.py
```

## URLs

| URL | Descripción |
|-----|-------------|
| `/` | Interfaz web |
| `/api/docs` | Documentación Swagger |
| `/api/redoc` | Documentación ReDoc |
| `/health` | Health check |

## API Endpoints

### Marcas (`/api/marcas`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/marcas` | Crear marca |
| GET | `/api/marcas` | Listar marcas |
| GET | `/api/marcas/{id}` | Obtener marca |
| PUT | `/api/marcas/{id}` | Actualizar marca |
| DELETE | `/api/marcas/{id}` | Eliminar marca |
| GET | `/api/marcas/fecha/{fecha}` | Marcas de una fecha |
| GET | `/api/marcas/agrupadas` | Marcas agrupadas por día (acepta `fecha_desde` y `fecha_hasta`) |
| GET | `/api/marcas/estadisticas/semana` | Estadísticas semanales (acepta `fecha`) |
| GET | `/api/marcas/estadisticas/mes` | Estadísticas mensuales (acepta `fecha`) |
| GET | `/api/marcas/art15/saldo/{año}/{mes}` | Saldo de Art. 15 del mes |

### Feriados (`/api/feriados`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/feriados` | Crear feriado |
| GET | `/api/feriados` | Listar feriados del año actual |
| GET | `/api/feriados/año/{año}` | Feriados de un año |
| GET | `/api/feriados/{id}` | Obtener feriado |
| PUT | `/api/feriados/{id}` | Actualizar feriado |
| DELETE | `/api/feriados/{id}` | Eliminar feriado |
| POST | `/api/feriados/precargar/{año}` | Precargar feriados de Uruguay para un año |
| GET | `/api/feriados/verificar/{fecha}` | Verificar si una fecha es feriado |

## Modelo de datos

### Tabla `marcas`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | Integer | ID único (autoincremental) |
| fecha | Date | Fecha de la marca |
| tipo | String | `ENTRADA`, `SALIDA` o `ART15` |
| hora | Time | Hora de la marca (nullable para ART15) |
| horas_art15 | Integer | Horas del Art. 15 en **minutos** (ej: 90 = 1.5 h) |
| observacion | String | Nota opcional (máx. 500 chars) |
| created_at | DateTime | Fecha de creación |
| updated_at | DateTime | Fecha de última actualización |

### Tabla `feriados`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | Integer | ID único (autoincremental) |
| nombre | String | Nombre del feriado |
| fecha | Date | Fecha efectiva del feriado |
| tipo | String | `FIJO` o `MOVIL` |
| se_repite_anualmente | Boolean | True para feriados fijos |
| observacion | String | Nota opcional |

## Reglas de negocio

- **Horas semanales requeridas:** 43 horas (lunes a domingo)
- **Ajuste por feriado:** se descuentan 8 h 36 min (516 min) por cada feriado que caiga en día laborable (lun–vie)
- **Tope diario:** 10 horas máximo por día en el cálculo de totales
- **Art. 15:** cuota mensual de 4 horas; los valores válidos al registrar son 1, 1.5, 2, 2.5, 3 y 4 horas
- **Feriados móviles trasladables:** se guardan con la fecha efectiva (lunes resultante del traslado según la regla uruguaya)

## Tecnologías

- **Backend:** FastAPI + Uvicorn
- **ORM:** SQLAlchemy 2.x
- **Validación:** Pydantic 2.x
- **Base de datos:** SQLite
- **Frontend:** HTML5 + CSS3 + JavaScript vanilla
