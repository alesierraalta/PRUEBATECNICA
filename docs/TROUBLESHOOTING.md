# Guía de Solución de Problemas

## Resumen

Esta guía proporciona soluciones detalladas para los problemas más comunes que pueden ocurrir con el Microservicio de Resumen LLM. Incluye diagnósticos paso a paso, comandos de verificación y soluciones específicas para diferentes entornos.

## Problemas Comunes

### 1. Problemas de Autenticación

#### Error: 401 No Autorizado

**Síntomas:**
- Todas las solicitudes devuelven error 401
- Mensaje: "Clave API inválida" o "Clave API faltante"

**Diagnóstico:**
```bash
# Verificar formato de header de autorización
curl -H "Authorization: Bearer tu_clave_api" http://localhost:8000/v1/healthz

# Verificar que la clave API esté configurada
echo $API_KEYS_ALLOWED

# Verificar logs de autenticación
docker-compose logs api | grep -i "auth"
```

**Soluciones:**

1. **Verificar formato de clave API:**
   ```bash
   # Formato correcto
   Authorization: Bearer tu_clave_api_aqui
   
   # Formato incorrecto
   Authorization: tu_clave_api_aqui  # Falta "Bearer "
   ```

2. **Verificar configuración de claves API:**
   ```bash
   # En .env
   API_KEYS_ALLOWED=clave1,clave2,clave3
   
   # Verificar que no haya espacios extra
   API_KEYS_ALLOWED="clave1, clave2, clave3"  # ❌ Incorrecto
   API_KEYS_ALLOWED="clave1,clave2,clave3"   # ✅ Correcto
   ```

3. **Regenerar clave API:**
   ```bash
   # Generar nueva clave
   openssl rand -hex 32
   
   # Actualizar configuración
   API_KEYS_ALLOWED=nueva_clave_generada_aqui
   ```

#### Error: Esquema de Autorización Inválido

**Síntomas:**
- Error 401 con mensaje "Esquema de autorización inválido"
- Header Authorization no usa formato Bearer

**Solución:**
```bash
# Usar formato Bearer correcto
curl -H "Authorization: Bearer tu_clave_api" http://localhost:8000/v1/summarize

# No usar otros esquemas
curl -H "Authorization: Basic tu_clave_api" http://localhost:8000/v1/summarize  # ❌
```

### 2. Problemas de Limitación de Velocidad

#### Error: 429 Demasiadas Solicitudes

**Síntomas:**
- Solicitudes frecuentes devuelven error 429
- Headers muestran límite de velocidad excedido

**Diagnóstico:**
```bash
# Verificar headers de límite de velocidad
curl -I -H "Authorization: Bearer tu_clave_api" http://localhost:8000/v1/summarize

# Verificar configuración de límites
echo $RATE_LIMIT_PER_MINUTE
echo $RATE_LIMIT_WINDOW

# Verificar estado de Redis
docker-compose exec redis redis-cli info stats | grep keyspace
```

**Soluciones:**

1. **Aumentar límite de velocidad:**
   ```bash
   # En .env
   RATE_LIMIT_PER_MINUTE=200  # Aumentar de 100 a 200
   RATE_LIMIT_WINDOW=60       # Ventana de 60 segundos
   ```

2. **Deshabilitar limitación temporalmente:**
   ```bash
   # Para pruebas
   ENABLE_RATE_LIMIT=false
   ```

3. **Limpiar contadores de Redis:**
   ```bash
   # Limpiar todos los contadores
   docker-compose exec redis redis-cli FLUSHDB
   
   # O limpiar contadores específicos
   docker-compose exec redis redis-cli KEYS "*rate_limit*" | xargs docker-compose exec redis redis-cli DEL
   ```

4. **Implementar retroceso exponencial:**
   ```python
   import time
   import random
   
   def hacer_solicitud_con_reintento(url, headers, data, max_reintentos=3):
       for intento in range(max_reintentos):
           try:
               response = requests.post(url, headers=headers, json=data)
               if response.status_code != 429:
                   return response
               
               # Esperar antes del siguiente intento
               tiempo_espera = (2 ** intento) + random.uniform(0, 1)
               time.sleep(tiempo_espera)
               
           except Exception as e:
               if intento == max_reintentos - 1:
                   raise e
               time.sleep(1)
   ```

### 3. Problemas del Proveedor LLM

#### Error: 503 Servicio No Disponible

**Síntomas:**
- Errores 503 frecuentes en solicitudes de resumen
- Mensaje: "Servicio de resumen temporalmente no disponible"

**Diagnóstico:**
```bash
# Verificar conectividad a Gemini API
curl -H "Authorization: Bearer $GEMINI_API_KEY" \
  https://generativelanguage.googleapis.com/v1/models

# Verificar configuración de timeout
echo $LLM_TIMEOUT_MS

# Verificar logs del proveedor LLM
docker-compose logs api | grep -i "gemini\|llm"
```

**Soluciones:**

1. **Verificar clave API de Gemini:**
   ```bash
   # Probar clave API directamente
   curl -H "Authorization: Bearer $GEMINI_API_KEY" \
     https://generativelanguage.googleapis.com/v1/models
   
   # Debería devolver lista de modelos disponibles
   ```

2. **Aumentar timeout:**
   ```bash
   # En .env
   LLM_TIMEOUT_MS=15000  # Aumentar de 8000 a 15000
   REQUEST_TIMEOUT_MS=20000  # Aumentar timeout general
   ```

3. **Verificar límites de cuota:**
   ```bash
   # Verificar uso de cuota en Google Cloud Console
   # O usar API de monitoreo
   curl -H "Authorization: Bearer $GEMINI_API_KEY" \
     https://generativelanguage.googleapis.com/v1/models/gemini-pro
   ```

4. **Habilitar respaldo automático:**
   ```bash
   # El servicio automáticamente recurre a TextRank si Gemini falla
   # Verificar que el respaldo esté funcionando
   curl -H "Authorization: Bearer tu_clave_api" \
     -d '{"text": "Texto de prueba"}' \
     http://localhost:8000/v1/summarize
   ```

#### Error: Timeout del LLM

**Síntomas:**
- Solicitudes que tardan mucho tiempo
- Errores de timeout después de 8-10 segundos

**Solución:**
```bash
# Aumentar timeout específico del LLM
LLM_TIMEOUT_MS=20000

# Reducir tamaño de texto si es muy largo
# El servicio tiene límite de 50,000 caracteres
```

### 4. Problemas de Redis/Caché

#### Error: Conexión Redis Fallida

**Síntomas:**
- Errores de conexión a Redis en logs
- Caché no funciona
- Servicio funciona pero sin caché

**Diagnóstico:**
```bash
# Verificar estado de Redis
docker-compose ps redis

# Probar conexión Redis
docker-compose exec redis redis-cli ping

# Verificar URL de Redis
echo $REDIS_URL

# Verificar logs de Redis
docker-compose logs redis
```

**Soluciones:**

1. **Reiniciar Redis:**
   ```bash
   docker-compose restart redis
   
   # O recrear contenedor
   docker-compose down redis
   docker-compose up -d redis
   ```

2. **Verificar configuración de URL:**
   ```bash
   # Formato correcto
   REDIS_URL=redis://localhost:6379/0
   
   # Con autenticación
   REDIS_URL=redis://usuario:contraseña@localhost:6379/0
   
   # Con SSL
   REDIS_URL=rediss://usuario:contraseña@redis-cluster.com:6380/0
   ```

3. **Verificar conectividad de red:**
   ```bash
   # Desde el contenedor de la API
   docker-compose exec api ping redis
   
   # Verificar puerto
   docker-compose exec api telnet redis 6379
   ```

4. **Deshabilitar caché temporalmente:**
   ```bash
   # Si Redis no es crítico
   ENABLE_CACHE=false
   ```

#### Error: Caché No Funciona

**Síntomas:**
- Solicitudes repetidas no se sirven desde caché
- Tiempo de respuesta siempre alto
- Campo "cached" siempre false

**Solución:**
```bash
# Verificar configuración de caché
echo $ENABLE_CACHE
echo $CACHE_TTL_SECONDS

# Limpiar caché y probar
docker-compose exec redis redis-cli FLUSHDB

# Verificar que las claves se están generando
docker-compose exec redis redis-cli KEYS "*"
```

### 5. Problemas de Rendimiento

#### Error: Alta Latencia

**Síntomas:**
- Tiempo de respuesta > 5 segundos
- Timeouts frecuentes
- Usuarios reportan lentitud

**Diagnóstico:**
```bash
# Medir tiempo de respuesta
time curl -H "Authorization: Bearer tu_clave_api" \
  -d '{"text": "Texto de prueba"}' \
  http://localhost:8000/v1/summarize

# Verificar uso de recursos
docker stats

# Verificar logs de rendimiento
docker-compose logs api | grep -i "latency\|time"
```

**Soluciones:**

1. **Optimizar configuración:**
   ```bash
   # Aumentar workers
   WORKERS=4
   
   # Optimizar timeout
   LLM_TIMEOUT_MS=8000
   REQUEST_TIMEOUT_MS=10000
   ```

2. **Habilitar caché:**
   ```bash
   ENABLE_CACHE=true
   CACHE_TTL_SECONDS=3600  # 1 hora
   ```

3. **Escalar horizontalmente:**
   ```bash
   # En docker-compose.prod.yml
   deploy:
     replicas: 3
   ```

4. **Optimizar texto de entrada:**
   ```bash
   # Reducir tamaño de texto si es muy largo
   # El servicio funciona mejor con textos de 1000-5000 caracteres
   ```

#### Error: Alto Uso de Memoria

**Síntomas:**
- Contenedores siendo terminados por OOM
- Uso de memoria > 512MB por instancia
- Rendimiento degradado

**Solución:**
```bash
# Aumentar límites de memoria
# En docker-compose.yml
deploy:
  resources:
    limits:
      memory: 1G
    reservations:
      memory: 512M

# En Kubernetes
resources:
  limits:
    memory: "1Gi"
  requests:
    memory: "512Mi"
```

### 6. Problemas de Validación

#### Error: 400 Solicitud Incorrecta

**Síntomas:**
- Errores de validación en solicitudes
- Mensajes sobre campos requeridos o inválidos

**Diagnóstico:**
```bash
# Verificar formato de solicitud
curl -H "Authorization: Bearer tu_clave_api" \
  -H "Content-Type: application/json" \
  -d '{"text": "Texto muy corto"}' \
  http://localhost:8000/v1/summarize

# Verificar logs de validación
docker-compose logs api | grep -i "validation\|error"
```

**Soluciones:**

1. **Verificar longitud de texto:**
   ```bash
   # Mínimo: 10 caracteres
   # Máximo: 50,000 caracteres
   
   # Texto muy corto
   {"text": "Corto"}  # ❌ Muy corto
   
   # Texto válido
   {"text": "Este es un texto válido para resumir."}  # ✅
   ```

2. **Verificar parámetros:**
   ```bash
   # max_tokens debe estar entre 10 y 500
   {"max_tokens": 5}   # ❌ Muy bajo
   {"max_tokens": 100} # ✅ Válido
   
   # lang debe ser válido
   {"lang": "invalid"} # ❌ Inválido
   {"lang": "es"}      # ✅ Válido
   
   # tone debe ser válido
   {"tone": "invalid"} # ❌ Inválido
   {"tone": "neutral"} # ✅ Válido
   ```

3. **Verificar formato JSON:**
   ```bash
   # JSON válido
   {"text": "Texto válido", "lang": "es"}
   
   # JSON inválido
   {"text": "Texto válido", "lang": "es",}  # ❌ Coma extra
   ```

## Diagnóstico Avanzado

### Verificación de Salud del Sistema

```bash
#!/bin/bash
# scripts/health-check.sh

echo "=== Verificación de Salud del Sistema ==="

# Verificar servicios Docker
echo "1. Verificando servicios Docker..."
docker-compose ps

# Verificar conectividad Redis
echo "2. Verificando Redis..."
if docker-compose exec redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis: Conectado"
else
    echo "❌ Redis: No conectado"
fi

# Verificar API
echo "3. Verificando API..."
if curl -f http://localhost:8000/v1/healthz > /dev/null 2>&1; then
    echo "✅ API: Funcionando"
else
    echo "❌ API: No responde"
fi

# Verificar Gemini API
echo "4. Verificando Gemini API..."
if curl -H "Authorization: Bearer $GEMINI_API_KEY" \
   https://generativelanguage.googleapis.com/v1/models > /dev/null 2>&1; then
    echo "✅ Gemini API: Conectado"
else
    echo "❌ Gemini API: No conectado"
fi

# Verificar uso de recursos
echo "5. Verificando recursos..."
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

echo "=== Verificación Completada ==="
```

### Análisis de Logs

```bash
#!/bin/bash
# scripts/analyze-logs.sh

echo "=== Análisis de Logs ==="

# Errores recientes
echo "1. Errores recientes:"
docker-compose logs --tail=100 api | grep -i "error\|exception\|failed"

# Errores de autenticación
echo "2. Errores de autenticación:"
docker-compose logs --tail=100 api | grep -i "auth\|unauthorized\|invalid.*key"

# Errores de límite de velocidad
echo "3. Errores de límite de velocidad:"
docker-compose logs --tail=100 api | grep -i "rate.*limit\|429"

# Errores de LLM
echo "4. Errores de LLM:"
docker-compose logs --tail=100 api | grep -i "gemini\|llm\|503"

# Estadísticas de solicitudes
echo "5. Estadísticas de solicitudes:"
docker-compose logs --tail=1000 api | grep -c "POST /v1/summarize"

echo "=== Análisis Completado ==="
```

### Monitoreo de Rendimiento

```bash
#!/bin/bash
# scripts/performance-monitor.sh

echo "=== Monitoreo de Rendimiento ==="

# Medir tiempo de respuesta
echo "1. Tiempo de respuesta:"
time curl -s -H "Authorization: Bearer $API_KEY" \
  -d '{"text": "Texto de prueba para medir rendimiento"}' \
  http://localhost:8000/v1/summarize > /dev/null

# Verificar uso de memoria
echo "2. Uso de memoria:"
docker stats --no-stream --format "{{.MemUsage}}" api

# Verificar uso de CPU
echo "3. Uso de CPU:"
docker stats --no-stream --format "{{.CPUPerc}}" api

# Verificar conexiones de red
echo "4. Conexiones de red:"
docker-compose exec api netstat -an | grep :8000 | wc -l

echo "=== Monitoreo Completado ==="
```

## Herramientas de Depuración

### Modo Debug

```bash
# Habilitar logging de debug
LOG_LEVEL=DEBUG docker-compose up

# Ver logs en tiempo real
docker-compose logs -f api

# Filtrar logs específicos
docker-compose logs -f api | grep -i "error\|warning"
```

### Herramientas de Red

```bash
# Verificar conectividad
docker-compose exec api ping google.com

# Verificar DNS
docker-compose exec api nslookup generativelanguage.googleapis.com

# Verificar puertos
docker-compose exec api netstat -tlnp
```

### Herramientas de Base de Datos

```bash
# Conectar a Redis
docker-compose exec redis redis-cli

# Ver información de Redis
docker-compose exec redis redis-cli info

# Ver claves en Redis
docker-compose exec redis redis-cli keys "*"

# Monitorear comandos Redis
docker-compose exec redis redis-cli monitor
```

## Contacto y Soporte

### Recursos de Ayuda

- **Documentación**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/tuusuario/microservicio-resumen-llm/issues)
- **Discusiones**: [GitHub Discussions](https://github.com/tuusuario/microservicio-resumen-llm/discussions)

### Información para Reportar Problemas

Al reportar un problema, incluye:

1. **Versión del software**
2. **Configuración de entorno**
3. **Logs relevantes**
4. **Pasos para reproducir**
5. **Comportamiento esperado vs actual**

### Plantilla de Reporte de Problema

```markdown
## Descripción del Problema
Descripción clara y concisa del problema.

## Pasos para Reproducir
1. Ir a '...'
2. Hacer clic en '...'
3. Ver error

## Comportamiento Esperado
Qué esperabas que pasara.

## Comportamiento Actual
Qué está pasando realmente.

## Información del Entorno
- OS: [e.g. Ubuntu 20.04]
- Docker: [e.g. 20.10.7]
- Versión: [e.g. 1.0.0]

## Logs
```
Logs relevantes aquí
```

## Configuración
```
Variables de entorno relevantes
```
```