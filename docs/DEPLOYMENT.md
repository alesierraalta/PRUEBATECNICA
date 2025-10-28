# Guía de Despliegue

## Resumen

Esta guía proporciona instrucciones detalladas para desplegar el Microservicio de Resumen LLM en diferentes entornos, desde desarrollo local hasta producción en la nube. Incluye configuraciones optimizadas, mejores prácticas de seguridad y estrategias de monitoreo.

## Prerrequisitos

### Requisitos del Sistema

- **Docker**: 20.10+ con Docker Compose
- **Memoria**: Mínimo 2GB RAM disponible
- **Almacenamiento**: Mínimo 5GB espacio libre
- **Red**: Acceso a internet para descargar imágenes

### Requisitos de Software

- **Python**: 3.11+ (para desarrollo local)
- **Git**: Para clonar el repositorio
- **curl**: Para pruebas de API
- **jq**: Para procesamiento de JSON (opcional)

### Requisitos de Servicios Externos

- **Google Gemini API**: Clave API válida
- **Redis**: Para caché y limitación de velocidad (opcional)

## Despliegue Local

### Opción 1: Docker Compose (Recomendado)

1. **Clonar el repositorio**
   ```bash
git clone https://github.com/alesierraalta/PRUEBATECNICA.git
cd PRUEBATECNICA
   ```

2. **Configurar variables de entorno**
   ```bash
   cp env.example .env
   # Editar .env con tu configuración
   ```

3. **Iniciar servicios**
   ```bash
   docker-compose up -d
   ```

4. **Verificar despliegue**
   ```bash
   curl http://localhost:8000/v1/healthz
   ```

### Opción 2: Desarrollo Local

1. **Crear entorno virtual**
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

2. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurar Redis (opcional)**
   ```bash
   # Con Docker
   docker run -d -p 6379:6379 redis:7-alpine
   
   # O instalar localmente
   # Ubuntu/Debian: sudo apt install redis-server
   # macOS: brew install redis
   ```

4. **Ejecutar aplicación**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

## Despliegue de Desarrollo

### Configuración de Desarrollo

```bash
# .env.development
ENVIRONMENT=development
LOG_LEVEL=DEBUG
WORKERS=1
API_KEYS_ALLOWED=dev_key_123,test_key_456
GEMINI_API_KEY=tu_clave_gemini_desarrollo
REDIS_URL=redis://localhost:6379/0
ENABLE_CACHE=true
ENABLE_RATE_LIMIT=false
CORS_ORIGINS=*
```

### Comandos de Desarrollo

```bash
# Iniciar con hot reload
docker-compose -f docker-compose.yml up -d

# Ver logs en tiempo real
docker-compose logs -f api

# Reiniciar servicio específico
docker-compose restart api

# Ejecutar pruebas
docker-compose exec api pytest

# Acceder al contenedor
docker-compose exec api bash
```

## Despliegue de Staging

### Configuración de Staging

```bash
# .env.staging
ENVIRONMENT=staging
LOG_LEVEL=INFO
WORKERS=2
API_KEYS_ALLOWED=staging_key_123,staging_key_456
GEMINI_API_KEY=tu_clave_gemini_staging
REDIS_URL=redis://redis-staging:6379/0
ENABLE_CACHE=true
ENABLE_RATE_LIMIT=true
RATE_LIMIT_PER_MINUTE=50
CORS_ORIGINS=https://staging.tu-dominio.com
```

### Despliegue con Docker Compose

```bash
# Usar configuración de staging
docker-compose -f docker-compose.yml --env-file .env.staging up -d

# Verificar salud
curl https://staging.tu-dominio.com/v1/healthz

# Ejecutar pruebas de integración
docker-compose exec api pytest tests/integration/
```

## Despliegue de Producción

### Configuración de Producción

```bash
# .env.production
ENVIRONMENT=production
LOG_LEVEL=INFO
WORKERS=4
API_KEYS_ALLOWED=prod_key_abc123,prod_key_def456
GEMINI_API_KEY=tu_clave_gemini_produccion
REDIS_URL=redis://redis-cluster:6379/0
ENABLE_CACHE=true
ENABLE_RATE_LIMIT=true
RATE_LIMIT_PER_MINUTE=100
CORS_ORIGINS=https://tu-dominio.com,https://api.tu-dominio.com
SSL_REDIRECT=true
SECURE_COOKIES=true
```

### Despliegue con Docker Compose de Producción

```bash
# Desplegar stack completo
docker-compose -f docker-compose.prod.yml --env-file .env.production up -d

# Desplegar con monitoreo
docker-compose -f docker-compose.prod.yml --env-file .env.production --profile monitoring up -d

# Verificar servicios
docker-compose -f docker-compose.prod.yml ps
```

### Configuración de Nginx

```nginx
# nginx.conf
upstream api_servers {
    server api:8000;
}

server {
    listen 80;
    server_name tu-dominio.com;
    
    location / {
        proxy_pass http://api_servers;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Health check para balanceadores de carga
    location /healthz {
        access_log off;
        return 200 '{"status": "healthy"}';
        add_header Content-Type application/json;
    }
}
```

## Despliegue en Servidores

### Despliegue en Servidor VPS

Para desplegar en un servidor VPS (DigitalOcean, Linode, AWS EC2, etc.):

1. **Preparar servidor**
   ```bash
   # Actualizar sistema
   sudo apt update && sudo apt upgrade -y
   
   # Instalar Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   
   # Instalar Docker Compose
   sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

2. **Clonar y configurar**
   ```bash
git clone https://github.com/alesierraalta/PRUEBATECNICA.git
cd PRUEBATECNICA
   
   # Configurar variables de entorno
   cp env.production .env.production
   nano .env.production  # Editar con tus valores
   ```

3. **Desplegar**
   ```bash
   # Desplegar con Docker Compose
   docker-compose -f docker-compose.prod.yml --env-file .env.production up -d
   
   # Verificar estado
   docker-compose -f docker-compose.prod.yml ps
   ```

### Despliegue con Nginx

Para usar Nginx como proxy reverso:

1. **Instalar Nginx**
   ```bash
   sudo apt install nginx
   ```

2. **Configurar sitio**
   ```bash
   sudo nano /etc/nginx/sites-available/llm-resumen
   ```

3. **Contenido de configuración**
   ```nginx
   server {
       listen 80;
       server_name tu-dominio.com;
       
       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

4. **Activar sitio**
   ```bash
   sudo ln -s /etc/nginx/sites-available/llm-resumen /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   ```

## Automatización de Despliegue

### Script de Despliegue Simple

Crear un script para automatizar el despliegue:

```bash
#!/bin/bash
# scripts/deploy.sh

set -e

echo "🚀 Iniciando despliegue..."

# Verificar que Docker esté ejecutándose
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker no está ejecutándose"
    exit 1
fi

# Construir imagen
echo "📦 Construyendo imagen Docker..."
docker-compose -f docker-compose.prod.yml build

# Detener servicios existentes
echo "🛑 Deteniendo servicios existentes..."
docker-compose -f docker-compose.prod.yml down

# Iniciar servicios
echo "▶️ Iniciando servicios..."
docker-compose -f docker-compose.prod.yml up -d

# Verificar salud
echo "🏥 Verificando salud del servicio..."
sleep 10
if curl -f http://localhost:8000/v1/healthz > /dev/null 2>&1; then
    echo "✅ Servicio desplegado correctamente"
else
    echo "❌ Error en el despliegue"
    docker-compose -f docker-compose.prod.yml logs
    exit 1
fi

echo "🎉 Despliegue completado exitosamente"
```

### GitHub Actions Básico

Para automatizar despliegues con GitHub Actions:

```yaml
# .github/workflows/deploy.yml
name: Despliegue Automático

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Configurar Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Construir imagen
      run: |
        docker build -t llm-resumen-api:${{ github.sha }} .
    
    - name: Desplegar en servidor
      env:
        SERVER_HOST: ${{ secrets.SERVER_HOST }}
        SERVER_USER: ${{ secrets.SERVER_USER }}
        SERVER_KEY: ${{ secrets.SERVER_KEY }}
      run: |
        # Copiar archivos al servidor
        scp -i $SERVER_KEY docker-compose.prod.yml $SERVER_USER@$SERVER_HOST:/app/
        scp -i $SERVER_KEY .env.production $SERVER_USER@$SERVER_HOST:/app/
        
        # Ejecutar despliegue en servidor
        ssh -i $SERVER_KEY $SERVER_USER@$SERVER_HOST "
          cd /app &&
          docker-compose -f docker-compose.prod.yml pull &&
          docker-compose -f docker-compose.prod.yml up -d
        "
```

## Monitoreo Básico

### Verificación de Salud

El servicio incluye un endpoint de salud que puedes usar para monitoreo básico:

```bash
# Verificar salud del servicio
curl http://localhost:8000/v1/healthz

# Respuesta esperada
{
  "overall_status": "healthy",
  "timestamp": "2024-01-15T10:00:00Z",
  "services": {
    "llm_provider": {
      "status": "healthy",
      "response_time_ms": 150
    },
    "redis": {
      "status": "healthy", 
      "response_time_ms": 5
    }
  },
  "version": "1.0.0"
}
```

### Script de Monitoreo Simple

```bash
#!/bin/bash
# scripts/monitor.sh

echo "🔍 Verificando estado del servicio..."

# Verificar salud
if curl -f http://localhost:8000/v1/healthz > /dev/null 2>&1; then
    echo "✅ Servicio saludable"
else
    echo "❌ Servicio no responde"
    exit 1
fi

# Verificar uso de recursos
echo "📊 Uso de recursos:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Verificar logs recientes
echo "📝 Logs recientes:"
docker-compose logs --tail=10 api
```

### Configurar Alertas Básicas

Para recibir alertas cuando el servicio esté caído:

```bash
#!/bin/bash
# scripts/health-check.sh

# Verificar salud cada 5 minutos
while true; do
    if ! curl -f http://localhost:8000/v1/healthz > /dev/null 2>&1; then
        echo "ALERTA: Servicio no responde - $(date)"
        # Aquí puedes agregar notificaciones por email, Slack, etc.
    fi
    sleep 300  # 5 minutos
done
```

## Rollback y Recuperación

### Rollback Simple

Si necesitas volver a una versión anterior:

```bash
#!/bin/bash
# scripts/rollback.sh

echo "🔄 Ejecutando rollback..."

# Detener servicios actuales
docker-compose -f docker-compose.prod.yml down

# Volver a imagen anterior (si tienes tags de versión)
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d

# Verificar que funcione
sleep 10
if curl -f http://localhost:8000/v1/healthz > /dev/null 2>&1; then
    echo "✅ Rollback exitoso"
else
    echo "❌ Error en rollback"
    exit 1
fi
```

### Verificación Post-Despliegue

```bash
#!/bin/bash
# scripts/verify-deployment.sh

echo "🔍 Verificando despliegue..."

# Verificar salud
if curl -f http://localhost:8000/v1/healthz > /dev/null 2>&1; then
    echo "✅ Servicio saludable"
else
    echo "❌ Servicio no responde"
    exit 1
fi

# Verificar tiempo de respuesta
RESPONSE_TIME=$(curl -o /dev/null -s -w '%{time_total}' http://localhost:8000/v1/healthz)
echo "⏱️ Tiempo de respuesta: ${RESPONSE_TIME}s"

# Verificar logs de errores
ERROR_COUNT=$(docker-compose logs api | grep -c "ERROR" || echo "0")
if [ "$ERROR_COUNT" -gt 5 ]; then
    echo "⚠️ Advertencia: $ERROR_COUNT errores en logs"
fi

echo "✅ Verificación completada"
```

## Mejores Prácticas

### 1. Seguridad

- **Nunca hardcodear secretos** en imágenes Docker
- **Usar secretos gestionados** (AWS Secrets Manager, Azure Key Vault, etc.)
- **Implementar HTTPS** en producción
- **Configurar firewalls** apropiadamente
- **Rotar claves API** regularmente

### 2. Escalabilidad

- **Usar múltiples réplicas** en producción
- **Implementar health checks** apropiados
- **Configurar auto-scaling** basado en métricas
- **Usar load balancers** para distribución de carga

### 3. Monitoreo

- **Implementar métricas de negocio** además de técnicas
- **Configurar alertas proactivas** antes de que ocurran problemas
- **Mantener dashboards actualizados** con métricas relevantes
- **Revisar logs regularmente** para identificar patrones

### 4. Backup y Recuperación

- **Hacer backup de configuraciones** importantes
- **Documentar procedimientos de recuperación**
- **Probar procedimientos de rollback** regularmente
- **Mantener múltiples entornos** (dev, staging, prod)

## Solución de Problemas

### Problema: Servicio No Inicia

**Síntomas:**
- Contenedor se reinicia constantemente
- Logs muestran errores de inicio

**Solución:**
```bash
# Verificar logs
docker-compose logs api

# Verificar configuración
docker-compose config

# Verificar recursos
docker stats
```

### Problema: Errores de Conectividad

**Síntomas:**
- Errores de conexión a Redis
- Timeouts en llamadas a Gemini

**Solución:**
```bash
# Verificar conectividad de red
docker-compose exec api ping redis

# Verificar configuración de URLs
docker-compose exec api env | grep -E "(REDIS_URL|GEMINI_API_KEY)"
```

### Problema: Alto Uso de Memoria

**Síntomas:**
- Contenedores siendo terminados por OOM
- Rendimiento degradado

**Solución:**
```bash
# Aumentar límites de memoria
# En docker-compose.yml
deploy:
  resources:
    limits:
      memory: 1G

# En Kubernetes
resources:
  limits:
    memory: "1Gi"
```