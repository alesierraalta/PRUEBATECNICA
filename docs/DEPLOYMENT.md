# Guía de Despliegue

## Resumen

Esta guía proporciona instrucciones para desplegar el Microservicio de Resumen LLM usando Docker Compose.

## Prerrequisitos

### Requisitos del Sistema
- **Sistema Operativo**: Linux, macOS, o Windows con WSL2
- **RAM**: Mínimo 2GB disponibles
- **Espacio en Disco**: Mínimo 1GB libre
- **CPU**: 2+ cores recomendados

### Requisitos de Software
- **Docker**: Versión 20.10+ 
- **Docker Compose**: Versión 2.0+
- **Git**: Para clonar el repositorio

### Requisitos de Servicios Externos
- **Clave API de Google Gemini**: Para el proveedor LLM
- **Redis**: Opcional, se ejecuta automáticamente con Docker Compose

## Despliegue Local

### Instalación con Docker Compose

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

3. **Construir y ejecutar**
   ```bash
   docker-compose up --build -d
   ```

4. **Verificar el despliegue**
   ```bash
   # Verificar que los servicios estén ejecutándose
   docker-compose ps
   
   # Verificar salud del servicio
   curl http://localhost:8000/v1/healthz
   ```

5. **Acceder a la documentación**
   - API Docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Comandos Útiles

```bash
# Ver logs en tiempo real
docker-compose logs -f

# Detener servicios
docker-compose down

# Reiniciar servicios
docker-compose restart

# Reconstruir imágenes
docker-compose up --build
```

## Configuración

### Variables de Entorno Principales

| Variable | Descripción | Requerido | Predeterminado |
|----------|-------------|-----------|----------------|
| `API_KEYS_ALLOWED` | Claves API permitidas | Sí | - |
| `GEMINI_API_KEY` | Clave API de Google Gemini | Sí | - |
| `LLM_PROVIDER` | Proveedor LLM | No | `gemini` |
| `REDIS_URL` | URL de Redis | No | `redis://redis:6379/0` |
| `ENABLE_RATE_LIMIT` | Habilitar rate limiting | No | `true` |
| `LOG_LEVEL` | Nivel de logging | No | `INFO` |

### Ejemplo de archivo `.env`

```bash
# API Keys
API_KEYS_ALLOWED="tu_clave_api_1,tu_clave_api_2"

# LLM Provider
LLM_PROVIDER="gemini"
GEMINI_API_KEY="tu_clave_gemini_api"

# Redis (opcional)
REDIS_URL="redis://redis:6379/0"
ENABLE_RATE_LIMIT="true"

# Logging
LOG_LEVEL="INFO"
```

## Verificación del Despliegue

### Health Check

```bash
curl http://localhost:8000/v1/healthz
```

Respuesta esperada:
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

### Prueba de Funcionalidad

```bash
curl -X POST "http://localhost:8000/v1/summarize" \
  -H "Authorization: Bearer tu_clave_api" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Este es un texto de prueba para verificar que el servicio funciona correctamente.",
    "lang": "es",
    "max_tokens": 50,
    "tone": "neutral"
  }'
```

## Solución de Problemas

### Problema: Servicio No Inicia

**Verificar logs:**
```bash
docker-compose logs api
```

**Causas comunes:**
- Variables de entorno faltantes o incorrectas
- Puerto 8000 ya en uso
- Problemas con la clave API de Gemini

### Problema: Errores de Conectividad

**Verificar Redis:**
```bash
docker-compose exec redis redis-cli ping
```

**Verificar conectividad externa:**
```bash
docker-compose exec api curl -I https://generativelanguage.googleapis.com
```

### Problema: Alto Uso de Memoria

**Verificar uso de recursos:**
```bash
docker stats
```

**Soluciones:**
- Reducir `SUMMARY_MAX_TOKENS`
- Deshabilitar evaluación automática (`ENABLE_AUTO_EVALUATION=false`)
- Aumentar límites de memoria en Docker

## Soporte

- **Documentación API**: http://localhost:8000/docs
- **Issues**: [GitHub Issues](https://github.com/alesierraalta/PRUEBATECNICA/issues)
- **Repositorio**: [GitHub Repository](https://github.com/alesierraalta/PRUEBATECNICA)