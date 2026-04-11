#!/bin/bash
# Script para iniciar el servidor con Docker

set -e

echo "🐳 Control Horario - Docker Setup"
echo "=================================="
echo ""

# Verificar si Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker no está instalado"
    echo "   Instalá Docker desde: https://docs.docker.com/get-docker/"
    exit 1
fi

# Verificar si docker-compose está instalado
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Error: docker-compose no está instalado"
    exit 1
fi

# Crear directorio para la base de datos si no existe
mkdir -p data

echo "📦 Construyendo imagen Docker..."
docker-compose build

echo ""
echo "🚀 Iniciando contenedor..."
docker-compose up -d

echo ""
echo "✅ Servidor iniciado correctamente!"
echo ""
echo "📍 Accedé a la aplicación en:"
echo "   http://localhost:8200"
echo ""
echo "📚 Documentación API:"
echo "   http://localhost:8200/api/docs"
echo ""
echo "📊 Ver logs:"
echo "   docker-compose logs -f"
echo ""
echo "🛑 Detener servidor:"
echo "   docker-compose down"
echo ""
