"""
Sistema de actualización automática de datos
Plataforma FC Penafiel
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import logging
from pathlib import Path

from config import Config

logger = logging.getLogger(__name__)


class DataUpdateScheduler:
    """Programador de actualización automática de datos"""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.config = Config
        self.is_running = False

    def start(self):
        """Inicia el programador"""
        if self.is_running:
            logger.warning("El programador ya está en ejecución")
            return

        if not self.config.AUTO_UPDATE_ENABLED:
            logger.info("Actualización automática deshabilitada en configuración")
            return

        try:
            # Job de actualización periódica
            self.scheduler.add_job(
                func=self.actualizar_datos,
                trigger=IntervalTrigger(minutes=self.config.UPDATE_INTERVAL_MINUTES),
                id='actualizar_datos',
                name='Actualización periódica de datos',
                replace_existing=True
            )

            # Job de limpieza de caché diaria
            self.scheduler.add_job(
                func=self.limpiar_cache,
                trigger=CronTrigger(hour=3, minute=0),  # Todos los días a las 3:00 AM
                id='limpiar_cache',
                name='Limpieza de caché diaria',
                replace_existing=True
            )

            # Job de verificación de salud cada 5 minutos
            self.scheduler.add_job(
                func=self.verificar_salud,
                trigger=IntervalTrigger(minutes=5),
                id='verificar_salud',
                name='Verificación de salud',
                replace_existing=True
            )

            self.scheduler.start()
            self.is_running = True
            logger.info(f"Programador iniciado. Actualización cada {self.config.UPDATE_INTERVAL_MINUTES} minutos")

        except Exception as e:
            logger.error(f"Error al iniciar programador: {str(e)}")

    def stop(self):
        """Detiene el programador"""
        if not self.is_running:
            return

        try:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Programador detenido")
        except Exception as e:
            logger.error(f"Error al detener programador: {str(e)}")

    def actualizar_datos(self):
        """Actualiza los datos desde las fuentes"""
        try:
            logger.info("Iniciando actualización automática de datos...")

            # TODO: Implementar lógica de actualización de datos
            # Aquí podrías:
            # 1. Verificar si hay nuevos archivos Excel
            # 2. Procesar los datos
            # 3. Regenerar visualizaciones si es necesario
            # 4. Actualizar caché

            # Ejemplo de verificación de archivos
            archivo_promedios = self.config.ARCHIVO_PROMEDIOS_EQUIPOS
            if archivo_promedios.exists():
                ultima_modificacion = datetime.fromtimestamp(archivo_promedios.stat().st_mtime)
                logger.info(f"Archivo promedios última modificación: {ultima_modificacion}")

            logger.info("Actualización automática completada")

        except Exception as e:
            logger.error(f"Error en actualización automática: {str(e)}")

    def limpiar_cache(self):
        """Limpia los archivos de caché antiguos"""
        try:
            logger.info("Iniciando limpieza de caché...")

            cache_dir = self.config.CACHE_DIR
            if not cache_dir.exists():
                return

            # Eliminar archivos de caché más antiguos que el timeout
            timeout_minutes = self.config.CACHE_TIMEOUT_MINUTES
            now = datetime.now()

            archivos_eliminados = 0
            for archivo in cache_dir.glob('*'):
                if archivo.is_file():
                    tiempo_modificacion = datetime.fromtimestamp(archivo.stat().st_mtime)
                    diferencia = (now - tiempo_modificacion).total_seconds() / 60

                    if diferencia > timeout_minutes:
                        archivo.unlink()
                        archivos_eliminados += 1

            logger.info(f"Limpieza de caché completada. {archivos_eliminados} archivos eliminados")

        except Exception as e:
            logger.error(f"Error en limpieza de caché: {str(e)}")

    def verificar_salud(self):
        """Verifica el estado de salud del sistema"""
        try:
            # Verificar que los archivos de datos existan
            archivos_criticos = [
                self.config.ARCHIVO_PROMEDIOS_EQUIPOS,
                self.config.ARCHIVO_PARTIDOS_COMPLETO
            ]

            archivos_faltantes = []
            for archivo in archivos_criticos:
                if not archivo.exists():
                    archivos_faltantes.append(str(archivo))

            if archivos_faltantes:
                logger.warning(f"Archivos de datos faltantes: {archivos_faltantes}")

            # Verificar espacio en disco para logs y caché
            import shutil
            stats = shutil.disk_usage(self.config.BASE_DIR)
            espacio_libre_gb = stats.free / (1024 ** 3)

            if espacio_libre_gb < 1:  # Menos de 1 GB libre
                logger.warning(f"Espacio en disco bajo: {espacio_libre_gb:.2f} GB libres")

        except Exception as e:
            logger.error(f"Error en verificación de salud: {str(e)}")

    def get_status(self):
        """Obtiene el estado actual del programador"""
        if not self.is_running:
            return {
                'running': False,
                'message': 'Programador detenido'
            }

        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None
            })

        return {
            'running': True,
            'jobs': jobs,
            'update_interval_minutes': self.config.UPDATE_INTERVAL_MINUTES
        }


# Instancia global del programador
scheduler = DataUpdateScheduler()


def init_scheduler(app):
    """Inicializa el programador con la aplicación Flask"""
    @app.before_first_request
    def start_scheduler():
        scheduler.start()
        logger.info("Sistema de actualización automática iniciado")

    # Registrar el cierre del programador al cerrar la app
    import atexit
    atexit.register(lambda: scheduler.stop())


if __name__ == "__main__":
    # Prueba del programador
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("Iniciando programador de prueba...")
    scheduler.start()

    print(f"Estado: {scheduler.get_status()}")
    print("Presiona Ctrl+C para detener...")

    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nDeteniendo programador...")
        scheduler.stop()
        print("Programador detenido")
