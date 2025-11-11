"""
Plataforma Web FC Penafiel
Portal de visualización de datos físicos y estadísticos
"""

from flask import Flask, render_template, jsonify, send_file, request
from flask_cors import CORS
import os
from datetime import datetime
import logging
from pathlib import Path

# Importar configuración
from config import Config

# Importar módulos de visualización
from modules.fisicos import FisicosModule
from modules.estadisticos import EstadisticosModule
from modules.rankings import RankingsModule
from modules.estilo_juego import EstiloJuegoModule

# Importar programador de actualización automática
from scheduler import scheduler

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Crear aplicación Flask
app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Inicializar módulos
fisicos = FisicosModule()
estadisticos = EstadisticosModule()
rankings = RankingsModule()
estilo_juego = EstiloJuegoModule()


# ==================== RUTAS PRINCIPALES ====================

@app.route('/')
def index():
    """Página principal con dashboard general"""
    return render_template('index.html',
                         titulo="Dashboard General",
                         ultima_actualizacion=datetime.now().strftime("%d/%m/%Y %H:%M"))


@app.route('/fisicos')
def fisicos_view():
    """Vista de datos físicos - Control de Competición"""
    return render_template('fisicos.html',
                         titulo="Control de Competición")


@app.route('/microciclos')
def microciclos_view():
    """Vista de microciclos de entrenamiento"""
    return render_template('microciclos.html',
                         titulo="Control de Microciclos")


@app.route('/estadisticos')
def estadisticos_view():
    """Vista de datos estadísticos"""
    return render_template('estadisticos.html',
                         titulo="Análisis Estadístico")


@app.route('/rankings')
def rankings_view():
    """Vista de rankings - Rendimiento Colectivo"""
    return render_template('rankings.html',
                         titulo="Rendimiento Colectivo")


@app.route('/rendimiento-individual')
def rendimiento_individual_view():
    """Vista de rendimiento individual"""
    return render_template('rendimiento_individual.html',
                         titulo="Rendimiento Individual")


@app.route('/medico')
def medico_view():
    """Vista de control médico"""
    return render_template('medico.html',
                         titulo="Control Médico")


@app.route('/antropometrico')
def antropometrico_view():
    """Vista de control antropométrico"""
    return render_template('antropometrico.html',
                         titulo="Control Antropométrico")


@app.route('/psicologico')
def psicologico_view():
    """Vista de control psicológico"""
    return render_template('psicologico.html',
                         titulo="Control Psicológico")


@app.route('/capacidad-funcional')
def capacidad_funcional_view():
    """Vista de capacidad funcional"""
    return render_template('capacidad_funcional.html',
                         titulo="Capacidad Funcional")


@app.route('/ficha-jugador')
def ficha_jugador_view():
    """Vista de ficha del jugador"""
    return render_template('ficha_jugador.html',
                         titulo="Ficha del Jugador")


@app.route('/estilo-juego')
def estilo_juego_view():
    """Vista de estilo de juego"""
    return render_template('estilo_juego.html',
                         titulo="Estilo de Juego")


# ==================== API ENDPOINTS ====================

@app.route('/api/fisicos/barras-colectivas')
def api_fisicos_barras_colectivas():
    """API para obtener gráficas de barras colectivas"""
    try:
        data = fisicos.generar_barras_colectivas()
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error en barras colectivas: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/fisicos/barras-individuales')
def api_fisicos_barras_individuales():
    """API para obtener gráficas de barras individuales"""
    try:
        data = fisicos.generar_barras_individuales()
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error en barras individuales: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/fisicos/evolutivo')
def api_fisicos_evolutivo():
    """API para obtener gráficas evolutivas físicas"""
    try:
        data = fisicos.generar_evolutivo()
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error en evolutivo físico: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/fisicos/partidos')
def api_fisicos_partidos():
    """API para obtener lista de partidos disponibles"""
    try:
        data = fisicos.obtener_lista_partidos()
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error obteniendo lista de partidos: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/fisicos/scatter-individual')
def api_fisicos_scatter_individual():
    """API para obtener scatter individual por partido"""
    try:
        partido = request.args.get('partido', None)
        data = fisicos.generar_scatter_individual(partido)
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error en scatter individual: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/microciclos/lista')
def api_microciclos_lista():
    """API para obtener lista de microciclos disponibles"""
    try:
        data = fisicos.obtener_lista_microciclos()
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error obteniendo lista de microciclos: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/microciclos/equipo')
def api_microciclos_equipo():
    """API para obtener datos de microciclo por equipo"""
    try:
        jornada = request.args.get('jornada', None)
        tipo_distancia = request.args.get('tipo_distancia', 'Distancia_total')
        data = fisicos.obtener_datos_microciclo_equipo(jornada, tipo_distancia)
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error obteniendo datos de microciclo: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/rankings/global')
def api_rankings_global():
    """API para obtener ranking global de liga"""
    try:
        data = rankings.generar_ranking_global()
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error en ranking global: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/rankings/verticales')
def api_rankings_verticales():
    """API para obtener gráficas verticales de rankings"""
    try:
        data = rankings.generar_graficas_verticales()
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error en gráficas verticales: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/estilo-juego/scatter-ofensivo')
def api_scatter_ofensivo():
    """API para obtener scatter ofensivo"""
    try:
        data = estilo_juego.generar_scatter_ofensivo()
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error en scatter ofensivo: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/estilo-juego/scatter-defensivo')
def api_scatter_defensivo():
    """API para obtener scatter defensivo"""
    try:
        data = estilo_juego.generar_scatter_defensivo()
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error en scatter defensivo: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/estadisticos/resumen')
def api_estadisticos_resumen():
    """API para obtener resumen estadístico"""
    try:
        data = estadisticos.get_resumen_estadistico()
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error en resumen estadístico: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/estadisticos/comparativa')
def api_estadisticos_comparativa():
    """API para obtener comparativa vs promedio liga"""
    try:
        data = estadisticos.generar_comparativa_promedios()
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error en comparativa: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/actualizar-datos')
def api_actualizar_datos():
    """API para forzar actualización de datos"""
    try:
        # Implementar lógica de actualización
        return jsonify({'status': 'success', 'message': 'Datos actualizados correctamente'})
    except Exception as e:
        logger.error(f"Error al actualizar datos: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/health')
def health_check():
    """Endpoint de salud para monitoreo"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })


# ==================== MANEJO DE ERRORES ====================

@app.errorhandler(404)
def not_found(error):
    """Manejo de página no encontrada"""
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """Manejo de error interno del servidor"""
    logger.error(f"Error interno: {str(error)}")
    return render_template('500.html'), 500


# ==================== INICIALIZACIÓN ====================

if __name__ == '__main__':
    # Crear directorios necesarios si no existen
    Path('logs').mkdir(exist_ok=True)
    Path('data').mkdir(exist_ok=True)
    Config.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Iniciar programador de actualización automática
    logger.info("Iniciando sistema de actualización automática...")
    scheduler.start()

    # Registrar cierre del programador al cerrar la app
    import atexit
    atexit.register(lambda: scheduler.stop())

    # Iniciar aplicación
    logger.info("Iniciando Plataforma FC Penafiel...")
    logger.info(f"Servidor: http://{Config.HOST}:{Config.PORT}")
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )
