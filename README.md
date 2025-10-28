# Microservicio de Resumen LLM

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-green.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-Repository-black.svg)](https://github.com/alesierraalta/PRUEBATECNICA)

Un microservicio backend que recibe texto y devuelve un resumen generado por un modelo de lenguaje (LLM), priorizando latencia y confiabilidad según los requisitos del ejercicio.

## Tabla de Contenidos

- [Inicio Rápido](#inicio-rápido)
- [Arquitectura](#arquitectura)
- [Documentación de API](#documentación-de-api)
- [Configuración](#configuración)
- [Despliegue](#despliegue)
- [Latencia y Confiabilidad](#latencia-y-confiabilidad)

## Inicio Rápido

### Prerrequisitos

- **Docker & Docker Compose**
- **Clave API de Google Gemini**

### Instalación

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

3. **Ejecutar con Docker Compose**
   ```bash
   docker-compose up --build -d
   ```

4. **Acceder a la API**
   - API: http://localhost:8000
   - Documentación OpenAPI: http://localhost:8000/docs
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

### Claves API Disponibles

Para usar la aplicación, utiliza una de estas claves API en el header `Authorization`:

```bash
# Clave de prueba 1
Authorization: Bearer test_api_key_1

# Clave de prueba 2  
Authorization: Bearer test_api_key_2

# Clave de desarrollo
Authorization: Bearer dev_api_key_2024
```

**Nota**: Estas claves están configuradas en el archivo `.env` de ejemplo. Para producción, configura tus propias claves en la variable `API_KEYS_ALLOWED`.

### Ejemplo Práctico

```bash
# Ejemplo usando una de las claves disponibles
curl -X POST "http://localhost:8000/v1/summarize" \
  -H "Authorization: Bearer test_api_key_1" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "El cambio climático es uno de los desafíos más urgentes de nuestro tiempo. Los científicos han documentado un aumento constante en las temperaturas globales durante las últimas décadas, principalmente debido a las actividades humanas que liberan gases de efecto invernadero. Este fenómeno está causando cambios significativos en los patrones climáticos, incluyendo sequías más intensas, tormentas más frecuentes y el derretimiento de los casquetes polares. Las consecuencias del cambio climático ya son visibles en todo el mundo, afectando ecosistemas, economías y comunidades humanas. Para abordar este problema, se requieren acciones coordinadas a nivel global, incluyendo la reducción de emisiones de carbono, la transición a energías renovables y la implementación de políticas ambientales más estrictas.",
    "lang": "es",
    "max_tokens": 80,
    "tone": "concise"
  }'
```

## Arquitectura

El microservicio implementa la arquitectura requerida: **Cliente → API (FastAPI) → LLM Provider** con fallback extractivo.

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Aplicación    │───▶│   API FastAPI   │───▶│  Proveedor LLM  │
│     Cliente     │    │                 │    │   (Gemini)      │
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
                       │ (Cache Redis)   │
                       └─────────────────┘
```

### Componentes Principales

- **API**: Valida, autentica y llama al LLM
- **Proveedor LLM**: Google Gemini (único, configurable)
- **Fallback**: TextRank para resumen extractivo
- **Caché**: Redis para reducir latencia
- **Middleware**: Autenticación, rate limiting, logging JSON

## Documentación de API

La documentación interactiva está disponible en `/docs` cuando el servicio está ejecutándose.

### Autenticación

Todos los endpoints requieren autenticación con clave API:

```bash
Authorization: Bearer tu_clave_api_aqui
```

### Endpoints

#### POST /v1/summarize

Genera un resumen de texto usando LLM con fallback automático.

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
  "cached": false
}
```

#### GET /v1/healthz

Revisión del estado del servicio y conectividad al LLM.

**Respuesta:**
```json
{
  "status": "healthy",
  "timestamp": 1640995200.123,
  "services": {
    "llm_provider": {
      "status": "healthy",
      "response_time_ms": 150
    },
    "redis": {
      "status": "healthy",
      "response_time_ms": 5
    }
  }
}
```

### Manejo de Errores

Respuestas de error consistentes con códigos HTTP estándar:

- `200` - Éxito
- `400` - Solicitud Incorrecta (validación fallida)
- `401` - No Autorizado (clave API inválida)
- `429` - Demasiadas Solicitudes (rate limit excedido)
- `503` - Servicio No Disponible (LLM caído)

## Configuración

### Variables de Entorno Principales

| Variable | Descripción | Predeterminado | Requerido |
|----------|-------------|----------------|-----------|
| `API_KEYS_ALLOWED` | Claves API separadas por comas | - | Sí |
| `GEMINI_API_KEY` | Clave API de Google Gemini | - | Sí |
| `LLM_PROVIDER` | Proveedor LLM | `gemini` | No |
| `SUMMARY_MAX_TOKENS` | Máximo de tokens predeterminado | `100` | No |
| `LANG_DEFAULT` | Idioma predeterminado | `auto` | No |
| `REQUEST_TIMEOUT_MS` | Timeout de solicitud | `10000` | No |
| `ENABLE_RATE_LIMIT` | Habilitar rate limiting | `true` | No |
| `REDIS_URL` | URL de Redis (opcional) | `redis://localhost:6379/0` | No |

### Ejemplo de archivo `.env`

```bash
# API Keys
API_KEYS_ALLOWED="tu_clave_api_1,tu_clave_api_2"

# LLM Provider
LLM_PROVIDER="gemini"
GEMINI_API_KEY="tu_clave_gemini_api"

# Configuración
SUMMARY_MAX_TOKENS=100
LANG_DEFAULT="auto"
REQUEST_TIMEOUT_MS=10000

# Características opcionales
ENABLE_RATE_LIMIT=true
REDIS_URL="redis://redis:6379/0"
LOG_LEVEL="INFO"
```

## Despliegue

### Docker Compose (Recomendado)

```bash
# Despliegue completo
docker-compose up --build -d

# Verificar estado
docker-compose ps

# Ver logs
docker-compose logs -f
```

### Comandos Útiles

```bash
# Detener servicios
docker-compose down

# Reiniciar servicios
docker-compose restart

# Reconstruir imágenes
docker-compose up --build
```

## Latencia y Confiabilidad

Este microservicio está diseñado para cumplir con los objetivos de **baja latencia** y **alta confiabilidad** requeridos en el ejercicio.

### Optimizaciones para Latencia

**1. Caché Inteligente con Redis**
- Almacena respuestas de resumen para textos idénticos
- Reduce latencia de ~2000ms a ~50ms para solicitudes repetidas
- Tasa de acierto objetivo: >80%

**2. Procesamiento Asíncrono**
- FastAPI con `async/await` para operaciones no bloqueantes
- Pool de conexiones HTTP para minimizar overhead
- Procesamiento concurrente de múltiples solicitudes

**3. Optimización de LLM**
- Timeout configurable (8s por defecto) para evitar esperas largas
- Retry automático con backoff exponencial (hasta 2 reintentos)
- Fallback extractivo (TextRank) si el LLM falla

### Mecanismos de Confiabilidad

**1. Fallback Automático**
- Si Google Gemini falla → TextRank (resumen extractivo)
- Si Redis falla → servicio continúa sin caché
- Timeouts: cliente 10s, LLM 8s

**2. Manejo Robusto de Errores**
- Retry automático en errores 429/5xx (hasta 2 reintentos)
- Logs JSON estructurados para debugging
- Health checks integrales en `/v1/healthz`

**3. Rate Limiting y Seguridad**
- Limitación de velocidad por API key (opcional con Redis)
- Validación estricta de entrada (≤50k caracteres)
- Autenticación obligatoria con API Key
- Headers de seguridad automáticos

### Métricas Objetivo

| Métrica | Objetivo | Implementación |
|---------|----------|-----------------|
| **Latencia P95** | < 2000ms | Caché Redis + async |
| **Disponibilidad** | > 99% | Fallback automático |
| **Tasa de Éxito** | > 95% | Retry + fallback |
| **Memoria** | < 512MB | Optimización de modelos |

### Arquitectura de Resiliencia

```
Cliente → API Gateway → FastAPI → LLM Provider
                ↓              ↓
            Rate Limit    Fallback (TextRank)
                ↓              ↓
            Redis Cache ← Evaluación Opcional
```

**Flujo de Recuperación:**
1. **LLM falla** → Retry automático (2x)
2. **Retry falla** → TextRank como fallback
3. **Redis falla** → Servicio continúa sin caché
4. **Rate limit** → Respuesta 429 con headers informativos

## Soporte

- **Documentación API**: http://localhost:8000/docs
- **Issues**: [GitHub Issues](https://github.com/alesierraalta/PRUEBATECNICA/issues)
- **Repositorio**: [GitHub Repository](https://github.com/alesierraalta/PRUEBATECNICA)

---

**Microservicio de Resumen LLM - Prueba Técnica**