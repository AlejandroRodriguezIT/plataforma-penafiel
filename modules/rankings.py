"""
Módulo de rankings y comparativas de liga
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
    get_color_scheme,
    safe_div
)

logger = logging.getLogger(__name__)


class RankingsModule:
    """Módulo para generar rankings y gráficas comparativas"""

    def __init__(self):
        self.config = Config
        self.colors = get_color_scheme()
        self.archivo_promedios = self.config.ARCHIVO_PROMEDIOS_EQUIPOS
        self.equipo_destacado = self.config.EQUIPO_DESTACADO

    def generar_ranking_global(self) -> dict:
        """
        Genera gráfica de ranking global en todas las métricas

        Returns:
            Diccionario con los datos de la visualización
        """
        try:
            logger.info("Generando ranking global...")

            # Cargar datos
            df = load_excel_data(self.archivo_promedios)
            df = filter_promedio_global(df)

            # Encontrar datos del equipo
            equipo_data = df[df['Equipo'] == self.equipo_destacado].iloc[0]

            # Definir métricas
            metrics_config = {
                'eficacia_ofensiva': {
                    'formula': lambda df_input: safe_div(df_input["team_shot"], df_input["team_passToFinalThird"]) * 100,
                    'higher_better': True,
                    'label': 'Eficacia construcción ofensiva (%)'
                },
                'expected_goals': {
                    'formula': lambda df_input: df_input['team_xgShot'],
                    'higher_better': True,
                    'label': 'Expected Goals (XG)'
                },
                'eficacia_finalizacion': {
                    'formula': lambda df_input: safe_div(df_input["team_goal"], df_input["team_shot"]) * 100,
                    'higher_better': True,
                    'label': 'Eficacia finalización (%)'
                },
                'goles_a_favor': {
                    'formula': lambda df_input: df_input['team_goal'],
                    'higher_better': True,
                    'label': 'Goles a favor'
                },
                'eficacia_defensiva': {
                    'formula': lambda df_input: 100 - safe_div(df_input["opp_shot"], df_input["opp_passToFinalThird"]) * 100,
                    'higher_better': True,
                    'label': 'Eficacia de contención defensiva (%)'
                },
                'expected_goals_contra': {
                    'formula': lambda df_input: df_input['opp_xgShot'],
                    'higher_better': False,
                    'label': 'Expected goals en contra'
                },
                'eficacia_evitacion': {
                    'formula': lambda df_input: 100 - safe_div(df_input["opp_goal"], df_input["opp_shot"]) * 100,
                    'higher_better': True,
                    'label': 'Eficacia evitación (%)'
                },
                'goles_en_contra': {
                    'formula': lambda df_input: df_input['opp_goal'],
                    'higher_better': False,
                    'label': 'Goles en contra'
                }
            }

            # Calcular rankings
            rankings = {}
            values = {}

            for metric_name, config in metrics_config.items():
                df[metric_name] = config['formula'](df)

                if config['higher_better']:
                    df_sorted = df.sort_values(metric_name, ascending=False, na_position='last')
                else:
                    df_sorted = df.sort_values(metric_name, ascending=True, na_position='last')

                position = df_sorted.reset_index().index[df_sorted['Equipo'] == self.equipo_destacado].tolist()[0] + 1
                rankings[metric_name] = position

                equipo_value = config['formula'](pd.DataFrame([equipo_data])).iloc[0]
                values[metric_name] = equipo_value if not pd.isna(equipo_value) else 0

            # Crear gráfica
            fig, ax = plt.subplots(figsize=(14, 8))

            labels = [config['label'] for config in metrics_config.values()]
            positions = list(rankings.values())
            metric_values = list(values.values())

            total_teams = len(df)
            bar_heights = [total_teams - pos + 1 for pos in positions]

            x_pos = np.arange(len(labels))
            bars = ax.bar(x_pos, bar_heights, bottom=0, color=self.colors['penafiel'], width=0.6)

            ax.set_ylim(0.5, total_teams + 0.5)
            ax.set_ylabel('Posición en el Ranking', fontsize=12, fontweight='bold')
            ax.set_xlabel('Métricas', fontsize=12, fontweight='bold')

            y_ticks = list(range(1, total_teams + 1))
            y_labels = [f"{tick}º" for tick in reversed(y_ticks)]
            ax.set_yticks(y_ticks)
            ax.set_yticklabels(y_labels)

            ax.set_xticks(x_pos)
            ax.set_xticklabels(labels, rotation=15, ha='right', fontsize=10)

            ax.grid(True, axis='y', alpha=0.3, linestyle='-', linewidth=0.5)
            ax.set_axisbelow(True)

            # Añadir etiquetas
            for i, (bar, pos, val, height) in enumerate(zip(bars, positions, metric_values, bar_heights)):
                if isinstance(val, float):
                    if val < 1:
                        value_text = f"{val:.2f}"
                    elif val < 10:
                        value_text = f"{val:.1f}"
                    else:
                        value_text = f"{val:.0f}"
                else:
                    value_text = f"{val}"

                if 'eficacia' in list(metrics_config.keys())[i] and 'goals' not in labels[i].lower():
                    value_text += "%"

                position_text = f"{pos}º"
                bar_center = bar.get_x() + bar.get_width()/2.

                ax.text(bar_center, height + 0.3, value_text,
                        ha='center', va='bottom',
                        fontweight='bold',
                        color='black',
                        fontsize=10)

                ax.text(bar_center, height/2, position_text,
                        ha='center',
                        va='center',
                        fontweight='bold',
                        color='black',
                        fontsize=10,
                        bbox=dict(facecolor='white',
                                 edgecolor='lightgray',
                                 boxstyle='round,pad=0.2',
                                 alpha=0.9))

            plt.title(f'FC {self.equipo_destacado} • Ranking vs Liga',
                      fontsize=14, fontweight='bold', pad=20)

            plt.tight_layout()
            result = fig_to_json(fig)

            logger.info("Ranking global generado exitosamente")
            return {
                'status': 'success',
                'data': result,
                'rankings': rankings,
                'values': values,
                'message': 'Ranking generado correctamente'
            }

        except Exception as e:
            logger.error(f"Error generando ranking global: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def generar_graficas_verticales(self) -> dict:
        """
        Genera gráficas verticales para cada métrica

        Returns:
            Diccionario con múltiples visualizaciones
        """
        try:
            logger.info("Generando gráficas verticales...")

            df = load_excel_data(self.archivo_promedios)
            df = filter_promedio_global(df)

            metricas = [
                "team_xgShot",
                "team_goal",
                "team_shot",
                "team_shotSuccess",
                "opp_xgShot",
                "opp_goal",
                "opp_shot",
                "opp_shotSuccess"
            ]

            spanish_names = self.config.METRICS_RANKINGS

            graficas = {}

            for metrica in metricas:
                if metrica not in df.columns:
                    continue

                invertir_orden = self.config.INVERSE_METRICS.get(metrica, False)

                fig, ax = plt.subplots(figsize=(10, 8))

                promedio = df[metrica].mean()
                df_temp = df[['Equipo', metrica]].copy()
                df_promedio = pd.DataFrame({
                    'Equipo': ['Promedio Liga'],
                    metrica: [promedio]
                })

                df_con_promedio = pd.concat([df_temp, df_promedio], ignore_index=True)
                df_ordenado = df_con_promedio.sort_values(by=metrica, ascending=not invertir_orden)

                colores = []
                for equipo in df_ordenado['Equipo']:
                    if equipo == self.equipo_destacado:
                        colores.append(self.colors['penafiel'])
                    elif equipo == 'Promedio Liga':
                        colores.append(self.colors['promedio'])
                    else:
                        colores.append(self.colors['otros'])

                ax.barh(range(len(df_ordenado)), df_ordenado[metrica],
                        color=colores, height=0.7, edgecolor='white', linewidth=0.7)

                ax.set_yticks(range(len(df_ordenado)))
                ax.set_yticklabels(df_ordenado['Equipo'], fontsize=9)

                titulo_eje_x = spanish_names.get(metrica, metrica)
                ax.set_xlabel(titulo_eje_x, fontsize=10, labelpad=10)
                ax.set_title(f'Comparativa de {titulo_eje_x} por equipo',
                             pad=20, fontsize=12, fontweight='bold')

                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.xaxis.grid(True, linestyle='--', alpha=0.7)

                plt.tight_layout()
                graficas[metrica] = fig_to_json(fig)

            logger.info(f"Generadas {len(graficas)} gráficas verticales")
            return {
                'status': 'success',
                'data': graficas,
                'message': f'{len(graficas)} gráficas generadas correctamente'
            }

        except Exception as e:
            logger.error(f"Error generando gráficas verticales: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
