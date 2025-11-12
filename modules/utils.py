"""
Utilidades compartidas para módulos de visualización
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Backend sin GUI para servidor
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from pathlib import Path
import logging
from sqlalchemy import create_engine
from config import Config

logger = logging.getLogger(__name__)

# Configurar estilo de matplotlib
plt.style.use('default')
sns.set_palette("deep")


def get_db_engine():
    """
    Crea un engine de SQLAlchemy para conectar a MySQL

    Returns:
        Engine de SQLAlchemy
    """
    try:
        # Crear URL de conexión
        connection_url = f"mysql+pymysql://{Config.DB_USER}:{Config.DB_PASSWORD}@{Config.DB_HOST}/{Config.DB_NAME}?charset=utf8mb4"

        # Crear engine
        engine = create_engine(connection_url, pool_pre_ping=True)
        return engine
    except Exception as e:
        logger.error(f"Error creando engine de base de datos: {str(e)}")
        raise


def load_from_database(table_name: str) -> pd.DataFrame:
    """
    Carga datos desde una tabla de MySQL con conversión automática de tipos

    Args:
        table_name: Nombre de la tabla

    Returns:
        DataFrame con los datos
    """
    try:
        engine = get_db_engine()
        query = f"SELECT * FROM {table_name}"
        df = pd.read_sql(query, engine)

        # Limpiar nombres de columnas
        df.columns = df.columns.str.strip()

        # Convertir columnas de fecha si existen
        date_columns = ['Fecha', 'fecha', 'Date', 'date']
        for col in df.columns:
            if col in date_columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

        # Procesar columna Jornada de manera especial (puede venir como "Jornada 1", "J1", etc.)
        if 'Jornada' in df.columns:
            # Mostrar valores únicos para debug
            logger.info(f"Valores únicos en Jornada antes de conversión: {df['Jornada'].unique()[:10]}")

            # Intentar extraer solo números de la columna Jornada
            df['Jornada'] = df['Jornada'].astype(str).str.extract(r'(\d+)', expand=False)
            df['Jornada'] = pd.to_numeric(df['Jornada'], errors='coerce')

            logger.info(f"Valores únicos en Jornada después de conversión: {df['Jornada'].unique()[:10]}")

        # Convertir columnas numéricas comunes
        numeric_columns = [
            'Minutos_jugados', 'Distancia_total', 'Distancia_HSR', 'Distancia_Sprint',
            'Velocidad_Maxima', 'id', 'team_xgShot', 'team_goal', 'team_shot',
            'team_shotSuccess', 'team_possession', 'team_ppda', 'opp_xgShot', 'opp_goal',
            'opp_shot', 'opp_shotSuccess', 'team_passToFinalThird', 'opp_passToFinalThird',
            'Codigo'
        ]

        for col in df.columns:
            if col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Limpiar columnas de texto (eliminar espacios adicionales)
        text_columns = ['Sesion', 'Tarea', 'Jugador', 'Partido', 'Situacion', 'Posicion', 'Equipo', 'Resultado']
        for col in df.columns:
            if col in text_columns and col in df.columns:
                df[col] = df[col].astype(str).str.strip()

        logger.info(f"Datos cargados exitosamente desde la tabla {table_name}")
        return df
    except Exception as e:
        logger.error(f"Error cargando desde tabla {table_name}: {str(e)}")
        raise


def safe_div(a: pd.Series, b: pd.Series) -> pd.Series:
    """
    División segura que evita división por cero

    Args:
        a: Serie numerador
        b: Serie denominador

    Returns:
        Serie con el resultado de la división
    """
    b = b.replace(0, np.nan)
    return a / b


def to_numeric(s: pd.Series) -> pd.Series:
    """
    Convierte una serie a numérica manejando formatos especiales

    Args:
        s: Serie a convertir

    Returns:
        Serie numérica
    """
    if pd.api.types.is_numeric_dtype(s):
        return s
    s = (
        s.astype(str)
         .str.replace("%", "", regex=False)
         .str.replace(",", ".", regex=False)
         .str.strip()
    )
    return pd.to_numeric(s, errors="coerce")


def load_excel_data(file_path: Path, sheet_name: str = None) -> pd.DataFrame:
    """
    Carga datos directamente desde la base de datos MySQL

    IMPORTANTE: Esta función ahora carga EXCLUSIVAMENTE desde base de datos.
    Los archivos Excel locales ya no se utilizan.

    Args:
        file_path: Ruta al archivo Excel (solo para obtener el mapeo a tabla)
        sheet_name: Nombre de la hoja (ignorado, mantenido por compatibilidad)

    Returns:
        DataFrame con los datos desde MySQL
    """
    # Mapeo de archivos a tablas de base de datos
    file_to_table_map = {
        'Entrenos_Completo.xlsx': 'Datos_Fisicos_Entreno',
        'Partidos_Completo.xlsx': 'Datos_Fisicos_Partido',
        'promedios_equipos.xlsx': 'Datos_Estadisticos_Promedio',
        'Resultados.xlsx': 'Resultado',
    }

    # Obtener nombre del archivo
    file_name = Path(file_path).name

    # Buscar tabla correspondiente
    table_name = file_to_table_map.get(file_name)

    if not table_name:
        logger.error(f"No hay mapeo de tabla para el archivo {file_name}")
        raise ValueError(f"Archivo {file_name} sin mapeo a tabla de BD")

    try:
        # Cargar directamente desde base de datos
        logger.info(f"Cargando datos desde base de datos (tabla {table_name})...")
        df = load_from_database(table_name)
        logger.info(f"Datos cargados exitosamente desde tabla {table_name}")
        return df
    except Exception as e:
        logger.error(f"Error cargando desde base de datos (tabla {table_name}): {str(e)}")
        raise


def filter_promedio_global(df: pd.DataFrame, column: str = 'Equipo') -> pd.DataFrame:
    """
    Filtra la fila de promedio global de la competición

    Args:
        df: DataFrame a filtrar
        column: Nombre de la columna que contiene los nombres de equipos

    Returns:
        DataFrame filtrado
    """
    return df[df[column] != 'PROMEDIO GLOBAL COMPETICIÓN'].reset_index(drop=True)


def fig_to_base64(fig) -> str:
    """
    Convierte una figura de matplotlib a base64 para usar en HTML

    Args:
        fig: Figura de matplotlib

    Returns:
        String en base64 de la imagen
    """
    buffer = io.BytesIO()
    fig.savefig(buffer, format='png', dpi=180, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    plt.close(fig)
    return image_base64


def fig_to_json(fig) -> dict:
    """
    Convierte una figura de matplotlib a formato JSON con imagen base64

    Args:
        fig: Figura de matplotlib

    Returns:
        Diccionario con la imagen en base64
    """
    img_base64 = fig_to_base64(fig)
    return {
        'image': img_base64,
        'format': 'png'
    }


def create_plotly_config() -> dict:
    """
    Configuración estándar para gráficas Plotly

    Returns:
        Diccionario de configuración
    """
    return {
        'displayModeBar': True,
        'displaylogo': False,
        'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d'],
        'toImageButtonOptions': {
            'format': 'png',
            'filename': 'grafica_penafiel',
            'height': 800,
            'width': 1200,
            'scale': 2
        }
    }


def get_color_scheme():
    """
    Esquema de colores estándar para la plataforma
    Colores corporativos FC Penafiel: Rojo y Negro

    Returns:
        Diccionario con los colores
    """
    return {
        'penafiel': '#DC143C',   # Rojo Penafiel (Crimson)
        'promedio': '#2ecc71',   # Verde
        'otros': '#95a5a6',      # Gris
        'fondo': '#f5f6fa',      # Gris claro
        'success': '#27ae60',    # Verde oscuro
        'warning': '#f39c12',    # Naranja
        'danger': '#DC143C',     # Rojo Penafiel
        'info': '#1a1a1a',       # Negro corporativo
        'negro': '#000000',      # Negro puro
        'rojo': '#DC143C'        # Rojo corporativo
    }


def format_metric_name(metric_key: str, spanish_names: dict) -> str:
    """
    Formatea el nombre de una métrica

    Args:
        metric_key: Clave de la métrica
        spanish_names: Diccionario con traducciones

    Returns:
        Nombre formateado
    """
    return spanish_names.get(metric_key, metric_key.replace('_', ' ').title())


def calculate_percentile_rank(value: float, series: pd.Series, higher_is_better: bool = True) -> float:
    """
    Calcula el percentil de un valor en una serie

    Args:
        value: Valor a evaluar
        series: Serie de valores para comparar
        higher_is_better: Si True, valores más altos son mejores

    Returns:
        Percentil (0-100)
    """
    if higher_is_better:
        percentile = (series < value).sum() / len(series) * 100
    else:
        percentile = (series > value).sum() / len(series) * 100
    return round(percentile, 1)


def validate_dataframe(df: pd.DataFrame, required_columns: list) -> bool:
    """
    Valida que un DataFrame tenga las columnas requeridas

    Args:
        df: DataFrame a validar
        required_columns: Lista de columnas requeridas

    Returns:
        True si todas las columnas existen, False en caso contrario
    """
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        logger.warning(f"Columnas faltantes: {missing_columns}")
        return False
    return True


class CacheManager:
    """Gestor de caché para visualizaciones"""

    def __init__(self, cache_dir: Path, timeout_minutes: int = 15):
        self.cache_dir = cache_dir
        self.timeout_minutes = timeout_minutes
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get(self, key: str):
        """Obtiene un valor del caché"""
        # Implementar lógica de caché
        pass

    def set(self, key: str, value):
        """Guarda un valor en caché"""
        # Implementar lógica de caché
        pass

    def clear(self):
        """Limpia el caché"""
        # Implementar lógica de limpieza
        pass
