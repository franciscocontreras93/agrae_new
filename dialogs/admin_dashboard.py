import requests
import json

from qgis.PyQt.QtWidgets import (QMainWindow, QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, # type: ignore
                                 QLabel, QComboBox, QPushButton, QSizePolicy, QSpacerItem, QWidget, QFrame, QMessageBox, QCompleter)
from qgis.PyQt.QtCore import Qt, QThread, pyqtSignal  # type: ignore
from qgis.PyQt.QtGui import QIcon, QMovie # type: ignore

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import numpy as np
from ..gui import agraeGUI
from qgis.core import QgsMessageLog, Qgis # For logging if needed, but not for API results # type: ignore


class ApiWorker(QThread):
    """
    Worker thread para realizar peticiones API sin bloquear la GUI.
    """
    # Señal emitida cuando la petición es exitosa. El argumento es el JSON de respuesta.
    finished = pyqtSignal(object, object) # (api_response, kpi_targets_config)
    # Señal emitida cuando ocurre un error. El argumento es el mensaje de error.
    error = pyqtSignal(str, object)    # (error_message, kpi_targets_config)

    def __init__(self, endpoint_url: str, endpoint: str, kpi_targets_config: list, params=None, method='GET', data=None, headers=None):
        super().__init__()
        self.base_url = endpoint_url
        self.endpoint = endpoint
        self.kpi_targets_config = kpi_targets_config # Lista de configuraciones de widgets a actualizar
        self.params = params
        self.method = method.upper()
        self.data = data
        self.headers = headers
    def run(self):
        try:
            url = self.base_url + self.endpoint
            if self.method == 'GET':
                response = requests.get(url, params=self.params, headers=self.headers, timeout=10000) # Increased timeout
            elif self.method == 'POST':
                response = requests.post(url, json=self.data, params=self.params, headers=self.headers, timeout=10000) # Increased timeout
            # Añadir más métodos (PUT, DELETE) si es necesario
            else:
                self.error.emit(f"Método HTTP no soportado: {self.method}", self.kpi_targets_config)
                return
            response.raise_for_status()  # Lanza una excepción para códigos de error HTTP (4xx o 5xx)
            self.finished.emit(response.json(), self.kpi_targets_config)
        except requests.exceptions.RequestException as e:
            self.error.emit(f"Error de red: {e}", self.kpi_targets_config)
        except json.JSONDecodeError as e:
            self.error.emit(f"Error al decodificar JSON: {e}", self.kpi_targets_config)
        except Exception as e:
            self.error.emit(f"Error inesperado: {e}", self.kpi_targets_config)

# Stylesheet for KPI Cards
KPI_CARD_STYLE = """
QFrame#kpiCard {
    border: 1px solid #D3D3D3;
    border-radius: 8px;
    background-color: white;
    min-width: 180px;
    max-width: 220px;
    min-height: 90px;
    max-height: 110px;
}
QFrame#kpiCard:hover {
    background-color: #E6F2FF;
    border: 1px solid #B0C4DE;
}
QLabel#kpiTitle {
    font-size: 10pt;
    color: #555555;
    padding-bottom: 5px;
}
QLabel#kpiValue {
    font-size: 14pt;
    font-weight: bold;
    color: #005A9C;
}
QLabel#kpiValue[status="loading"] { color: #FFA500; }
QLabel#kpiValue[status="error"] { color: #FF0000; font-size: 11pt; }
QLabel#kpiValue[status="ok"] { color: #005A9C; }
QLabel#kpiValue[status="idle"] { color: #808080; }
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

    def plot_bar_chart(self, labels, values, title="Gráfico de Barras", xlabel="Categorías", ylabel="Valores"):
        self.axes.cla()
        if not labels or not values or len(labels) != len(values):
            self.axes.text(0.5, 0.5, 'Datos insuficientes para graficar',
                           ha='center', va='center', transform=self.axes.transAxes)
            self.draw()
            return
        bars = self.axes.bar(labels, values)
        self.axes.set_title(title)
        self.axes.set_ylabel(ylabel)
        self.axes.set_xlabel(xlabel)

        # Rotar etiquetas del eje X si son muchas para evitar superposición
        if len(labels) > 7: # Ajusta este número según sea necesario
            self.axes.tick_params(axis='x', labelrotation=45, labelsize=8)
        else:
            self.axes.tick_params(axis='x', labelrotation=0, labelsize=10)

        self.fig.tight_layout()
        self.draw()
    def plot_pie_chart(self, labels, sizes, title="Gráfico Circular"): # Renombrado para generalidad
        self.axes.cla()
        if not labels or not sizes or len(labels) != len(sizes) or sum(sizes) == 0:
            self.axes.text(0.5, 0.5, 'No hay datos de cultivos para graficar',
                           ha='center', va='center', transform=self.axes.transAxes)
            self.draw()
            return

        # Filter out zero sizes to prevent pie chart errors/warnings
        filtered_labels_sizes = [(label, size) for label, size in zip(labels, sizes) if size > 0]
        if not filtered_labels_sizes:
            self.axes.text(0.5, 0.5, 'Todas las áreas de cultivo son cero.',
                           ha='center', va='center', transform=self.axes.transAxes)
            self.draw()
            return
            
        filtered_labels, filtered_sizes = zip(*filtered_labels_sizes)

        self.axes.pie(filtered_sizes, labels=filtered_labels, autopct='%1.1f%%', startangle=90)
        self.axes.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        self.axes.set_title(title)
        self.fig.tight_layout()
        self.draw()

class AgraeDashboardWindow(QMainWindow): # Cambiado de QDialog a QMainWindow
    closingPlugin = pyqtSignal() # Definir la señal aquí

    def __init__(self, parent=None):
        super().__init__(parent) # Llamar al constructor de QMainWindow
        self.setWindowTitle("aGrae Dashboard General")
        self.resize(1024, 768)
        self.endpoint_url = 'http://localhost:8000' # Asegúrate que tu API esté corriendo aquí
        self.active_workers = [] # Para mantener referencia a los workers activos
        self.UIComponents()
        self.setStyleSheet(KPI_CARD_STYLE)
        self.load_campanias_data()
        self.on_campania_changed_and_update_kpis() # Carga inicial de explotaciones y KPIs

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
        card_lotes = self._create_kpi_card("Nº de Lotes", self.lbl_num_lotes)
        card_explotaciones = self._create_kpi_card("Nº de Lotes", self.lbl_num_explotaciones)
        card_area_mapeada = self._create_kpi_card("Área Mapeada", self.lbl_area_mapeada)
        kpi_layout.addWidget(card_hectareas, 0, 0)
        kpi_layout.addWidget(card_lotes, 0, 1)
        kpi_layout.addWidget(card_area_mapeada, 0, 2)
        kpi_layout.addWidget(card_explotaciones, 0, 3)
        kpi_layout.setColumnStretch(3, 1)
        kpi_layout.setRowStretch(2, 1)
        return kpi_group

    def UIComponents(self):
        # Crear un widget central para QMainWindow
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget) # Aplicar el layout al widget central
        main_layout.setSpacing(15)
        filter_group = QGroupBox("Filtros")
        filter_layout = QHBoxLayout(filter_group)
        self.combo_campania = QComboBox()
        self.combo_campania.setMinimumWidth(180)
        self.combo_campania.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.combo_explotacion = QComboBox()
        self.combo_explotacion.setMinimumWidth(180)
        self.combo_explotacion.setEditable(True) # Hacer el combo editable
        self.combo_explotacion.setInsertPolicy(QComboBox.NoInsert) # No permitir insertar nuevos items
        self.combo_explotacion.completer().setCompletionMode(QCompleter.PopupCompletion) # Opcional: mostrar completer como popup
        self.combo_explotacion.completer().setFilterMode(Qt.MatchContains) # Hacer la búsqueda menos estricta
        self.combo_explotacion.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.combo_campania.currentIndexChanged.connect(self.on_campania_changed)
        
        self.combo_chart_type = QComboBox()
        self.combo_chart_type.addItem("Áreas por Cultivo", "area_cultivos")
        # self.combo_chart_type.addItem("Otro Tipo de Gráfico", "otro_tipo") # Ejemplo para futura expansión
        self.btn_actualizar_dashboard = QPushButton("Actualizar")
        self.btn_actualizar_dashboard.setIcon(agraeGUI().getIcon('reload'))
        self.lbl_total_hectareas = QLabel("N/A")
        self.lbl_total_hectareas.setObjectName("kpiValue")
        self.lbl_total_hectareas.setProperty("status", "idle")
        self.lbl_num_lotes = QLabel("N/A")
        self.lbl_num_lotes.setObjectName("kpiValue")
        self.lbl_num_lotes.setProperty("status", "idle")
        self.lbl_num_explotaciones = QLabel("N/A")
        self.lbl_num_explotaciones.setObjectName("kpiValue")
        self.lbl_num_explotaciones.setProperty("status", "idle")
        self.lbl_area_mapeada = QLabel("N/A")
        self.lbl_area_mapeada.setObjectName("kpiValue")
        self.lbl_area_mapeada.setProperty("status", "idle")
        filter_layout.addWidget(QLabel("Campaña:"))
        filter_layout.addWidget(self.combo_campania)
        filter_layout.addSpacing(20)
        filter_layout.addWidget(QLabel("Explotación:"))
        filter_layout.addWidget(self.combo_explotacion)
        filter_layout.addSpacing(20)
        filter_layout.addWidget(QLabel("Tipo de Gráfico:"))
        filter_layout.addWidget(self.combo_chart_type)
        filter_layout.addStretch(1)

        self.combo_campania.currentIndexChanged.connect(self.on_campania_changed_and_update_kpis)
        self.combo_explotacion.currentIndexChanged.connect(self.update_all_kpis)
        filter_layout.addWidget(self.btn_actualizar_dashboard)
        self.btn_actualizar_dashboard.clicked.connect(self.update_all_kpis)

        main_layout.addWidget(filter_group)

        kpi_section_widget = self._create_kpi_section()
        main_layout.addWidget(kpi_section_widget)
        charts_group = QGroupBox("Gráficos")
        charts_layout = QVBoxLayout(charts_group)
        self.chart_canvas1 = MplCanvasDashboard(self, width=7, height=3, dpi=100)
        charts_layout.addWidget(self.chart_canvas1)
        self.combo_chart_type.currentIndexChanged.connect(self.update_all_kpis) # Actualizar al cambiar tipo de gráfico
        main_layout.addWidget(charts_group)
        main_layout.setStretchFactor(charts_group, 1)

    def load_campanias_data(self):
        """
        Carga las campañas desde la API y las añade al QComboBox.
        """
        self.combo_campania.clear()
        self.combo_campania.addItem("Todas las Campañas", None) # Primer elemento

        campanias_data = self.fetch_data_synchronous('/api/campanias/')

        if campanias_data:
            if isinstance(campanias_data, list): # Asegurarse que es una lista
                for campania in campanias_data:
                    if isinstance(campania, dict) and 'id' in campania and 'nombre' in campania: # type: ignore
                        self.combo_campania.addItem(str(campania['nombre']), campania['id'])
                    else:
                        QgsMessageLog.logMessage(f"Formato de campaña inesperado: {campania}", "Dashboard API", Qgis.Warning)
            else:
                QgsMessageLog.logMessage(f"Respuesta de API para campañas no es una lista: {campanias_data}", "Dashboard API", Qgis.Warning)

    def load_explotaciones_data(self, idcampania=None):
        """
        Carga las explotaciones desde la API para una campaña dada y las añade al QComboBox.
        """
        self.combo_explotacion.clear()
        self.combo_explotacion.addItem("Todas las Explotaciones", None) # Primer elemento

        if idcampania is None:
            # Si no hay campaña seleccionada (o es "Todas las Campañas"), no cargar más explotaciones.
            return

        endpoint_explotaciones = f'/api/explotaciones/?idcampania={idcampania}'
        explotaciones_data = self.fetch_data_synchronous(endpoint_explotaciones)

        if explotaciones_data:
            if isinstance(explotaciones_data, list): # Asegurarse que es una lista
                for explotacion in explotaciones_data:
                    if isinstance(explotacion, dict) and 'id' in explotacion and 'nombre' in explotacion: # type: ignore
                        self.combo_explotacion.addItem(f'{explotacion['id']}-{str(explotacion['nombre'])}', explotacion['id']) # Mostrar solo el nombre
                    else:
                        QgsMessageLog.logMessage(f"Formato de explotación inesperado: {explotacion}", "Dashboard API", Qgis.Warning)
            else:
                QgsMessageLog.logMessage(f"Respuesta de API para explotaciones no es una lista: {explotaciones_data}", "Dashboard API", Qgis.Warning)

    def on_campania_changed(self):
        id_campania_seleccionada = self.combo_campania.currentData()
        self.load_explotaciones_data(id_campania_seleccionada)

    def on_campania_changed_and_update_kpis(self):
        self.on_campania_changed() # Carga/actualiza las explotaciones
        self.update_all_kpis()     # Actualiza todos los KPIs

    def _start_kpi_fetch_worker(self, endpoint: str, params: dict, kpi_targets_config: list): # type: ignore
        """
        Inicia un worker para obtener datos de un endpoint y actualizar los widgets configurados.
        kpi_targets_config: Lista de diccionarios, cada uno con:
            {'widget': QLabel, 'key': str, 'unit': str, 'default': str, 'is_float': bool}
            o para gráficos:
            {'target_type': 'chart_crop_area', 'canvas': MplCanvasDashboard, 'default_title': str}
        """
        if not kpi_targets_config: # type: ignore
            QgsMessageLog.logMessage("Error: kpi_targets_config está vacío.", "Dashboard Worker", Qgis.Critical)
            return

        for config_item in kpi_targets_config:
            if 'widget' in config_item: # Es un KPI para un QLabel
                widget = config_item['widget']
                widget.setText("Cargando...")
                widget.setProperty("status", "loading")
                self._apply_style_refresh(widget) # Asegurar que el estilo de "loading" se aplique
            elif config_item.get('target_type') and config_item.get('target_type').startswith('chart_'): # Es para un gráfico
                canvas = config_item.get('canvas')
                if canvas:
                    # Mostrar un estado de "Cargando..." en el gráfico
                    base_title = config_item.get('default_title', "Gráfico")
                    loading_title = self._get_dynamic_chart_title(f"{base_title} - Cargando...")
                    # Usar plot_bar_chart para el estado de carga, ya que es el principal ahora
                    if config_item.get('target_type') == 'chart_area_cultivos':
                        canvas.plot_bar_chart([], [], title=loading_title, xlabel="Cultivo", ylabel="Área (ha)")
                    # else: # Para otros tipos de gráficos futuros
                        # canvas.plot_bar_chart([], [], title=loading_title) # O un método de ploteo genérico
            # else: # Configuración no reconocida (opcional: loguear una advertencia)
                # QgsMessageLog.logMessage(f"Configuración de KPI no reconocida: {config_item}", "Dashboard Worker", Qgis.Warning)

        worker = ApiWorker(self.endpoint_url, endpoint, kpi_targets_config, params=params)
        worker.finished.connect(self._handle_kpi_response)
        worker.error.connect(self._handle_kpi_error)
        self.active_workers.append(worker) # Guardar referencia
        worker.start()

    def _process_and_plot_area_cultivos(self, api_response: object, canvas: MplCanvasDashboard, default_title: str):
        labels = []
        sizes = []
        chart_title = default_title

        if isinstance(api_response, list):
            for item_dict in api_response:
                if isinstance(item_dict, dict):
                    for _id, details in item_dict.items(): # Assumes one key-value pair per item_dict
                        if isinstance(details, dict) and 'nombre' in details and 'area' in details:
                            labels.append(str(details['nombre'])) # Nombres de cultivo
                            try:
                                sizes.append(float(details['area'])) # Áreas
                            except (ValueError, TypeError):
                                QgsMessageLog.logMessage(f"Área inválida para cultivo {details['nombre']}: {details['area']}", "Dashboard", Qgis.Warning)
                                # Optionally skip or add a placeholder if needed
                        else:
                             QgsMessageLog.logMessage(f"Estructura de item inesperada en datos de área de cultivo: {details}", "Dashboard", Qgis.Warning)
        else:
            QgsMessageLog.logMessage(f"Respuesta de API de área de cultivo no es una lista: {api_response}", "Dashboard", Qgis.Warning)
        canvas.plot_bar_chart(labels, sizes, title=self._get_dynamic_chart_title(default_title), xlabel="Cultivo", ylabel="Área (ha)")

    def _apply_style_refresh(self, widget: QWidget):
        """Fuerza la reaplicación de estilos y el repintado del widget."""
        if widget: # Asegurarse de que el widget no sea None
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            widget.update()

    def _handle_kpi_response(self, api_response: object, kpi_targets_config: list):
        # Check if this response is for the crop area chart
        chart_config_item = next((item for item in kpi_targets_config if item.get('target_type') == 'chart_area_cultivos'), None)
        if chart_config_item:
            canvas = chart_config_item['canvas']
            default_title = chart_config_item.get('default_title', "Distribución de Cultivos")
            self._process_and_plot_area_cultivos(api_response, canvas, default_title)
            self._remove_worker_reference(QThread.currentThread()) # Ensure worker is removed
            return # Exit after handling chart

        if not isinstance(api_response, dict):
            error_msg = "Error Respuesta API"
            for config_item in kpi_targets_config:
                widget = config_item['widget']
                widget.setText(error_msg)
                widget.setProperty("status", "error")
                self._apply_style_refresh(widget)
            self._remove_worker_reference(QThread.currentThread())
            return

        for config_item in kpi_targets_config:
            widget = config_item['widget']
            key = config_item['key']
            unit = config_item.get('unit', '')
            default_val = config_item.get('default', "N/A")
            is_float = config_item.get('is_float', False)

            raw_value = api_response.get(key)

            if raw_value is not None:
                if is_float:
                    try:
                        value_to_display = f"{float(raw_value):.2f}{unit}"
                        widget.setText(value_to_display)
                        widget.setProperty("status", "ok")
                    except (ValueError, TypeError):
                        value_to_display = f"Error Formato{unit}"
                        widget.setText(value_to_display)
                        widget.setProperty("status", "error")
                else:
                    value_to_display = f"{str(raw_value)}{unit}"
                    widget.setText(value_to_display)
                    widget.setProperty("status", "ok")
            else: # raw_value is None
                widget.setText(default_val)
                if "Error" in str(default_val) or default_val == "N/A":
                    widget.setProperty("status", "error" if "Error" in str(default_val) else "idle")
                else:
                    widget.setProperty("status", "idle")
            self._apply_style_refresh(widget)

        self._remove_worker_reference(QThread.currentThread())

    def _handle_kpi_error(self, error_message: str, kpi_targets_config: list):
        chart_config_item = next((item for item in kpi_targets_config if item.get('target_type') == 'chart_area_cultivos'), None)
        if chart_config_item:
            canvas = chart_config_item['canvas']
            error_title = chart_config_item.get('default_title', "Error Cargando Datos de Cultivo")
            # Usar plot_bar_chart para mostrar el error
            canvas.plot_bar_chart([], [], title=f"{error_title}: {error_message.split(':')[0]}", xlabel="Cultivo", ylabel="Área (ha)")
            self._remove_worker_reference(QThread.currentThread())
            return

        for config_item in kpi_targets_config:
            widget = config_item['widget']
            widget.setText(error_message)
            widget.setProperty("status", "error")
            self._apply_style_refresh(widget)

        self._remove_worker_reference(QThread.currentThread())

    def update_all_kpis(self):
        idcampania = self.combo_campania.currentData()
        idexplotacion = self.combo_explotacion.currentData()
        params = {}
        if idcampania is not None:
            params['idcampania'] = idcampania
        if idexplotacion is not None:
            params['idexplotacion'] = idexplotacion

        # Iniciar workers para cada KPI
        kpi_total_hectareas_config = [{
            'widget': self.lbl_total_hectareas, 'key': 'area_ha', 
            'unit': ' ha', 'default': "0.00 ha", 'is_float': True
        }]
        self._start_kpi_fetch_worker('/api/area_lotes/', params.copy(), kpi_total_hectareas_config)

        kpi_num_lotes_config = [{
            'widget': self.lbl_num_lotes, 'key': 'num_lotes', 
            'unit': '', 'default': "0", 'is_float': False
        }]
        self._start_kpi_fetch_worker('/api/num_lotes/', params.copy(), kpi_num_lotes_config)

        # Para /api/area_mapeada/ que actualiza dos KPIs
        kpi_area_mapeada_multiple_config = [
            {
                'widget': self.lbl_area_mapeada, 'key': 'area_mapeada',
                'unit': ' ha', 'default': "0.00 ha", 'is_float': True
            },
            {
                'widget': self.lbl_num_explotaciones, 'key': 'lotes_mapeados', # Asumiendo que este es el QLabel para lotes_mapeados
                'unit': '', 'default': "0", 'is_float': False
            }
        ]
        self._start_kpi_fetch_worker('/api/area_mapeada/', params.copy(), kpi_area_mapeada_multiple_config)

        # Worker for the selected chart type
        selected_chart_type = self.combo_chart_type.currentData()
        if selected_chart_type == "area_cultivos":
            kpi_chart_config = [{
                'target_type': 'chart_area_cultivos', # Specific target type
                'canvas': self.chart_canvas1,
                'default_title': "Distribución de Cultivos por Área"
            }]
            self._start_kpi_fetch_worker('/api/area_cultivos/', params.copy(), kpi_chart_config)
        # elif selected_chart_type == "otro_tipo":
            # Lógica para otro tipo de gráfico y su API

    def _get_dynamic_chart_title(self, base_title: str) -> str:
        """Determina el título del gráfico basado en la selección actual de filtros."""
        campania_text = self.combo_campania.currentText()
        explotacion_text = self.combo_explotacion.currentText()

        if self.combo_explotacion.currentData() is not None: # Si hay una explotación específica
            # Tomar nombre después del ID si el formato es "ID-Nombre"
            explotacion_nombre_display = explotacion_text.split('-', 1)[-1] if '-' in explotacion_text else explotacion_text
            title_chart = f"{base_title} para Explotación: {explotacion_nombre_display}"
        elif self.combo_campania.currentData() is not None: # Si hay una campaña específica
            title_chart = f"{base_title} para Campaña: {campania_text}"
        else: # Todas las campañas y todas las explotaciones
            title_chart = f"{base_title} (General)"
        return title_chart

    def _remove_worker_reference(self, worker_thread):
        """Elimina la referencia al worker una vez que ha terminado."""
        # Asegurarse de que worker_thread es una instancia de QThread (o ApiWorker)
        # y no un objeto None o algo inesperado.
        if isinstance(worker_thread, QThread) and worker_thread in self.active_workers:
            self.active_workers.remove(worker_thread)

    def fetch_data_synchronous(self, endpoint, params=None, headers=None, method='GET', data=None) -> dict | None:
        """
        Sincrónicamente obtiene datos de un endpoint API usando requests.
        Usado para cargas iniciales donde el bloqueo breve es aceptable (ej. llenar combos).

        Args:
            endpoint (str): El endpoint de la API.
            params (dict, optional): Parámetros de la query.
            headers (dict, optional): Cabeceras HTTP.
            method (str, optional): Método HTTP.
            data (dict, optional): Datos para peticiones POST.

        Returns:
            dict or None: La respuesta JSON de la API si es exitosa, None en caso contrario.
        """
        try:
            url = self.endpoint_url + endpoint
            response = requests.request(method.upper(), url, params=params, headers=headers, json=data, timeout=10000) # Increased timeout
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(None, "Error", f"Error de conexion: {e}")
            return None
        except json.JSONDecodeError as e:
            QMessageBox.critical(None, "Error", f"Error al analizar la respuesta JSON: {e}")
            return None
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Error inesperado: {e}")
            return None

    def closeEvent(self, event):
        """
        Sobrescribe el evento de cierre para ocultar la ventana en lugar de destruirla.
        Y emite la señal closingPlugin.
        """
        # Detener todos los workers activos si es necesario
        for worker in list(self.active_workers): # Iterar sobre una copia por si se modifica la lista
            if worker.isRunning():
                worker.quit() # Pide al hilo que termine limpiamente
                worker.wait() # Espera a que termine
        self.active_workers.clear() # Limpiar la lista después de detenerlos

        self.closingPlugin.emit() # Emitir la señal antes de ocultar/ignorar
        self.hide()  # Oculta la ventana
        event.ignore() # Ignora el evento de cierre para que no se destruya
