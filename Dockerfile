# Dockerfile para Control Horario con UV
# Usa la imagen oficial de Python con UV preinstalado

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Establecer directorio de trabajo
WORKDIR /app

# Variables de entorno para Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Copiar archivos de dependencias
COPY pyproject.toml ./
COPY requirements.txt ./

# Instalar dependencias con UV
RUN uv pip install --system --no-cache -r requirements.txt

# Copiar el resto del código
COPY database ./database
COPY routers ./routers
COPY schemas ./schemas
COPY services ./services
COPY static ./static
COPY templates ./templates
COPY main.py ./

# Crear directorio para la base de datos
RUN mkdir -p /app/data

# Exponer puerto 8200
EXPOSE 8200

# Healthcheck para verificar que el servidor está funcionando
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8200/health')"

# Comando para ejecutar la aplicación
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8200"]
