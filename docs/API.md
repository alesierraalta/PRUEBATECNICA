# Documentación de API

## Resumen

El Microservicio de Resumen LLM proporciona una API RESTful para resumen inteligente de texto usando modelos de IA avanzados. La API está construida con FastAPI y proporciona documentación integral, validación y manejo de errores.

## URL Base

- **Desarrollo**: `http://localhost:8000`
- **Producción**: `https://tu-dominio.com`

## Autenticación

Todos los endpoints de API requieren autenticación usando claves API en el header `Authorization`:

```http
Authorization: Bearer tu_clave_api_aqui
```

### Gestión de Claves API

- Las claves API se configuran a través de la variable de entorno `API_KEYS_ALLOWED`
- Se pueden configurar múltiples claves (separadas por comas)
- Las claves se validan en cada solicitud
- Las claves inválidas devuelven `401 No Autorizado`

## Endpoints

### POST /v1/summarize

Resumir texto usando IA con manejo integral de errores y mecanismos de respaldo.

#### Solicitud

**Headers:**
```http
Authorization: Bearer tu_clave_api_aqui
Content-Type: application/json
```

**Cuerpo:**
```json
{
  "text": "string (requerido, 10-50000 caracteres)",
  "lang": "string (opcional, predeterminado: 'auto')",
  "max_tokens": "integer (opcional, predeterminado: 100, rango: 10-500)",
  "tone": "string (opcional, predeterminado: 'neutral')"
}
```

**Parámetros:**

| Parámetro | Tipo | Requerido | Predeterminado | Descripción |
|-----------|------|-----------|----------------|-------------|
| `text` | string | Sí | - | Texto para resumir (10-50,000 caracteres) |
| `lang` | string | No | "auto" | Idioma objetivo (auto, en, es, fr, de, etc.) |
| `max_tokens` | integer | No | 100 | Máximo de tokens en el resumen (10-500) |
| `tone` | string | No | "neutral" | Estilo del resumen (neutral, concise, bullet) |

**Idiomas Soportados:**
- `auto` - Detección automática
- `en` - Inglés
- `es` - Español
- `fr` - Francés
- `de` - Alemán
- `it` - Italiano
- `pt` - Portugués
- `ru` - Ruso
- `ja` - Japonés
- `ko` - Coreano
- `zh` - Chino

**Tonos Soportados:**
- `neutral` - Resumen equilibrado e informativo
- `concise` - Resumen breve y condensado
- `bullet` - Puntos estructurados

#### Respuesta

**Respuesta de Éxito (200 OK):**
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

**Campos de Respuesta:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `summary` | string | Texto del resumen generado |
| `usage` | object | Estadísticas de uso de tokens |
| `usage.prompt_tokens` | integer | Tokens usados en la entrada |
| `usage.completion_tokens` | integer | Tokens generados |
| `usage.total_tokens` | integer | Total de tokens usados |
| `model` | string | Modelo usado para la generación |
| `latency_ms` | integer | Tiempo de procesamiento en milisegundos |
| `evaluation` | object | Métricas de calidad (si está habilitado) |
| `evaluation.rouge_1_f` | float | Puntuación ROUGE-1 F (0-1) |
| `evaluation.rouge_2_f` | float | Puntuación ROUGE-2 F (0-1) |
| `evaluation.rouge_l_f` | float | Puntuación ROUGE-L F (0-1) |
| `evaluation.semantic_similarity` | float | Similitud semántica (0-1) |
| `evaluation.compression_ratio` | float | Ratio de compresión (0-1) |
| `evaluation.quality_score` | float | Puntuación de calidad compuesta (0-1) |
| `cached` | boolean | Si el resultado fue servido desde caché |

#### Respuestas de Error

**400 Solicitud Incorrecta - Error de Validación:**
```json
{
  "error": "validation_error",
  "message": "Texto muy corto (3 palabras). Mínimo 5 palabras requeridas / Text too short (3 words). Minimum 5 words required",
  "details": [
    {
      "loc": ["body", "text"],
      "msg": "Texto muy corto",
      "type": "value_error"
    }
  ],
  "timestamp": 1640995200.123,
  "request_id": "uuid-aqui"
}
```

**401 No Autorizado - Error de Autenticación:**
```json
{
  "error": "authentication_error",
  "message": "Clave API inválida / Invalid API key",
  "timestamp": 1640995200.123,
  "request_id": "uuid-aqui"
}
```

**429 Demasiadas Solicitudes - Límite de Velocidad Excedido:**
```json
{
  "error": "rate_limit_exceeded",
  "message": "Límite de velocidad excedido (100/minuto) / Rate limit exceeded (100/minute)",
  "retry_after": 60,
  "timestamp": 1640995200.123,
  "request_id": "uuid-aqui"
}
```

**503 Servicio No Disponible - Error del Proveedor LLM:**
```json
{
  "error": "service_unavailable",
  "message": "Servicio de resumen temporalmente no disponible / Summarization service temporarily unavailable",
  "timestamp": 1640995200.123,
  "request_id": "uuid-aqui"
}
```

### GET /v1/healthz

Verificación integral de salud para todos los componentes del servicio.

#### Solicitud

**Headers:**
```http
Content-Type: application/json
```

**Nota:** No se requiere autenticación para verificaciones de salud.

#### Respuesta

**Respuesta de Éxito (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": 1640995200.123,
  "services": {
    "llm_provider": {
      "status": "healthy",
      "response_time_ms": 150,
      "details": {
        "model": "gemini-pro",
        "provider": "gemini"
      }
    },
    "redis": {
      "status": "healthy",
      "response_time_ms": 5,
      "details": {
        "connected_clients": 10,
        "memory_usage": "2.5MB"
      }
    },
    "evaluation_service": {
      "status": "healthy",
      "response_time_ms": 200,
      "details": {
        "model": "all-MiniLM-L6-v2"
      }
    }
  },
  "version": "1.0.0",
  "uptime_seconds": 86400.0
}
```

**Respuesta Degradada (200 OK):**
```json
{
  "status": "degraded",
  "timestamp": 1640995200.123,
  "services": {
    "llm_provider": {
      "status": "healthy",
      "response_time_ms": 150
    },
    "redis": {
      "status": "unhealthy",
      "response_time_ms": 5000,
      "error": "Timeout de conexión"
    }
  },
  "version": "1.0.0",
  "uptime_seconds": 86400.0
}
```

**Respuesta No Saludable (503 Servicio No Disponible):**
```json
{
  "status": "unhealthy",
  "timestamp": 1640995200.123,
  "services": {
    "llm_provider": {
      "status": "unhealthy",
      "response_time_ms": 10000,
      "error": "Clave API inválida"
    },
    "redis": {
      "status": "unhealthy",
      "response_time_ms": 5000,
      "error": "Conexión rechazada"
    }
  },
  "version": "1.0.0",
  "uptime_seconds": 86400.0
}
```

**Niveles de Estado de Salud:**
- `healthy` - Todos los servicios operativos
- `degraded` - Algunos servicios tienen problemas pero la funcionalidad principal funciona
- `unhealthy` - Servicios críticos no disponibles

### GET /

Endpoint raíz con información básica de la API.

#### Respuesta

```json
{
  "message": "API de Resumen LLM",
  "version": "1.0.0",
  "status": "operacional",
  "timestamp": 1640995200.123,
  "docs_url": "/docs",
  "health_url": "/v1/healthz"
}
```

### GET /health

Endpoint simple de verificación de salud para balanceadores de carga.

#### Respuesta

```json
{
  "status": "healthy",
  "timestamp": 1640995200.123
}
```

## Limitación de Velocidad

La API implementa limitación de velocidad por clave API para asegurar uso justo.

### Headers de Limitación de Velocidad

Todas las respuestas incluyen información de limitación de velocidad:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

### Configuración de Limitación de Velocidad

- **Límite Predeterminado**: 100 solicitudes por minuto
- **Ventana**: 60 segundos (ventana deslizante)
- **Clave**: Por clave API
- **Almacenamiento**: Contadores respaldados por Redis

### Límite de Velocidad Excedido

Cuando se excede el límite de velocidad:

```http
HTTP/1.1 429 Demasiadas Solicitudes
Retry-After: 60
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1640995200
```

## Manejo de Errores

La API proporciona respuestas de error consistentes con mensajes bilingües e información detallada.

### Formato de Respuesta de Error

```json
{
  "error": "tipo_error",
  "message": "Mensaje de error bilingüe / Bilingual error message",
  "timestamp": 1640995200.123,
  "request_id": "uuid-aqui",
  "details": {}
}
```

### Tipos de Error

| Tipo de Error | Estado HTTP | Descripción |
|---------------|-------------|-------------|
| `validation_error` | 400 | Fallo de validación de solicitud |
| `authentication_error` | 401 | Clave API inválida o faltante |
| `rate_limit_exceeded` | 429 | Límite de velocidad excedido |
| `service_unavailable` | 503 | Servicio temporalmente no disponible |
| `internal_server_error` | 500 | Error inesperado del servidor |

### ID de Solicitud

Cada solicitud recibe un identificador único para seguimiento y depuración:

```http
X-Request-ID: uuid-aqui
```

## Ejemplos

### Resumen Básico

```bash
curl -X POST "http://localhost:8000/v1/summarize" \
  -H "Authorization: Bearer tu_clave_api" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "La inteligencia artificial está revolucionando industrias en todo el mundo. Desde la atención médica hasta las finanzas, las tecnologías de IA están permitiendo niveles sin precedentes de automatización y eficiencia.",
    "lang": "es",
    "max_tokens": 50,
    "tone": "concise"
  }'
```

### Resumen Multiidioma

```bash
curl -X POST "http://localhost:8000/v1/summarize" \
  -H "Authorization: Bearer tu_clave_api" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "La inteligencia artificial está revolucionando las industrias en todo el mundo. Desde la atención médica hasta las finanzas, las tecnologías de IA están permitiendo niveles sin precedentes de automatización y eficiencia.",
    "lang": "es",
    "max_tokens": 100,
    "tone": "neutral"
  }'
```

### Resumen en Puntos

```bash
curl -X POST "http://localhost:8000/v1/summarize" \
  -H "Authorization: Bearer tu_clave_api" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Tu texto largo aquí...",
    "lang": "auto",
    "max_tokens": 200,
    "tone": "bullet"
  }'
```

### Verificación de Salud

```bash
curl -X GET "http://localhost:8000/v1/healthz"
```

## Ejemplos de SDK

### Python

```python
import requests

class ClienteResumenLLM:
    def __init__(self, url_base, clave_api):
        self.url_base = url_base
        self.headers = {
            "Authorization": f"Bearer {clave_api}",
            "Content-Type": "application/json"
        }
    
    def resumir(self, texto, idioma="auto", max_tokens=100, tono="neutral"):
        respuesta = requests.post(
            f"{self.url_base}/v1/summarize",
            headers=self.headers,
            json={
                "text": texto,
                "lang": idioma,
                "max_tokens": max_tokens,
                "tone": tono
            }
        )
        respuesta.raise_for_status()
        return respuesta.json()
    
    def verificar_salud(self):
        respuesta = requests.get(f"{self.url_base}/v1/healthz")
        respuesta.raise_for_status()
        return respuesta.json()

# Uso
cliente = ClienteResumenLLM("http://localhost:8000", "tu_clave_api")
resultado = cliente.resumir("Tu texto aquí...")
print(resultado["summary"])
```

### JavaScript/Node.js

```javascript
class ClienteResumenLLM {
    constructor(urlBase, claveApi) {
        this.urlBase = urlBase;
        this.headers = {
            'Authorization': `Bearer ${claveApi}`,
            'Content-Type': 'application/json'
        };
    }
    
    async resumir(texto, idioma = 'auto', maxTokens = 100, tono = 'neutral') {
        const respuesta = await fetch(`${this.urlBase}/v1/summarize`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify({
                texto,
                idioma,
                max_tokens: maxTokens,
                tono
            })
        });
        
        if (!respuesta.ok) {
            throw new Error(`Error HTTP! estado: ${respuesta.status}`);
        }
        
        return await respuesta.json();
    }
    
    async verificarSalud() {
        const respuesta = await fetch(`${this.urlBase}/v1/healthz`);
        if (!respuesta.ok) {
            throw new Error(`Error HTTP! estado: ${respuesta.status}`);
        }
        return await respuesta.json();
    }
}

// Uso
const cliente = new ClienteResumenLLM('http://localhost:8000', 'tu_clave_api');
const resultado = await cliente.resumir('Tu texto aquí...');
console.log(resultado.summary);
```

## Documentación OpenAPI

La documentación interactiva de la API está disponible en:

- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`
- **Esquema OpenAPI**: `/openapi.json`

## Mejores Prácticas

### 1. Manejo de Errores

Siempre maneja errores potenciales en tu código cliente:

```python
try:
    resultado = cliente.resumir(texto)
    print(resultado["summary"])
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 429:
        print("Límite de velocidad excedido, reintentar más tarde")
    elif e.response.status_code == 401:
        print("Clave API inválida")
    else:
        print(f"Error de API: {e}")
```

### 2. Limitación de Velocidad

Respeta los límites de velocidad e implementa retroceso exponencial:

```python
import time
import random

def resumir_con_reintento(cliente, texto, max_reintentos=3):
    for intento in range(max_reintentos):
        try:
            return cliente.resumir(texto)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                retry_after = int(e.response.headers.get('Retry-After', 60))
                tiempo_espera = retry_after + random.uniform(0, 10)
                time.sleep(tiempo_espera)
            else:
                raise
    raise Exception("Máximo de reintentos excedido")
```

### 3. Caché

Aprovecha el caché integrado para solicitudes repetidas:

```python
# Primera solicitud - será cachead
resultado1 = cliente.resumir("Mismo contenido de texto")

# Segunda solicitud - servida desde caché (más rápido)
resultado2 = cliente.resumir("Mismo contenido de texto")
```

### 4. Monitoreo de Salud

Implementa verificaciones de salud en tu aplicación:

```python
def verificar_salud_servicio(cliente):
    try:
        salud = cliente.verificar_salud()
        if salud["status"] == "healthy":
            return True
        else:
            print(f"Servicio degradado: {salud}")
            return False
    except Exception as e:
        print(f"Verificación de salud falló: {e}")
        return False
```