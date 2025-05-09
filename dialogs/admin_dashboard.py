import traceback
from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, 
                                 QLabel, QComboBox, QPushButton, QSizePolicy, QSpacerItem, QWidget, QFrame) # Added QFrame
from qgis.PyQt.QtCore import Qt, QThread, QObject, pyqtSignal # <--- Añadimos QThread, QObject, pyqtSignal
from qgis.PyQt.QtGui import QIcon
from qgis.core import Qgis, QgsMessageLog
from qgis.utils import iface # Para la barra de mensajes
import requests
import psycopg2
from psycopg2 import extras

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import numpy as np

from ..gui import agraeGUI # Asumiendo que tienes iconos aquí
from ..db import agraeDataBaseDriver # Para la conexión a BD
from ..sql import aGraeSQLTools # Si tienes queries predefinidas
from ..tools import aGraeTools # Para herramientas generales

# Stylesheet for KPI Cards
KPI_CARD_STYLE = """
QFrame#kpiCard {
    border: 1px solid #D3D3D3; /* Light gray border */
    border-radius: 8px;
    background-color: white;
    min-width: 180px; 
    max-width: 220px; /* Adjusted max-width */
    min-height: 90px; 
    max-height: 110px;
}
QFrame#kpiCard:hover {
    background-color: #E6F2FF; /* Lighter blue on hover */
    border: 1px solid #B0C4DE; /* LightSteelBlue on hover */
}
QLabel#kpiTitle {
    font-size: 10pt;
    color: #555555; /* Dark gray for title */
    padding-bottom: 5px;
}
QLabel#kpiValue {
    font-size: 14pt;
    font-weight: bold;
    color: #005A9C; /* Darker blue for value */
}
"""

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
        except Exception:
            pass

    def clear_plot(self):
        self.axes.cla()
        self.draw()

    def plot_example_bar_chart(self, labels, values, title="Ejemplo Gráfico de Barras"):
        self.axes.cla()
        if not labels or not values or len(labels) != len(values):
            self.axes.text(0.5, 0.5, 'Datos insuficientes para graficar',
                           ha='center', va='center', transform=self.axes.transAxes)
            self.draw()
            return
        
        self.axes.bar(labels, values)
        self.axes.set_title(title)
        self.axes.set_ylabel("Valores")
        self.axes.set_xlabel("Categorías")
        self.fig.tight_layout()
        self.draw()

# --- Worker para peticiones API asíncronas ---
class ApiWorker(QObject):
    finished = pyqtSignal(object) # Emitirá el diccionario de datos o None en caso de error
    error = pyqtSignal(str)     # Emitirá el mensaje de error
    api_url_hectareas_worker = pyqtSignal(str, dict) # Señal para iniciar la petición

    def clear_plot(self):
        self.axes.cla()
        self.draw()

    def plot_example_bar_chart(self, labels, values, title="Ejemplo Gráfico de Barras"):
        self.axes.cla()
        if not labels or not values or len(labels) != len(values):
            self.axes.text(0.5, 0.5, 'Datos insuficientes para graficar',
                           ha='center', va='center', transform=self.axes.transAxes)
            self.draw()
            return
        
        self.axes.bar(labels, values)
        self.axes.set_title(title)
        self.axes.set_ylabel("Valores")
        self.axes.set_xlabel("Categorías")
        self.fig.tight_layout()
        self.draw()

    def __init__(self): # No necesita url, params, timeout en el constructor
        super().__init__()

    # Slot para ser llamado desde el hilo principal
    def fetch_data(self, url, params, timeout=10):
        try:
            QgsMessageLog.logMessage(f"Worker: Iniciando petición a {url} con params {params}", "AgraeDashboard", Qgis.Info)
            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            print(data) # Para depuración, puedes quitarlo después
            self.finished.emit(data)
        except requests.exceptions.RequestException as e:
            self.error.emit(f"Error de red: {e}")
        except ValueError as e: # Error al parsear JSON
            self.error.emit(f"Error de JSON: {e}")
        except Exception as e: # Captura general para otros errores inesperados
            self.error.emit(f"Error inesperado en worker: {e}")

class AgraeDashboardDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tools = aGraeTools() # Si necesitas herramientas comunes
        self.setWindowTitle("aGrae Dashboard General")
        self.setMinimumSize(950, 700) # Adjusted for potentially wider layout
        self.api_thread = None # Para mantener una referencia al hilo
        self.api_worker = None # Para mantener una referencia al worker

        # Initialize KPI labels here so they can be passed to create_kpi_card
        self.lbl_total_hectareas = QLabel("N/A")
        self.lbl_total_hectareas.setObjectName("kpiValue")
        self.lbl_num_lotes = QLabel("N/A")
        self.lbl_num_lotes.setObjectName("kpiValue")
        self.lbl_num_explotaciones = QLabel("N/A")
        self.lbl_num_explotaciones.setObjectName("kpiValue")
        self.lbl_cultivos_principales = QLabel("N/A")
        self.lbl_cultivos_principales.setObjectName("kpiValue")
        self.lbl_area_mapeada = QLabel("N/A") 
        self.lbl_area_mapeada.setObjectName("kpiValue")

        self.UIComponents()
        self.load_initial_data()
        self.setStyleSheet(KPI_CARD_STYLE) # Apply stylesheet to the dialog

    def _create_kpi_card(self, title_text: str, value_label: QLabel) -> QFrame:
        card = QFrame()
        card.setObjectName("kpiCard")
        card.setFrameShape(QFrame.StyledPanel)
        card.setFrameShadow(QFrame.Raised) 

        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 10, 10, 10) 
        layout.setSpacing(5)

        title_label = QLabel(title_text)
        title_label.setObjectName("kpiTitle")
        title_label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        title_label.setWordWrap(True)

        value_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        value_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        value_label.setWordWrap(True)

        layout.addWidget(title_label)
        layout.addWidget(value_label)
        
        layout.setStretchFactor(value_label, 1)
        return card

    def _create_kpi_section(self) -> QGroupBox:
        kpi_group = QGroupBox("Indicadores Clave (KPIs)")
        kpi_layout = QGridLayout(kpi_group) 
        kpi_layout.setSpacing(15) 

        card_hectareas = self._create_kpi_card("Total Hectáreas", self.lbl_total_hectareas)
        card_lotes = self._create_kpi_card("Número de Lotes", self.lbl_num_lotes)
        card_explotaciones = self._create_kpi_card("Nº Explotaciones", self.lbl_num_explotaciones)
        card_cultivos = self._create_kpi_card("Cultivo(s) Principal(es)", self.lbl_cultivos_principales)
        card_area_mapeada = self._create_kpi_card("Área Mapeada", self.lbl_area_mapeada)

        kpi_layout.addWidget(card_hectareas, 0, 0)
        kpi_layout.addWidget(card_lotes, 0, 1)
        kpi_layout.addWidget(card_area_mapeada, 0, 2)
        kpi_layout.addWidget(card_explotaciones, 1, 0)
        kpi_layout.addWidget(card_cultivos, 1, 1, 1, 2) # Span 2 columns

        # Add spacers to push cards to the top-left
        kpi_layout.setColumnStretch(3, 1) 
        kpi_layout.setRowStretch(2, 1)    
        
        return kpi_group

    def UIComponents(self):
        main_layout = QVBoxLayout(self) # Changed to QVBoxLayout
        main_layout.setSpacing(15)

        # --- Sección de Filtros ---
        filter_group = QGroupBox("Filtros")
        filter_layout = QHBoxLayout(filter_group) # Changed to QHBoxLayout for horizontal layout

        self.combo_campania = QComboBox()
        self.combo_campania.setMinimumWidth(180)
        self.combo_campania.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.combo_explotacion = QComboBox()
        self.combo_explotacion.setMinimumWidth(180)
        self.combo_explotacion.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_actualizar_dashboard = QPushButton("Actualizar")
        self.btn_actualizar_dashboard.setIcon(agraeGUI().getIcon('reload')) # Asume que tienes este icono

        filter_layout.addWidget(QLabel("Campaña:"))
        filter_layout.addWidget(self.combo_campania)
        filter_layout.addSpacing(20) # Add some space between filter groups
        filter_layout.addWidget(QLabel("Explotación:"))
        filter_layout.addWidget(self.combo_explotacion)
        filter_layout.addStretch(1) # Pushes the button to the right
        filter_layout.addWidget(self.btn_actualizar_dashboard)
        filter_group.setLayout(filter_layout)
        main_layout.addWidget(filter_group) # Filters at the top

        # --- Sección de KPIs ---
        kpi_section_widget = self._create_kpi_section()
        main_layout.addWidget(kpi_section_widget) # KPIs below filters

        # --- Sección de Gráficos ---
        charts_group = QGroupBox("Gráficos")
        charts_layout = QVBoxLayout(charts_group) 

        self.chart_canvas1 = MplCanvasDashboard(self, width=7, height=3, dpi=100)
        charts_layout.addWidget(self.chart_canvas1)
        main_layout.addWidget(charts_group) # Charts below KPIs
        main_layout.setStretchFactor(charts_group, 1) # Charts group takes available vertical space

        # Conexiones
        self.combo_campania.currentIndexChanged.connect(self.on_campania_changed)
        self.btn_actualizar_dashboard.clicked.connect(self.update_dashboard_data)

    def load_initial_data(self):
        self.load_campanias()
        # Cargar datos iniciales del dashboard (ej. todas las campañas o la más reciente)
        self.update_dashboard_data()

    def load_campanias(self):
        self.combo_campania.clear()
        # Lógica para cargar campañas desde la BD (similar a lab_dialog.py)
        try:
            conn = agraeDataBaseDriver().connection()
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                # Asume que tienes una tabla 'campaign.campanias'
                cursor.execute("SELECT id, nombre FROM campaign.campanias ORDER BY nombre DESC")
                campanias = cursor.fetchall()
                self.combo_campania.addItem("Todas las Campañas", None) # Opción para ver todo
                for camp in campanias:
                    self.combo_campania.addItem(camp['nombre'], camp['id'])
            conn.close()
        except Exception as e:
            QgsMessageLog.logMessage(f"Error cargando campañas: {e}\n{traceback.format_exc()}", "AgraeDashboard", Qgis.Critical)

    def on_campania_changed(self, index):
        self.combo_explotacion.clear()
        id_campania = self.combo_campania.itemData(index)
        self.combo_explotacion.addItem("Todas las Explotaciones", None)
        if id_campania is not None:
            # Lógica para cargar explotaciones de la campaña seleccionada
            try:
                conn = agraeDataBaseDriver().connection()
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                    # Asume que tienes una tabla 'agrae.explotacion' y una tabla de unión
                    cursor.execute("SELECT DISTINCT e.idexplotacion, e.nombre FROM agrae.explotacion e JOIN campaign.data cd ON e.idexplotacion = cd.idexplotacion WHERE cd.idcampania = %s ORDER BY e.nombre", (id_campania,))
                    explotaciones = cursor.fetchall()
                    for exp in explotaciones:
                        self.combo_explotacion.addItem(exp['nombre'], exp['idexplotacion'])
                conn.close()
            except Exception as e:
                QgsMessageLog.logMessage(f"Error cargando explotaciones: {e}\n{traceback.format_exc()}", "AgraeDashboard", Qgis.Critical)
        self.update_dashboard_data() # Actualizar dashboard cuando cambia la campaña

    def update_dashboard_data(self):
        id_campania = self.combo_campania.currentData()
        id_explotacion = self.combo_explotacion.currentData()

        QgsMessageLog.logMessage(f"Actualizando dashboard para Campaña ID: {id_campania}, Explotación ID: {id_explotacion}", "AgraeDashboard", Qgis.Info)

        # --- Obtener total de hectáreas desde la API (ASÍNCRONO) ---
        self.lbl_total_hectareas.setText("Cargando...")
        self.lbl_total_hectareas.setProperty("status", "loading") 
        self.style().unpolish(self.lbl_total_hectareas); self.style().polish(self.lbl_total_hectareas)

        api_url_hectareas = "http://localhost:8000/api/area_lotes/"
        params_hectareas = {}
        if id_campania is not None:
            params_hectareas['id_campania'] = id_campania
        if id_explotacion is not None:
            params_hectareas['id_explotacion'] = id_explotacion

        # Si ya hay un hilo corriendo, no iniciar otro hasta que termine o se maneje.
        # Por ahora, una solución simple es no iniciar uno nuevo si ya hay uno.
        # Una solución más robusta podría cancelar el anterior o poner en cola las peticiones.
        # if self.api_thread and self.api_thread.isRunning(): # Condición original
        if self.api_worker is not None: 
            return

        self.btn_actualizar_dashboard.setEnabled(False) # Deshabilitar botón mientras la API está trabajando

        self.api_thread = QThread()
        self.api_worker = ApiWorker()
        self.api_worker.moveToThread(self.api_thread)

        # Conectar señales del worker a slots en el diálogo
        self.api_worker.finished.connect(self.handle_api_hectareas_result)
        self.api_worker.error.connect(self.handle_api_hectareas_error)

        # Conectar la señal de inicio del hilo a la función de trabajo del worker
        # Usaremos una señal personalizada para pasar los argumentos de forma segura entre hilos
        self.api_worker.api_url_hectareas_worker.connect(self.api_worker.fetch_data)
        self.api_thread.started.connect(lambda: self.api_worker.api_url_hectareas_worker.emit(api_url_hectareas, params_hectareas))

        # Limpieza cuando el hilo termine
        self.api_worker.finished.connect(self.api_thread.quit)
        self.api_worker.error.connect(self.api_thread.quit) # También salir en caso de error
        self.api_worker.finished.connect(self.api_worker.deleteLater)
        self.api_thread.finished.connect(self.api_thread.deleteLater)
        self.api_thread.finished.connect(lambda: self.btn_actualizar_dashboard.setEnabled(True)) # Rehabilitar botón
        self.api_thread.finished.connect(self._clear_thread_references) # Limpiar referencias

        self.api_thread.start()

        # --- Otros datos (pueden ser síncronos por ahora o también asíncronos) ---
        self.lbl_num_lotes.setText("Cargando...")
        self.lbl_num_lotes.setProperty("status", "loading"); self.style().unpolish(self.lbl_num_lotes); self.style().polish(self.lbl_num_lotes)
        self.lbl_num_explotaciones.setText("Cargando...")
        self.lbl_num_explotaciones.setProperty("status", "loading"); self.style().unpolish(self.lbl_num_explotaciones); self.style().polish(self.lbl_num_explotaciones)
        self.lbl_cultivos_principales.setText("Cargando...")
        self.lbl_cultivos_principales.setProperty("status", "loading"); self.style().unpolish(self.lbl_cultivos_principales); self.style().polish(self.lbl_cultivos_principales)
        self.lbl_area_mapeada.setText("Cargando...")
        self.lbl_area_mapeada.setProperty("status", "loading"); self.style().unpolish(self.lbl_area_mapeada); self.style().polish(self.lbl_area_mapeada)

        self.chart_canvas1.plot_example_bar_chart(["Cultivo A", "Cultivo B"], [120, 250], "Ejemplo")

        QgsMessageLog.logMessage("Petición API para hectáreas iniciada asíncronamente.", "AgraeDashboard", Qgis.Info)

    def _clear_thread_references(self):
        """Slot para limpiar las referencias al hilo y al worker después de que el hilo haya terminado."""
        QgsMessageLog.logMessage("Limpiando referencias de hilo y worker.", "AgraeDashboard", Qgis.Info)
        self.api_thread = None
        self.api_worker = None

    # Necesitarás crear métodos para obtener los datos específicos de la BD
    # def get_summary_data(self, id_campania, id_explotacion): ...
    # def get_chart1_data(self, id_campania, id_explotacion): ...



    def handle_api_hectareas_result(self, data):
        if data:
            total_ha = data.get("area_ha") # <--- CAMBIO: Usar la clave correcta de tu API
            if total_ha is not None:
                try:
                    self.lbl_total_hectareas.setText(f"<b>{float(total_ha):,.2f}</b> ha".replace(",", "@").replace(".", ",").replace("@", "."))
                    self.lbl_total_hectareas.setProperty("status", "ok")
                    QgsMessageLog.logMessage(f"Total hectáreas obtenido: {total_ha}", "AgraeDashboard", Qgis.Success)
                except ValueError:
                    self.lbl_total_hectareas.setText("Dato inválido (API)")
                    self.lbl_total_hectareas.setProperty("status", "error")
                    QgsMessageLog.logMessage(f"Valor de total_hectareas no es un número: {total_ha}", "AgraeDashboard", Qgis.Warning)
            else:
                self.lbl_total_hectareas.setText("N/A (API)")
                self.lbl_total_hectareas.setProperty("status", "error")
                QgsMessageLog.logMessage("La API no devolvió 'area_ha'.", "AgraeDashboard", Qgis.Warning)
        else:
            self.lbl_total_hectareas.setText("Respuesta vacía (API)")
            self.lbl_total_hectareas.setProperty("status", "error")
            QgsMessageLog.logMessage("El worker de la API devolvió datos vacíos.", "AgraeDashboard", Qgis.Warning)
        
        self.style().unpolish(self.lbl_total_hectareas); self.style().polish(self.lbl_total_hectareas)
        # La limpieza del hilo se maneja con las conexiones a finished/deleteLater

    def handle_api_hectareas_error(self, error_message):
        self.lbl_total_hectareas.setText("Error API")
        self.lbl_total_hectareas.setProperty("status", "error")
        self.style().unpolish(self.lbl_total_hectareas); self.style().polish(self.lbl_total_hectareas)
        QgsMessageLog.logMessage(f"Error en API para total_hectareas: {error_message}", "AgraeDashboard", Qgis.Critical)
        iface.messageBar().pushMessage("Error API", error_message, level=Qgis.Critical, duration=5)
        # La limpieza del hilo se maneja con las conexiones a finished/deleteLater

    def closeEvent(self, event):
        if self.api_thread and self.api_thread.isRunning():
            QgsMessageLog.logMessage("Cerrando diálogo, intentando detener hilo API...", "AgraeDashboard", Qgis.Info)
            # Aquí podrías intentar alguna lógica para detener el hilo si es posible,
            # o simplemente advertir que una operación está en curso.
            # Por ahora, solo lo registramos.
        super().closeEvent(event)