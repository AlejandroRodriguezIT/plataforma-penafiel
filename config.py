"""
Configuración de la Plataforma FC Penafiel
"""

import os
from pathlib import Path

class Config:
    """Configuración base de la aplicación"""

    # Configuración del servidor
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Rutas de datos
    BASE_DIR = Path(__file__).parent
    # Permitir rutas configurables via variables de entorno o usar rutas locales por defecto
    DATA_DIR = Path(os.environ.get('DATA_DIR', r"C:\Users\DEPOR\OneDrive - Real Club Deportivo de La Coruña\IT\Penafiel\Datos"))
    CODIGOS_DIR = Path(os.environ.get('CODIGOS_DIR', r"C:\Users\DEPOR\OneDrive - Real Club Deportivo de La Coruña\IT\Penafiel\Automatizacion_Datos\Codigos"))
    GRAFICAS_DIR = Path(os.environ.get('GRAFICAS_DIR', r"C:\Users\DEPOR\OneDrive - Real Club Deportivo de La Coruña\IT\Penafiel\Graficas"))

    # Rutas específicas de datos
    DATOS_FISICOS = DATA_DIR / "Fisicos"
    DATOS_ESTADISTICOS = DATA_DIR / "Estadisticos"

    # Archivos de datos principales
    ARCHIVO_PARTIDOS_COMPLETO = DATOS_FISICOS / "Partidos" / "Partidos_Completo.xlsx"
    ARCHIVO_ENTRENOS = DATOS_FISICOS / "Entrenos" / "Entrenos_Completo.xlsx"
    ARCHIVO_PROMEDIOS_EQUIPOS = DATOS_ESTADISTICOS / "Promedios" / "promedios_equipos.xlsx"
    ARCHIVO_RESULTADOS = DATA_DIR / "Resultados.xlsx"

    # Configuración de base de datos
    DB_USER = os.environ.get('DB_USER', 'alen_depor')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'ik3QJOq6n')
    DB_HOST = os.environ.get('DB_HOST', '82.165.192.201')
    DB_NAME = os.environ.get('DB_NAME', 'penafiel')

    # Configuración de visualizaciones
    EQUIPO_DESTACADO = "Penafiel"
    COLOR_PENAFIEL = "#9b59b6"  # Lila
    COLOR_PROMEDIO = "#2ecc71"  # Verde
    COLOR_OTROS = "#95a5a6"     # Gris

    # Configuración de actualización automática
    AUTO_UPDATE_ENABLED = True
    UPDATE_INTERVAL_MINUTES = 30  # Actualizar cada 30 minutos

    # Configuración de caché
    CACHE_ENABLED = True
    CACHE_DIR = BASE_DIR / "data" / "cache"
    CACHE_TIMEOUT_MINUTES = 15

    # Configuración de logs
    LOG_DIR = BASE_DIR / "logs"
    LOG_LEVEL = "INFO"

    # Jornada actual (configurable)
    JORNADA_ACTUAL = 10

    # Métricas para rankings
    METRICS_RANKINGS = {
        "team_xgShot": "xG (expected goals)",
        "team_goal": "Goles a Favor",
        "team_shot": "Tiros",
        "team_shotSuccess": "Tiros a puerta",
        "team_possession": "Posesión (%)",
        "team_ppda": "PPDA",
        "opp_xgShot": "xG en Contra",
        "opp_goal": "Goles en Contra",
        "opp_shot": "Tiros en Contra",
        "opp_shotSuccess": "Tiros a puerta en Contra"
    }

    # Métricas inversas (menor es mejor)
    INVERSE_METRICS = {
        "opp_xgShot": True,
        "opp_goal": True,
        "opp_shot": True,
        "opp_shotSuccess": True,
        "team_ppda": True
    }

    @classmethod
    def init_app(cls, app):
        """Inicializar configuración de la aplicación"""
        # Crear directorios necesarios
        cls.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOG_DIR.mkdir(parents=True, exist_ok=True)


class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False
    TESTING = False
    # Cambiar SECRET_KEY en producción
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'production-secret-key'


class TestingConfig(Config):
    """Configuración para testing"""
    DEBUG = True
    TESTING = True


# Diccionario de configuraciones
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
