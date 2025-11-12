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
        Genera scatter plot de eficacia ofensiva

        Returns:
            Diccionario con los datos de la visualización
        """
        try:
            logger.info("Generando scatter ofensivo...")

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

            # Medias
            x_mean = data["x"].mean()
            y_mean = data["y"].mean()

            # Crear figura
            fig, ax = plt.subplots(figsize=(14, 8))

            # Establecer límites
            def pad_limits(s: pd.Series, frac=0.12):
                mn, mx = float(s.min()), float(s.max())
                margin = max(1e-6, (mx - mn) * frac)
                return (mn - margin, mx + margin)

            xlim = pad_limits(data["x"], 0.12)
            ylim = pad_limits(data["y"], 0.18)
            ax.set_xlim(*xlim)
            ax.set_ylim(*ylim)

            # Líneas de media
            ax.axvline(x_mean, ls="--", lw=1.5, color=self.colors['success'], alpha=0.8)
            ax.axhline(y_mean, ls="--", lw=1.5, color=self.colors['success'], alpha=0.8)

            ax.text(x_mean, ylim[1], f"Media: {x_mean:.2f}%",
                    ha="left", va="top", fontsize=9,
                    color=self.colors['success'], fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none", alpha=0.7))

            ax.text(xlim[0], y_mean, f"Media: {y_mean:.2f}%",
                    ha="left", va="bottom", fontsize=9,
                    color=self.colors['success'], fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none", alpha=0.7))

            # Pintar escudos
            for _, row in data.iterrows():
                cx, cy = row["x"], row["y"]
                name = row["Equipo"]
                is_highlight = (name == self.equipo_destacado)

                # Usar escudo en lugar de punto
                self._add_team_logo(ax, cx, cy, name, is_highlight)

                if is_highlight:
                    ax.annotate(name, (cx, cy), xytext=(10, 30),
                               textcoords='offset points',
                               fontsize=11, fontweight='bold',
                               bbox=dict(boxstyle='round,pad=0.5',
                                       fc=self.colors['penafiel'], alpha=0.7,
                                       edgecolor='white'),
                               color='white')

            # Configuración de ejes
            ax.set_xlabel("Eficacia construcción ofensiva (%)",
                         fontsize=12, fontweight='bold')
            ax.set_ylabel("Eficacia finalización (%)",
                         fontsize=12, fontweight='bold')
            ax.set_title("COMPARATIVA EFICACIA OFENSIVA EQUIPOS",
                        fontsize=14, fontweight='bold', pad=20, loc='center')

            ax.grid(True, ls=":", lw=0.8, alpha=0.4)
            ax.set_axisbelow(True)

            for spine in ["top", "right"]:
                ax.spines[spine].set_visible(False)

            plt.tight_layout()
            result = fig_to_json(fig)

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
            return {
                'status': 'error',
                'message': str(e)
            }

    def generar_scatter_defensivo(self) -> dict:
        """
        Genera scatter plot de eficacia defensiva

        Returns:
            Diccionario con los datos de la visualización
        """
        try:
            logger.info("Generando scatter defensivo...")

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

            # Medias
            x_mean = data["x"].mean()
            y_mean = data["y"].mean()

            # Crear figura
            fig, ax = plt.subplots(figsize=(14, 8))

            # Establecer límites
            def pad_limits(s: pd.Series, frac=0.12):
                mn, mx = float(s.min()), float(s.max())
                margin = max(1e-6, (mx - mn) * frac)
                return (mn - margin, mx + margin)

            xlim = pad_limits(data["x"], 0.12)
            ylim = pad_limits(data["y"], 0.18)
            ax.set_xlim(*xlim)
            ax.set_ylim(*ylim)

            # Líneas de media
            ax.axvline(x_mean, ls="--", lw=1.5, color=self.colors['success'], alpha=0.8)
            ax.axhline(y_mean, ls="--", lw=1.5, color=self.colors['success'], alpha=0.8)

            ax.text(x_mean, ylim[1], f"Media: {x_mean:.2f}%",
                    ha="left", va="top", fontsize=9,
                    color=self.colors['success'], fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none", alpha=0.7))

            ax.text(xlim[0], y_mean, f"Media: {y_mean:.2f}%",
                    ha="left", va="bottom", fontsize=9,
                    color=self.colors['success'], fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none", alpha=0.7))

            # Pintar escudos
            for _, row in data.iterrows():
                cx, cy = row["x"], row["y"]
                name = row["Equipo"]
                is_highlight = (name == self.equipo_destacado)

                # Usar escudo en lugar de punto
                self._add_team_logo(ax, cx, cy, name, is_highlight)

                if is_highlight:
                    ax.annotate(name, (cx, cy), xytext=(10, 30),
                               textcoords='offset points',
                               fontsize=11, fontweight='bold',
                               bbox=dict(boxstyle='round,pad=0.5',
                                       fc=self.colors['penafiel'], alpha=0.7,
                                       edgecolor='white'),
                               color='white')

            # Configuración de ejes
            ax.set_xlabel("Eficacia contención defensiva (%)",
                         fontsize=12, fontweight='bold')
            ax.set_ylabel("Eficacia evitación (%)",
                         fontsize=12, fontweight='bold')
            ax.set_title("COMPARATIVA EFICACIA DEFENSIVA EQUIPOS",
                        fontsize=14, fontweight='bold', pad=20, loc='center')

            ax.grid(True, ls=":", lw=0.8, alpha=0.4)
            ax.set_axisbelow(True)

            for spine in ["top", "right"]:
                ax.spines[spine].set_visible(False)

            plt.tight_layout()
            result = fig_to_json(fig)

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
            return {
                'status': 'error',
                'message': str(e)
            }
