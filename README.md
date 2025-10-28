# Microservicio de Resumen LLM

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-green.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/Code%20Style-Black-black.svg)](https://github.com/psf/black)

Un microservicio de alto rendimiento y listo para producción para resumen inteligente de texto usando modelos de IA avanzados. Construido con FastAPI, incluye manejo integral de errores, caché, limitación de velocidad y mecanismos de respaldo automático.

## Tabla de Contenidos

- [Inicio Rápido](#inicio-rápido)
- [Arquitectura](#arquitectura)
- [Documentación de API](#documentación-de-api)
- [Configuración](#configuración)
- [Despliegue](#despliegue)
- [Pruebas](#pruebas)
- [Rendimiento](#rendimiento)
- [Solución de Problemas](#solución-de-problemas)

## Inicio Rápido

### Prerrequisitos

- Python 3.11+
- Docker & Docker Compose
- Clave API de Google Gemini

### Instalación

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/tuusuario/microservicio-resumen-llm.git
   cd microservicio-resumen-llm
   ```

2. **Configurar variables de entorno**
   ```bash
   cp env.example .env
   # Editar .env con tu configuración
   ```

3. **Ejecutar con Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Acceder a la API**
   - API: http://localhost:8000
   - Documentación: http://localhost:8000/docs
   - Verificación de Salud: http://localhost:8000/v1/healthz

### Uso Básico

```bash
# Resumir texto
curl -X POST "http://localhost:8000/v1/summarize" \
  -H "Authorization: Bearer tu_clave_api" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Tu texto para resumir aquí...",
    "lang": "es",
    "max_tokens": 100,
    "tone": "neutral"
  }'
```

## Arquitectura

El microservicio sigue un patrón de arquitectura en capas diseñado para alto rendimiento, confiabilidad y mantenibilidad. La arquitectura enfatiza la separación de responsabilidades, inyección de dependencias y manejo integral de errores.

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Aplicación    │───▶│   API FastAPI   │───▶│  Proveedor LLM  │
│     Cliente     │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Middleware    │    │   Respaldo      │
                       │  (Auth, Rate    │    │   Extractivo    │
                       │   Limit, Log)   │    │  (TextRank)     │
                       └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Servicios     │
                       │ (Cache, Eval)   │
                       └─────────────────┘
```

### Componentes Clave

- **Capa API**: Routers FastAPI con validación Pydantic
- **Middleware**: Autenticación, limitación de velocidad, logging, CORS
- **Servicios**: Caché (Redis), evaluación (ROUGE + similitud semántica)
- **Proveedores**: LLM (Gemini), respaldo (TextRank)
- **Infraestructura**: Docker, Nginx, monitoreo

## Documentación de API

### Autenticación

Todos los endpoints requieren autenticación con clave API:

```bash
Authorization: Bearer tu_clave_api_aqui
```

### Endpoints

#### POST /v1/summarize

Resumir texto usando IA con manejo integral de errores y respaldo.

**Solicitud:**
```json
{
  "text": "Texto para resumir (10-50,000 caracteres)",
  "lang": "auto|es|en|fr|de|...",
  "max_tokens": 100,
  "tone": "neutral|concise|bullet"
}
```

**Respuesta:**
```json
{
  "summary": "Texto del resumen generado",
  "usage": {
    "prompt_tokens": 120,
    "completion_tokens": 40,
    "total_tokens": 160
  },
  "model": "gemini-pro",
  "latency_ms": 1250,
  "evaluation": {
    "rouge_1_f": 0.75,
    "rouge_2_f": 0.65,
    "rouge_l_f": 0.70,
    "semantic_similarity": 0.85,
    "compression_ratio": 0.20,
    "quality_score": 0.78
  },
  "cached": false
}
```

#### GET /v1/healthz

Verificación integral de salud para todos los componentes del servicio.

**Respuesta:**
```json
{
  "status": "healthy",
  "timestamp": 1640995200.123,
  "services": {
    "llm_provider": {
      "status": "healthy",
      "response_time_ms": 150,
      "details": {"model": "gemini-pro"}
    },
    "redis": {
      "status": "healthy",
      "response_time_ms": 5,
      "details": {"connected_clients": 10}
    }
  },
  "version": "1.0.0",
  "uptime_seconds": 86400.0
}
```

### Manejo de Errores

La API devuelve respuestas de error consistentes:

```json
{
  "error": "tipo_error",
  "message": "Mensaje de error bilingüe / Bilingual error message",
  "timestamp": 1640995200.123,
  "request_id": "uuid-aqui"
}
```

**Códigos de Estado:**
- `200` - Éxito
- `400` - Solicitud Incorrecta (error de validación)
- `401` - No Autorizado (clave API inválida)
- `429` - Demasiadas Solicitudes (límite de velocidad excedido)
- `503` - Servicio No Disponible (proveedor LLM caído)

## Configuración

### Variables de Entorno

| Variable | Descripción | Predeterminado | Requerido |
|----------|-------------|----------------|-----------|
| `API_KEYS_ALLOWED` | Claves API separadas por comas | - | Sí |
| `GEMINI_API_KEY` | Clave API de Google Gemini | - | Sí |
| `REDIS_URL` | URL de conexión Redis | `redis://localhost:6379/0` | No |
| `ENABLE_RATE_LIMIT` | Habilitar limitación de velocidad | `true` | No |
| `ENABLE_AUTO_EVALUATION` | Habilitar evaluación de calidad | `true` | No |
| `LOG_LEVEL` | Nivel de logging | `INFO` | No |
| `SUMMARY_MAX_TOKENS` | Máximo de tokens predeterminado | `100` | No |
| `REQUEST_TIMEOUT_MS` | Timeout de solicitud | `10000` | No |

### Configuración Completa

```bash
# Aplicación
ENVIRONMENT=production
LOG_LEVEL=INFO
WORKERS=4

# API
API_KEYS_ALLOWED=clave1,clave2,clave3
API_TITLE=API de Resumen LLM
API_VERSION=1.0.0

# Proveedor LLM
LLM_PROVIDER=gemini
GEMINI_API_KEY=tu_clave_gemini_api
GEMINI_MODEL=gemini-pro

# Características
ENABLE_RATE_LIMIT=true
ENABLE_AUTO_EVALUATION=true
EVALUATION_MODEL=all-MiniLM-L6-v2

# Caché
REDIS_URL=redis://localhost:6379/0
CACHE_TTL_SECONDS=3600

# CORS
CORS_ORIGINS=https://tudominio.com
```

## Despliegue

### Docker Compose (Recomendado)

1. **Despliegue de producción**
   ```bash
   # Copiar entorno de producción
   cp env.production .env.production
   
   # Desplegar con monitoreo
   docker-compose -f docker-compose.prod.yml --profile monitoring up -d
   ```

2. **Despliegue de desarrollo**
   ```bash
   docker-compose up -d
   ```

### Construcción Manual de Docker

```bash
# Construir imagen
./scripts/docker-build.sh 1.0.0

# Desplegar
./scripts/docker-deploy.sh deploy
```

### Configuraciones Específicas por Entorno

- **Desarrollo**: `docker-compose.yml`
- **Producción**: `docker-compose.prod.yml`
- **Pruebas**: `docker-compose.test.yml`

## Pruebas

### Ejecutar Pruebas

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar todas las pruebas
pytest

# Ejecutar con cobertura
pytest --cov=app --cov-report=html

# Ejecutar tipos específicos de pruebas
pytest -m unit          # Solo pruebas unitarias
pytest -m integration   # Solo pruebas de integración
pytest -m slow          # Solo pruebas lentas
```

### Estructura de Pruebas

```
tests/
├── conftest.py              # Fixtures globales
├── fixtures/
│   └── test_data.py         # Datos de prueba
├── unit/
│   ├── test_config.py       # Pruebas de configuración
│   ├── test_schemas.py      # Pruebas de esquemas
│   └── test_*.py           # Otras pruebas unitarias
└── integration/
    └── test_api.py          # Pruebas de integración de API
```

### Cobertura de Pruebas

El proyecto mantiene cobertura de pruebas del 80%+ en:
- Pruebas unitarias para todos los componentes
- Pruebas de integración para endpoints de API
- Escenarios de manejo de errores
- Características de rendimiento

## Rendimiento

### Puntos de Referencia

| Métrica | Valor |
|---------|-------|
| **Latencia** | < 2s (percentil 95) |
| **Rendimiento** | 100+ solicitudes/minuto |
| **Uso de Memoria** | < 512MB por instancia |
| **Tasa de Acierto de Caché** | > 80% |
| **Tiempo de Actividad** | 99.9% |

### Características de Optimización

- **Caché Redis**: Caché inteligente con TTL
- **Pool de Conexiones**: Conexiones de base de datos optimizadas
- **Procesamiento Asíncrono**: Operaciones I/O no bloqueantes
- **Límites de Recursos**: Restricciones de recursos Docker
- **Balanceamiento de Carga**: Proxy reverso Nginx

### Monitoreo

- **Verificaciones de Salud**: Monitoreo automatizado de servicios
- **Métricas**: Integración con Prometheus
- **Logging**: Logging JSON estructurado
- **Alertas**: Dashboards de Grafana

## Solución de Problemas

### Problemas Comunes

#### 1. Fallo de Autenticación de Clave API

**Error**: `401 No Autorizado`

**Solución**:
```bash
# Verificar formato de clave API
curl -H "Authorization: Bearer tu_clave_api" http://localhost:8000/v1/healthz

# Verificar clave API en entorno
echo $API_KEYS_ALLOWED
```

#### 2. Límite de Velocidad Excedido

**Error**: `429 Demasiadas Solicitudes`

**Solución**:
```bash
# Verificar headers de límite de velocidad
curl -I -H "Authorization: Bearer tu_clave_api" http://localhost:8000/v1/summarize

# Ajustar límites de velocidad en configuración
ENABLE_RATE_LIMIT=false  # Deshabilitar para pruebas
```

#### 3. Proveedor LLM No Disponible

**Error**: `503 Servicio No Disponible`

**Solución**:
```bash
# Verificar clave API de Gemini
curl -H "Authorization: Bearer $GEMINI_API_KEY" https://generativelanguage.googleapis.com/v1/models

# Verificar que el respaldo esté funcionando
# El servicio automáticamente recurre a TextRank
```

#### 4. Fallo de Conexión Redis

**Error**: Operaciones de caché fallando

**Solución**:
```bash
# Verificar conexión Redis
docker-compose exec redis redis-cli ping

# Verificar URL de Redis
echo $REDIS_URL
```

### Modo Debug

Habilitar logging de debug:

```bash
LOG_LEVEL=DEBUG docker-compose up
```

### Logs

Ver logs del servicio:

```bash
# Todos los servicios
docker-compose logs -f

# Servicio específico
docker-compose logs -f api

# Con marcas de tiempo
docker-compose logs -f -t api
```
