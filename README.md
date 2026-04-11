# Control Horario UdelaR 🕐

Sistema de registro y control de marcas horarias (entradas y salidas) desarrollado con FastAPI y SQLite.

## 📋 Características

- ✅ Registro de marcas de entrada y salida
- 📅 Soporte para cualquier fecha (presente, pasado)
- ✏️ Edición y eliminación de marcas
- 📊 Visualización agrupada por día con cálculo de horas
- 💾 Persistencia local con SQLite
- 🎨 Interfaz web moderna y responsive
- 🔌 API REST completa con documentación automática
- ✅ Navegar semana por semana con las flechas
- ✅ Saltar a cualquier fecha con el selector
- ✅ Volver rápido a hoy con el botón "Hoy"
- ✅ Se muestra el rango exacto de la semana (Lun X - Dom Y)
- ✅ Persiste la navegación mientras no recargues la página
- ✅ Actualización automática cuando volvés a "Hoy" tras registrar marcas

## 🚀 Instalación y Ejecución

### Opción 1: Docker (Recomendado para producción) 🐳

```bash
# Inicio rápido con script
chmod +x start-docker.sh
./start-docker.sh

# O manualmente
docker-compose up -d
```

**Acceso:** http://localhost:8200

📘 Ver [DOCKER.md](DOCKER.md) para guía completa de deployment

### Opción 2: Con UV (Desarrollo local) ⚡

```bash
# Instalar dependencias y ejecutar
uv sync
uv run uvicorn main:app --reload
```

**Acceso:** http://localhost:8000

### Opción 3: Con pip tradicional

```bash
pip install -r requirements.txt
python main.py
```

### 📍 URLs de acceso

- **Interfaz Web**: http://localhost:8200 (Docker) o http://localhost:8000 (local)
- **Documentación API (Swagger)**: `/api/docs`
- **Documentación API (ReDoc)**: `/api/redoc`
- **Health Check**: `/health`

## 📁 Estructura del Proyecto

```
control_horario/
├── main.py                  # Aplicación principal FastAPI
├── requirements.txt         # Dependencias del proyecto
├── control_horario.db       # Base de datos SQLite (se crea automáticamente)
│
├── database/               # Capa de base de datos
│   ├── __init__.py
│   ├── connection.py       # Configuración de conexión
│   └── models.py           # Modelos SQLAlchemy
│
├── schemas/                # Validación de datos (Pydantic)
│   ├── __init__.py
│   └── marca.py            # Schemas de marcas
│
├── services/               # Lógica de negocio
│   ├── __init__.py
│   └── marca_service.py    # Servicio de marcas
│
├── routers/                # Endpoints de la API
│   ├── __init__.py
│   └── marcas.py           # Router de marcas
│
├── static/                 # Archivos estáticos
│   ├── css/
│   │   └── style.css       # Estilos CSS
│   └── js/
│       └── app.js          # JavaScript frontend
│
└── templates/              # Templates HTML
    └── index.html          # Interfaz principal
```

## 🔌 API Endpoints

### Marcas

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/marcas` | Crear nueva marca |
| GET | `/api/marcas` | Listar todas las marcas |
| GET | `/api/marcas/{id}` | Obtener marca específica |
| PUT | `/api/marcas/{id}` | Actualizar marca |
| DELETE | `/api/marcas/{id}` | Eliminar marca |
| GET | `/api/marcas/fecha/{fecha}` | Marcas de una fecha |
| GET | `/api/marcas/agrupadas` | Marcas agrupadas por día |
| GET | `/api/marcas/estadisticas/semana` | Estadísticas de la semana actual |

| GET | `/api/marcas/estadisticas/semana?fecha=2026-04-10` | Estadísticas de cualquier semana |
| GET | `/api/marcas/estadisticas/mes` | Estadísticas del mes |

### Ejemplo de uso

**Crear marca:**
```bash
curl -X POST "http://localhost:8000/api/marcas" \
  -H "Content-Type: application/json" \
  -d '{
    "fecha": "2026-04-10",
    "tipo": "ENTRADA",
    "hora": "08:30:00",
    "observacion": "Llegada normal"
  }'
```

**Listar marcas agrupadas:**
```bash
curl "http://localhost:8000/api/marcas/agrupadas"
```

## 💾 Modelo de Datos

### Tabla: `marcas`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | Integer | ID único (autoincremental) |
| fecha | Date | Fecha de la marca |
| tipo | String | 'ENTRADA' o 'SALIDA' |
| hora | Time | Hora de la marca |
| observacion | String | Nota opcional (max 500 chars) |
| created_at | DateTime | Fecha de creación del registro |
| updated_at | DateTime | Fecha de última actualización |

## 🎯 Próximas Funcionalidades (Roadmap)

- [ ] Importación de datos desde PDF/TXT
- [ ] Gestión de licencias y días no trabajados
- [ ] Reportes mensuales con estadísticas
- [ ] Exportación a Excel/PDF
- [ ] Gestión de múltiples usuarios
- [ ] Dashboard con gráficos

## 🛠️ Tecnologías Utilizadas

- **Backend**: FastAPI 0.115.0
- **ORM**: SQLAlchemy 2.0.35
- **Validación**: Pydantic 2.9.2
- **Base de Datos**: SQLite
- **Frontend**: HTML5 + CSS3 + JavaScript vanilla
- **Servidor**: Uvicorn

## 📝 Notas

- La base de datos SQLite (`control_horario.db`) se crea automáticamente en la primera ejecución
- El servidor corre en modo desarrollo con auto-reload activado
- Los datos se persisten localmente, no requiere configuración adicional
- La interfaz es responsive y funciona en dispositivos móviles

## 🤝 Contribuciones

Este es un proyecto personal. Si encontrás bugs o tenés sugerencias, podés crear un issue o pull request.

## 📄 Licencia

Proyecto de uso personal para control horario en UdelaR.

---

Desarrollado con ❤️ para facilitar el control de asistencia
