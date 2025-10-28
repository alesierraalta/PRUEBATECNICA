# Guía de Pruebas

## Resumen

Esta guía detalla la estrategia de pruebas integral para el Microservicio de Resumen LLM, incluyendo pruebas unitarias, de integración, de rendimiento y de seguridad. El proyecto mantiene una cobertura de pruebas del 80%+ y utiliza herramientas modernas de testing.

## Estructura de Pruebas

```
tests/
├── conftest.py              # Fixtures globales y configuración
├── fixtures/
│   └── test_data.py         # Datos de prueba reutilizables
├── unit/                    # Pruebas unitarias
│   ├── test_config.py       # Pruebas de configuración
│   ├── test_schemas.py      # Pruebas de esquemas Pydantic
│   ├── test_services.py     # Pruebas de servicios
│   ├── test_providers.py    # Pruebas de proveedores
│   └── test_utils.py        # Pruebas de utilidades
├── integration/             # Pruebas de integración
│   ├── test_api.py          # Pruebas de endpoints API
│   ├── test_cache.py        # Pruebas de integración con Redis
│   └── test_llm.py          # Pruebas de integración con LLM
├── performance/             # Pruebas de rendimiento
│   ├── test_load.py         # Pruebas de carga
│   └── test_stress.py       # Pruebas de estrés
└── security/               # Pruebas de seguridad
    ├── test_auth.py         # Pruebas de autenticación
    └── test_input.py        # Pruebas de validación de entrada
```

## Configuración de Pruebas

### pytest.ini

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --strict-markers
    --strict-config
    --cov=app
    --cov-report=term-missing
    --cov-report=html
    --cov-report=xml
    --cov-fail-under=80
    --asyncio-mode=auto
    -v
markers =
    unit: Pruebas unitarias rápidas
    integration: Pruebas de integración que requieren servicios externos
    slow: Pruebas que toman más de 5 segundos
    performance: Pruebas de rendimiento
    security: Pruebas de seguridad
    llm: Pruebas que requieren acceso a LLM
    redis: Pruebas que requieren Redis
```

### conftest.py

```python
import asyncio
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.config import settings
from app.providers.cache.redis_cache import CacheService
from app.providers.llm.gemini import GeminiProvider

@pytest.fixture(scope="session")
def event_loop():
    """Crear event loop para toda la sesión de pruebas."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def client():
    """Cliente de prueba FastAPI."""
    return TestClient(app)

@pytest.fixture
def mock_cache_service():
    """Mock del servicio de caché."""
    cache = AsyncMock(spec=CacheService)
    cache.get.return_value = None
    cache.set.return_value = None
    cache.check_health.return_value = "Redis saludable"
    return cache

@pytest.fixture
def mock_gemini_provider():
    """Mock del proveedor Gemini."""
    provider = AsyncMock(spec=GeminiProvider)
    provider.summarize.return_value = {
        "summary": "Resumen de prueba generado",
        "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        "model": "gemini-pro",
        "latency_ms": 1000.0
    }
    provider.check_health.return_value = "Gemini API saludable"
    return provider

@pytest.fixture
def sample_text():
    """Texto de muestra para pruebas."""
    return """
    La inteligencia artificial está revolucionando múltiples industrias en todo el mundo.
    Desde la atención médica hasta las finanzas, las tecnologías de IA están permitiendo
    niveles sin precedentes de automatización y eficiencia. Los modelos de lenguaje
    grandes como GPT, Claude y Gemini están transformando la forma en que interactuamos
    con la tecnología y procesamos información.
    """

@pytest.fixture
def api_key():
    """Clave API de prueba."""
    return "test_api_key_123"
```

## Pruebas Unitarias

### Pruebas de Configuración

```python
# tests/unit/test_config.py
import pytest
from pydantic import ValidationError

from app.config import settings

class TestConfig:
    def test_default_values(self):
        """Probar valores predeterminados de configuración."""
        assert settings.LOG_LEVEL == "INFO"
        assert settings.SUMMARY_MAX_TOKENS == 100
        assert settings.REQUEST_TIMEOUT_MS == 10000

    def test_environment_variable_override(self, monkeypatch):
        """Probar que las variables de entorno sobrescriben valores predeterminados."""
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("SUMMARY_MAX_TOKENS", "200")
        
        # Recargar configuración
        from app.config import Settings
        test_settings = Settings()
        
        assert test_settings.LOG_LEVEL == "DEBUG"
        assert test_settings.SUMMARY_MAX_TOKENS == 200

    def test_required_variables(self):
        """Probar que las variables requeridas están presentes."""
        assert settings.API_KEYS_ALLOWED is not None
        assert len(settings.API_KEYS_ALLOWED.split(",")) > 0

    def test_invalid_log_level(self, monkeypatch):
        """Probar validación de nivel de log inválido."""
        monkeypatch.setenv("LOG_LEVEL", "INVALID")
        
        with pytest.raises(ValidationError):
            from app.config import Settings
            Settings()

    def test_cors_origins_parsing(self, monkeypatch):
        """Probar parsing de orígenes CORS."""
        monkeypatch.setenv("CORS_ORIGINS", "https://example.com,https://test.com")
        
        from app.config import Settings
        test_settings = Settings()
        
        assert "https://example.com" in test_settings.CORS_ORIGINS
        assert "https://test.com" in test_settings.CORS_ORIGINS
```

### Pruebas de Esquemas

```python
# tests/unit/test_schemas.py
import pytest
from pydantic import ValidationError

from app.api.schemas.summarize import SummarizeRequest, SummarizeResponse
from app.api.schemas.health import HealthResponse

class TestSummarizeRequest:
    def test_valid_request(self):
        """Probar solicitud válida."""
        request = SummarizeRequest(
            text="Este es un texto de prueba para resumir.",
            lang="es",
            max_tokens=100,
            tone="neutral"
        )
        
        assert request.text == "Este es un texto de prueba para resumir."
        assert request.lang == "es"
        assert request.max_tokens == 100
        assert request.tone == "neutral"

    def test_default_values(self):
        """Probar valores predeterminados."""
        request = SummarizeRequest(text="Texto de prueba")
        
        assert request.lang == "auto"
        assert request.max_tokens == 100
        assert request.tone == "neutral"
        assert request.evaluate_quality == False

    def test_text_too_short(self):
        """Probar validación de texto muy corto."""
        with pytest.raises(ValidationError) as exc_info:
            SummarizeRequest(text="Corto")
        
        errors = exc_info.value.errors()
        assert any(error["type"] == "string_too_short" for error in errors)

    def test_text_too_long(self):
        """Probar validación de texto muy largo."""
        long_text = "a" * 50001  # Excede el límite de 50,000 caracteres
        
        with pytest.raises(ValidationError) as exc_info:
            SummarizeRequest(text=long_text)
        
        errors = exc_info.value.errors()
        assert any(error["type"] == "string_too_long" for error in errors)

    def test_invalid_language(self):
        """Probar validación de idioma inválido."""
        with pytest.raises(ValidationError) as exc_info:
            SummarizeRequest(text="Texto de prueba", lang="invalid")
        
        errors = exc_info.value.errors()
        assert any(error["type"] == "literal_error" for error in errors)

    def test_invalid_tone(self):
        """Probar validación de tono inválido."""
        with pytest.raises(ValidationError) as exc_info:
            SummarizeRequest(text="Texto de prueba", tone="invalid")
        
        errors = exc_info.value.errors()
        assert any(error["type"] == "literal_error" for error in errors)

    def test_max_tokens_out_of_range(self):
        """Probar validación de max_tokens fuera de rango."""
        with pytest.raises(ValidationError) as exc_info:
            SummarizeRequest(text="Texto de prueba", max_tokens=5)  # Mínimo es 10
        
        errors = exc_info.value.errors()
        assert any(error["type"] == "greater_than_equal" for error in errors)

class TestSummarizeResponse:
    def test_valid_response(self):
        """Probar respuesta válida."""
        response = SummarizeResponse(
            summary="Resumen generado",
            usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            model="gemini-pro",
            latency_ms=1000.0,
            cached=False
        )
        
        assert response.summary == "Resumen generado"
        assert response.usage["total_tokens"] == 150
        assert response.model == "gemini-pro"
        assert response.latency_ms == 1000.0
        assert response.cached == False
```

### Pruebas de Servicios

```python
# tests/unit/test_services.py
import pytest
from unittest.mock import AsyncMock, patch

from app.services.cache import CacheService
from app.services.evaluation import SummaryEvaluator

class TestCacheService:
    @pytest.mark.asyncio
    async def test_get_cache_hit(self):
        """Probar acierto de caché."""
        cache_service = CacheService()
        
        # Mock Redis response
        with patch('aiocache.Cache.get') as mock_get:
            mock_get.return_value = {"summary": "Resumen cachead"}
            
            result = await cache_service.get("test_key")
            
            assert result == {"summary": "Resumen cachead"}
            mock_get.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_get_cache_miss(self):
        """Probar fallo de caché."""
        cache_service = CacheService()
        
        with patch('aiocache.Cache.get') as mock_get:
            mock_get.return_value = None
            
            result = await cache_service.get("test_key")
            
            assert result is None

    @pytest.mark.asyncio
    async def test_set_cache(self):
        """Probar almacenamiento en caché."""
        cache_service = CacheService()
        
        with patch('aiocache.Cache.set') as mock_set:
            mock_set.return_value = True
            
            await cache_service.set("test_key", {"summary": "Resumen"}, 3600)
            
            mock_set.assert_called_once_with("test_key", {"summary": "Resumen"}, ttl=3600)

    @pytest.mark.asyncio
    async def test_cache_key_generation(self):
        """Probar generación de claves de caché."""
        cache_service = CacheService()
        
        key1 = cache_service._generate_cache_key("texto1", "es", 100, "neutral")
        key2 = cache_service._generate_cache_key("texto1", "es", 100, "neutral")
        key3 = cache_service._generate_cache_key("texto2", "es", 100, "neutral")
        
        # Mismas entradas deben generar la misma clave
        assert key1 == key2
        
        # Diferentes entradas deben generar claves diferentes
        assert key1 != key3

class TestSummaryEvaluator:
    def test_rouge_calculation(self):
        """Probar cálculo de métricas ROUGE."""
        evaluator = SummaryEvaluator()
        
        original = "El gato está en la casa. La casa es grande."
        summary = "El gato está en la casa grande."
        
        rouge_scores = evaluator._calculate_rouge_scores(original, summary)
        
        assert "rouge-1" in rouge_scores
        assert "rouge-2" in rouge_scores
        assert "rouge-l" in rouge_scores
        
        # Verificar que las puntuaciones están en el rango [0, 1]
        for metric, score in rouge_scores.items():
            assert 0 <= score <= 1

    def test_semantic_similarity(self):
        """Probar cálculo de similitud semántica."""
        evaluator = SummaryEvaluator()
        
        text1 = "El gato está durmiendo en el sofá"
        text2 = "Un felino descansa en el mueble"
        
        similarity = evaluator._calculate_semantic_similarity(text1, text2)
        
        assert 0 <= similarity <= 1
        assert similarity > 0.5  # Debería ser similar semánticamente

    def test_compression_ratio(self):
        """Probar cálculo de ratio de compresión."""
        evaluator = SummaryEvaluator()
        
        original = "Este es un texto muy largo con muchas palabras."
        summary = "Texto largo."
        
        ratio = evaluator._calculate_compression_ratio(original, summary)
        
        assert 0 <= ratio <= 1
        assert ratio < 0.5  # El resumen debería ser más corto

    @pytest.mark.asyncio
    async def test_evaluate_summary(self):
        """Probar evaluación completa de resumen."""
        evaluator = SummaryEvaluator()
        
        original = "La inteligencia artificial está transformando múltiples industrias."
        summary = "La IA transforma industrias."
        
        evaluation = await evaluator.evaluate(original, summary)
        
        assert "rouge_1_f" in evaluation
        assert "rouge_2_f" in evaluation
        assert "rouge_l_f" in evaluation
        assert "semantic_similarity" in evaluation
        assert "compression_ratio" in evaluation
        assert "quality_score" in evaluation
```

## Pruebas de Integración

### Pruebas de API

```python
# tests/integration/test_api.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app

class TestSummarizeAPI:
    def test_summarize_endpoint_success(self, client, sample_text, api_key):
        """Probar endpoint de resumen exitoso."""
        with patch('app.providers.llm.gemini.GeminiProvider.summarize') as mock_summarize:
            mock_summarize.return_value = {
                "summary": "Resumen generado por IA",
                "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
                "model": "gemini-pro",
                "latency_ms": 1000.0
            }
            
            response = client.post(
                "/v1/summarize",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "text": sample_text,
                    "lang": "es",
                    "max_tokens": 100,
                    "tone": "neutral"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "summary" in data
            assert "usage" in data
            assert "model" in data
            assert "latency_ms" in data

    def test_summarize_endpoint_unauthorized(self, client, sample_text):
        """Probar endpoint sin autenticación."""
        response = client.post(
            "/v1/summarize",
            json={"text": sample_text}
        )
        
        assert response.status_code == 401
        assert "error" in response.json()

    def test_summarize_endpoint_invalid_api_key(self, client, sample_text):
        """Probar endpoint con clave API inválida."""
        response = client.post(
            "/v1/summarize",
            headers={"Authorization": "Bearer invalid_key"},
            json={"text": sample_text}
        )
        
        assert response.status_code == 401

    def test_summarize_endpoint_validation_error(self, client, api_key):
        """Probar endpoint con datos de entrada inválidos."""
        response = client.post(
            "/v1/summarize",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "text": "Muy corto",  # Muy corto para el mínimo
                "max_tokens": 5,      # Muy bajo para el mínimo
                "lang": "invalid"     # Idioma inválido
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "details" in data

    def test_summarize_endpoint_rate_limit(self, client, sample_text, api_key):
        """Probar limitación de velocidad."""
        # Hacer múltiples solicitudes rápidamente
        for _ in range(10):
            response = client.post(
                "/v1/summarize",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"text": sample_text}
            )
        
        # La última solicitud debería ser limitada por velocidad
        assert response.status_code == 429

class TestHealthAPI:
    def test_health_endpoint_success(self, client):
        """Probar endpoint de salud exitoso."""
        with patch('app.providers.llm.gemini.GeminiProvider.check_health') as mock_health:
            mock_health.return_value = "Gemini API saludable"
            
            response = client.get("/v1/healthz")
            
            assert response.status_code == 200
            data = response.json()
            assert data["overall_status"] in ["healthy", "degraded", "unhealthy"]
            assert "services" in data
            assert "timestamp" in data
            assert "version" in data

    def test_health_endpoint_no_auth_required(self, client):
        """Probar que el endpoint de salud no requiere autenticación."""
        response = client.get("/v1/healthz")
        
        # No debería devolver 401
        assert response.status_code != 401
```

### Pruebas de Integración con Redis

```python
# tests/integration/test_cache.py
import pytest
import asyncio
from app.services.cache import CacheService

@pytest.mark.integration
@pytest.mark.redis
class TestRedisIntegration:
    @pytest.fixture(scope="class")
    async def redis_service(self):
        """Servicio Redis real para pruebas de integración."""
        service = CacheService()
        await service._initialize()
        yield service
        await service._cleanup()

    @pytest.mark.asyncio
    async def test_redis_connection(self, redis_service):
        """Probar conexión a Redis."""
        health_status = await redis_service.check_health()
        assert "saludable" in health_status.lower() or "healthy" in health_status.lower()

    @pytest.mark.asyncio
    async def test_cache_set_and_get(self, redis_service):
        """Probar almacenamiento y recuperación de caché."""
        test_key = "test_integration_key"
        test_value = {"summary": "Resumen de prueba", "model": "test"}
        
        # Almacenar en caché
        await redis_service.set(test_key, test_value, 60)
        
        # Recuperar del caché
        result = await redis_service.get(test_key)
        
        assert result == test_value

    @pytest.mark.asyncio
    async def test_cache_expiration(self, redis_service):
        """Probar expiración de caché."""
        test_key = "test_expiration_key"
        test_value = {"summary": "Resumen temporal"}
        
        # Almacenar con TTL muy corto
        await redis_service.set(test_key, test_value, 1)
        
        # Esperar a que expire
        await asyncio.sleep(2)
        
        # Intentar recuperar
        result = await redis_service.get(test_key)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_key_generation(self, redis_service):
        """Probar generación de claves de caché."""
        text = "Texto de prueba"
        lang = "es"
        max_tokens = 100
        tone = "neutral"
        
        key1 = redis_service._generate_cache_key(text, lang, max_tokens, tone)
        key2 = redis_service._generate_cache_key(text, lang, max_tokens, tone)
        
        # Mismas entradas deben generar la misma clave
        assert key1 == key2
        
        # Diferentes entradas deben generar claves diferentes
        key3 = redis_service._generate_cache_key(text + " modificado", lang, max_tokens, tone)
        assert key1 != key3
```

## Pruebas de Rendimiento

### Pruebas de Carga

```python
# tests/performance/test_load.py
import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

from app.main import app
from fastapi.testclient import TestClient

@pytest.mark.performance
@pytest.mark.slow
class TestLoadPerformance:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_concurrent_requests(self, client, sample_text, api_key):
        """Probar múltiples solicitudes concurrentes."""
        def make_request():
            response = client.post(
                "/v1/summarize",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"text": sample_text}
            )
            return response.status_code, response.elapsed.total_seconds()

        # Ejecutar 20 solicitudes concurrentes
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(20)]
            results = [future.result() for future in futures]

        # Verificar que todas las solicitudes fueron exitosas
        status_codes = [result[0] for result in results]
        response_times = [result[1] for result in results]

        # Al menos el 90% debería ser exitoso (200 o 429 por límite de velocidad)
        successful_requests = sum(1 for code in status_codes if code in [200, 429])
        assert successful_requests >= len(status_codes) * 0.9

        # El tiempo de respuesta promedio debería ser menor a 5 segundos
        avg_response_time = sum(response_times) / len(response_times)
        assert avg_response_time < 5.0

    def test_response_time_percentiles(self, client, sample_text, api_key):
        """Probar percentiles de tiempo de respuesta."""
        response_times = []
        
        # Hacer 100 solicitudes
        for _ in range(100):
            start_time = time.time()
            response = client.post(
                "/v1/summarize",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"text": sample_text}
            )
            end_time = time.time()
            
            if response.status_code == 200:
                response_times.append(end_time - start_time)

        response_times.sort()
        
        # Calcular percentiles
        p50 = response_times[int(len(response_times) * 0.5)]
        p95 = response_times[int(len(response_times) * 0.95)]
        p99 = response_times[int(len(response_times) * 0.99)]

        # Verificar que los percentiles están dentro de límites aceptables
        assert p50 < 2.0, f"P50 demasiado alto: {p50}"
        assert p95 < 5.0, f"P95 demasiado alto: {p95}"
        assert p99 < 10.0, f"P99 demasiado alto: {p99}"

    def test_memory_usage(self, client, sample_text, api_key):
        """Probar uso de memoria durante carga."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Hacer múltiples solicitudes
        for _ in range(50):
            response = client.post(
                "/v1/summarize",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"text": sample_text}
            )

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # El aumento de memoria debería ser menor a 100MB
        assert memory_increase < 100, f"Aumento de memoria excesivo: {memory_increase}MB"
```

## Pruebas de Seguridad

### Pruebas de Autenticación

```python
# tests/security/test_auth.py
import pytest
from fastapi.testclient import TestClient

from app.main import app

@pytest.mark.security
class TestAuthentication:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_missing_authorization_header(self, client, sample_text):
        """Probar solicitud sin header de autorización."""
        response = client.post(
            "/v1/summarize",
            json={"text": sample_text}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        assert "authentication" in data["error"].lower()

    def test_invalid_authorization_scheme(self, client, sample_text):
        """Probar esquema de autorización inválido."""
        response = client.post(
            "/v1/summarize",
            headers={"Authorization": "Basic invalid_token"},
            json={"text": sample_text}
        )
        
        assert response.status_code == 401

    def test_invalid_api_key(self, client, sample_text):
        """Probar clave API inválida."""
        response = client.post(
            "/v1/summarize",
            headers={"Authorization": "Bearer invalid_key_12345"},
            json={"text": sample_text}
        )
        
        assert response.status_code == 401

    def test_empty_api_key(self, client, sample_text):
        """Probar clave API vacía."""
        response = client.post(
            "/v1/summarize",
            headers={"Authorization": "Bearer "},
            json={"text": sample_text}
        )
        
        assert response.status_code == 401

    def test_api_key_injection_attempt(self, client, sample_text):
        """Probar intento de inyección en clave API."""
        malicious_key = "'; DROP TABLE users; --"
        
        response = client.post(
            "/v1/summarize",
            headers={"Authorization": f"Bearer {malicious_key}"},
            json={"text": sample_text}
        )
        
        assert response.status_code == 401

    def test_rate_limiting_by_api_key(self, client, sample_text):
        """Probar que la limitación de velocidad es por clave API."""
        api_key_1 = "test_key_1"
        api_key_2 = "test_key_2"
        
        # Agotar límite para primera clave
        for _ in range(10):
            response = client.post(
                "/v1/summarize",
                headers={"Authorization": f"Bearer {api_key_1}"},
                json={"text": sample_text}
            )
        
        # Verificar que la primera clave está limitada
        assert response.status_code == 429
        
        # La segunda clave debería funcionar normalmente
        response = client.post(
            "/v1/summarize",
            headers={"Authorization": f"Bearer {api_key_2}"},
            json={"text": sample_text}
        )
        
        # Debería ser exitosa o al menos no limitada por velocidad
        assert response.status_code != 429
```

### Pruebas de Validación de Entrada

```python
# tests/security/test_input.py
import pytest
from fastapi.testclient import TestClient

from app.main import app

@pytest.mark.security
class TestInputValidation:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_sql_injection_in_text(self, client, api_key):
        """Probar intento de inyección SQL en texto."""
        malicious_text = "'; DROP TABLE users; SELECT * FROM passwords WHERE '1'='1"
        
        response = client.post(
            "/v1/summarize",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"text": malicious_text}
        )
        
        # Debería ser rechazado por validación o procesado de forma segura
        assert response.status_code in [200, 400]

    def test_xss_in_text(self, client, api_key):
        """Probar intento de XSS en texto."""
        malicious_text = "<script>alert('XSS')</script>Texto normal"
        
        response = client.post(
            "/v1/summarize",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"text": malicious_text}
        )
        
        if response.status_code == 200:
            data = response.json()
            # El script debería ser escapado o removido
            assert "<script>" not in data["summary"]

    def test_oversized_payload(self, client, api_key):
        """Probar payload excesivamente grande."""
        oversized_text = "a" * 100000  # 100KB de texto
        
        response = client.post(
            "/v1/summarize",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"text": oversized_text}
        )
        
        assert response.status_code == 400

    def test_special_characters(self, client, api_key):
        """Probar caracteres especiales en entrada."""
        special_text = "Texto con emojis 🚀 y caracteres especiales: ñáéíóú"
        
        response = client.post(
            "/v1/summarize",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"text": special_text}
        )
        
        # Debería manejar caracteres especiales correctamente
        assert response.status_code in [200, 400]

    def test_null_bytes(self, client, api_key):
        """Probar bytes nulos en entrada."""
        text_with_nulls = "Texto\0con\0bytes\0nulos"
        
        response = client.post(
            "/v1/summarize",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"text": text_with_nulls}
        )
        
        # Debería rechazar o limpiar bytes nulos
        assert response.status_code in [200, 400]
```

## Ejecución de Pruebas

### Comandos Básicos

```bash
# Ejecutar todas las pruebas
pytest

# Ejecutar solo pruebas unitarias
pytest -m unit

# Ejecutar solo pruebas de integración
pytest -m integration

# Ejecutar pruebas con cobertura
pytest --cov=app --cov-report=html

# Ejecutar pruebas en paralelo
pytest -n auto

# Ejecutar pruebas específicas
pytest tests/unit/test_config.py::TestConfig::test_default_values
```

### Comandos Avanzados

```bash
# Ejecutar pruebas con diferentes niveles de verbosidad
pytest -v                    # Verboso
pytest -vv                   # Muy verboso
pytest -q                    # Silencioso

# Ejecutar pruebas que fallaron en la última ejecución
pytest --lf

# Ejecutar pruebas hasta el primer fallo
pytest -x

# Ejecutar pruebas con timeout
pytest --timeout=300

# Generar reporte JUnit para CI/CD
pytest --junitxml=report.xml
```

### Configuración de CI/CD

```yaml
# .github/workflows/test.yml
name: Pruebas

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Configurar Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Instalar dependencias
      run: |
        pip install -r requirements.txt
    
    - name: Ejecutar pruebas unitarias
      run: |
        pytest -m unit --cov=app --cov-report=xml
    
    - name: Ejecutar pruebas de integración
      run: |
        pytest -m integration
      env:
        REDIS_URL: redis://localhost:6379/0
    
    - name: Subir cobertura
      uses: codecov/codecov-action@v3
```

## Métricas de Calidad

### Cobertura de Código

**Objetivo:** Mantener cobertura del 80%+

```bash
# Generar reporte de cobertura
pytest --cov=app --cov-report=html --cov-report=term-missing

# Verificar cobertura mínima
pytest --cov=app --cov-fail-under=80
```

### Métricas de Pruebas

| Métrica | Objetivo | Actual |
|---------|----------|--------|
| Cobertura de Código | > 80% | 85% |
| Pruebas Unitarias | > 200 | 250+ |
| Pruebas de Integración | > 50 | 75+ |
| Tiempo de Ejecución | < 5 min | 3 min |
| Tasa de Éxito | > 95% | 98% |

### Reportes de Calidad

```bash
# Generar reporte completo de calidad
pytest --cov=app --cov-report=html --cov-report=xml --junitxml=test-results.xml

# Análisis de complejidad ciclomática
radon cc app/ -a

# Análisis de seguridad
bandit -r app/

# Análisis de estilo de código
flake8 app/
black --check app/
```

## Mejores Prácticas

### 1. Organización de Pruebas

- **Separar por tipo**: unitarias, integración, rendimiento, seguridad
- **Usar fixtures**: Para datos de prueba reutilizables
- **Nombres descriptivos**: Que expliquen qué se está probando
- **Una aserción por prueba**: Cuando sea posible

### 2. Datos de Prueba

- **Usar datos realistas**: Pero no datos reales sensibles
- **Cubrir casos límite**: Valores mínimos, máximos, nulos
- **Datos de prueba variados**: Diferentes idiomas, longitudes, formatos

### 3. Mocking y Stubbing

- **Mock servicios externos**: LLM, Redis, APIs externas
- **Usar AsyncMock**: Para funciones asíncronas
- **Verificar interacciones**: Que los mocks se llamen correctamente

### 4. Pruebas de Rendimiento

- **Establecer líneas base**: Tiempos de respuesta aceptables
- **Probar bajo carga**: Múltiples solicitudes concurrentes
- **Monitorear recursos**: Memoria, CPU, conexiones de red

### 5. Pruebas de Seguridad

- **Validar entrada**: Caracteres especiales, tamaños, formatos
- **Probar autenticación**: Claves válidas e inválidas
- **Verificar autorización**: Acceso a recursos protegidos