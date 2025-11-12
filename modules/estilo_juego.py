"""
Módulo de análisis de estilo de juego
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import logging
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from PIL import Image
import plotly.graph_objects as go
import plotly.express as px
import base64

from config import Config
from .utils import (
    load_excel_data,
    filter_promedio_global,
    fig_to_json,
    get_color_scheme,
    safe_div
)

logger = logging.getLogger(__name__)


class EstiloJuegoModule:
    """Módulo para análisis de estilo de juego ofensivo y defensivo"""

    def __init__(self):
        self.config = Config
        self.colors = get_color_scheme()
        self.archivo_promedios = self.config.ARCHIVO_PROMEDIOS_EQUIPOS
        self.equipo_destacado = self.config.EQUIPO_DESTACADO
        self.escudos_dir = Path("assets/escudos_portugal")

    def _load_image_as_base64(self, team_name):
        """
        Carga el escudo de un equipo y lo convierte a base64 para Plotly

        Args:
            team_name: Nombre del equipo

        Returns:
            String base64 de la imagen o None si no se encuentra
        """
        try:
            logo_path = self.escudos_dir / f"{team_name}.png"
            if not logo_path.exists():
                return None

            with open(logo_path, 'rb') as f:
                img_bytes = f.read()
                img_base64 = base64.b64encode(img_bytes).decode()
                return f"data:image/png;base64,{img_base64}"
        except Exception as e:
            logger.debug(f"Error cargando escudo de {team_name}: {e}")
            return None

    def _add_team_logo(self, ax, x, y, team_name, is_highlight=False):
        """
        Añade el escudo del equipo en la posición especificada

        Args:
            ax: Axes de matplotlib
            x, y: Coordenadas donde colocar el escudo
            team_name: Nombre del equipo
            is_highlight: Si es True, el escudo se mostrará más grande
        """
        try:
            # Construir ruta del archivo
            logo_path = self.escudos_dir / f"{team_name}.png"

            if not logo_path.exists():
                logger.debug(f"Escudo no encontrado para {team_name}: {logo_path}, usando punto de color")
                # Dibujar punto si no se encuentra el escudo
                color = self.colors['penafiel'] if is_highlight else self.colors['info']
                size = 200 if is_highlight else 100
                alpha = 1.0 if is_highlight else 0.6
                ax.scatter(x, y, s=size, c=color, alpha=alpha,
                          edgecolors='white', linewidth=2, zorder=3)
                return

            # Cargar imagen
            img = Image.open(logo_path)

            # Redimensionar a tamaño fijo según si es destacado o no
            # Esto asegura que todas las imágenes tengan el mismo tamaño final
            if is_highlight:
                fixed_size = (40,40)  # Tamaño mayor para equipo destacado
            else:
                fixed_size = (40, 40)  # Tamaño estándar para todos los equipos

            img_resized = img.resize(fixed_size, Image.Resampling.LANCZOS)

            # Crear OffsetImage con zoom=1 ya que la imagen ya está en el tamaño deseado
            imagebox = OffsetImage(img_resized, zoom=1)

            # Si es destacado, añadir borde
            if is_highlight:
                imagebox.image.axes = ax

            # Crear AnnotationBbox
            ab = AnnotationBbox(imagebox, (x, y),
                              frameon=is_highlight,
                              pad=0.2 if is_highlight else 0,
                              bboxprops=dict(
                                  edgecolor=self.colors['penafiel'],
                                  linewidth=3,
                                  facecolor='white'
                              ) if is_highlight else None,
                              zorder=4 if is_highlight else 3)

            ax.add_artist(ab)

        except Exception as e:
            logger.error(f"Error al añadir escudo de {team_name}: {str(e)}")
            # Dibujar punto como fallback
            color = self.colors['penafiel'] if is_highlight else self.colors['info']
            size = 200 if is_highlight else 100
            alpha = 1.0 if is_highlight else 0.6
            ax.scatter(x, y, s=size, c=color, alpha=alpha,
                      edgecolors='white', linewidth=2, zorder=3)

    def generar_scatter_ofensivo(self) -> dict:
        """
        Genera scatter plot de eficacia ofensiva usando Plotly para interactividad

        Returns:
            Diccionario con los datos de la visualización
        """
        try:
            logger.info("Generando scatter ofensivo con Plotly...")

            # Cargar datos
            df = load_excel_data(self.archivo_promedios)
            df = filter_promedio_global(df)

            # Calcular métricas
            x = safe_div(df["team_shot"], df["team_passToFinalThird"]) * 100
            y = safe_div(df["team_goal"], df["team_shot"]) * 100

            data = pd.DataFrame({
                "Equipo": df['Equipo'].astype(str),
                "x": x,
                "y": y
            }).dropna(subset=["x", "y"]).reset_index(drop=True)

            if data.empty:
                raise ValueError("No hay datos válidos para calcular las métricas")

            # Añadir columna para destacar Penafiel
            data['is_penafiel'] = data['Equipo'] == self.equipo_destacado

            # Medias
            x_mean = data["x"].mean()
            y_mean = data["y"].mean()

            # Crear figura de Plotly
            fig = go.Figure()

            # Añadir líneas de promedio
            fig.add_hline(y=y_mean, line_dash="dash", line_color="#2ecc71", line_width=3,
                         annotation_text=f"Media: {y_mean:.2f}%",
                         annotation_position="left",
                         annotation_font_size=14,
                         annotation_font_color="#2ecc71")

            fig.add_vline(x=x_mean, line_dash="dash", line_color="#2ecc71", line_width=3,
                         annotation_text=f"Media: {x_mean:.2f}%",
                         annotation_position="top",
                         annotation_font_size=14,
                         annotation_font_color="#2ecc71")

            # Añadir scatter plots (Penafiel destacado)
            data_otros = data[~data['is_penafiel']]
            data_penafiel = data[data['is_penafiel']]

            # Otros equipos
            fig.add_trace(go.Scatter(
                x=data_otros['x'],
                y=data_otros['y'],
                mode='markers',
                name='Otros equipos',
                marker=dict(
                    size=16,
                    color='#95a5a6',
                    opacity=0.7,
                    line=dict(width=2, color='white')
                ),
                text=data_otros['Equipo'],
                hovertemplate='<b>%{text}</b><br>' +
                             'Construcción ofensiva: %{x:.2f}%<br>' +
                             'Finalización: %{y:.2f}%<br>' +
                             '<extra></extra>'
            ))

            # Penafiel
            if not data_penafiel.empty:
                fig.add_trace(go.Scatter(
                    x=data_penafiel['x'],
                    y=data_penafiel['y'],
                    mode='markers+text',
                    name='Penafiel',
                    marker=dict(
                        size=20,
                        color='#9b59b6',
                        opacity=1.0,
                        line=dict(width=3, color='white')
                    ),
                    text=data_penafiel['Equipo'],
                    textposition='top center',
                    textfont=dict(size=14, color='#9b59b6', family='Arial Black'),
                    hovertemplate='<b>%{text}</b><br>' +
                                 'Construcción ofensiva: %{x:.2f}%<br>' +
                                 'Finalización: %{y:.2f}%<br>' +
                                 '<extra></extra>'
                ))

            # Configuración del layout
            fig.update_layout(
                title=dict(
                    text='COMPARATIVA EFICACIA OFENSIVA',
                    font=dict(size=16, family='Arial Black', color='#2c3e50'),
                    x=0.5,
                    xanchor='center'
                ),
                xaxis=dict(
                    title=dict(
                        text='Eficacia construcción ofensiva (%)',
                        font=dict(size=12, family='Arial', color='#2c3e50')
                    ),
                    showgrid=True,
                    gridwidth=1,
                    gridcolor='rgba(0,0,0,0.1)',
                    tickfont=dict(size=11, color='#2c3e50')
                ),
                yaxis=dict(
                    title=dict(
                        text='Eficacia finalización (%)',
                        font=dict(size=12, family='Arial', color='#2c3e50')
                    ),
                    showgrid=True,
                    gridwidth=1,
                    gridcolor='rgba(0,0,0,0.1)',
                    tickfont=dict(size=11, color='#2c3e50')
                ),
                plot_bgcolor='rgba(250,250,250,0.95)',
                paper_bgcolor='white',
                hovermode='closest',
                showlegend=False,
                height=450,
                margin=dict(l=60, r=40, t=60, b=60)
            )

            # Convertir a JSON
            result = fig.to_json()

            logger.info("Scatter ofensivo generado exitosamente")
            return {
                'status': 'success',
                'data': result,
                'stats': {
                    'x_mean': round(x_mean, 2),
                    'y_mean': round(y_mean, 2)
                },
                'message': 'Scatter ofensivo generado correctamente'
            }

        except Exception as e:
            logger.error(f"Error generando scatter ofensivo: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'status': 'error',
                'message': str(e)
            }

    def generar_scatter_defensivo(self) -> dict:
        """
        Genera scatter plot de eficacia defensiva usando Plotly para interactividad

        Returns:
            Diccionario con los datos de la visualización
        """
        try:
            logger.info("Generando scatter defensivo con Plotly...")

            # Cargar datos
            df = load_excel_data(self.archivo_promedios)
            df = filter_promedio_global(df)

            # Calcular métricas defensivas
            x = 100 - safe_div(df["opp_shot"], df["opp_passToFinalThird"]) * 100
            y = 100 - safe_div(df["opp_goal"], df["opp_shot"]) * 100

            data = pd.DataFrame({
                "Equipo": df['Equipo'].astype(str),
                "x": x,
                "y": y
            }).dropna(subset=["x", "y"]).reset_index(drop=True)

            if data.empty:
                raise ValueError("No hay datos válidos para calcular las métricas")

            # Añadir columna para destacar Penafiel
            data['is_penafiel'] = data['Equipo'] == self.equipo_destacado

            # Medias
            x_mean = data["x"].mean()
            y_mean = data["y"].mean()

            # Crear figura de Plotly
            fig = go.Figure()

            # Añadir líneas de promedio
            fig.add_hline(y=y_mean, line_dash="dash", line_color="#2ecc71", line_width=3,
                         annotation_text=f"Media: {y_mean:.2f}%",
                         annotation_position="left",
                         annotation_font_size=14,
                         annotation_font_color="#2ecc71")

            fig.add_vline(x=x_mean, line_dash="dash", line_color="#2ecc71", line_width=3,
                         annotation_text=f"Media: {x_mean:.2f}%",
                         annotation_position="top",
                         annotation_font_size=14,
                         annotation_font_color="#2ecc71")

            # Añadir scatter plots (Penafiel destacado)
            data_otros = data[~data['is_penafiel']]
            data_penafiel = data[data['is_penafiel']]

            # Otros equipos
            fig.add_trace(go.Scatter(
                x=data_otros['x'],
                y=data_otros['y'],
                mode='markers',
                name='Otros equipos',
                marker=dict(
                    size=16,
                    color='#95a5a6',
                    opacity=0.7,
                    line=dict(width=2, color='white')
                ),
                text=data_otros['Equipo'],
                hovertemplate='<b>%{text}</b><br>' +
                             'Contención defensiva: %{x:.2f}%<br>' +
                             'Evitación: %{y:.2f}%<br>' +
                             '<extra></extra>'
            ))

            # Penafiel
            if not data_penafiel.empty:
                fig.add_trace(go.Scatter(
                    x=data_penafiel['x'],
                    y=data_penafiel['y'],
                    mode='markers+text',
                    name='Penafiel',
                    marker=dict(
                        size=20,
                        color='#9b59b6',
                        opacity=1.0,
                        line=dict(width=3, color='white')
                    ),
                    text=data_penafiel['Equipo'],
                    textposition='top center',
                    textfont=dict(size=14, color='#9b59b6', family='Arial Black'),
                    hovertemplate='<b>%{text}</b><br>' +
                                 'Contención defensiva: %{x:.2f}%<br>' +
                                 'Evitación: %{y:.2f}%<br>' +
                                 '<extra></extra>'
                ))

            # Configuración del layout
            fig.update_layout(
                title=dict(
                    text='COMPARATIVA EFICACIA DEFENSIVA',
                    font=dict(size=16, family='Arial Black', color='#2c3e50'),
                    x=0.5,
                    xanchor='center'
                ),
                xaxis=dict(
                    title=dict(
                        text='Eficacia contención defensiva (%)',
                        font=dict(size=12, family='Arial', color='#2c3e50')
                    ),
                    showgrid=True,
                    gridwidth=1,
                    gridcolor='rgba(0,0,0,0.1)',
                    tickfont=dict(size=11, color='#2c3e50')
                ),
                yaxis=dict(
                    title=dict(
                        text='Eficacia evitación (%)',
                        font=dict(size=12, family='Arial', color='#2c3e50')
                    ),
                    showgrid=True,
                    gridwidth=1,
                    gridcolor='rgba(0,0,0,0.1)',
                    tickfont=dict(size=11, color='#2c3e50')
                ),
                plot_bgcolor='rgba(250,250,250,0.95)',
                paper_bgcolor='white',
                hovermode='closest',
                showlegend=False,
                height=450,
                margin=dict(l=60, r=40, t=60, b=60)
            )

            # Convertir a JSON
            result = fig.to_json()

            logger.info("Scatter defensivo generado exitosamente")
            return {
                'status': 'success',
                'data': result,
                'stats': {
                    'x_mean': round(x_mean, 2),
                    'y_mean': round(y_mean, 2)
                },
                'message': 'Scatter defensivo generado correctamente'
            }

        except Exception as e:
            logger.error(f"Error generando scatter defensivo: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'status': 'error',
                'message': str(e)
            }
