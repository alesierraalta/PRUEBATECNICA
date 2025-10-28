# Arquitectura del Sistema

## Resumen

El Microservicio de Resumen LLM está diseñado con una arquitectura en capas que enfatiza la separación de responsabilidades, escalabilidad y mantenibilidad. La arquitectura sigue principios de diseño modernos incluyendo inyección de dependencias, manejo integral de errores y patrones de resilencia.

## Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                        Cliente                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   Web App   │  │  Mobile App │  │   API Client│            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Capa de Infraestructura                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   Nginx     │  │   Docker    │  │   Scripts   │            │
│  │ (Proxy Rev) │  │ (Container) │  │(Automatiz.) │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Capa de API                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   FastAPI   │  │ Middleware  │  │ Validación  │            │
│  │ (Framework) │  │   Stack     │  │ (Pydantic)  │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Capa de Servicios                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   Caché     │  │ Evaluación  │  │  Logging    │            │
│  │  (Redis)    │  │ (ROUGE)     │  │(Structlog)  │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Capa de Proveedores                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   LLM       │  │  Respaldo   │  │  Externo    │            │
│  │ (Gemini)    │  │(TextRank)   │  │   APIs      │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

## Componentes Principales

### 1. Capa de API (FastAPI)

**Responsabilidades:**
- Manejo de solicitudes HTTP
- Validación de entrada con Pydantic
- Serialización de respuestas
- Documentación automática (OpenAPI/Swagger)

**Componentes:**
- **Routers**: Endpoints organizados por funcionalidad
- **Schemas**: Modelos de datos con validación
- **Dependencies**: Inyección de dependencias
- **Exception Handlers**: Manejo global de errores

```python
# Ejemplo de estructura de router
@router.post("/v1/summarize", response_model=SummarizeResponse)
async def summarize_text(
    request: SummarizeRequest,
    llm_provider: LLMProvider = Depends(get_llm_provider),
    cache_service: CacheService = Depends(get_cache_service)
) -> SummarizeResponse:
    # Lógica del endpoint
```

### 2. Middleware Stack

**Orden de Ejecución:**
1. **Logging Middleware** - Registro de solicitudes/respuestas
2. **CORS Middleware** - Manejo de Cross-Origin Resource Sharing
3. **Authentication Middleware** - Validación de claves API
4. **Rate Limiting Middleware** - Control de velocidad
5. **Error Handler Middleware** - Manejo global de errores

**Características:**
- Procesamiento asíncrono
- Manejo de errores robusto
- Logging estructurado
- Headers de seguridad automáticos

### 3. Capa de Servicios

#### Servicio de Caché (Redis)

**Propósito:**
- Almacenamiento temporal de resultados
- Reducción de llamadas a LLM
- Mejora de rendimiento

**Implementación:**
```python
class CacheService:
    async def get(self, key: str) -> Optional[dict]:
        # Obtener del caché
    
    async def set(self, key: str, value: dict, ttl: int) -> None:
        # Almacenar en caché
    
    async def check_health(self) -> str:
        # Verificar salud del servicio
```

#### Servicio de Evaluación

**Propósito:**
- Evaluación automática de calidad de resúmenes
- Métricas ROUGE (ROUGE-1, ROUGE-2, ROUGE-L)
- Similitud semántica usando Sentence Transformers

**Implementación:**
```python
class SummaryEvaluator:
    def __init__(self):
        self.rouge = Rouge()
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    async def evaluate(self, original: str, summary: str) -> EvaluationMetrics:
        # Calcular métricas de calidad
```

### 4. Capa de Proveedores

#### Proveedor LLM (Gemini)

**Características:**
- Integración con Google Gemini API
- Manejo de reintentos con backoff exponencial
- Timeouts configurables
- Manejo de errores específicos

**Implementación:**
```python
class GeminiProvider(BaseLLMProvider):
    @stamina.retry(
        on=Exception,
        attempts=3,
        wait_initial=1.0,
        wait_max=8.0,
        wait_exp_base=2.0
    )
    async def summarize(self, text: str, **kwargs) -> SummaryResult:
        # Llamada a Gemini API
```

#### Proveedor de Respaldo (TextRank)

**Propósito:**
- Respaldo cuando el LLM no está disponible
- Algoritmo extractivo basado en grafos
- Funciona sin dependencias externas

**Implementación:**
```python
class ExtractiveFallbackProvider(BaseLLMProvider):
    async def summarize(self, text: str, **kwargs) -> SummaryResult:
        # Implementación de TextRank
        summarizer = TextRankSummarizer()
        summary = summarizer(text, sentences_count=sentences_count)
```

## Patrones de Diseño

### 1. Inyección de Dependencias

**Beneficios:**
- Código más testeable
- Acoplamiento reducido
- Configuración flexible

**Implementación:**
```python
def get_llm_provider() -> BaseLLMProvider:
    if settings.LLM_PROVIDER == "gemini":
        return GeminiProvider()
    elif settings.LLM_PROVIDER == "fallback":
        return ExtractiveFallbackProvider()
    else:
        raise ValueError(f"Proveedor LLM no soportado: {settings.LLM_PROVIDER}")
```

### 2. Patrón Strategy

**Aplicación:**
- Selección dinámica de proveedores LLM
- Diferentes estrategias de evaluación
- Múltiples formatos de salida

### 3. Patrón Circuit Breaker

**Implementación:**
- Detección de fallos del proveedor LLM
- Cambio automático a respaldo
- Recuperación gradual

### 4. Patrón Repository

**Aplicación:**
- Abstracción de acceso a datos
- Intercambiabilidad de almacenes
- Caché transparente

## Flujo de Datos

### Flujo de Solicitud de Resumen

```
1. Cliente → Solicitud HTTP POST /v1/summarize
2. Nginx → Proxy reverso + limitación de velocidad
3. FastAPI → Validación de entrada (Pydantic)
4. Middleware → Autenticación + logging
5. Servicio → Verificación de caché
6. Proveedor LLM → Generación de resumen
7. Evaluador → Cálculo de métricas de calidad
8. Caché → Almacenamiento del resultado
9. Respuesta → Serialización JSON
```

### Flujo de Manejo de Errores

```
1. Error Detectado → En cualquier capa
2. Logging → Registro estructurado del error
3. Clasificación → Tipo de error (validación, autenticación, etc.)
4. Respuesta → Formato JSON consistente
5. Headers → Información adicional (retry-after, etc.)
```

## Escalabilidad

### Escalabilidad Horizontal

**Estrategias:**
- Múltiples instancias de aplicación
- Balanceador de carga (Nginx)
- Caché distribuido (Redis Cluster)
- Base de datos compartida

**Implementación:**
```yaml
# docker-compose.prod.yml
services:
  api:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
```

### Escalabilidad Vertical

**Optimizaciones:**
- Pool de conexiones optimizado
- Caché en memoria
- Procesamiento asíncrono
- Lazy loading de modelos ML

## Seguridad

### Autenticación y Autorización

**Implementación:**
- Claves API con hash SHA-256
- Validación en cada solicitud
- Logging seguro (sin exposición de claves)

### Protección de Datos

**Medidas:**
- Validación de entrada estricta
- Sanitización de datos
- Logging sin información sensible
- Headers de seguridad automáticos

### Rate Limiting

**Características:**
- Límites por clave API
- Ventana deslizante
- Almacenamiento en Redis
- Headers informativos

## Monitoreo y Observabilidad

### Logging Estructurado

**Formato JSON:**
```json
{
  "timestamp": "2023-10-27T10:00:00Z",
  "level": "INFO",
  "event": "request_completed",
  "request_id": "uuid-aqui",
  "method": "POST",
  "path": "/v1/summarize",
  "status_code": 200,
  "latency_ms": 1250.5,
  "api_key_hash": "abc123..."
}
```

### Métricas

**Métricas Clave:**
- Latencia de solicitudes (percentiles)
- Tasa de error por endpoint
- Uso de recursos (CPU, memoria)
- Tasa de acierto de caché
- Disponibilidad del servicio

### Health Checks

**Verificaciones:**
- Conectividad LLM
- Estado de Redis
- Carga de modelos ML
- Recursos del sistema

## Resilencia y Recuperación

### Manejo de Fallos

**Estrategias:**
- Reintentos con backoff exponencial
- Circuit breaker para LLM
- Respaldo automático (TextRank)
- Degradación gradual

### Timeouts

**Configuración:**
- Timeout de solicitud: 10 segundos
- Timeout de LLM: 8 segundos
- Timeout de caché: 2 segundos
- Timeout de evaluación: 5 segundos

### Recuperación Automática

**Mecanismos:**
- Reconexión automática a Redis
- Recarga de modelos ML
- Limpieza de caché corrupto
- Restart de servicios

## Consideraciones de Rendimiento

### Optimizaciones de Código

**Técnicas:**
- Procesamiento asíncrono (async/await)
- Pool de conexiones HTTP
- Caché de modelos ML
- Compresión de respuestas

### Optimizaciones de Infraestructura

**Configuraciones:**
- Nginx con compresión gzip
- Redis con persistencia optimizada
- Docker con multi-stage builds
- Scripts de automatización para escalado

### Benchmarks

**Métricas Objetivo:**
- Latencia P95: < 2 segundos
- Rendimiento: 100+ RPS
- Uso de memoria: < 512MB por instancia
- Tasa de acierto de caché: > 80%

## Decisiones Arquitectónicas

### ADR-001: Elección de FastAPI

**Decisión:** Usar FastAPI como framework web principal

**Justificación:**
- Rendimiento superior (comparable a Node.js)
- Documentación automática (OpenAPI)
- Validación integrada (Pydantic)
- Soporte nativo para async/await
- Type hints integrados

### ADR-002: Redis como Caché

**Decisión:** Usar Redis para almacenamiento de caché

**Justificación:**
- Rendimiento excepcional
- Estructuras de datos ricas
- Persistencia opcional
- Soporte para clustering
- Ecosistema maduro

### ADR-003: Arquitectura en Capas

**Decisión:** Implementar arquitectura en capas

**Justificación:**
- Separación clara de responsabilidades
- Facilidad de testing
- Mantenibilidad mejorada
- Escalabilidad horizontal
- Reutilización de código

### ADR-004: Manejo de Errores Centralizado

**Decisión:** Implementar manejo global de errores

**Justificación:**
- Consistencia en respuestas de error
- Logging centralizado
- Manejo de errores no capturados
- Información de debugging
- Experiencia de usuario mejorada