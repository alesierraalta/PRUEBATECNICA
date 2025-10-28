# Guía de Contribución

¡Gracias por tu interés en contribuir al Microservicio de Resumen LLM! Esta guía te ayudará a entender cómo puedes contribuir de manera efectiva al proyecto.

## Tabla de Contenidos

- [Código de Conducta](#código-de-conducta)
- [¿Cómo Contribuir?](#cómo-contribuir)
- [Configuración del Entorno de Desarrollo](#configuración-del-entorno-de-desarrollo)
- [Proceso de Desarrollo](#proceso-de-desarrollo)
- [Estándares de Código](#estándares-de-código)
- [Proceso de Pull Request](#proceso-de-pull-request)
- [Reportar Problemas](#reportar-problemas)
- [Solicitar Características](#solicitar-características)
- [Preguntas Frecuentes](#preguntas-frecuentes)

## Código de Conducta

Este proyecto sigue un código de conducta para asegurar un ambiente acogedor y respetuoso para todos los contribuidores. Al participar en este proyecto, aceptas mantener este código.

### Nuestros Compromisos

- Usar lenguaje acogedor e inclusivo
- Respetar diferentes puntos de vista y experiencias
- Aceptar críticas constructivas con gracia
- Enfocarse en lo que es mejor para la comunidad
- Mostrar empatía hacia otros miembros de la comunidad

### Comportamiento Inaceptable

- Uso de lenguaje o imágenes sexualizadas
- Trolling, comentarios insultantes o despectivos
- Acoso público o privado
- Publicar información privada sin permiso
- Cualquier conducta inapropiada en un contexto profesional

## ¿Cómo Contribuir?

Hay muchas maneras de contribuir al proyecto:

### 🐛 Reportar Errores
- Usa el sistema de Issues de GitHub
- Incluye información detallada para reproducir el problema
- Verifica que el error no haya sido reportado previamente

### 💡 Sugerir Mejoras
- Propón nuevas características o mejoras
- Discute ideas en GitHub Discussions
- Participa en conversaciones sobre el roadmap

### 📝 Mejorar Documentación
- Corrige errores tipográficos
- Mejora la claridad de la documentación existente
- Agrega ejemplos o casos de uso

### 🔧 Contribuir Código
- Corrige errores existentes
- Implementa nuevas características
- Mejora el rendimiento o la seguridad
- Agrega pruebas

### 🧪 Mejorar Pruebas
- Agrega casos de prueba faltantes
- Mejora la cobertura de código
- Optimiza pruebas existentes

## Configuración del Entorno de Desarrollo

### Prerrequisitos

- **Python 3.11+**
- **Docker y Docker Compose**
- **Git**
- **Editor de código** (VS Code, PyCharm, etc.)

### Configuración Inicial

1. **Hacer Fork del Repositorio**
   ```bash
   # En GitHub, hacer fork del repositorio
   # Luego clonar tu fork localmente
git clone https://github.com/alesierraalta/PRUEBATECNICA.git
cd PRUEBATECNICA
   ```

2. **Configurar Remote Upstream**
   ```bash
   git remote add upstream https://github.com/alesierraalta/PRUEBATECNICA.git
   ```

3. **Crear Entorno Virtual**
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

4. **Instalar Dependencias**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Si existe
   ```

5. **Configurar Variables de Entorno**
   ```bash
   cp env.example .env
   # Editar .env con tu configuración de desarrollo
   ```

6. **Iniciar Servicios de Desarrollo**
   ```bash
   docker-compose up -d redis
   # O instalar Redis localmente
   ```

### Herramientas de Desarrollo

#### Pre-commit Hooks
```bash
# Instalar pre-commit
pip install pre-commit

# Instalar hooks
pre-commit install

# Ejecutar manualmente
pre-commit run --all-files
```

#### Herramientas de Calidad de Código
```bash
# Formateo de código
black app/ tests/

# Linting
flake8 app/ tests/

# Verificación de tipos
mypy app/

# Análisis de seguridad
bandit -r app/
```

## Proceso de Desarrollo

### 1. Crear una Rama

```bash
# Actualizar rama principal
git checkout main
git pull upstream main

# Crear nueva rama
git checkout -b feature/nombre-de-caracteristica
# o
git checkout -b fix/descripcion-del-error
# o
git checkout -b docs/mejora-documentacion
```

### 2. Desarrollo

- **Hacer commits frecuentes** con mensajes descriptivos
- **Escribir pruebas** para nueva funcionalidad
- **Actualizar documentación** cuando sea necesario
- **Seguir estándares de código** del proyecto

### 3. Testing

```bash
# Ejecutar todas las pruebas
pytest

# Ejecutar pruebas específicas
pytest tests/unit/test_config.py

# Ejecutar con cobertura
pytest --cov=app --cov-report=html

# Ejecutar pruebas de integración
pytest -m integration
```

### 4. Actualizar Rama Principal

```bash
# Antes de crear PR, actualizar con cambios recientes
git checkout main
git pull upstream main
git checkout feature/tu-rama
git rebase main
```

## Estándares de Código

### Estilo de Código Python

#### Formateo
- **Black** para formateo automático
- **Línea máxima**: 88 caracteres
- **Indentación**: 4 espacios
- **Comillas**: Dobles para strings

#### Nomenclatura
```python
# Variables y funciones: snake_case
user_name = "juan"
def calculate_sum(a, b):
    return a + b

# Clases: PascalCase
class UserService:
    pass

# Constantes: UPPER_SNAKE_CASE
MAX_RETRIES = 3
API_BASE_URL = "https://api.example.com"
```

#### Docstrings
```python
def summarize_text(text: str, max_tokens: int = 100) -> str:
    """
    Resumir texto usando IA.

    Args:
        text (str): Texto a resumir.
        max_tokens (int, optional): Máximo de tokens en el resumen. 
                                   Predeterminado: 100.

    Returns:
        str: Texto resumido.

    Raises:
        ValueError: Si el texto está vacío.
        LLMProviderError: Si el proveedor LLM falla.

    Example:
        >>> summarize_text("Texto largo aquí...", 50)
        "Resumen corto..."
    """
    pass
```

#### Type Hints
```python
from typing import List, Optional, Dict, Any

def process_data(
    items: List[str], 
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, int]:
    """Procesar lista de elementos con configuración opcional."""
    pass
```

### Estándares de Git

#### Mensajes de Commit
Seguir el formato [Conventional Commits](https://www.conventionalcommits.org/):

```
tipo(alcance): descripción

Descripción más detallada si es necesario.

Cuerpo del commit con más contexto.

Footer con información adicional (opcional).
```

**Tipos de Commit:**
- `feat`: Nueva característica
- `fix`: Corrección de error
- `docs`: Cambios en documentación
- `style`: Cambios de formato (no afectan código)
- `refactor`: Refactorización de código
- `test`: Agregar o corregir pruebas
- `chore`: Cambios en herramientas o configuración

**Ejemplos:**
```bash
feat(api): agregar endpoint de evaluación de calidad
fix(cache): corregir problema de expiración de TTL
docs(readme): actualizar instrucciones de instalación
test(unit): agregar pruebas para servicio de caché
```

#### Estructura de Commits
```bash
# Hacer commits atómicos
git add archivo1.py archivo2.py
git commit -m "feat(api): agregar validación de entrada"

# No hacer commits masivos
git add .
git commit -m "cambios varios"  # ❌ Evitar
```

### Estándares de Testing

#### Estructura de Pruebas
```python
class TestUserService:
    """Pruebas para UserService."""
    
    def test_create_user_success(self):
        """Probar creación exitosa de usuario."""
        # Arrange
        user_data = {"name": "Juan", "email": "juan@test.com"}
        
        # Act
        result = user_service.create_user(user_data)
        
        # Assert
        assert result.id is not None
        assert result.name == "Juan"
    
    def test_create_user_invalid_email(self):
        """Probar creación de usuario con email inválido."""
        # Arrange
        user_data = {"name": "Juan", "email": "email-invalido"}
        
        # Act & Assert
        with pytest.raises(ValidationError):
            user_service.create_user(user_data)
```

#### Cobertura de Pruebas
- **Mínimo**: 80% de cobertura de código
- **Objetivo**: 90%+ para código crítico
- **Incluir**: Casos límite y manejo de errores

## Proceso de Pull Request

### 1. Preparar Pull Request

```bash
# Asegurar que todas las pruebas pasen
pytest

# Verificar calidad de código
black --check app/ tests/
flake8 app/ tests/
mypy app/

# Actualizar documentación si es necesario
# Actualizar CHANGELOG.md si aplica
```

### 2. Crear Pull Request

1. **Ir a GitHub** y hacer clic en "New Pull Request"
2. **Seleccionar ramas** correctas (tu-rama → main)
3. **Completar plantilla** de PR
4. **Agregar etiquetas** apropiadas
5. **Asignar revisores** si es necesario

### 3. Plantilla de Pull Request

```markdown
## Descripción
Breve descripción de los cambios realizados.

## Tipo de Cambio
- [ ] Corrección de error (cambio que corrige un problema)
- [ ] Nueva característica (cambio que agrega funcionalidad)
- [ ] Cambio que rompe compatibilidad (fix o feature que cambiaría funcionalidad existente)
- [ ] Documentación (cambios solo en documentación)

## ¿Cómo se Probó?
Describe las pruebas que ejecutaste para verificar tus cambios.

## Checklist
- [ ] Mi código sigue las guías de estilo del proyecto
- [ ] He realizado una auto-revisión de mi código
- [ ] He comentado mi código, especialmente en áreas difíciles de entender
- [ ] He hecho cambios correspondientes en la documentación
- [ ] Mis cambios no generan nuevas advertencias
- [ ] He agregado pruebas que prueban que mi corrección es efectiva o que mi característica funciona
- [ ] Las pruebas nuevas y existentes pasan localmente
- [ ] Cualquier cambio dependiente ha sido mergeado y publicado

## Capturas de Pantalla (si aplica)
Agregar capturas de pantalla para ayudar a explicar tu problema o solución.

## Información Adicional
Cualquier otra información relevante para los revisores.
```

### 4. Revisión de Código

#### Para Revisores
- **Revisar código** dentro de 48 horas
- **Proporcionar feedback** constructivo
- **Aprobar o solicitar cambios** claramente
- **Probar cambios** localmente si es necesario

#### Para Autores
- **Responder a comentarios** rápidamente
- **Hacer cambios solicitados** en commits separados
- **Mantener PR actualizado** con main
- **Solicitar nueva revisión** cuando esté listo

### 5. Merge

- **Squash and merge** para commits pequeños
- **Merge commit** para cambios complejos
- **Eliminar rama** después del merge

## Reportar Problemas

### Plantilla de Issue

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

## Capturas de Pantalla
Si aplica, agregar capturas de pantalla.

## Información del Entorno
- OS: [e.g. Ubuntu 20.04]
- Python: [e.g. 3.11.0]
- Docker: [e.g. 20.10.7]
- Versión: [e.g. 1.0.0]

## Logs
```
Logs relevantes aquí
```

## Información Adicional
Cualquier otra información relevante.
```

### Tipos de Issues

- **🐛 Bug**: Algo no funciona como debería
- **✨ Feature**: Solicitud de nueva funcionalidad
- **📚 Documentation**: Mejoras en documentación
- **🔧 Enhancement**: Mejora de funcionalidad existente
- **❓ Question**: Pregunta sobre el proyecto
- **🚀 Performance**: Problemas de rendimiento

## Solicitar Características

### Proceso

1. **Verificar** que la característica no exista
2. **Buscar** issues similares
3. **Crear issue** con etiqueta "enhancement"
4. **Discutir** en GitHub Discussions si es necesario
5. **Esperar** aprobación antes de implementar

### Plantilla de Feature Request

```markdown
## ¿Tu solicitud de característica está relacionada con un problema?
Descripción clara del problema.

## Describe la solución que te gustaría
Descripción clara de lo que quieres que pase.

## Describe alternativas que has considerado
Descripción de soluciones alternativas.

## Contexto adicional
Cualquier otro contexto sobre la solicitud.
```

## Preguntas Frecuentes

### ¿Cómo empiezo a contribuir?

1. **Lee la documentación** completa del proyecto
2. **Configura el entorno** de desarrollo
3. **Busca issues** etiquetados como "good first issue"
4. **Haz fork** del repositorio
5. **Crea una rama** para tu contribución

### ¿Qué tipo de contribuciones son más valiosas?

- **Corrección de errores** críticos
- **Nuevas características** bien diseñadas
- **Mejoras de rendimiento**
- **Documentación** clara y completa
- **Pruebas** que aumenten la cobertura

### ¿Cómo puedo obtener ayuda?

- **GitHub Discussions** para preguntas generales
- **Issues** para problemas específicos
- **Pull Requests** para discusiones sobre código
- **Email** para asuntos privados

### ¿Cuánto tiempo toma revisar un PR?

- **Pruebas simples**: 1-2 días
- **Características pequeñas**: 3-5 días
- **Características grandes**: 1-2 semanas
- **Cambios complejos**: Puede tomar más tiempo

### ¿Qué pasa si mi PR es rechazado?

- **No te desanimes** - es parte del proceso
- **Lee los comentarios** cuidadosamente
- **Haz las mejoras** sugeridas
- **Pregunta** si algo no está claro
- **Resubmit** cuando esté listo

## Reconocimientos

### Contribuidores

Gracias a todos los contribuidores que han ayudado a hacer este proyecto mejor:

- [Lista de contribuidores](https://github.com/alesierraalta/PRUEBATECNICA/graphs/contributors)

### Agradecimientos Especiales

- **Mantenedores**: Por su dedicación y liderazgo
- **Revisores**: Por su tiempo y expertise
- **Comunidad**: Por reportar errores y sugerir mejoras

## Licencia

Al contribuir a este proyecto, aceptas que tus contribuciones serán licenciadas bajo la misma licencia que el proyecto (MIT License).

## Contacto

- **Mantenedor Principal**: [Tu Nombre](mailto:tu-email@ejemplo.com)
- **Proyecto**: [GitHub Repository](https://github.com/alesierraalta/PRUEBATECNICA)
- **Issues**: [GitHub Issues](https://github.com/alesierraalta/PRUEBATECNICA/issues)
- **Discusiones**: [GitHub Discussions](https://github.com/alesierraalta/PRUEBATECNICA/discussions)

---

**¡Gracias por contribuir al Microservicio de Resumen LLM!** 🚀