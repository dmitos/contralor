# 🐳 Control Horario - Deployment con Docker

Guía completa para deployar el sistema usando Docker y UV en tu servidor.

## 📋 Prerequisitos

- Docker instalado (versión 20.10 o superior)
- Docker Compose instalado (versión 2.0 o superior)
- Puerto 8200 disponible en tu servidor

## 🚀 Inicio Rápido

### Opción 1: Script automático (Recomendado)

```bash
# Dar permisos de ejecución
chmod +x start-docker.sh

# Ejecutar
./start-docker.sh
```

### Opción 2: Comandos manuales

```bash
# 1. Crear directorio para la base de datos
mkdir -p data

# 2. Construir la imagen
docker-compose build

# 3. Iniciar el contenedor
docker-compose up -d

# 4. Verificar que está corriendo
docker-compose ps
```

## 🌐 Acceso

Una vez iniciado, el servidor estará disponible en:

- **Aplicación Web**: `http://tu-servidor:8200`
- **API Docs (Swagger)**: `http://tu-servidor:8200/api/docs`
- **API Docs (ReDoc)**: `http://tu-servidor:8200/api/redoc`
- **Health Check**: `http://tu-servidor:8200/health`

## 📊 Gestión del Contenedor

### Ver logs en tiempo real
```bash
docker-compose logs -f
```

### Ver logs de las últimas 100 líneas
```bash
docker-compose logs --tail=100
```

### Detener el servidor
```bash
docker-compose down
```

### Reiniciar el servidor
```bash
docker-compose restart
```

### Detener y eliminar todo (incluyendo volúmenes)
```bash
docker-compose down -v
```

## 🔄 Actualizar la aplicación

Cuando hagas cambios en el código:

```bash
# 1. Detener el contenedor
docker-compose down

# 2. Reconstruir la imagen
docker-compose build

# 3. Iniciar nuevamente
docker-compose up -d
```

O en un solo comando:
```bash
docker-compose up -d --build
```

## 💾 Persistencia de Datos

La base de datos SQLite se guarda en:
```
./data/control_horario.db
```

Este archivo se monta como volumen en el contenedor, por lo que **tus datos persisten** incluso si recreás el contenedor.

### Hacer backup de la base de datos

```bash
# Copiar la base de datos
cp data/control_horario.db data/control_horario_backup_$(date +%Y%m%d).db

# O exportar desde el contenedor
docker-compose exec control-horario cp /app/data/control_horario.db /app/data/backup.db
```

## 🔧 Configuración Avanzada

### Cambiar puerto

Editá `docker-compose.yml` y cambiá el mapeo de puertos:

```yaml
ports:
  - "8200:8200"  # Cambiar el primer número al puerto que quieras
```

### Variables de entorno

Podés agregar variables de entorno en `docker-compose.yml`:

```yaml
environment:
  - TZ=America/Montevideo
  - DATABASE_URL=sqlite:///./data/control_horario.db
```

### Modo desarrollo con hot-reload

Para desarrollo, descomentá los volúmenes en `docker-compose.yml`:

```yaml
volumes:
  - ./data:/app/data
  - ./main.py:/app/main.py
  - ./database:/app/database
  # ... resto de las carpetas
```

Luego ejecutá:
```bash
docker-compose up
```

## 🔒 Seguridad en Producción

### 1. Usar un reverse proxy (Nginx/Caddy)

Ejemplo de configuración Nginx:

```nginx
server {
    listen 80;
    server_name tu-dominio.com;

    location / {
        proxy_pass http://localhost:8200;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### 2. Configurar HTTPS con Certbot

```bash
sudo certbot --nginx -d tu-dominio.com
```

### 3. Limitar acceso por IP (opcional)

En Nginx:
```nginx
allow 192.168.1.0/24;  # Tu red local
deny all;
```

## 📈 Monitoreo

### Ver estado del contenedor
```bash
docker-compose ps
```

### Ver uso de recursos
```bash
docker stats control_horario_app
```

### Inspeccionar el contenedor
```bash
docker-compose exec control-horario sh
```

## 🐛 Troubleshooting

### El contenedor no inicia

```bash
# Ver logs detallados
docker-compose logs

# Verificar que el puerto no esté en uso
sudo lsof -i :8200
# o
sudo netstat -tulpn | grep 8200
```

### Error de permisos en /app/data

```bash
# Dar permisos al directorio
chmod -R 755 data/
```

### La base de datos no persiste

Verificá que el volumen esté montado correctamente:
```bash
docker-compose exec control-horario ls -la /app/data/
```

## 🔄 Migración desde versión local

Si ya tenías la app corriendo localmente y querés migrar a Docker:

```bash
# 1. Copiar la base de datos existente
mkdir -p data
cp control_horario.db data/

# 2. Iniciar con Docker
docker-compose up -d
```

## 📦 Comandos Útiles

```bash
# Ver versión de las imágenes
docker-compose images

# Limpiar imágenes antiguas
docker system prune -a

# Ver todos los contenedores (incluso detenidos)
docker ps -a

# Forzar recreación del contenedor
docker-compose up -d --force-recreate
```

## 🆘 Soporte

Si encontrás problemas:

1. Verificá los logs: `docker-compose logs -f`
2. Verificá el health check: `curl http://localhost:8200/health`
3. Inspeccioná el contenedor: `docker-compose exec control-horario sh`

---

**Desarrollado para UdelaR - Control Horario v1.0.0**
