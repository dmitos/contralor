"""
Aplicación principal FastAPI.

Punto de entrada del servidor. Configura la aplicación, inicializa la base de datos,
registra routers y sirve la interfaz web.

Para ejecutar:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routers import marcas_router

# Crear aplicación FastAPI
app = FastAPI(
    title="Control Horario UdelaR",
    description="Sistema de control de marcas horarias - Entrada y Salida",
    version="1.0.0",
    docs_url="/api/docs",  # Swagger UI en /api/docs
    redoc_url="/api/redoc"  # ReDoc en /api/redoc
)

# Configurar CORS (permite requests desde el navegador)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar archivos estáticos (CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configurar templates Jinja2
templates = Jinja2Templates(directory="templates")

# Registrar routers
app.include_router(marcas_router)


@app.on_event("startup")
async def startup_event():
    """
    Evento que se ejecuta al iniciar la aplicación.
    Inicializa la base de datos creando las tablas si no existen.
    """
    print("🚀 Iniciando aplicación...")
    init_db()
    print("✅ Aplicación lista en http://localhost:8000")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """
    Ruta principal que sirve la interfaz web.
    
    Args:
        request: Objeto Request de FastAPI
        
    Returns:
        Template HTML renderizado
    """
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health_check():
    """
    Endpoint de health check para verificar que el servidor está activo.
    
    Returns:
        Diccionario con estado de la aplicación
    """
    return {
        "status": "healthy",
        "service": "Control Horario API",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    
    # Ejecutar servidor
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload en desarrollo
        log_level="info"
    )
