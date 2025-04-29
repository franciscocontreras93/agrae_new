# -*- coding: utf-8 -*-
# --- Imports ---
from pvlib import solarposition
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from datetime import timedelta, date, datetime
import os
from typing import Dict, Tuple, List, Optional, Any

# Define un tipo para la información de fechas para claridad
DateInfoDict = Dict[str, Dict[str, Any]]

class SolarDiagramGenerator:
    """
    Genera diagramas polares de posición solar para ubicaciones dadas,
    con opciones de coloreado basado en analema y marca de agua de logo configurables por instancia.
    """

    # --- Constants ---
    TZ: str = 'UTC'
    HOUR_FOR_ANALEMMA: int = 13
    RMAX: int = 90
    COLOR_YELLOW: str = '#ffc000'
    COLOR_BLUE: str = '#5b9bd5'
    ALPHA_FONDO: float = 0.75
    LINEWIDTH_DIVISION: int = 4
    MONTH_ABBR_ES: Dict[int, str] = { 1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun", 7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic" }
    STYLES: Dict[str, Any] = { 'linewidth_path': 1.0, 'linewidth_path_intermediate': 0.5, 'marker_size_hourly_solstice': 20, 'marker_size_hourly_intermediate': 8 }

    # --- MODIFIED __init__ ---
    def __init__(self):
        """
        Inicializa el generador con la configuración del logo.
        La latitud y longitud se pasarán al método generate_plot.
        """



        self.logo_path: Optional[str] = 'logo.png'
        self.logo_alpha: float = 1
        self.logo_height_frac: float = 0.08
        self.logo_margin_frac: float = 0.02
        if self.logo_path and not os.path.exists(self.logo_path):
            # print(f"ADVERTENCIA al inicializar: El archivo de logo '{self.logo_path}' no existe. Se generarán los gráficos sin logo.")
            self.logo_path = None

    @staticmethod
    def obtener_flanco(azimut_grados: float) -> str:
        """Determina el flanco cardinal/intercardinal basado en grados de azimut."""
        flancos_rangos_grados: Dict[str, Tuple[float, float]] = { 'Flanco N': (337.5, 22.5), 'Flanco NE': (22.5, 67.5), 'Flanco E': (67.5, 112.5), 'Flanco SE': (112.5, 157.5), 'Flanco S': (157.5, 202.5), 'Flanco SO': (202.5, 247.5), 'Flanco O': (247.5, 292.5), 'Flanco NO': (292.5, 337.5) }
        az: float = azimut_grados % 360; rango_n: Tuple[float, float] = flancos_rangos_grados['Flanco N']
        if az >= rango_n[0] or az < rango_n[1]: return 'Flanco N'
        for nombre, (inicio, fin) in flancos_rangos_grados.items():
            if nombre == 'Flanco N': continue
            if inicio <= az < fin: return nombre
        return "Flanco Desconocido"

    def _determine_dominant_analemma_side(self, solpos_analemma: pd.DataFrame, azimuth_degrees: float) -> str:
        """Determina qué lado ('clockwise' o 'counter_clockwise') contiene más puntos del analema."""
        if solpos_analemma.empty: return 'counter_clockwise'
        azimuth_ref_norm: float = azimuth_degrees % 360; count_counter_clockwise: int = 0; count_clockwise: int = 0
        for az_sun in solpos_analemma['azimuth']:
            relative_az: float = (az_sun - azimuth_ref_norm + 360) % 360
            if 0 < relative_az < 180: count_clockwise += 1
            elif 180 < relative_az < 360: count_counter_clockwise += 1
        return 'clockwise' if count_clockwise > count_counter_clockwise else 'counter_clockwise'

    def _calculate_solar_positions(self, latitude: float, longitude: float,
                                   year: int, dates_info: DateInfoDict,
                                   envero_start_date_obj: date, envero_end_date_obj: date) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, pd.DataFrame]]:
        """Calcula posiciones solares del analema y diarias para una lat/lon dada."""
        times_analemma_base: pd.DatetimeIndex = pd.date_range(f'{year}-01-01 00:00:00', f'{year+1}-01-01 00:00:00', freq='D', tz=self.TZ, inclusive='left')
        times_analemma: pd.DatetimeIndex = times_analemma_base + timedelta(hours=self.HOUR_FOR_ANALEMMA)
        solpos_analemma: pd.DataFrame = solarposition.get_solarposition(times_analemma, latitude, longitude)
        solpos_analemma = solpos_analemma.loc[solpos_analemma['apparent_elevation'] > 0, :]
        solpos_envero_analemma: pd.DataFrame = solpos_analemma[ (solpos_analemma.index.date >= envero_start_date_obj) & (solpos_analemma.index.date <= envero_end_date_obj) ]
        solpos_days: Dict[str, pd.DataFrame] = {}
        for label, info in dates_info.items():
            date_day: date = info['date']
            localized_date: pd.Timestamp = pd.Timestamp(datetime(year, date_day.month, date_day.day), tz=self.TZ)
            times_day: pd.DatetimeIndex = pd.date_range(localized_date, localized_date + timedelta(days=1), freq='1min', tz=self.TZ, inclusive='left')
            solpos_day: pd.DataFrame = solarposition.get_solarposition(times_day, latitude, longitude)
            solpos_day = solpos_day.loc[solpos_day['apparent_elevation'] > 0, :]
            solpos_days[label] = solpos_day
        return solpos_analemma, solpos_envero_analemma, solpos_days

    def _plot_background_and_azimuth(self, ax: Axes, azimuth_degrees: float, color_counter_clockwise: str, color_clockwise: str) -> None:
        """Dibuja los fondos coloreados, la rejilla y la línea de azimut."""
        custom_azimuth_rad: float = np.radians(azimuth_degrees); opposite_rad: float = (custom_azimuth_rad + np.pi) % (2 * np.pi)
        ccw_start_rad: float = custom_azimuth_rad - np.pi; ccw_end_rad: float = custom_azimuth_rad
        theta_ccw: np.ndarray = np.linspace(ccw_start_rad, ccw_end_rad, 100)
        ax.fill_between(theta_ccw, 0, self.RMAX, color=color_counter_clockwise, alpha=self.ALPHA_FONDO, zorder=0)
        cw_start_rad: float = custom_azimuth_rad; cw_end_rad: float = custom_azimuth_rad + np.pi
        theta_cw: np.ndarray = np.linspace(cw_start_rad, cw_end_rad, 100)
        ax.fill_between(theta_cw, 0, self.RMAX, color=color_clockwise, alpha=self.ALPHA_FONDO, zorder=0)
        ax.grid(color='white', linestyle='dashed', linewidth=0.6, zorder=1)
        ax.plot([custom_azimuth_rad, custom_azimuth_rad], [0, self.RMAX], color='red', linewidth=self.LINEWIDTH_DIVISION, linestyle='-', zorder=2)
        ax.plot([opposite_rad, opposite_rad], [0, self.RMAX], color='red', linewidth=self.LINEWIDTH_DIVISION, linestyle='-', zorder=2)

    def _plot_analemma(self, ax: Axes, solpos_analemma: pd.DataFrame, solpos_envero_analemma: pd.DataFrame) -> None:
        """Dibuja el analema completo y resalta el período de Envero."""
        ax.plot(np.radians(solpos_analemma.azimuth), solpos_analemma.apparent_zenith, linewidth=0.5, color='black', linestyle='-', zorder=10)
        if not solpos_envero_analemma.empty:
            ax.plot(np.radians(solpos_envero_analemma.azimuth), solpos_envero_analemma.apparent_zenith, linewidth=2.5, color='green', linestyle='-', zorder=11)

    # --- RESTORED Implementation ---
    def _plot_daily_paths_and_labels(self, ax: Axes, solpos_days: Dict[str, pd.DataFrame], dates_info: DateInfoDict) -> None:
        """Dibuja las trayectorias solares diarias, marcadores horarios y etiquetas."""
        for label, info in dates_info.items():
            solpos_day = solpos_days[label]
            if solpos_day.empty: continue # Skip if no sun path data for this day

            date_day = info['date']
            label_type = info['type']

            # --- Plot Daily Path Line ---
            line_color = 'black'
            # Use class attribute self.STYLES
            if label_type == 'Solsticio':
                linestyle_path = '-'
                current_linewidth = self.STYLES['linewidth_path']
            elif label_type == 'Intermedio':
                linestyle_path = '--'
                current_linewidth = self.STYLES['linewidth_path_intermediate']
            else: # Fallback
                linestyle_path = '-'
                current_linewidth = self.STYLES['linewidth_path']

            ax.plot(np.radians(solpos_day.azimuth), solpos_day.apparent_zenith,
                    zorder=3, color=line_color,
                    linewidth=current_linewidth,
                    linestyle=linestyle_path)

            # --- Plot Hourly Markers and Labels ---
            solpos_day_hourly = solpos_day[solpos_day.index.minute == 0]
            if not solpos_day_hourly.empty:
                marker_color = 'black'
                # Use class attribute self.STYLES
                current_marker_size = self.STYLES['marker_size_hourly_solstice'] if label_type == 'Solsticio' else self.STYLES['marker_size_hourly_intermediate']

                ax.scatter(np.radians(solpos_day_hourly.azimuth), solpos_day_hourly.apparent_zenith,
                           s=current_marker_size, color=marker_color,
                           marker='+', zorder=4)

                # Add hourly labels only for Solstices
                if label == 'Solsticio Verano' or label == 'Solsticio Invierno':
                    radial_offset_label = 2.5 # Offset for label placement
                    va_align = 'bottom' if label == 'Solsticio Verano' else 'top' # Above/Below marker
                    zenith_offset = -radial_offset_label if label == 'Solsticio Verano' else radial_offset_label

                    for index, row in solpos_day_hourly.iterrows():
                        hour_label = f'{index.hour}h'
                        ax.text(np.radians(row.azimuth), row.apparent_zenith + zenith_offset, hour_label,
                                fontsize='xx-small', color='black', ha='center',
                                va=va_align, zorder=6)

            # --- Plot Trajectory Label (Outside Plot Area) ---
            if label != 'Envero': # Envero label is handled in the legend
                 # Ensure there's data to plot
                if solpos_day.empty: continue
                first_point = solpos_day.iloc[0]
                first_az_rad = np.radians(first_point.azimuth)
                first_az_deg = first_point.azimuth
                # Use class attribute self.RMAX
                radial_pos_outside = self.RMAX + 10 # Position outside the main circle

                # Determine alignment based on starting azimuth
                if 0 <= first_az_deg < 90: ha, va = 'left', 'bottom'
                elif 90 <= first_az_deg < 180: ha, va = 'left', 'top'
                elif 180 <= first_az_deg < 270: ha, va = 'right', 'top'
                else: ha, va = 'right', 'bottom'

                # Format label text
                if label_type == 'Solsticio':
                    # Use class attribute self.MONTH_ABBR_ES
                    month_str = self.MONTH_ABBR_ES.get(date_day.month, f"{date_day.month:02d}")
                    new_label = f"{date_day.day} {month_str} {label_type}"
                elif label == '21 Mar/Sep': new_label = "21 Mar-Sep"
                elif label == '21 Abr/Ago': new_label = "21 Abr-Ago"
                elif label == '21 May/Jul': new_label = "21 May-Jul"
                elif label == '21 Feb/Oct': new_label = "21 Feb-Oct"
                elif label == '21 Jan/Nov': new_label = "21 Ene-Nov"
                else: new_label = label # Fallback

                ax.text(first_az_rad, radial_pos_outside, new_label,
                        fontsize='xx-small', ha=ha, va=va, color='black', rotation=0, zorder=6)

    # --- RESTORED Implementation ---
    def _configure_polar_axes(self, ax: Axes) -> None:
        """Configura la apariencia de los ejes polares."""
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
        # Use class attribute self.RMAX
        ax.set_rmax(self.RMAX)

        # Zenith (Radial) Ticks and Labels
        ax.set_yticks(range(0, self.RMAX + 1, 15))
        yticklabels = ax.set_yticklabels([f'{y}°' for y in range(0, self.RMAX + 1, 15)], fontsize='x-small')
        ax.set_rlabel_position(0) # Position labels at North
        for label_obj in ax.get_yticklabels():
            label_obj.set_rotation(90)
            label_obj.set_horizontalalignment('center')
            label_obj.set_verticalalignment('center')
            label_obj.set_zorder(7) # Ensure labels are on top

        # Azimuth (Angular) Ticks and Labels
        azimuth_ticks_deg = np.arange(0, 360, 10)
        azimuth_ticks_rad = np.radians(azimuth_ticks_deg)
        ax.set_xticks(azimuth_ticks_rad)

        # Create labels, highlighting cardinal directions
        azimuth_labels = [''] * len(azimuth_ticks_deg)
        cardinals = {0: 'N', 90: 'E', 180: 'S', 270: 'W'}
        for i, deg in enumerate(azimuth_ticks_deg):
            if deg in cardinals:
                azimuth_labels[i] = cardinals[deg]
            elif deg % 10 == 0: # Label every 30 degrees non-cardinal
                 azimuth_labels[i] = f'{deg}°'
            # else: keep empty string for less clutter

        xticklabels = ax.set_xticklabels(azimuth_labels, fontsize='xx-small')
        for label_obj in ax.get_xticklabels():
            if label_obj.get_text() in cardinals.values():
                label_obj.set_color('red')
                label_obj.set_fontweight('bold')
            label_obj.set_zorder(7) # Ensure labels are on top
        
        ax.tick_params(axis='x', pad=-3)

    # --- RESTORED Implementation ---
    def _add_title_and_legend(self, fig: Figure, latitude: float, longitude: float,
                              name: str, azimuth_degrees: float,
                              color_counter_clockwise: str, flank_label_ccw: str,
                              color_clockwise: str, flank_label_cw: str) -> None:
        """Añade el cuadro de título y el cuadro de leyenda a la figura."""
        # --- Title Box ---
        title_ax_rect: List[float] = [0.80, 0.75, 0.18, 0.15]; ax_title: Axes = fig.add_axes(title_ax_rect); ax_title.axis('off')
        current_date_str: str = date.today().strftime('%Y-%m-%d')
        title_text: str = (f"Diagrama Posición Solar\n"
                           f"Lote: {name.upper()}\n"
                           f"Lat: {latitude:.2f}°\n"
                           f"Lon: {longitude:.2f}°\n"
                           f"Fecha: {current_date_str}\n"
                           f"Dirección: {azimuth_degrees}°\n")
        ax_title.text(0.0, 1.0, title_text, transform=ax_title.transAxes, fontsize='xx-small', va='top', ha='left', wrap=True)

        # --- Legend Box ---
        legend_ax_rect: List[float] = [0.75, 0.05, 0.18, 0.25]; ax_legend: Axes = fig.add_axes(legend_ax_rect); ax_legend.axis('off')
        envero_legend_line = Line2D([0], [0], color='green', lw=2.5, label="Envero")
        # Use class attributes self.ALPHA_FONDO, self.LINEWIDTH_DIVISION
        legend_elements: List[Any] = [
            Patch(facecolor=color_counter_clockwise, alpha=self.ALPHA_FONDO, label=f'Insolación {flank_label_ccw}'),
            Patch(facecolor=color_clockwise, alpha=self.ALPHA_FONDO, label=f'Insolación {flank_label_cw}'),
            Line2D([0], [0], color='red', lw=self.LINEWIDTH_DIVISION, label=f'Dirección ({azimuth_degrees}°)'),
            envero_legend_line
        ]
        # Use class attribute self.COLOR_YELLOW
        if color_clockwise == self.COLOR_YELLOW:
            legend_elements = [legend_elements[1], legend_elements[0]] + legend_elements[2:]
        ax_legend.legend(handles=legend_elements, loc='center left', bbox_to_anchor=(0.0, 0.5), fontsize='x-small', borderaxespad=0.)

    def _add_logo_watermark(self, fig: Figure) -> None:
        """
        Añade una marca de agua de logo en la esquina inferior izquierda,
        usando la configuración de la instancia.
        """
        if not self.logo_path: return
        try:
            logo = mpimg.imread(self.logo_path); img_h, img_w, _ = logo.shape; aspect_ratio = img_w / img_h
            fig_w_inch, fig_h_inch = fig.get_size_inches(); logo_h_inch = fig_h_inch * self.logo_height_frac; logo_w_inch = logo_h_inch * aspect_ratio
            ax_width = logo_w_inch / fig_w_inch; ax_height = logo_h_inch / fig_h_inch; ax_left = self.logo_margin_frac; ax_bottom = self.logo_margin_frac
            logo_ax: Axes = fig.add_axes([ax_left, ax_bottom, ax_width, ax_height], anchor='SW', zorder=0.5)
            logo_ax.imshow(logo, alpha=self.logo_alpha); logo_ax.axis('off')
        except FileNotFoundError: pass
        except Exception as e: print(f"Advertencia: Ocurrió un error al añadir el logo: {e}")


    # --- Public Method ---
    def generate_plot(self,
                      latitude: float,
                      longitude: float,
                      azimuth_degrees: float,
                      name: str = 'lote prueba',
                      year: Optional[int] = None,
                      output_directory: str = 'graficos_solares',
                      save_plot: bool = True,
                      show_plot: bool = False) -> None:
        """
        Genera, opcionalmente guarda y opcionalmente muestra un diagrama solar polar
        para la latitud/longitud especificadas. Usa la configuración de logo de la instancia.
        """
        if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
             print(f"Advertencia para '{name}': Latitud o Longitud inválida ({latitude}, {longitude}). Saltando gráfico.")
             return
        current_year: int = year if year is not None else date.today().year

        # --- Key Dates ---
        summer_solstice_date: date = date(current_year, 6, 21)
        winter_solstice_date: date = date(current_year, 12, 21)
        dates_info: DateInfoDict = { 'Solsticio Verano': {'date': summer_solstice_date, 'type': 'Solsticio'}, 'Solsticio Invierno': {'date': winter_solstice_date, 'type': 'Solsticio'}, '21 May/Jul': {'date': date(current_year, 7, 21), 'type': 'Intermedio'}, '21 Abr/Ago': {'date': date(current_year, 8, 21), 'type': 'Intermedio'}, '21 Mar/Sep': {'date': date(current_year, 9, 21), 'type': 'Intermedio'}, '21 Feb/Oct': {'date': date(current_year, 10, 21), 'type': 'Intermedio'}, '21 Jan/Nov': {'date': date(current_year, 11, 21), 'type': 'Intermedio'}, 'Envero': {'date': date(current_year, 8, 15), 'type': 'Intermedio'}, }
        envero_start_day: int = 15; envero_start_month: int = 8; envero_duration_days: int = 20
        envero_start_date_obj: date = date(current_year, envero_start_month, envero_start_day)
        envero_end_date_obj: date = envero_start_date_obj + timedelta(days=envero_duration_days - 1)

        # --- Calculations and Plotting Steps ---
        solpos_analemma, solpos_envero_analemma, solpos_days = self._calculate_solar_positions( latitude, longitude, current_year, dates_info, envero_start_date_obj, envero_end_date_obj )
        dominant_side: str = self._determine_dominant_analemma_side(solpos_analemma, azimuth_degrees)
        color_for_clockwise_side: str; color_for_counter_clockwise_side: str
        if dominant_side == 'clockwise': color_for_clockwise_side = self.COLOR_YELLOW; color_for_counter_clockwise_side = self.COLOR_BLUE
        else: color_for_clockwise_side = self.COLOR_BLUE; color_for_counter_clockwise_side = self.COLOR_YELLOW
        flank_azimuth_ccw: float = (azimuth_degrees - 90) % 360; flank_label_ccw: str = SolarDiagramGenerator.obtener_flanco(flank_azimuth_ccw)
        flank_azimuth_cw: float = (azimuth_degrees + 90) % 360; flank_label_cw: str = SolarDiagramGenerator.obtener_flanco(flank_azimuth_cw)

        fig: Figure; ax: Axes
        fig, ax = plt.subplots(1, 1, subplot_kw={'projection': 'polar'})
        fig.subplots_adjust(left=0.1, right=0.75, top=0.9, bottom=0.1)

        self._plot_background_and_azimuth(ax, azimuth_degrees, color_for_counter_clockwise_side, color_for_clockwise_side)
        self._plot_analemma(ax, solpos_analemma, solpos_envero_analemma)
        # --- Make sure to pass dates_info ---
        self._plot_daily_paths_and_labels(ax, solpos_days, dates_info)
        self._configure_polar_axes(ax)
        self._add_title_and_legend(fig, latitude, longitude, name, azimuth_degrees, color_for_counter_clockwise_side, flank_label_ccw, color_for_clockwise_side, flank_label_cw)
        self._add_logo_watermark(fig)

        # --- Save/Show/Close ---
        if save_plot:
            os.makedirs(output_directory, exist_ok=True)
            safe_name = "".join(c if c.isalnum() else "_" for c in name)
            output_filename = f'MAPA_SOLAR_{safe_name}_lat{latitude:.2f}_lon{longitude:.2f}_az{azimuth_degrees}.png'
            output_path = os.path.join(output_directory, output_filename)
            try: plt.savefig(output_path, dpi=300); print(f"Gráfico guardado en: {output_path}")
            except Exception as e: print(f"Error al guardar el gráfico '{output_filename}': {e}")
        if show_plot: plt.show()
        plt.close(fig)

