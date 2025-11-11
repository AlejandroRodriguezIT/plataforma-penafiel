# Inicio Rápido - Plataforma FC Penafiel

Guía rápida para poner en marcha la plataforma en pocos minutos.

## Requisitos Previos

- Python 3.8 o superior instalado
- Acceso a los archivos de datos del club

## Pasos de Instalación

### 1. Navegar al directorio del proyecto

```bash
cd "C:\Users\DEPOR\OneDrive - Real Club Deportivo de La Coruña\IT\Penafiel\Automatizacion_Datos\Plataforma_Penafiel"
```

### 2. Crear entorno virtual

```bash
python -m venv venv
```

### 3. Activar el entorno virtual

```bash
venv\Scripts\activate
```

### 4. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 5. Verificar configuración

Abre el archivo `config.py` y verifica que las rutas de datos sean correctas:
- `DATOS_FISICOS`
- `DATOS_ESTADISTICOS`
- `ARCHIVO_PARTIDOS_COMPLETO`
- `ARCHIVO_PROMEDIOS_EQUIPOS`

### 6. Crear archivo de variables de entorno (opcional)

```bash
copy .env.example .env
```

Edita `.env` según tus necesidades.

### 7. Iniciar la aplicación

```bash
python app.py
```

### 8. Abrir en el navegador

Abre tu navegador y ve a: **http://localhost:5000**

## Solución de Problemas Comunes

### Error: No se encuentra el archivo de datos

**Solución**: Verifica en `config.py` que las rutas sean correctas y que los archivos existan.

### Error: Puerto 5000 ya en uso

**Solución**: Cambia el puerto en `config.py` o en el archivo `.env`:
```
PORT=8000
```

### Error al instalar dependencias

**Solución**: Asegúrate de tener pip actualizado:
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Las gráficas no se muestran

**Solución**:
1. Verifica que los archivos Excel existan y tengan datos
2. Revisa los logs en la carpeta `logs/app.log`
3. Recarga la página (F5)

## Características de la Plataforma

✅ **Dashboard General** - Vista unificada de métricas principales
✅ **Análisis Físico** - Datos de rendimiento físico de jugadores
✅ **Rankings** - Comparativas con otros equipos de la liga
✅ **Estilo de Juego** - Análisis ofensivo y defensivo
✅ **Actualización Automática** - Los datos se actualizan cada 30 minutos

## Comandos Útiles

### Detener el servidor
Presiona `Ctrl + C` en la terminal

### Desactivar entorno virtual
```bash
deactivate
```

### Ver logs en tiempo real
```bash
tail -f logs/app.log
```

### Limpiar caché
```bash
rmdir /s /q data\cache
```

## Próximos Pasos

1. Revisa el archivo `README.md` para información detallada
2. Explora las diferentes secciones de la plataforma
3. Personaliza los colores y configuración en `config.py`
4. Agrega nuevas visualizaciones según tus necesidades

## Soporte

Para reportar problemas o sugerencias:
- Revisa los logs en `logs/app.log`
- Contacta al Departamento IT del FC Penafiel

---

**¡Listo!** Tu plataforma debería estar funcionando correctamente. 🚀
