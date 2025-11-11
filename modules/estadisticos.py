"""
Módulo de estadísticas generales
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import logging

from config import Config
from .utils import (
    load_excel_data,
    filter_promedio_global,
    fig_to_json,
    get_color_scheme
)

logger = logging.getLogger(__name__)


class EstadisticosModule:
    """Módulo para análisis de estadísticas generales del equipo"""

    def __init__(self):
        self.config = Config
        self.colors = get_color_scheme()
        self.archivo_promedios = self.config.ARCHIVO_PROMEDIOS_EQUIPOS
        self.equipo_destacado = self.config.EQUIPO_DESTACADO

    def get_resumen_estadistico(self) -> dict:
        """
        Obtiene resumen estadístico del equipo

        Returns:
            Diccionario con métricas principales
        """
        try:
            df = load_excel_data(self.archivo_promedios)
            df = filter_promedio_global(df)

            equipo_data = df[df['Equipo'] == self.equipo_destacado].iloc[0]

            resumen = {
                'goles_favor': float(equipo_data.get('team_goal', 0)),
                'goles_contra': float(equipo_data.get('opp_goal', 0)),
                'xg': float(equipo_data.get('team_xgShot', 0)),
                'xg_contra': float(equipo_data.get('opp_xgShot', 0)),
                'posesion': float(equipo_data.get('team_possession', 0)),
                'tiros': float(equipo_data.get('team_shot', 0)),
                'tiros_puerta': float(equipo_data.get('team_shotSuccess', 0)),
                'ppda': float(equipo_data.get('team_ppda', 0))
            }

            # Calcular posición en la liga
            total_equipos = len(df)
            goles_ranking = (df['team_goal'] > equipo_data['team_goal']).sum() + 1

            resumen['posicion_goles'] = goles_ranking
            resumen['total_equipos'] = total_equipos

            return resumen

        except Exception as e:
            logger.error(f"Error obteniendo resumen estadístico: {str(e)}")
            return {}

    def generar_comparativa_promedios(self) -> dict:
        """
        Genera comparativa del equipo vs promedio de liga

        Returns:
            Diccionario con visualización
        """
        try:
            logger.info("Generando comparativa de promedios...")

            df = load_excel_data(self.archivo_promedios)
            df = filter_promedio_global(df)

            equipo_data = df[df['Equipo'] == self.equipo_destacado].iloc[0]
            promedios_liga = df.mean(numeric_only=True)

            # Métricas a comparar
            metricas = {
                'team_goal': 'Goles a favor',
                'opp_goal': 'Goles en contra',
                'team_xgShot': 'xG',
                'team_possession': 'Posesión (%)',
                'team_shot': 'Tiros',
                'team_shotSuccess': 'Tiros a puerta'
            }

            # Crear figura
            fig, ax = plt.subplots(figsize=(12, 8))

            labels = list(metricas.values())
            equipo_values = [float(equipo_data.get(k, 0)) for k in metricas.keys()]
            liga_values = [float(promedios_liga.get(k, 0)) for k in metricas.keys()]

            x = np.arange(len(labels))
            width = 0.35

            bars1 = ax.bar(x - width/2, equipo_values, width,
                          label=self.equipo_destacado,
                          color=self.colors['penafiel'])
            bars2 = ax.bar(x + width/2, liga_values, width,
                          label='Promedio Liga',
                          color=self.colors['promedio'])

            # Añadir valores sobre las barras
            def autolabel(bars):
                for bar in bars:
                    height = bar.get_height()
                    ax.annotate(f'{height:.1f}',
                               xy=(bar.get_x() + bar.get_width() / 2, height),
                               xytext=(0, 3),
                               textcoords="offset points",
                               ha='center', va='bottom',
                               fontsize=9, fontweight='bold')

            autolabel(bars1)
            autolabel(bars2)

            ax.set_ylabel('Valor', fontsize=12, fontweight='bold')
            ax.set_title(f'Comparativa {self.equipo_destacado} vs Promedio Liga',
                        fontsize=14, fontweight='bold', pad=20)
            ax.set_xticks(x)
            ax.set_xticklabels(labels, rotation=45, ha='right')
            ax.legend(fontsize=11)

            ax.grid(True, axis='y', alpha=0.3)
            ax.set_axisbelow(True)

            plt.tight_layout()
            result = fig_to_json(fig)

            logger.info("Comparativa de promedios generada exitosamente")
            return {
                'status': 'success',
                'data': result,
                'message': 'Comparativa generada correctamente'
            }

        except Exception as e:
            logger.error(f"Error generando comparativa: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
