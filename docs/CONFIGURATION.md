# Guía de Configuración

## Resumen

Esta guía detalla todas las opciones de configuración disponibles para el Microservicio de Resumen LLM. La configuración sigue los principios de la aplicación de 12 factores y utiliza variables de entorno para máxima flexibilidad.

## Variables de Entorno

### Configuración de Aplicación

| Variable | Descripción | Predeterminado | Requerido | Ejemplo |
|----------|-------------|----------------|-----------|---------|
| `ENVIRONMENT` | Entorno de ejecución | `development` | No | `production` |
| `LOG_LEVEL` | Nivel de logging | `INFO` | No | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `WORKERS` | Número de workers Uvicorn | `1` | No | `4` |
| `API_TITLE` | Título de la API | `API de Resumen LLM` | No | `Mi API de Resumen` |
| `API_VERSION` | Versión de la API | `1.0.0` | No | `2.0.0` |

### Configuración de API

| Variable | Descripción | Predeterminado | Requerido | Ejemplo |
|----------|-------------|----------------|-----------|---------|
| `API_KEYS_ALLOWED` | Claves API separadas por comas | - | Sí | `clave1,clave2,clave3` |
| `CORS_ORIGINS` | Orígenes CORS permitidos | `*` | No | `https://mi-dominio.com` |
| `REQUEST_TIMEOUT_MS` | Timeout de solicitud en ms | `10000` | No | `15000` |
| `MAX_TEXT_LENGTH` | Longitud máxima de texto | `50000` | No | `100000` |
| `MIN_TEXT_LENGTH` | Longitud mínima de texto | `10` | No | `5` |

### Configuración de Proveedor LLM

| Variable | Descripción | Predeterminado | Requerido | Ejemplo |
|----------|-------------|----------------|-----------|---------|
| `LLM_PROVIDER` | Proveedor LLM a usar | `gemini` | No | `gemini`, `fallback` |
| `GEMINI_API_KEY` | Clave API de Google Gemini | - | Sí* | `AIzaSy...` |
| `GEMINI_MODEL` | Modelo Gemini específico | `gemini-pro` | No | `gemini-pro-vision` |
| `LLM_TIMEOUT_MS` | Timeout del LLM en ms | `8000` | No | `12000` |
| `LLM_MAX_RETRIES` | Máximo de reintentos | `3` | No | `5` |
| `LLM_TEMPERATURE` | Temperatura del modelo | `0.7` | No | `0.5` |

*Requerido si `LLM_PROVIDER=gemini`

### Configuración de Resumen

| Variable | Descripción | Predeterminado | Requerido | Ejemplo |
|----------|-------------|----------------|-----------|---------|
| `SUMMARY_MAX_TOKENS` | Máximo de tokens predeterminado | `100` | No | `200` |
| `LANG_DEFAULT` | Idioma predeterminado | `auto` | No | `es`, `en` |
| `TONE_DEFAULT` | Tono predeterminado | `neutral` | No | `concise`, `bullet` |
| `ENABLE_AUTO_EVALUATION` | Habilitar evaluación automática | `true` | No | `false` |
| `EVALUATION_MODEL` | Modelo para evaluación | `all-MiniLM-L6-v2` | No | `all-mpnet-base-v2` |

### Configuración de Caché

| Variable | Descripción | Predeterminado | Requerido | Ejemplo |
|----------|-------------|----------------|-----------|---------|
| `ENABLE_CACHE` | Habilitar caché | `true` | No | `false` |
| `REDIS_URL` | URL de conexión Redis | `redis://localhost:6379/0` | No | `redis://user:pass@host:port/db` |
| `CACHE_TTL_SECONDS` | TTL del caché en segundos | `3600` | No | `7200` |
| `REDIS_POOL_MAX_CONNECTIONS` | Máximo de conexiones en pool | `20` | No | `50` |
| `REDIS_POOL_TIMEOUT` | Timeout del pool en segundos | `5` | No | `10` |

### Configuración de Limitación de Velocidad

| Variable | Descripción | Predeterminado | Requerido | Ejemplo |
|----------|-------------|----------------|-----------|---------|
| `ENABLE_RATE_LIMIT` | Habilitar limitación de velocidad | `true` | No | `false` |
| `RATE_LIMIT_PER_MINUTE` | Límite por minuto | `100` | No | `200` |
| `RATE_LIMIT_WINDOW` | Ventana de tiempo en segundos | `60` | No | `300` |
| `RATE_LIMIT_BURST` | Ráfaga permitida | `20` | No | `50` |

### Configuración de Seguridad

| Variable | Descripción | Predeterminado | Requerido | Ejemplo |
|----------|-------------|----------------|-----------|---------|
| `SECRET_KEY` | Clave secreta para JWT | - | No | `mi-clave-secreta-super-segura` |
| `ALLOWED_HOSTS` | Hosts permitidos | `*` | No | `mi-dominio.com,api.mi-dominio.com` |
| `SSL_REDIRECT` | Redirección SSL forzada | `false` | No | `true` |
| `SECURE_COOKIES` | Cookies seguras | `false` | No | `true` |

## Archivos de Configuración

### Archivo .env (Desarrollo)

```bash
# ===========================================
# CONFIGURACIÓN DE APLICACIÓN
# ===========================================
ENVIRONMENT=development
LOG_LEVEL=DEBUG
WORKERS=1
API_TITLE=API de Resumen LLM - Desarrollo
API_VERSION=1.0.0

# ===========================================
# CONFIGURACIÓN DE API
# ===========================================
API_KEYS_ALLOWED=dev_key_123,test_key_456
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
REQUEST_TIMEOUT_MS=15000
MAX_TEXT_LENGTH=10000
MIN_TEXT_LENGTH=5

# ===========================================
# CONFIGURACIÓN DE PROVEEDOR LLM
# ===========================================
LLM_PROVIDER=gemini
GEMINI_API_KEY=tu_clave_gemini_api_aqui
GEMINI_MODEL=gemini-pro
LLM_TIMEOUT_MS=10000
LLM_MAX_RETRIES=5
LLM_TEMPERATURE=0.7

# ===========================================
# CONFIGURACIÓN DE RESUMEN
# ===========================================
SUMMARY_MAX_TOKENS=150
LANG_DEFAULT=es
TONE_DEFAULT=neutral
ENABLE_AUTO_EVALUATION=true
EVALUATION_MODEL=all-MiniLM-L6-v2

# ===========================================
# CONFIGURACIÓN DE CACHÉ
# ===========================================
ENABLE_CACHE=true
REDIS_URL=redis://localhost:6379/0
CACHE_TTL_SECONDS=1800
REDIS_POOL_MAX_CONNECTIONS=10
REDIS_POOL_TIMEOUT=5

# ===========================================
# CONFIGURACIÓN DE LIMITACIÓN DE VELOCIDAD
# ===========================================
ENABLE_RATE_LIMIT=true
RATE_LIMIT_PER_MINUTE=200
RATE_LIMIT_WINDOW=60
RATE_LIMIT_BURST=30

# ===========================================
# CONFIGURACIÓN DE SEGURIDAD
# ===========================================
SECRET_KEY=clave-secreta-desarrollo-no-produccion
ALLOWED_HOSTS=localhost,127.0.0.1
SSL_REDIRECT=false
SECURE_COOKIES=false
```

### Archivo .env.production (Producción)

```bash
# ===========================================
# CONFIGURACIÓN DE APLICACIÓN
# ===========================================
ENVIRONMENT=production
LOG_LEVEL=INFO
WORKERS=4
API_TITLE=API de Resumen LLM
API_VERSION=1.0.0

# ===========================================
# CONFIGURACIÓN DE API
# ===========================================
API_KEYS_ALLOWED=prod_key_abc123,prod_key_def456,prod_key_ghi789
CORS_ORIGINS=https://mi-dominio.com,https://api.mi-dominio.com
REQUEST_TIMEOUT_MS=10000
MAX_TEXT_LENGTH=50000
MIN_TEXT_LENGTH=10

# ===========================================
# CONFIGURACIÓN DE PROVEEDOR LLM
# ===========================================
LLM_PROVIDER=gemini
GEMINI_API_KEY=tu_clave_gemini_produccion_aqui
GEMINI_MODEL=gemini-pro
LLM_TIMEOUT_MS=8000
LLM_MAX_RETRIES=3
LLM_TEMPERATURE=0.7

# ===========================================
# CONFIGURACIÓN DE RESUMEN
# ===========================================
SUMMARY_MAX_TOKENS=100
LANG_DEFAULT=auto
TONE_DEFAULT=neutral
ENABLE_AUTO_EVALUATION=true
EVALUATION_MODEL=all-MiniLM-L6-v2

# ===========================================
# CONFIGURACIÓN DE CACHÉ
# ===========================================
ENABLE_CACHE=true
REDIS_URL=redis://redis-cluster:6379/0
CACHE_TTL_SECONDS=3600
REDIS_POOL_MAX_CONNECTIONS=50
REDIS_POOL_TIMEOUT=10

# ===========================================
# CONFIGURACIÓN DE LIMITACIÓN DE VELOCIDAD
# ===========================================
ENABLE_RATE_LIMIT=true
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_WINDOW=60
RATE_LIMIT_BURST=20

# ===========================================
# CONFIGURACIÓN DE SEGURIDAD
# ===========================================
SECRET_KEY=clave-secreta-super-segura-produccion
ALLOWED_HOSTS=mi-dominio.com,api.mi-dominio.com
SSL_REDIRECT=true
SECURE_COOKIES=true
```

## Configuración por Entorno

### Desarrollo

**Características:**
- Logging detallado (DEBUG)
- CORS permisivo
- Timeouts más largos
- Caché con TTL corto
- Límites de velocidad altos

**Configuración Recomendada:**
```bash
ENVIRONMENT=development
LOG_LEVEL=DEBUG
CORS_ORIGINS=*
REQUEST_TIMEOUT_MS=15000
CACHE_TTL_SECONDS=300
RATE_LIMIT_PER_MINUTE=1000
```

### Testing

**Características:**
- Logging mínimo
- Sin caché
- Sin limitación de velocidad
- Timeouts cortos
- Datos de prueba

**Configuración Recomendada:**
```bash
ENVIRONMENT=testing
LOG_LEVEL=WARNING
ENABLE_CACHE=false
ENABLE_RATE_LIMIT=false
REQUEST_TIMEOUT_MS=5000
```

### Staging

**Características:**
- Configuración similar a producción
- Logging INFO
- Caché habilitado
- Limitación de velocidad moderada
- Datos reales

**Configuración Recomendada:**
```bash
ENVIRONMENT=staging
LOG_LEVEL=INFO
ENABLE_CACHE=true
ENABLE_RATE_LIMIT=true
RATE_LIMIT_PER_MINUTE=50
```

### Producción

**Características:**
- Logging optimizado
- Seguridad máxima
- Caché optimizado
- Limitación de velocidad estricta
- Monitoreo completo

**Configuración Recomendada:**
```bash
ENVIRONMENT=production
LOG_LEVEL=INFO
ENABLE_CACHE=true
ENABLE_RATE_LIMIT=true
RATE_LIMIT_PER_MINUTE=100
SSL_REDIRECT=true
SECURE_COOKIES=true
```

## Configuración Avanzada

### Configuración de Redis

#### Conexión Básica
```bash
REDIS_URL=redis://localhost:6379/0
```

#### Conexión con Autenticación
```bash
REDIS_URL=redis://usuario:contraseña@localhost:6379/0
```

#### Conexión con SSL
```bash
REDIS_URL=rediss://usuario:contraseña@redis-cluster.com:6380/0
```

#### Configuración de Pool de Conexiones
```bash
REDIS_POOL_MAX_CONNECTIONS=50
REDIS_POOL_TIMEOUT=10
REDIS_POOL_RETRY_ON_TIMEOUT=true
REDIS_POOL_HEALTH_CHECK_INTERVAL=30
```

### Configuración de LLM

#### Configuración de Gemini
```bash
LLM_PROVIDER=gemini
GEMINI_API_KEY=tu_clave_api
GEMINI_MODEL=gemini-pro
GEMINI_TEMPERATURE=0.7
GEMINI_MAX_TOKENS=1000
GEMINI_TOP_P=0.9
GEMINI_TOP_K=40
```

#### Configuración de Reintentos
```bash
LLM_MAX_RETRIES=3
LLM_RETRY_DELAY=1.0
LLM_RETRY_BACKOFF=2.0
LLM_RETRY_MAX_DELAY=8.0
```

### Configuración de Evaluación

#### Modelos de Evaluación Disponibles
```bash
# Modelo rápido (predeterminado)
EVALUATION_MODEL=all-MiniLM-L6-v2

# Modelo más preciso
EVALUATION_MODEL=all-mpnet-base-v2

# Modelo multilingüe
EVALUATION_MODEL=paraphrase-multilingual-MiniLM-L12-v2
```

#### Configuración de Métricas
```bash
ENABLE_ROUGE_METRICS=true
ENABLE_SEMANTIC_SIMILARITY=true
ENABLE_COMPRESSION_RATIO=true
EVALUATION_CACHE_TTL=3600
```

### Configuración de Logging

#### Niveles de Logging
```bash
# Desarrollo
LOG_LEVEL=DEBUG

# Producción
LOG_LEVEL=INFO

# Solo errores
LOG_LEVEL=ERROR
```

#### Configuración de Formato
```bash
LOG_FORMAT=json
LOG_COLORIZE=false
LOG_INCLUDE_TIMESTAMP=true
LOG_INCLUDE_REQUEST_ID=true
```

#### Configuración de Archivos
```bash
LOG_FILE_PATH=/app/logs/app.log
LOG_MAX_SIZE=100MB
LOG_BACKUP_COUNT=5
LOG_ROTATION_INTERVAL=daily
```

## Validación de Configuración

### Verificación Automática

La aplicación valida automáticamente la configuración al iniciar:

```python
# Verificación de configuración requerida
if not settings.API_KEYS_ALLOWED:
    raise ValueError("API_KEYS_ALLOWED es requerido")

if settings.LLM_PROVIDER == "gemini" and not settings.GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY es requerido para proveedor gemini")

# Verificación de rangos válidos
if not (10 <= settings.SUMMARY_MAX_TOKENS <= 500):
    raise ValueError("SUMMARY_MAX_TOKENS debe estar entre 10 y 500")
```

### Script de Validación

```bash
#!/bin/bash
# scripts/validate-config.sh

echo "Validando configuración..."

# Verificar variables requeridas
if [ -z "$API_KEYS_ALLOWED" ]; then
    echo "ERROR: API_KEYS_ALLOWED no está configurado"
    exit 1
fi

if [ -z "$GEMINI_API_KEY" ]; then
    echo "ERROR: GEMINI_API_KEY no está configurado"
    exit 1
fi

# Verificar conectividad Redis
if [ "$ENABLE_CACHE" = "true" ]; then
    redis-cli -u "$REDIS_URL" ping || {
        echo "ERROR: No se puede conectar a Redis"
        exit 1
    }
fi

echo "Configuración válida ✓"
```

## Configuración de Docker

### Variables de Entorno en Docker Compose

```yaml
# docker-compose.yml
services:
  api:
    environment:
      - API_KEYS_ALLOWED=${API_KEYS_ALLOWED}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - REDIS_URL=redis://redis:6379/0
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    env_file:
      - .env
```

### Configuración de Secrets

```yaml
# docker-compose.prod.yml
services:
  api:
    secrets:
      - gemini_api_key
      - api_keys_allowed
    environment:
      - GEMINI_API_KEY_FILE=/run/secrets/gemini_api_key
      - API_KEYS_ALLOWED_FILE=/run/secrets/api_keys_allowed

secrets:
  gemini_api_key:
    file: ./secrets/gemini_api_key.txt
  api_keys_allowed:
    file: ./secrets/api_keys_allowed.txt
```

## Configuración de Kubernetes

### ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: llm-resumen-config
data:
  LOG_LEVEL: "INFO"
  WORKERS: "4"
  SUMMARY_MAX_TOKENS: "100"
  CACHE_TTL_SECONDS: "3600"
  RATE_LIMIT_PER_MINUTE: "100"
```

### Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: llm-resumen-secrets
type: Opaque
data:
  gemini-api-key: <base64-encoded-key>
  api-keys-allowed: <base64-encoded-keys>
```

### Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-resumen-api
spec:
  template:
    spec:
      containers:
      - name: api
        envFrom:
        - configMapRef:
            name: llm-resumen-config
        - secretRef:
            name: llm-resumen-secrets
```

## Mejores Prácticas

### 1. Gestión de Secretos

**❌ Incorrecto:**
```bash
# Nunca hardcodear secretos en código
GEMINI_API_KEY=AIzaSy...
```

**✅ Correcto:**
```bash
# Usar variables de entorno o secretos
GEMINI_API_KEY=${GEMINI_API_KEY}
```

### 2. Configuración por Entorno

**❌ Incorrecto:**
```bash
# Usar la misma configuración para todos los entornos
LOG_LEVEL=DEBUG
```

**✅ Correcto:**
```bash
# Configuración específica por entorno
LOG_LEVEL=${LOG_LEVEL:-INFO}
```

### 3. Validación de Configuración

**❌ Incorrecto:**
```bash
# No validar configuración
# Asumir que todo está correcto
```

**✅ Correcto:**
```bash
# Validar configuración al inicio
python -c "from app.config import settings; print('Configuración válida')"
```

### 4. Documentación de Configuración

**❌ Incorrecto:**
```bash
# Variables sin documentación
MYSTERY_VAR=value
```

**✅ Correcto:**
```bash
# Variables documentadas
# TTL del caché en segundos (predeterminado: 3600)
CACHE_TTL_SECONDS=3600
```

## Solución de Problemas de Configuración

### Problema: Clave API Inválida

**Síntomas:**
- Error 401 en todas las solicitudes
- Logs: "Clave API inválida"

**Solución:**
```bash
# Verificar formato de clave API
echo $API_KEYS_ALLOWED

# Verificar que la clave esté en la lista
curl -H "Authorization: Bearer tu_clave" http://localhost:8000/v1/healthz
```

### Problema: Redis No Disponible

**Síntomas:**
- Errores de conexión Redis
- Caché no funciona

**Solución:**
```bash
# Verificar conexión Redis
redis-cli -u "$REDIS_URL" ping

# Verificar configuración de URL
echo $REDIS_URL
```

### Problema: Timeout de LLM

**Síntomas:**
- Errores 503 frecuentes
- Timeouts en solicitudes largas

**Solución:**
```bash
# Aumentar timeout
LLM_TIMEOUT_MS=15000

# Verificar conectividad a Gemini
curl -H "Authorization: Bearer $GEMINI_API_KEY" \
  https://generativelanguage.googleapis.com/v1/models
```

### Problema: Límite de Velocidad Muy Estricto

**Síntomas:**
- Errores 429 frecuentes
- Headers de límite de velocidad muestran límites bajos

**Solución:**
```bash
# Aumentar límite de velocidad
RATE_LIMIT_PER_MINUTE=200

# O deshabilitar temporalmente
ENABLE_RATE_LIMIT=false
```