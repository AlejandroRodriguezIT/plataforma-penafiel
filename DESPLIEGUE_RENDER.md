# Guía de Despliegue en Render

Esta guía te ayudará a desplegar la Plataforma FC Penafiel en Render para que puedas compartir el enlace con personas externas.

## Requisitos Previos

1. Una cuenta en [Render](https://render.com) (plan gratuito disponible)
2. Tu código en un repositorio Git (GitHub, GitLab, o Bitbucket)
3. Las credenciales de la base de datos

## Pasos para el Despliegue

### 1. Preparar el Repositorio

Asegúrate de que tu código esté en un repositorio Git. Si no lo tienes aún:

```bash
git init
git add .
git commit -m "Preparar proyecto para despliegue en Render"
```

Sube el código a GitHub:
```bash
git remote add origin https://github.com/tu-usuario/plataforma-penafiel.git
git branch -M main
git push -u origin main
```

### 2. Crear el Servicio en Render

1. Inicia sesión en [Render Dashboard](https://dashboard.render.com)
2. Haz clic en **"New +"** y selecciona **"Web Service"**
3. Conecta tu repositorio de GitHub/GitLab/Bitbucket
4. Selecciona el repositorio `plataforma-penafiel`

### 3. Configurar el Servicio

En la página de configuración del servicio, completa los siguientes campos:

#### Configuración Básica
- **Name**: `plataforma-penafiel` (o el nombre que prefieras)
- **Region**: Selecciona la región más cercana (Frankfurt para Europa)
- **Branch**: `main` (o la rama que uses)
- **Root Directory**: (déjalo vacío si el código está en la raíz)
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`

#### Plan
- Selecciona el **Plan Free** (gratis) para empezar

### 4. Configurar Variables de Entorno

En la sección **Environment Variables**, añade las siguientes variables:

| Variable | Valor | Descripción |
|----------|-------|-------------|
| `PYTHON_VERSION` | `3.11.0` | Versión de Python |
| `DEBUG` | `False` | Desactivar modo debug en producción |
| `SECRET_KEY` | `[genera-una-clave-segura]` | Clave secreta para Flask |
| `DB_USER` | `alen_depor` | Usuario de la base de datos |
| `DB_PASSWORD` | `[tu-contraseña]` | Contraseña de la base de datos |
| `DB_HOST` | `82.165.192.201` | Host de la base de datos |
| `DB_NAME` | `penafiel` | Nombre de la base de datos |

**Importante**: Para generar una clave segura para `SECRET_KEY`, puedes usar:
```python
import secrets
print(secrets.token_hex(32))
```

### 5. Configurar Directorios de Datos

Si necesitas datos persistentes, deberás:

1. **Opción A**: Usar un servicio de almacenamiento externo (recomendado)
   - Amazon S3
   - Google Cloud Storage
   - Dropbox API

2. **Opción B**: Incluir datos estáticos en el repositorio
   - Crear carpetas `data/`, `graficas/` en el repositorio
   - Añadir archivos necesarios
   - Commit y push al repositorio

Para la opción B, añade estas variables de entorno:
```
DATA_DIR=/opt/render/project/src/data
GRAFICAS_DIR=/opt/render/project/src/graficas
CODIGOS_DIR=/opt/render/project/src/modules
```

### 6. Desplegar

1. Haz clic en **"Create Web Service"**
2. Render comenzará a construir y desplegar tu aplicación
3. Espera a que el deploy termine (puede tomar 5-10 minutos)
4. Una vez completado, verás el estado como **"Live"**

### 7. Acceder a tu Aplicación

Tu aplicación estará disponible en:
```
https://plataforma-penafiel.onrender.com
```

O el nombre que hayas elegido para tu servicio.

## Consideraciones Importantes

### Limitaciones del Plan Gratuito

- **Suspensión por inactividad**: Los servicios gratuitos se suspenden después de 15 minutos de inactividad
- **Tiempo de arranque**: Cuando se accede después de la suspensión, puede tardar 30-50 segundos en arrancar
- **750 horas/mes**: Límite de horas de ejecución gratuitas
- **Ancho de banda limitado**: 100 GB/mes

### Mantener el Servicio Activo

Si quieres evitar la suspensión automática, puedes:

1. **Upgrade a plan de pago** ($7/mes mínimo)
2. **Usar un servicio de ping** (como UptimeRobot) para hacer requests cada 14 minutos

### Logs y Monitoreo

Para ver los logs de tu aplicación:
1. Ve a tu servicio en el Dashboard de Render
2. Haz clic en la pestaña **"Logs"**
3. Aquí verás todos los eventos y errores de la aplicación

### Health Check

La aplicación incluye un endpoint de salud:
```
https://tu-app.onrender.com/api/health
```

Puedes usarlo para verificar que la aplicación está funcionando correctamente.

## Actualizar la Aplicación

Cada vez que hagas cambios y los subas a tu repositorio:

```bash
git add .
git commit -m "Descripción de los cambios"
git push
```

Render automáticamente detectará los cambios y redesplegará la aplicación.

## Solución de Problemas

### Error: Application failed to start

1. Revisa los logs en el Dashboard de Render
2. Verifica que todas las variables de entorno estén configuradas
3. Asegúrate de que el comando de inicio sea correcto

### Error: Module not found

1. Verifica que `requirements.txt` incluya todas las dependencias
2. Asegúrate de que el build command sea `pip install -r requirements.txt`

### Error de conexión a base de datos

1. Verifica que las variables `DB_*` estén correctamente configuradas
2. Asegúrate de que la base de datos acepte conexiones desde la IP de Render

### La aplicación es muy lenta

1. El plan gratuito tiene recursos limitados
2. Considera upgrade a un plan de pago para mejor rendimiento
3. Optimiza las consultas a la base de datos

## Compartir el Enlace

Una vez desplegada, puedes compartir el enlace con cualquier persona:

```
https://tu-app.onrender.com
```

Las personas podrán acceder a la plataforma desde cualquier navegador, sin necesidad de instalar nada.

## Seguridad

### Recomendaciones:

1. **No subas archivos `.env` al repositorio**
   - Usa el archivo `.env.example` como plantilla
   - Configura las variables en el Dashboard de Render

2. **Cambia las credenciales por defecto**
   - Genera una nueva `SECRET_KEY`
   - Usa contraseñas seguras para la base de datos

3. **Considera añadir autenticación**
   - Si los datos son sensibles, implementa un sistema de login
   - Puedes usar Flask-Login o similar

## Contacto y Soporte

Si tienes problemas con el despliegue:
- [Documentación oficial de Render](https://render.com/docs)
- [Comunidad de Render](https://community.render.com)
- [Soporte de Render](https://render.com/support)

## Próximos Pasos

1. **Configurar un dominio personalizado** (opcional)
   - Puedes vincular tu propio dominio en la configuración del servicio

2. **Configurar SSL** (incluido automáticamente en Render)
   - Todos los servicios tienen HTTPS por defecto

3. **Monitoreo y alertas**
   - Configura notificaciones para errores o caídas del servicio

4. **Backups**
   - Asegúrate de tener backups de tu base de datos
   - Considera un servicio de backup automático
