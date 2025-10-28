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
   git clone https://github.com/tuusuario/microservicio-resumen-llm.git
   cd microservicio-resumen-llm
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

## Despliegue en la Nube

### AWS (Amazon Web Services)

#### Opción 1: ECS con Fargate

1. **Crear repositorio ECR**
   ```bash
   aws ecr create-repository --repository-name llm-resumen-api
   ```

2. **Construir y subir imagen**
   ```bash
   # Obtener token de login
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
   
   # Construir imagen
   docker build -t llm-resumen-api .
   
   # Etiquetar imagen
   docker tag llm-resumen-api:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/llm-resumen-api:latest
   
   # Subir imagen
   docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/llm-resumen-api:latest
   ```

3. **Configurar ECS Task Definition**
   ```json
   {
     "family": "llm-resumen-api",
     "networkMode": "awsvpc",
     "requiresCompatibilities": ["FARGATE"],
     "cpu": "512",
     "memory": "1024",
     "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
     "containerDefinitions": [
       {
         "name": "api",
         "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/llm-resumen-api:latest",
         "portMappings": [
           {
             "containerPort": 8000,
             "protocol": "tcp"
           }
         ],
         "environment": [
           {
             "name": "ENVIRONMENT",
             "value": "production"
           }
         ],
         "secrets": [
           {
             "name": "GEMINI_API_KEY",
             "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:llm-resumen/gemini-api-key"
           }
         ],
         "logConfiguration": {
           "logDriver": "awslogs",
           "options": {
             "awslogs-group": "/ecs/llm-resumen-api",
             "awslogs-region": "us-east-1",
             "awslogs-stream-prefix": "ecs"
           }
         }
       }
     ]
   }
   ```

#### Opción 2: EKS (Elastic Kubernetes Service)

1. **Crear cluster EKS**
   ```bash
   eksctl create cluster --name llm-resumen-cluster --region us-east-1 --nodegroup-name workers --node-type t3.medium --nodes 3
   ```

2. **Aplicar manifiestos Kubernetes**
   ```bash
   kubectl apply -f k8s/
   ```

### Google Cloud Platform (GCP)

#### Cloud Run

1. **Construir imagen**
   ```bash
   gcloud builds submit --tag gcr.io/tu-proyecto/llm-resumen-api
   ```

2. **Desplegar en Cloud Run**
   ```bash
   gcloud run deploy llm-resumen-api \
     --image gcr.io/tu-proyecto/llm-resumen-api \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars ENVIRONMENT=production \
     --set-secrets GEMINI_API_KEY=gemini-api-key:latest
   ```

#### Google Kubernetes Engine (GKE)

1. **Crear cluster GKE**
   ```bash
   gcloud container clusters create llm-resumen-cluster \
     --zone us-central1-a \
     --num-nodes 3 \
     --machine-type e2-medium
   ```

2. **Desplegar aplicación**
   ```bash
   kubectl apply -f k8s/
   ```

### Microsoft Azure

#### Azure Container Instances (ACI)

1. **Crear grupo de contenedores**
   ```bash
   az container create \
     --resource-group mi-grupo-recursos \
     --name llm-resumen-api \
     --image tu-registro.azurecr.io/llm-resumen-api:latest \
     --cpu 1 \
     --memory 2 \
     --ports 8000 \
     --environment-variables ENVIRONMENT=production \
     --secure-environment-variables GEMINI_API_KEY=tu_clave_api
   ```

#### Azure Kubernetes Service (AKS)

1. **Crear cluster AKS**
   ```bash
   az aks create \
     --resource-group mi-grupo-recursos \
     --name llm-resumen-cluster \
     --node-count 3 \
     --node-vm-size Standard_B2s \
     --enable-addons monitoring
   ```

2. **Desplegar aplicación**
   ```bash
   kubectl apply -f k8s/
   ```

## Despliegue con Kubernetes

### Manifiestos Kubernetes

#### Namespace
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: llm-resumen
```

#### ConfigMap
```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: llm-resumen-config
  namespace: llm-resumen
data:
  ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"
  WORKERS: "4"
  SUMMARY_MAX_TOKENS: "100"
  CACHE_TTL_SECONDS: "3600"
  RATE_LIMIT_PER_MINUTE: "100"
```

#### Secret
```yaml
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: llm-resumen-secrets
  namespace: llm-resumen
type: Opaque
data:
  gemini-api-key: <base64-encoded-key>
  api-keys-allowed: <base64-encoded-keys>
```

#### Deployment
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-resumen-api
  namespace: llm-resumen
spec:
  replicas: 3
  selector:
    matchLabels:
      app: llm-resumen-api
  template:
    metadata:
      labels:
        app: llm-resumen-api
    spec:
      containers:
      - name: api
        image: llm-resumen-api:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: llm-resumen-config
        - secretRef:
            name: llm-resumen-secrets
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /v1/healthz
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /v1/healthz
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

#### Service
```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: llm-resumen-service
  namespace: llm-resumen
spec:
  selector:
    app: llm-resumen-api
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

#### Ingress
```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: llm-resumen-ingress
  namespace: llm-resumen
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - api.tu-dominio.com
    secretName: llm-resumen-tls
  rules:
  - host: api.tu-dominio.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: llm-resumen-service
            port:
              number: 80
```

### Comandos de Despliegue

```bash
# Aplicar todos los manifiestos
kubectl apply -f k8s/

# Verificar despliegue
kubectl get pods -n llm-resumen

# Ver logs
kubectl logs -f deployment/llm-resumen-api -n llm-resumen

# Escalar deployment
kubectl scale deployment llm-resumen-api --replicas=5 -n llm-resumen

# Actualizar imagen
kubectl set image deployment/llm-resumen-api api=llm-resumen-api:v2.0.0 -n llm-resumen
```

## CI/CD Pipeline

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Despliegue

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Configurar Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Instalar dependencias
      run: |
        pip install -r requirements.txt
    
    - name: Ejecutar pruebas
      run: |
        pytest --cov=app --cov-report=xml
    
    - name: Subir cobertura
      uses: codecov/codecov-action@v3

  build-and-deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Construir imagen Docker
      run: |
        docker build -t llm-resumen-api:${{ github.sha }} .
    
    - name: Subir a ECR
      env:
        AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
        AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        AWS_REGION: us-east-1
      run: |
        aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REGISTRY
        docker tag llm-resumen-api:${{ github.sha }} $ECR_REGISTRY/llm-resumen-api:${{ github.sha }}
        docker push $ECR_REGISTRY/llm-resumen-api:${{ github.sha }}
    
    - name: Desplegar en ECS
      env:
        AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
        AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        AWS_REGION: us-east-1
      run: |
        aws ecs update-service --cluster llm-resumen-cluster --service llm-resumen-service --force-new-deployment
```

### GitLab CI/CD

```yaml
# .gitlab-ci.yml
stages:
  - test
  - build
  - deploy

variables:
  DOCKER_DRIVER: overlay2
  DOCKER_TLS_CERT_DIR: "/certs"

test:
  stage: test
  image: python:3.11
  before_script:
    - pip install -r requirements.txt
  script:
    - pytest --cov=app --cov-report=xml
  coverage: '/TOTAL.*\s+(\d+%)$/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml

build:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  only:
    - main

deploy:
  stage: deploy
  image: bitnami/kubectl:latest
  script:
    - kubectl set image deployment/llm-resumen-api api=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  only:
    - main
  when: manual
```

## Monitoreo y Observabilidad

### Prometheus y Grafana

#### Configuración de Prometheus

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'llm-resumen-api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: /metrics
    scrape_interval: 5s
```

#### Dashboard de Grafana

```json
{
  "dashboard": {
    "title": "LLM Resumen API",
    "panels": [
      {
        "title": "Solicitudes por Segundo",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Latencia P95",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "P95 Latency"
          }
        ]
      }
    ]
  }
}
```

### Alertas

#### Reglas de Prometheus

```yaml
# monitoring/alerts.yml
groups:
- name: llm-resumen-alerts
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "Alta tasa de errores en LLM Resumen API"
      description: "La tasa de errores 5xx es {{ $value }} por segundo"

  - alert: HighLatency
    expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Alta latencia en LLM Resumen API"
      description: "El percentil 95 de latencia es {{ $value }} segundos"
```

## Estrategias de Rollback

### Rollback Automático

```bash
# Script de rollback
#!/bin/bash
# scripts/rollback.sh

PREVIOUS_VERSION=$1
if [ -z "$PREVIOUS_VERSION" ]; then
    echo "Uso: $0 <versión_anterior>"
    exit 1
fi

echo "Ejecutando rollback a versión $PREVIOUS_VERSION..."

# Rollback en Kubernetes
kubectl rollout undo deployment/llm-resumen-api -n llm-resumen

# Rollback en Docker Compose
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d

echo "Rollback completado ✓"
```

### Verificación Post-Despliegue

```bash
#!/bin/bash
# scripts/post-deploy-check.sh

echo "Verificando despliegue..."

# Verificar salud del servicio
curl -f http://localhost:8000/v1/healthz || {
    echo "ERROR: Servicio no saludable"
    exit 1
}

# Verificar métricas básicas
RESPONSE_TIME=$(curl -o /dev/null -s -w '%{time_total}' http://localhost:8000/v1/healthz)
if (( $(echo "$RESPONSE_TIME > 5.0" | bc -l) )); then
    echo "ADVERTENCIA: Tiempo de respuesta alto: ${RESPONSE_TIME}s"
fi

# Verificar logs de errores
ERROR_COUNT=$(docker-compose logs api | grep -c "ERROR" || echo "0")
if [ "$ERROR_COUNT" -gt 10 ]; then
    echo "ADVERTENCIA: Muchos errores en logs: $ERROR_COUNT"
fi

echo "Verificación completada ✓"
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