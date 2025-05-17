from qgis.PyQt.QtWidgets import QToolTip
from qgis.PyQt.QtGui import QCursor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
from qgis.core import QgsMessageLog, Qgis # For logging

class MplCanvasDashboard(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super(MplCanvasDashboard, self).__init__(self.fig)
        self.setParent(parent)
        try:
            self.fig.patch.set_facecolor('None')
            self.fig.patch.set_alpha(0)
            self.axes.patch.set_facecolor('None')
            self.axes.patch.set_alpha(0)
        except Exception as e:
            QgsMessageLog.logMessage(f"Error setting transparent background for MplCanvasDashboard: {e}", "Dashboard", Qgis.Warning)

        self.bars_container = None
        self.bar_labels = []
        self.bar_values = []
        self.fig.canvas.mpl_connect('motion_notify_event', self._on_motion)

    def clear_plot(self):
        self.fig.clear() 
        self.axes = self.fig.add_subplot(111) 
        self.bars_container = None
        self.bar_labels = []
        self.bar_values = []
        self.draw()
        QToolTip.hideText()

    def plot_bar_chart(self, labels, values, title="Gráfico de Barras", xlabel="Categorías", ylabel="Valores"):
        self.clear_plot() 
        if not labels or not values or len(labels) != len(values):
            self.axes.text(0.5, 0.5, 'Datos insuficientes para graficar',
                           ha='center', va='center', transform=self.axes.transAxes)
            self.draw()
            return
        
        self.bar_labels = list(labels)
        self.bar_values = list(values)
        self.bars_container = self.axes.bar(self.bar_labels, self.bar_values)

        self.axes.set_title(title)
        self.axes.set_ylabel(ylabel)
        self.axes.set_xlabel(xlabel)

        if len(labels) > 7:
            self.axes.tick_params(axis='x', labelrotation=45, labelsize=8)
        else:
            self.axes.tick_params(axis='x', labelrotation=0, labelsize=10)

        self.fig.tight_layout()
        self.draw()

    def plot_pie_chart(self, labels, values, title="", colors=None):
        self.clear_plot()

        if not labels or not values or len(labels) != len(values):
            self.axes.text(0.5, 0.5, 'Datos de entrada inválidos',
                           ha='center', va='center', transform=self.axes.transAxes)
            self.draw()
            return

        processed_labels = []
        processed_values = []
        processed_colors = [] if colors else None

        for i in range(len(values)):
            value = values[i]
            label = labels[i]
            
            if value is not None and value > 0:
                processed_labels.append(label)
                processed_values.append(value)
                if colors:
                    if i < len(colors):
                        processed_colors.append(colors[i])
            
        if not processed_values:
            self.axes.text(0.5, 0.5, 'No hay datos positivos para graficar',
                           ha='center', va='center', transform=self.axes.transAxes)
            self.draw()
            return

        final_colors_for_pie = None
        if processed_colors: 
            if len(processed_colors) == len(processed_values):
                final_colors_for_pie = processed_colors
            else:
                QgsMessageLog.logMessage(
                    f"Advertencia: La lista de colores procesados ({len(processed_colors)}) no coincide con los valores a graficar ({len(processed_values)}). Se usarán colores por defecto.",
                    "Dashboard PieChart", Qgis.Warning
                )

        wedges, texts, autotexts = self.axes.pie(
            processed_values, 
            autopct='%1.1f%%', 
            startangle=90,
            colors=final_colors_for_pie, 
            pctdistance=0.85 
        )
        self.axes.axis('equal')  
        self.axes.set_title(title)
        if processed_labels and wedges: 
             self.axes.legend(wedges, processed_labels, title="Categorías", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
        self.fig.tight_layout() 
        self.draw()

    def plot_gauge_chart(self, percentage_value, title="", label="Área Mapeada", is_loading=False):
        self.fig.clear() 
        self.axes = self.fig.add_subplot(111)
        self.axes.set_title(title, va='bottom', y=1.05)

        if is_loading:
            self.axes.text(0.5, 0.5, "Cargando...", ha='center', va='center', fontsize=16, weight='bold', transform=self.axes.transAxes)
            self.axes.axis('off')
            self.draw()
            return

        if percentage_value is None:
             self.axes.text(0.5, 0.5, "Valor no disponible", ha='center', va='center', fontsize=14, transform=self.axes.transAxes)
             self.axes.axis('off')
             self.draw()
             return
        
        QgsMessageLog.logMessage(
            f"PlotGaugeChart received: percentage_value={percentage_value}",
            "DashboardGaugeDebug", Qgis.Info
        )

        min_gauge_val = 0
        max_gauge_val = 100.0

        clamped_percentage_value = np.clip(float(percentage_value), min_gauge_val, max_gauge_val)

        value_mapeado = clamped_percentage_value
        value_no_mapeado = max_gauge_val - clamped_percentage_value

        green_color = '#90EE90'
        red_color = '#FF7F7F'

        sizes = []
        colors = []

        if value_mapeado > 1e-3:
            sizes.append(value_mapeado)
            colors.append(green_color)
        if value_no_mapeado > 1e-3:
            sizes.append(value_no_mapeado)
            colors.append(red_color)

        if not sizes:
            sizes = [100]
            colors = [red_color]
            if clamped_percentage_value == 100.0:
                colors = [green_color]

        self.axes.pie(sizes, colors=colors, startangle=90, wedgeprops=dict(width=0.35, edgecolor='w'))
        self.axes.axis('equal')

        self.axes.text(0, 0, f"{clamped_percentage_value:.1f}%", ha='center', va='center', fontsize=16, weight='bold')
        self.axes.text(0, -0.15, label, ha='center', va='center', fontsize=9, color='gray')
        self.draw()

    def _on_motion(self, event):
        visible = False
        tooltip_text = ""

        if event.inaxes == self.axes:
            if self.bars_container and self.bar_labels and self.bar_values:
                for i, bar_patch in enumerate(self.bars_container.patches):
                    contains, _ = bar_patch.contains(event)
                    if contains:
                        if i < len(self.bar_labels) and i < len(self.bar_values):
                            label = self.bar_labels[i]
                            value = self.bar_values[i]
                            tooltip_text = f"{label}: {value:.2f}"
                            current_ylabel = self.axes.get_ylabel()
                            if "Área (ha)" in current_ylabel or "ha" in current_ylabel.lower():
                                tooltip_text += " ha"
                            elif "€" in current_ylabel:
                                tooltip_text += " €"
                            elif "Número de Lotes" in current_ylabel:
                                tooltip_text = f"{label}: {int(value)}"
                            visible = True
                        break
        
        if visible:
            QToolTip.showText(QCursor.pos(), tooltip_text, self)
        else:
            QToolTip.hideText()
