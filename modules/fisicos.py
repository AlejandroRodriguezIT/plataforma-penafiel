"""
Módulo de visualizaciones de datos físicos
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import logging
import pymysql
from pymysql import Error as MySQLError

from config import Config
from .utils import (
    load_excel_data,
    fig_to_json,
    fig_to_base64,
    get_color_scheme,
    safe_div
)

logger = logging.getLogger(__name__)


class FisicosModule:
    """Módulo para generar visualizaciones de datos físicos"""

    def __init__(self):
        self.config = Config
        self.colors = get_color_scheme()
        self.archivo_partidos = self.config.ARCHIVO_PARTIDOS_COMPLETO
        self.archivo_entrenos = self.config.ARCHIVO_ENTRENOS

    def _conectar_bd(self):
        """Establece conexión con la base de datos."""
        try:
            connection = pymysql.connect(
                host=self.config.DB_HOST,
                user=self.config.DB_USER,
                password=self.config.DB_PASSWORD,
                database=self.config.DB_NAME,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            return connection
        except MySQLError as e:
            logger.error(f"Error al conectar con la base de datos: {e}")
            return None

    def _obtener_datos_partidos_bd(self):
        """Obtiene los datos físicos de partidos desde la base de datos."""
        connection = self._conectar_bd()
        if not connection:
            logger.warning("No se pudo conectar a la BD, usando datos locales")
            return pd.DataFrame()

        try:
            cursor = connection.cursor()
            query = """
                SELECT
                    Partido,
                    Tarea,
                    Fecha,
                    Jugador,
                    Minutos_jugados,
                    Distancia_total,
                    Distancia_HSR,
                    Distancia_Sprint,
                    Velocidad_Maxima,
                    Jornada,
                    Posicion
                FROM Datos_Fisicos_Partido
                ORDER BY Fecha, Jornada
            """
            cursor.execute(query)
            resultados = cursor.fetchall()
            return pd.DataFrame(resultados)
        except MySQLError as e:
            logger.error(f"Error al obtener datos de partidos: {e}")
            return pd.DataFrame()
        finally:
            if connection:
                cursor.close()
                connection.close()

    def _obtener_resultados(self):
        """
        Obtiene los resultados de partidos desde la base de datos MySQL (tabla Resultado)
        Columnas: Jornada, Resultado, Codigo
        """
        try:
            # Cargar desde base de datos usando la función centralizada
            df = load_excel_data(self.config.ARCHIVO_RESULTADOS)

            # Normalizar Jornada a formato JX en mayúsculas
            df['Jornada'] = df['Jornada'].astype(str).str.strip().str.upper()

            return df[['Jornada', 'Codigo', 'Resultado']]

        except Exception as e:
            logger.error(f"Error al leer resultados desde base de datos: {e}")
            return pd.DataFrame()

    def generar_barras_colectivas(self) -> dict:
        """
        Genera datos JSON para gráficas de barras colectivas por partido
        Usa promedio estandarizado a 94 min de jugadores con >70 min jugados
        Colorea barras según resultado (V=verde, E=amarillo, D=rojo)

        Returns:
            Diccionario con los datos para las 3 visualizaciones
        """
        try:
            logger.info("Generando barras colectivas desde base de datos...")

            # 1. Obtener datos de partidos desde BD
            df_p = self._obtener_datos_partidos_bd()

            if df_p.empty:
                logger.warning("No se encontraron datos con consulta SQL directa, usando carga estándar desde BD")
                df_p = load_excel_data(self.archivo_partidos)

            # 2. Filtrar por 1ª y 2ª parte
            tarea_norm = (
                df_p["Tarea"].astype(str)
                .str.lower()
                .str.replace(r"\s+", " ", regex=True)
                .str.strip()
            )
            mask_halves = tarea_norm.str.contains(r"^(?:1|2)\s*ª?\s*parte$", regex=True, na=False)
            df_p_f = df_p.loc[mask_halves].copy()

            if df_p_f.empty:
                raise ValueError("No hay filas con Tarea 1ª/2ª parte")

            # 3. Asegurar columnas numéricas
            numeric_cols = ['Minutos_jugados', 'Distancia_total', 'Distancia_Sprint',
                          'Distancia_HSR', 'Velocidad_Maxima']
            for c in numeric_cols:
                if c in df_p_f.columns:
                    df_p_f.loc[:, c] = pd.to_numeric(df_p_f[c], errors="coerce")

            # 4. Normalizar Jornada
            df_p_f["Jornada"] = df_p_f["Jornada"].astype(str).str.strip().str.upper()

            # 5. Filtrar jugadores válidos (no nulos)
            df_p_f = df_p_f[df_p_f["Jugador"].notna()].copy()

            # 6. Agrupar por Jornada, Partido y Jugador (sumar 1ª y 2ª parte)
            df_jugadores = (
                df_p_f.groupby(["Jornada", "Partido", "Jugador"], as_index=False)
                .agg({
                    'Minutos_jugados': 'sum',
                    'Distancia_total': 'sum',
                    'Distancia_HSR': 'sum',
                    'Distancia_Sprint': 'sum'
                })
            )

            logger.info(f"Total registros de jugadores: {len(df_jugadores)}")

            # 7. Filtrar jugadores con más de 70 minutos
            df_jugadores = df_jugadores[df_jugadores["Minutos_jugados"] > 70].copy()
            logger.info(f"Jugadores con >70 min: {len(df_jugadores)}")

            if df_jugadores.empty:
                raise ValueError("No hay jugadores con más de 70 minutos")

            # 8. Estandarizar a 94 minutos
            factor_estandarizacion = 94.0
            df_jugadores["Distancia_total_Std"] = (df_jugadores["Distancia_total"] / df_jugadores["Minutos_jugados"]) * factor_estandarizacion
            df_jugadores["Distancia_HSR_Std"] = (df_jugadores["Distancia_HSR"] / df_jugadores["Minutos_jugados"]) * factor_estandarizacion
            df_jugadores["Distancia_Sprint_Std"] = (df_jugadores["Distancia_Sprint"] / df_jugadores["Minutos_jugados"]) * factor_estandarizacion

            # 9. Calcular promedios por jornada
            df_por_partido = (
                df_jugadores.groupby(["Jornada", "Partido"], as_index=False)
                .agg({
                    'Distancia_total_Std': 'mean',
                    'Distancia_HSR_Std': 'mean',
                    'Distancia_Sprint_Std': 'mean',
                    'Jugador': 'count'  # número de jugadores
                })
                .rename(columns={
                    'Distancia_total_Std': 'Distancia_total',
                    'Distancia_HSR_Std': 'Distancia_HSR',
                    'Distancia_Sprint_Std': 'Distancia_Sprint',
                    'Jugador': 'num_jugadores'
                })
            )

            logger.info(f"Partidos procesados: {len(df_por_partido)}")

            # 10. Obtener resultados desde tabla Resultados
            df_r = self._obtener_resultados()

            logger.info(f"Resultados obtenidos: {len(df_r)} filas")
            if not df_r.empty:
                logger.info(f"Columnas de resultados: {df_r.columns.tolist()}")
                logger.info(f"Primeras filas de resultados:\n{df_r.head()}")
                logger.info(f"Jornadas en resultados: {df_r['Jornada'].unique().tolist()}")
                logger.info(f"Jornadas en partidos: {df_por_partido['Jornada'].unique().tolist()}")

            if df_r.empty:
                logger.warning("No se encontraron resultados, usando colores por defecto")
                df_plot = df_por_partido.copy()
                df_plot["Codigo"] = ""
                df_plot["Resultado"] = "N/A"
            else:
                # Merge con resultados
                df_plot = df_por_partido.merge(
                    df_r[["Jornada", "Codigo", "Resultado"]],
                    on="Jornada",
                    how="left"
                )
                logger.info(f"Después del merge: {len(df_plot)} filas")
                logger.info(f"Valores de Resultado después del merge: {df_plot['Resultado'].unique().tolist()}")
                logger.info(f"Filas con Resultado NaN: {df_plot['Resultado'].isna().sum()}")

            # 11. Ordenar por jornada
            df_plot["J_orden"] = df_plot["Jornada"].str.extract(r'(\d+)', expand=False).astype(int)
            jornadas_unicas = sorted(df_plot["J_orden"].unique())

            # Reordenar jornadas 8 y 9 si es necesario
            orden_jornadas = [j for j in jornadas_unicas if j < 8]
            if 9 in jornadas_unicas:
                orden_jornadas.append(9)
            if 8 in jornadas_unicas:
                orden_jornadas.append(8)
            orden_jornadas += [j for j in jornadas_unicas if j > 9]

            df_plot["J_orden"] = pd.Categorical(
                df_plot["J_orden"],
                categories=orden_jornadas,
                ordered=True
            )
            df_plot = df_plot.sort_values(["J_orden", "Partido"], kind="stable")

            # 12. Mapa de colores por resultado
            color_map = {
                "V": "#4CAF50",   # verde - Victoria
                "E": "#FFC107",   # amarillo - Empate
                "D": "#DC143C",   # rojo - Derrota
            }
            logger.info(f"Valores de Resultado ANTES de normalizar: {df_plot['Resultado'].unique().tolist()}")
            df_plot["Resultado"] = df_plot["Resultado"].astype(str).str.strip().str.upper()
            logger.info(f"Valores de Resultado DESPUÉS de normalizar: {df_plot['Resultado'].unique().tolist()}")
            df_plot["color"] = df_plot["Resultado"].map(color_map).fillna("#9e9e9e")
            logger.info(f"Colores asignados: {df_plot['color'].unique().tolist()}")
            logger.info(f"Distribución de colores:\n{df_plot['color'].value_counts()}")

            # 13. Asegurar que las columnas de distancia son numéricas
            df_plot["Distancia_total"] = pd.to_numeric(df_plot["Distancia_total"], errors='coerce')
            df_plot["Distancia_HSR"] = pd.to_numeric(df_plot["Distancia_HSR"], errors='coerce')
            df_plot["Distancia_Sprint"] = pd.to_numeric(df_plot["Distancia_Sprint"], errors='coerce')

            # 14. Calcular promedios globales
            promedio_total = float(df_plot["Distancia_total"].mean())
            promedio_hsr = float(df_plot["Distancia_HSR"].mean())
            promedio_sprint = float(df_plot["Distancia_Sprint"].mean())

            # 15. Preparar datos para JSON
            jornadas = df_plot["Jornada"].tolist()
            codigos = df_plot["Codigo"].fillna("").tolist()
            distancia_total = df_plot["Distancia_total"].round(0).tolist()
            distancia_hsr = df_plot["Distancia_HSR"].round(0).tolist()
            distancia_sprint = df_plot["Distancia_Sprint"].round(0).tolist()
            colores = df_plot["color"].tolist()
            resultados = df_plot["Resultado"].tolist()
            num_jugadores = df_plot["num_jugadores"].tolist()

            logger.info("Barras colectivas generadas exitosamente (datos JSON)")
            return {
                'status': 'success',
                'data': {
                    'jornadas': jornadas,
                    'codigos': codigos,
                    'distancia_total': distancia_total,
                    'distancia_hsr': distancia_hsr,
                    'distancia_sprint': distancia_sprint,
                    'colores': colores,
                    'resultados': resultados,
                    'num_jugadores': num_jugadores,
                    'promedio_total': promedio_total,
                    'promedio_hsr': promedio_hsr,
                    'promedio_sprint': promedio_sprint
                },
                'message': 'Datos generados correctamente'
            }

        except Exception as e:
            logger.error(f"Error generando barras colectivas: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'status': 'error',
                'message': str(e)
            }

    def obtener_lista_partidos(self) -> dict:
        """
        Obtiene la lista de partidos disponibles desde la base de datos
        con formato 'JX - Nombre del rival'

        Returns:
            Diccionario con la lista de partidos y el partido más reciente
        """
        try:
            logger.info("Obteniendo lista de partidos...")

            df_p = self._obtener_datos_partidos_bd()

            if df_p.empty:
                logger.warning("No se encontraron datos con consulta SQL directa, usando carga estándar desde BD")
                df_p = load_excel_data(self.archivo_partidos)

            # Obtener partidos únicos con su fecha y jornada
            partidos_unicos = df_p[['Partido', 'Fecha', 'Jornada']].drop_duplicates()
            partidos_unicos = partidos_unicos.sort_values('Fecha', ascending=False)

            # Convertir a lista de diccionarios con formato 'JX - Rival'
            lista_partidos = []
            for _, row in partidos_unicos.iterrows():
                # Extraer jornada
                jornada = str(row['Jornada']).strip().upper()

                # Extraer rival del partido (formato: "Partido fútbol 11' contra X")
                partido_text = str(row['Partido'])
                rival = "Rival desconocido"
                if "contra" in partido_text:
                    rival = partido_text.split("contra")[-1].strip()

                # Crear label con formato 'JX - Rival'
                label = f"{jornada} - {rival}"

                lista_partidos.append({
                    'partido': row['Partido'],
                    'fecha': str(row['Fecha']),
                    'jornada': jornada,
                    'label': label
                })

            # Partido más reciente
            partido_reciente = lista_partidos[0]['partido'] if lista_partidos else None

            logger.info(f"Se encontraron {len(lista_partidos)} partidos")

            return {
                'status': 'success',
                'data': {
                    'partidos': lista_partidos,
                    'partido_reciente': partido_reciente
                }
            }

        except Exception as e:
            logger.error(f"Error obteniendo lista de partidos: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def generar_scatter_individual(self, partido: str = None) -> dict:
        """
        Genera diagrama de dispersión interactivo: Distancia Total (X) vs HSR (Y) por jugador
        con tooltips que muestran información detallada

        Args:
            partido: Nombre del partido a filtrar. Si es None, usa el más reciente.

        Returns:
            Diccionario con el HTML del scatter plot interactivo
        """
        try:
            logger.info(f"Generando scatter individual para partido: {partido}")

            # 1. Obtener datos desde BD
            df_p = self._obtener_datos_partidos_bd()

            if df_p.empty:
                logger.warning("No se encontraron datos con consulta SQL directa, usando carga estándar desde BD")
                df_p = load_excel_data(self.archivo_partidos)

            # 2. Si no se especifica partido, usar el más reciente
            if partido is None:
                partido = df_p.sort_values('Fecha', ascending=False)['Partido'].iloc[0]
                logger.info(f"Usando partido más reciente: {partido}")

            # 3. Filtrar por partido y 1ª/2ª parte
            df_partido = df_p[df_p['Partido'] == partido].copy()

            tarea_norm = (
                df_partido["Tarea"].astype(str)
                .str.lower()
                .str.replace(r"\s+", " ", regex=True)
                .str.strip()
            )
            mask_halves = tarea_norm.str.contains(r"^(?:1|2)\s*ª?\s*parte$", regex=True, na=False)
            df_partido = df_partido.loc[mask_halves].copy()

            if df_partido.empty:
                raise ValueError(f"No hay datos para el partido: {partido}")

            # 4. Convertir columnas a numérico
            for col in ['Minutos_jugados', 'Distancia_total', 'Distancia_HSR', 'Distancia_Sprint']:
                df_partido[col] = pd.to_numeric(df_partido[col], errors='coerce')

            # 5. Agrupar por jugador
            df_agg = df_partido.groupby('Jugador', as_index=False).agg({
                'Minutos_jugados': 'sum',
                'Distancia_total': 'sum',
                'Distancia_HSR': 'sum',
                'Distancia_Sprint': 'sum'
            })

            # 6. Filtrar jugadores con más de 70 minutos
            df_agg = df_agg[df_agg['Minutos_jugados'] > 70].copy()

            if df_agg.empty:
                raise ValueError(f"No hay jugadores con más de 70 minutos en el partido: {partido}")

            # 7. Calcular medias (usando distancias reales)
            mean_x = df_agg['Distancia_total'].mean()
            mean_y = df_agg['Distancia_HSR'].mean()

            # 8. Preparar datos para enviar al frontend
            jugadores_data = []
            for _, row in df_agg.iterrows():
                jugadores_data.append({
                    'jugador': row['Jugador'],
                    'minutos_jugados': int(row['Minutos_jugados']),
                    'distancia_total': int(row['Distancia_total']),
                    'distancia_hsr': int(row['Distancia_HSR']),
                    'distancia_sprint': int(row['Distancia_Sprint'])
                })

            logger.info("Scatter individual generado exitosamente")

            return {
                'status': 'success',
                'data': {
                    'jugadores': jugadores_data,
                    'partido': partido,
                    'num_jugadores': len(df_agg),
                    'mean_x': float(mean_x),
                    'mean_y': float(mean_y)
                },
                'message': 'Datos procesados correctamente'
            }

        except Exception as e:
            logger.error(f"Error generando scatter individual: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'status': 'error',
                'message': str(e)
            }

    def generar_barras_individuales(self) -> dict:
        """
        Genera gráficas de barras individuales por jugador

        Returns:
            Diccionario con los datos de la visualización
        """
        try:
            logger.info("Generando barras individuales...")

            # Cargar datos
            df = load_excel_data(self.archivo_partidos)

            # Filtrar jugadores con datos (sin NaN)
            df = df[df['Jugador'].notna()].copy()

            # Calcular promedios por jugador
            df_individual = df.groupby('Jugador').agg({
                'Distancia_total': 'mean',
                'Distancia_HSR': 'mean',
                'Distancia_Sprint': 'mean',
                'Velocidad_Maxima': 'max',
                'Minutos_jugados': 'sum'
            }).reset_index()

            # Filtrar jugadores con al menos 90 minutos jugados
            df_individual = df_individual[df_individual['Minutos_jugados'] >= 90].copy()

            # Ordenar por distancia total descendente
            df_individual = df_individual.sort_values('Distancia_total', ascending=False).head(15)

            # Crear figura con 3 subplots
            fig, axes = plt.subplots(1, 3, figsize=(18, 6))
            fig.suptitle('Análisis Físico Individual - Top 15 Jugadores', fontsize=16, fontweight='bold')

            jugadores = df_individual['Jugador'].tolist()

            # 1. Distancia Total Promedio
            ax = axes[0]
            bars = ax.barh(range(len(df_individual)), df_individual['Distancia_total']/1000,
                          color=self.colors['penafiel'], alpha=0.7, edgecolor='white', linewidth=1.5)
            ax.set_title('Distancia Total Promedio (km)', fontsize=12, fontweight='bold')
            ax.set_xlabel('Distancia (km)', fontsize=10)
            ax.set_yticks(range(len(jugadores)))
            ax.set_yticklabels(jugadores, fontsize=9)
            ax.invert_yaxis()
            ax.grid(True, alpha=0.3, axis='x')

            # 2. High Speed Running Promedio
            df_hsr_sorted = df_individual.sort_values('Distancia_HSR', ascending=False)
            jugadores_hsr = df_hsr_sorted['Jugador'].tolist()

            ax = axes[1]
            bars = ax.barh(range(len(df_hsr_sorted)), df_hsr_sorted['Distancia_HSR'],
                          color=self.colors['info'], alpha=0.7, edgecolor='white', linewidth=1.5)
            ax.set_title('HSR Promedio (m)', fontsize=12, fontweight='bold')
            ax.set_xlabel('Distancia HSR (m)', fontsize=10)
            ax.set_yticks(range(len(jugadores_hsr)))
            ax.set_yticklabels(jugadores_hsr, fontsize=9)
            ax.invert_yaxis()
            ax.grid(True, alpha=0.3, axis='x')

            # 3. Distancia Sprint Promedio
            df_sprint_sorted = df_individual.sort_values('Distancia_Sprint', ascending=False)
            jugadores_sprint = df_sprint_sorted['Jugador'].tolist()

            ax = axes[2]
            bars = ax.barh(range(len(df_sprint_sorted)), df_sprint_sorted['Distancia_Sprint'],
                          color=self.colors['warning'], alpha=0.7, edgecolor='white', linewidth=1.5)
            ax.set_title('Sprint Promedio (m)', fontsize=12, fontweight='bold')
            ax.set_xlabel('Distancia Sprint (m)', fontsize=10)
            ax.set_yticks(range(len(jugadores_sprint)))
            ax.set_yticklabels(jugadores_sprint, fontsize=9)
            ax.invert_yaxis()
            ax.grid(True, alpha=0.3, axis='x')

            plt.tight_layout()
            result = fig_to_json(fig)

            logger.info("Barras individuales generadas exitosamente")
            return {
                'status': 'success',
                'data': result,
                'message': 'Gráfica generada correctamente'
            }

        except Exception as e:
            logger.error(f"Error generando barras individuales: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def generar_evolutivo(self) -> dict:
        """
        Genera gráficas evolutivas de métricas físicas

        Returns:
            Diccionario con los datos de la visualización
        """
        try:
            logger.info("Generando evolutivo físico...")

            # Cargar datos
            df = load_excel_data(self.archivo_partidos)

            # Agrupar por jornada y calcular promedios del equipo
            df_evolutivo = df.groupby('Jornada').agg({
                'Distancia_total': 'mean',
                'Distancia_HSR': 'mean',
                'Distancia_Sprint': 'mean',
                'Velocidad_Maxima': 'mean'
            }).reset_index()

            # Ordenar por jornada
            df_evolutivo['Jornada_num'] = df_evolutivo['Jornada'].str.extract(r'(\d+)').astype(int)
            df_evolutivo = df_evolutivo.sort_values('Jornada_num')

            # Crear figura con 2x2 subplots
            fig, axes = plt.subplots(2, 2, figsize=(16, 10))
            fig.suptitle('Evolución de Métricas Físicas por Jornada', fontsize=16, fontweight='bold')

            jornadas = df_evolutivo['Jornada'].tolist()
            x_positions = range(len(jornadas))

            # 1. Evolución Distancia Total
            ax = axes[0, 0]
            ax.plot(x_positions, df_evolutivo['Distancia_total']/1000,
                   marker='o', linewidth=2.5, markersize=8,
                   color=self.colors['penafiel'], label='Distancia Total')
            ax.axhline(df_evolutivo['Distancia_total'].mean()/1000,
                      color=self.colors['success'], linestyle='--', linewidth=1.5,
                      alpha=0.7, label=f'Promedio: {df_evolutivo["Distancia_total"].mean()/1000:.1f} km')
            ax.set_title('Evolución Distancia Total Promedio', fontsize=12, fontweight='bold')
            ax.set_xlabel('Jornada', fontsize=10)
            ax.set_ylabel('Distancia (km)', fontsize=10)
            ax.set_xticks(x_positions)
            ax.set_xticklabels(jornadas, rotation=45, ha='right')
            ax.legend(loc='best')
            ax.grid(True, alpha=0.3)

            # 2. Evolución HSR
            ax = axes[0, 1]
            ax.plot(x_positions, df_evolutivo['Distancia_HSR'],
                   marker='s', linewidth=2.5, markersize=8,
                   color=self.colors['info'], label='HSR')
            ax.axhline(df_evolutivo['Distancia_HSR'].mean(),
                      color=self.colors['success'], linestyle='--', linewidth=1.5,
                      alpha=0.7, label=f'Promedio: {df_evolutivo["Distancia_HSR"].mean():.0f} m')
            ax.set_title('Evolución High Speed Running', fontsize=12, fontweight='bold')
            ax.set_xlabel('Jornada', fontsize=10)
            ax.set_ylabel('Distancia HSR (m)', fontsize=10)
            ax.set_xticks(x_positions)
            ax.set_xticklabels(jornadas, rotation=45, ha='right')
            ax.legend(loc='best')
            ax.grid(True, alpha=0.3)

            # 3. Evolución Sprint
            ax = axes[1, 0]
            ax.plot(x_positions, df_evolutivo['Distancia_Sprint'],
                   marker='^', linewidth=2.5, markersize=8,
                   color=self.colors['warning'], label='Sprint')
            ax.axhline(df_evolutivo['Distancia_Sprint'].mean(),
                      color=self.colors['success'], linestyle='--', linewidth=1.5,
                      alpha=0.7, label=f'Promedio: {df_evolutivo["Distancia_Sprint"].mean():.0f} m')
            ax.set_title('Evolución Distancia Sprint', fontsize=12, fontweight='bold')
            ax.set_xlabel('Jornada', fontsize=10)
            ax.set_ylabel('Distancia Sprint (m)', fontsize=10)
            ax.set_xticks(x_positions)
            ax.set_xticklabels(jornadas, rotation=45, ha='right')
            ax.legend(loc='best')
            ax.grid(True, alpha=0.3)

            # 4. Evolución Velocidad Máxima
            ax = axes[1, 1]
            ax.plot(x_positions, df_evolutivo['Velocidad_Maxima'],
                   marker='D', linewidth=2.5, markersize=8,
                   color=self.colors['danger'], label='Vel. Máxima')
            ax.axhline(df_evolutivo['Velocidad_Maxima'].mean(),
                      color=self.colors['success'], linestyle='--', linewidth=1.5,
                      alpha=0.7, label=f'Promedio: {df_evolutivo["Velocidad_Maxima"].mean():.1f} km/h')
            ax.set_title('Evolución Velocidad Máxima Promedio', fontsize=12, fontweight='bold')
            ax.set_xlabel('Jornada', fontsize=10)
            ax.set_ylabel('Velocidad (km/h)', fontsize=10)
            ax.set_xticks(x_positions)
            ax.set_xticklabels(jornadas, rotation=45, ha='right')
            ax.legend(loc='best')
            ax.grid(True, alpha=0.3)

            plt.tight_layout()
            result = fig_to_json(fig)

            logger.info("Evolutivo físico generado exitosamente")
            return {
                'status': 'success',
                'data': result,
                'message': 'Gráfica generada correctamente'
            }

        except Exception as e:
            logger.error(f"Error generando evolutivo: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def get_resumen_fisico(self) -> dict:
        """
        Obtiene resumen de datos físicos

        Returns:
            Diccionario con resumen de métricas
        """
        try:
            df = load_excel_data(self.archivo_partidos)

            # TODO: Calcular métricas de resumen
            resumen = {
                'total_partidos': 0,
                'promedio_distancia': 0,
                'promedio_velocidad': 0,
                'mejor_partido': '',
                'ultima_actualizacion': ''
            }

            return resumen

        except Exception as e:
            logger.error(f"Error obteniendo resumen físico: {str(e)}")
            return {}

    def obtener_lista_microciclos(self) -> dict:
        """
        Obtiene la lista de microciclos disponibles con su información

        Returns:
            Diccionario con la lista de microciclos
        """
        try:
            logger.info("Obteniendo lista de microciclos...")

            # Cargar datos de entrenamiento y partidos
            df_entreno = load_excel_data(self.archivo_entrenos)
            df_partido = load_excel_data(self.archivo_partidos)

            logger.info(f"Columnas en df_entreno: {df_entreno.columns.tolist()}")
            logger.info(f"Columnas en df_partido: {df_partido.columns.tolist()}")

            # Verificar que existe la columna Jornada en entrenos
            if 'Jornada' not in df_entreno.columns:
                raise ValueError("No se encontró la columna 'Jornada' en los datos de entrenamiento")

            # Obtener lista única de jornadas de entrenamiento
            jornadas_entreno = df_entreno['Jornada'].unique()
            logger.info(f"Jornadas encontradas: {jornadas_entreno}")

            microciclos = []

            for jornada in jornadas_entreno:
                if pd.isna(jornada):
                    continue

                # Extraer número de jornada
                # Puede venir como número (1, 2, 3...) o como string ("Semana_1", "J1", etc.)
                if isinstance(jornada, (int, float, np.integer, np.floating)):
                    jornada_num = int(jornada)
                else:
                    # Es string, intentar extraer número
                    jornada_num = str(jornada).replace('Semana_', '').replace('J', '').strip()
                    try:
                        jornada_num = int(jornada_num)
                    except ValueError:
                        jornada_num = str(jornada)

                # Buscar rival en datos de partidos (merge por fecha)
                df_jornada_entreno = df_entreno[df_entreno['Jornada'] == jornada].copy()

                # Obtener fechas del microciclo
                if not df_jornada_entreno.empty:
                    fecha_inicio = df_jornada_entreno['Fecha'].min()
                    fecha_fin = df_jornada_entreno['Fecha'].max()

                    # Buscar partido correspondiente a esta jornada
                    rival = "Sin rival"
                    fecha_partido = None
                    if 'Jornada' in df_partido.columns:
                        df_partido_jornada = df_partido[df_partido['Jornada'] == jornada_num].copy()

                        if not df_partido_jornada.empty:
                            # Obtener fecha del partido para ordenar
                            fecha_partido = pd.to_datetime(df_partido_jornada['Fecha'].iloc[0])

                            # Extraer rival del campo "Partido" (formato: "Partido fútbol 11' contra X")
                            if 'Partido' in df_partido.columns:
                                partido_text = df_partido_jornada['Partido'].iloc[0]
                                if isinstance(partido_text, str) and "contra" in partido_text:
                                    rival = partido_text.split("contra")[-1].strip()
                                    logger.info(f"Rival encontrado para {jornada}: {rival}")

                    # Formatear fechas
                    fecha_inicio_str = pd.to_datetime(fecha_inicio).strftime('%d/%m/%Y')
                    fecha_fin_str = pd.to_datetime(fecha_fin).strftime('%d/%m/%Y')

                    # Crear label del microciclo (solo jornada y rival, sin fechas)
                    label = f"J{jornada_num} - {rival}"

                    # Convertir tipos numpy a tipos Python para JSON serialization
                    microciclos.append({
                        'jornada': int(jornada) if pd.notna(jornada) else None,
                        'jornada_num': int(jornada_num) if isinstance(jornada_num, (int, np.integer)) else str(jornada_num),
                        'rival': str(rival),
                        'fecha_inicio': fecha_inicio_str,
                        'fecha_fin': fecha_fin_str,
                        'fecha_partido': fecha_partido.isoformat() if fecha_partido else None,
                        'label': label
                    })

            # Ordenar microciclos por fecha del partido
            microciclos_ordenados = sorted(
                [m for m in microciclos if m['fecha_partido'] is not None],
                key=lambda x: x['fecha_partido']
            )

            # Agregar al final los que no tienen fecha de partido
            microciclos_sin_fecha = [m for m in microciclos if m['fecha_partido'] is None]
            microciclos_ordenados.extend(microciclos_sin_fecha)

            # Eliminar el campo fecha_partido antes de devolver (solo se usó para ordenar)
            for m in microciclos_ordenados:
                m.pop('fecha_partido', None)

            logger.info(f"Se encontraron {len(microciclos_ordenados)} microciclos")

            return {
                'status': 'success',
                'data': {
                    'microciclos': microciclos_ordenados
                },
                'message': 'Lista de microciclos obtenida correctamente'
            }

        except Exception as e:
            logger.error(f"Error obteniendo lista de microciclos: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'status': 'error',
                'message': f'Error al obtener lista de microciclos: {str(e)}'
            }

    def obtener_datos_microciclo_equipo(self, jornada: str, tipo_distancia: str = 'Distancia_total') -> dict:
        """
        Obtiene los datos del microciclo por equipo desde la base de datos
        Usa la columna 'Situacion' que ya tiene las etiquetas MD calculadas

        Args:
            jornada: Nombre de la jornada (ej: "Semana_J1")
            tipo_distancia: Tipo de distancia a analizar ('Distancia_total', 'Distancia_HSR', 'Distancia_Sprint')

        Returns:
            Diccionario con los datos del microciclo
        """
        try:
            logger.info(f"Obteniendo datos de microciclo desde BD: {jornada}, tipo: {tipo_distancia}")

            if not jornada:
                raise ValueError("Se requiere especificar una jornada")

            # Conectar a la base de datos
            connection = self._conectar_bd()
            if not connection:
                raise ValueError("No se pudo conectar a la base de datos")

            try:
                # Obtener número de jornada - soportar múltiples formatos
                # Puede recibir: "1", "J1", "Semana_J1"
                jornada_str = str(jornada).strip()

                # Remover prefijo "Semana_" si existe
                jornada_str = jornada_str.replace('Semana_', '')

                # Si no empieza con "J", añadirlo
                if not jornada_str.startswith('J'):
                    jornada_num = f"J{jornada_str}"
                else:
                    jornada_num = jornada_str

                # Extraer número entero
                jornada_num_int = int(jornada_num.replace('J', ''))

                # Configuración especial para microciclos con intervalos largos o aplazamientos
                config_especial = {
                    'J5': {
                        'fecha_inicio': '2024-09-08',  # Lunes después de 2 semanas de descanso
                        'mostrar_partido_previo': False
                    },
                    'J6': {
                        'fecha_inicio': '2024-09-22',  # Inicio después de 14 días (partido otra competición)
                        'mostrar_partido_previo': False
                    },
                    'J8': {
                        'partido_previo_custom': 'J9',  # J8 se aplazó, usar J9 como referencia
                        'mostrar_partido_previo': True
                    },
                    'J9': {
                        'fecha_inicio': '2024-10-13',  # Inicio después de 14 días (J8 aplazada)
                        'mostrar_partido_previo': False
                    }
                }

                # Determinar jornada previa según configuración especial
                config_jornada = config_especial.get(jornada_num, {})
                if 'partido_previo_custom' in config_jornada:
                    jornada_prev_num = config_jornada['partido_previo_custom']
                else:
                    jornada_prev_num = f"J{jornada_num_int - 1}" if jornada_num_int > 1 else None

                # Flag para mostrar o no el partido previo
                mostrar_partido_previo = config_jornada.get('mostrar_partido_previo', True)
                fecha_inicio_custom = config_jornada.get('fecha_inicio', None)

                # Consultar entrenamientos de la jornada seleccionada usando cursor
                # Necesitamos también Minutos_jugados para filtrar jugadores
                # Buscar por múltiples formatos posibles: "J1", "1", o cualquier formato que contenga el número
                logger.info(f"Buscando entrenamientos para jornada: {jornada_num} (int: {jornada_num_int})")

                cursor = connection.cursor()

                # Para J1, buscar solo formatos exactos: "J1", "1", "Semana_J1"
                if jornada_num == "J1":
                    query_params = [jornada_num, jornada_num_int, f'Semana_{jornada_num}']
                    logger.info(f"Query específica para J1 - buscando exactamente: J1, 1, Semana_J1")
                    cursor.execute(f"""
                        SELECT Fecha, Situacion, {tipo_distancia}, Jugador, Minutos_jugados
                        FROM Datos_Fisicos_Entreno
                        WHERE (Jornada = %s OR Jornada = %s OR Jornada = %s)
                          AND Tarea = 'Total'
                          AND Jugador IS NOT NULL
                          AND Jugador != ''
                        ORDER BY Fecha
                    """, query_params)
                else:
                    # Para otras jornadas, usar la lógica existente
                    cursor.execute(f"""
                        SELECT Fecha, Situacion, {tipo_distancia}, Jugador, Minutos_jugados
                        FROM Datos_Fisicos_Entreno
                        WHERE (Jornada = %s OR Jornada = %s OR Jornada LIKE %s)
                          AND Tarea = 'Total'
                          AND Jugador IS NOT NULL
                          AND Jugador != ''
                        ORDER BY Fecha
                    """, [jornada_num, jornada_num_int, f'%{jornada_num_int}%'])

                resultados_entrenos = cursor.fetchall()
                logger.info(f"Resultados de entrenamientos obtenidos: {len(resultados_entrenos)} filas")

                # Si no hay resultados, diagnosticar el problema
                if not resultados_entrenos:
                    cursor2 = connection.cursor()
                    cursor2.execute("SELECT DISTINCT Jornada FROM Datos_Fisicos_Entreno ORDER BY Jornada LIMIT 20")
                    jornadas_disponibles_entreno = [row['Jornada'] for row in cursor2.fetchall()]
                    logger.warning(f"No se encontraron entrenamientos para {jornada_num}. Jornadas disponibles en Datos_Fisicos_Entreno: {jornadas_disponibles_entreno}")

                    # Ver qué datos hay para esta jornada sin filtros
                    cursor2.execute("""
                        SELECT Jornada, Tarea, COUNT(*) as count
                        FROM Datos_Fisicos_Entreno
                        WHERE Jornada LIKE %s
                        GROUP BY Jornada, Tarea
                    """, [f'%{jornada_num_int}%'])
                    datos_jornada = cursor2.fetchall()
                    logger.warning(f"Datos en Datos_Fisicos_Entreno para jornada {jornada_num_int}: {datos_jornada}")
                    cursor2.close()

                cursor.close()

                # Crear DataFrame desde los resultados del cursor (DictCursor)
                if resultados_entrenos:
                    df_entrenos = pd.DataFrame(resultados_entrenos)
                    logger.info(f"DataFrame de entrenamientos creado con {len(df_entrenos)} registros")
                    logger.info(f"Columnas: {df_entrenos.columns.tolist()}")
                    logger.info(f"Situaciones únicas: {df_entrenos['Situacion'].unique() if 'Situacion' in df_entrenos.columns else 'N/A'}")
                else:
                    df_entrenos = pd.DataFrame()
                    logger.warning(f"No se encontraron entrenamientos para {jornada_num}")

                # Obtener partido previo (si existe y si se debe mostrar)
                # Calcular promedio de distancia de jugadores que jugaron > 70 minutos, estandarizada a 94 min
                distancia_partido_previo = 0
                fecha_partido_previo = None
                num_jugadores_partido_previo = 0
                rival_partido_previo = "Rival desconocido"
                if jornada_prev_num and mostrar_partido_previo:
                    logger.info(f"Buscando partido previo: {jornada_prev_num}")
                    # Extraer número de jornada previa para búsqueda flexible
                    jornada_prev_num_int = int(jornada_prev_num.replace('J', ''))
                    cursor = connection.cursor()
                    cursor.execute(f"""
                        SELECT Fecha, Distancia_total, Distancia_HSR, Distancia_Sprint, Jugador, Tarea, Minutos_jugados, Partido
                        FROM Datos_Fisicos_Partido
                        WHERE (Jornada = %s OR Jornada = %s OR Jornada LIKE %s)
                          AND Tarea IN ('1ª parte', '2ª parte', '1 ª parte', '2 ª parte')
                          AND Jugador IS NOT NULL
                          AND Jugador != ''
                    """, [jornada_prev_num, jornada_prev_num_int, f'%{jornada_prev_num_int}%'])

                    resultados_partido_previo = cursor.fetchall()
                    logger.info(f"Resultados encontrados para {jornada_prev_num}: {len(resultados_partido_previo)} filas")

                    # Si no hay resultados, verificar qué jornadas existen y qué datos tiene J2
                    if not resultados_partido_previo:
                        cursor2 = connection.cursor()
                        cursor2.execute("SELECT DISTINCT Jornada FROM Datos_Fisicos_Partido ORDER BY Jornada LIMIT 10")
                        jornadas_disponibles = [row['Jornada'] for row in cursor2.fetchall()]
                        logger.warning(f"No se encontraron datos para {jornada_prev_num}. Jornadas disponibles: {jornadas_disponibles}")

                        # Ver qué datos hay en J2 sin filtros
                        cursor2.execute("""
                            SELECT Tarea, Jugador, COUNT(*) as count
                            FROM Datos_Fisicos_Partido
                            WHERE Jornada = %s
                            GROUP BY Tarea, Jugador
                            LIMIT 10
                        """, [jornada_prev_num])
                        datos_j2 = cursor2.fetchall()
                        logger.warning(f"Datos en {jornada_prev_num}: {datos_j2}")
                        cursor2.close()

                    cursor.close()

                    if resultados_partido_previo:
                        df_partido_prev = pd.DataFrame(resultados_partido_previo)
                        fecha_partido_previo = pd.to_datetime(df_partido_prev['Fecha'].iloc[0])

                        # Extraer rival del partido previo
                        if 'Partido' in df_partido_prev.columns and not df_partido_prev['Partido'].isna().all():
                            partido_text = df_partido_prev['Partido'].iloc[0]
                            if isinstance(partido_text, str) and "contra" in partido_text:
                                rival_partido_previo = partido_text.split("contra")[-1].strip()

                        # Agrupar por jugador y sumar minutos jugados
                        df_minutos = df_partido_prev.groupby('Jugador')['Minutos_jugados'].sum().reset_index()
                        logger.info(f"Minutos por jugador en {jornada_prev_num}: {df_minutos[['Jugador', 'Minutos_jugados']].to_dict('records')}")

                        # Filtrar jugadores que jugaron > 70 minutos
                        jugadores_validos = df_minutos[df_minutos['Minutos_jugados'] > 70]['Jugador'].tolist()
                        logger.info(f"Jugadores válidos (>70 min) en {jornada_prev_num}: {len(jugadores_validos)}")

                        if jugadores_validos:
                            # Obtener datos de jugadores válidos
                            df_validos = df_partido_prev[df_partido_prev['Jugador'].isin(jugadores_validos)]

                            # Agrupar por jugador y sumar distancias
                            df_por_jugador = df_validos.groupby('Jugador').agg({
                                'Distancia_total': 'sum',
                                'Distancia_HSR': 'sum',
                                'Distancia_Sprint': 'sum',
                                'Minutos_jugados': 'sum'
                            }).reset_index()

                            # Estandarizar a 94 minutos
                            df_por_jugador['Distancia_total_std'] = (df_por_jugador['Distancia_total'] / df_por_jugador['Minutos_jugados']) * 94
                            df_por_jugador['Distancia_HSR_std'] = (df_por_jugador['Distancia_HSR'] / df_por_jugador['Minutos_jugados']) * 94
                            df_por_jugador['Distancia_Sprint_std'] = (df_por_jugador['Distancia_Sprint'] / df_por_jugador['Minutos_jugados']) * 94

                            # Calcular promedio según el tipo de distancia solicitado
                            if tipo_distancia == 'Distancia_total':
                                distancia_partido_previo = df_por_jugador['Distancia_total_std'].mean()
                            elif tipo_distancia == 'Distancia_HSR':
                                distancia_partido_previo = df_por_jugador['Distancia_HSR_std'].mean()
                            elif tipo_distancia == 'Distancia_Sprint':
                                distancia_partido_previo = df_por_jugador['Distancia_Sprint_std'].mean()

                            num_jugadores_partido_previo = len(jugadores_validos)
                            logger.info(f"Partido previo {jornada_prev_num}: {fecha_partido_previo}, promedio: {distancia_partido_previo:.2f}, jugadores: {num_jugadores_partido_previo}")
                        else:
                            logger.warning(f"No hay jugadores válidos (>70 min) en partido {jornada_prev_num}. Total jugadores: {len(df_minutos)}")
                    else:
                        logger.warning(f"No se encontraron datos de partido para {jornada_prev_num}")

                # Obtener fecha y rival del partido actual (para el label del microciclo)
                cursor = connection.cursor()
                cursor.execute("""
                    SELECT Fecha, Partido
                    FROM Datos_Fisicos_Partido
                    WHERE Jornada = %s
                    LIMIT 1
                """, [jornada_num])

                resultado_partido_actual = cursor.fetchone()
                cursor.close()

                if not resultado_partido_actual:
                    raise ValueError(f"No se encontró partido para la jornada: {jornada_num}")

                # DictCursor devuelve diccionarios, acceder por nombre de columna
                fecha_partido_actual = pd.to_datetime(resultado_partido_actual['Fecha'])

                # Extraer rival del campo "Partido" (formato: "Partido fútbol 11' contra X")
                rival = "Rival desconocido"
                if resultado_partido_actual.get('Partido'):
                    partido_text = resultado_partido_actual['Partido']
                    if isinstance(partido_text, str) and "contra" in partido_text:
                        rival = partido_text.split("contra")[-1].strip()

                # Preparar datos del microciclo
                datos_microciclo = []

                # 1. Añadir partido previo (si existe)
                if fecha_partido_previo and distancia_partido_previo > 0:
                    datos_microciclo.append({
                        'Situacion': f'Partido {jornada_prev_num}<br>VS {rival_partido_previo}',
                        'Fecha': fecha_partido_previo,
                        'distancia': float(distancia_partido_previo),
                        'num_registros': num_jugadores_partido_previo,
                        'tipo': 'partido'
                    })

                # 2. Añadir entrenamientos - calcular promedio por jugador
                # Filtrar jugadores con minutos >= 70% del valor más frecuente
                if not df_entrenos.empty:
                    df_entrenos['Fecha'] = pd.to_datetime(df_entrenos['Fecha'])

                    # Filtrar por fecha de inicio custom si existe
                    if fecha_inicio_custom:
                        fecha_inicio_dt = pd.to_datetime(fecha_inicio_custom)
                        df_entrenos = df_entrenos[df_entrenos['Fecha'] >= fecha_inicio_dt]
                        logger.info(f"Filtrando entrenamientos desde {fecha_inicio_custom} para {jornada_num}")

                    # Agrupar por Situacion y Fecha
                    for (situacion, fecha), grupo in df_entrenos.groupby(['Situacion', 'Fecha']):
                        # Encontrar el valor más frecuente de Minutos_jugados (moda)
                        if not grupo.empty and 'Minutos_jugados' in grupo.columns:
                            minutos_series = grupo['Minutos_jugados'].dropna()
                            if len(minutos_series) > 0:
                                # Usar mode() para obtener el valor más frecuente
                                moda = minutos_series.mode()
                                if len(moda) > 0:
                                    valor_mas_frecuente = moda.iloc[0]
                                    umbral_70_pct = valor_mas_frecuente * 0.7

                                    # Filtrar jugadores con minutos >= 70% del valor más frecuente
                                    grupo_filtrado = grupo[grupo['Minutos_jugados'] >= umbral_70_pct]

                                    if not grupo_filtrado.empty:
                                        # Calcular promedio de distancia
                                        promedio_distancia = grupo_filtrado[tipo_distancia].mean()
                                        num_jugadores = len(grupo_filtrado)

                                        datos_microciclo.append({
                                            'Situacion': situacion,
                                            'Fecha': fecha,
                                            'distancia': float(promedio_distancia),
                                            'num_registros': num_jugadores,
                                            'tipo': 'entrenamiento'
                                        })
                                        logger.info(f"Entreno {situacion} ({fecha}): promedio={promedio_distancia:.2f}, jugadores={num_jugadores}, umbral={umbral_70_pct:.1f}")
                                else:
                                    logger.warning(f"No se pudo calcular moda para {situacion} en {fecha}")
                            else:
                                logger.warning(f"No hay datos de minutos para {situacion} en {fecha}")
                        else:
                            logger.warning(f"Grupo vacío o sin columna Minutos_jugados para {situacion} en {fecha}")

                # Convertir a DataFrame y ordenar cronológicamente
                if datos_microciclo:
                    df_datos = pd.DataFrame(datos_microciclo)

                    # Asegurar que Fecha sea datetime
                    df_datos['Fecha'] = pd.to_datetime(df_datos['Fecha'])

                    # Ordenar cronológicamente
                    df_datos = df_datos.sort_values('Fecha')

                    # Preparar datos para el gráfico
                    situaciones = df_datos['Situacion'].tolist()
                    distancias = df_datos['distancia'].tolist()
                    num_registros = df_datos['num_registros'].tolist()
                    fechas = df_datos['Fecha'].dt.strftime('%d/%m/%Y').tolist()
                    tipos = df_datos['tipo'].tolist()
                else:
                    situaciones = []
                    distancias = []
                    num_registros = []
                    fechas = []
                    tipos = []

                # Obtener label del tipo de distancia
                tipo_labels = {
                    'Distancia_total': 'Distancia Total',
                    'Distancia_HSR': 'Distancia HSR',
                    'Distancia_Sprint': 'Distancia Sprint'
                }
                tipo_distancia_label = tipo_labels.get(tipo_distancia, tipo_distancia)

                # Obtener label del microciclo: "Microciclo JX - Nombre Rival (Fecha inicio - Fecha fin)"
                # Prioridad: fecha_inicio_custom > fecha_partido_previo > min(entrenamientos)
                if fecha_inicio_custom:
                    fecha_inicio_str = pd.to_datetime(fecha_inicio_custom).strftime('%d/%m/%Y')
                elif fecha_partido_previo:
                    fecha_inicio_str = fecha_partido_previo.strftime('%d/%m/%Y')
                else:
                    fecha_inicio_str = df_entrenos['Fecha'].min().strftime('%d/%m/%Y') if not df_entrenos.empty else fecha_partido_actual.strftime('%d/%m/%Y')

                fecha_fin_str = fecha_partido_actual.strftime('%d/%m/%Y')
                microciclo_label = f"Microciclo {jornada_num} - {rival} ({fecha_inicio_str} - {fecha_fin_str})"

                logger.info(f"Datos de microciclo generados: {len(situaciones)} situaciones")

                return {
                    'status': 'success',
                    'data': {
                        'situaciones': situaciones,
                        'distancias': distancias,
                        'num_registros': num_registros,
                        'fechas': fechas,
                        'tipos': tipos,
                        'tipo_distancia': tipo_distancia,
                        'tipo_distancia_label': tipo_distancia_label,
                        'jornada': jornada,
                        'microciclo_label': microciclo_label
                    },
                    'message': 'Datos del microciclo obtenidos correctamente'
                }

            finally:
                connection.close()

        except Exception as e:
            logger.error(f"Error obteniendo datos del microciclo: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'status': 'error',
                'message': f'Error al obtener datos del microciclo: {str(e)}'
            }
