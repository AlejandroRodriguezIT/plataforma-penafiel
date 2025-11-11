# Plataforma FC Penafiel

Portal web para visualización y análisis de datos físicos y estadísticos del FC Penafiel.

## Características

- **Dashboard General**: Vista unificada de todas las métricas principales
- **Análisis Físico**: Visualización de datos de rendimiento físico de jugadores
  - Barras colectivas
  - Barras individuales por jugador
  - Evolutivos de partidos
- **Análisis Estadístico**: Métricas de juego y rendimiento del equipo
  - Rankings de liga
  - Gráficas comparativas verticales
- **Estilo de Juego**: Análisis de patrones ofensivos y defensivos
  - Scatter ofensivo
  - Scatter defensivo
- **Actualización Automática**: Los datos se actualizan automáticamente cada 30 minutos

## Estructura del Proyecto

```
Plataforma_Penafiel/
├── app.py                  # Aplicación principal Flask
├── config.py               # Configuración
├── requirements.txt        # Dependencias Python
├── README.md              # Este archivo
├── .env                   # Variables de entorno (no incluido en git)
├── .gitignore            # Archivos ignorados por git
│
├── modules/              # Módulos de generación de visualizaciones
│   ├── __init__.py
│   ├── fisicos.py        # Módulo de datos físicos
│   ├── estadisticos.py   # Módulo de datos estadísticos
│   ├── rankings.py       # Módulo de rankings
│   ├── estilo_juego.py   # Módulo de estilo de juego
│   └── utils.py          # Utilidades compartidas
│
├── static/               # Archivos estáticos
│   ├── css/
│   │   ├── main.css      # Estilos principales
│   │   └── dashboard.css # Estilos del dashboard
│   ├── js/
│   │   ├── main.js       # JavaScript principal
│   │   ├── charts.js     # Manejo de gráficas
│   │   └── api.js        # Llamadas a API
│   └── img/
│       └── logo.png      # Logo del equipo
│
├── templates/            # Plantillas HTML
│   ├── base.html         # Plantilla base
│   ├── index.html        # Dashboard principal
│   ├── fisicos.html      # Vista de datos físicos
│   ├── estadisticos.html # Vista de datos estadísticos
│   ├── rankings.html     # Vista de rankings
│   ├── estilo_juego.html # Vista de estilo de juego
│   ├── 404.html          # Página de error 404
│   ├── 500.html          # Página de error 500
│   └── partials/         # Componentes reutilizables
│       ├── navbar.html
│       ├── footer.html
│       └── sidebar.html
│
├── data/                 # Datos y caché
│   └── cache/            # Caché de visualizaciones
│
└── logs/                 # Logs de la aplicación
    └── app.log
```

## Instalación

### Requisitos Previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Pasos de Instalación

1. **Clonar o descargar el proyecto**

2. **Crear un entorno virtual** (recomendado)
   ```bash
   python -m venv venv
   ```

3. **Activar el entorno virtual**
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

4. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configurar variables de entorno** (opcional)
   Crear un archivo `.env` en la raíz del proyecto:
   ```
   FLASK_ENV=development
   SECRET_KEY=tu-clave-secreta
   ```

## Uso

### Iniciar el servidor en modo desarrollo

```bash
python app.py
```

La aplicación estará disponible en: `http://localhost:5000`

### Iniciar el servidor en modo producción

```bash
waitress-serve --host=0.0.0.0 --port=5000 app:app
```

O usando gunicorn (Linux/Mac):
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## API Endpoints

### Datos Físicos
- `GET /api/fisicos/barras-colectivas` - Barras colectivas
- `GET /api/fisicos/barras-individuales` - Barras individuales
- `GET /api/fisicos/evolutivo` - Evolutivo de partidos

### Rankings
- `GET /api/rankings/global` - Ranking global de liga
- `GET /api/rankings/verticales` - Gráficas verticales

### Estilo de Juego
- `GET /api/estilo-juego/scatter-ofensivo` - Scatter ofensivo
- `GET /api/estilo-juego/scatter-defensivo` - Scatter defensivo

### Utilidades
- `GET /api/actualizar-datos` - Forzar actualización de datos
- `GET /api/health` - Estado de salud de la aplicación

## Configuración

Editar el archivo `config.py` para cambiar:
- Rutas de datos
- Colores del equipo
- Intervalo de actualización automática
- Puerto del servidor
- Otras configuraciones

## Desarrollo

### Agregar nuevas visualizaciones

1. Crear un nuevo método en el módulo correspondiente (e.g., `modules/fisicos.py`)
2. Agregar una nueva ruta en `app.py`
3. Crear la vista correspondiente en `templates/`
4. Actualizar el frontend para consumir la nueva API

### Testing

```bash
pytest tests/
```

## Solución de Problemas

### Error: No se encuentra el archivo de datos
- Verificar que las rutas en `config.py` sean correctas
- Asegurarse de que los archivos Excel existan en las ubicaciones especificadas

### Error: Puerto 5000 ya en uso
- Cambiar el puerto en `config.py` o usar:
  ```bash
  python app.py --port 8000
  ```

### Error de permisos
- Verificar permisos de lectura en las carpetas de datos
- Verificar permisos de escritura en carpetas `logs/` y `data/`

## Contribuciones

Este es un proyecto interno del FC Penafiel. Para sugerencias o reportar bugs, contactar con el equipo de IT.

## Licencia

Uso interno FC Penafiel - Todos los derechos reservados

## Contacto

Departamento IT - FC Penafiel
