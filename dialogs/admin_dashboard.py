import requests
import json
import matplotlib.pyplot as plt # <--- AÑADIDO para cerrar figuras de Matplotlib


from qgis.PyQt.QtWidgets import (QMainWindow, QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, QToolTip, QFileDialog, QAction, # type: ignore
                                 QLabel, QComboBox, QPushButton, QSizePolicy, QSpacerItem, QWidget, QFrame, QMessageBox, QCompleter,
                                 QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget, QSplitter) 
from qgis.PyQt.QtCore import Qt, pyqtSignal, QThread  # type: ignore
from qgis.core import QgsMessageLog, Qgis # type: ignore

from ..gui import agraeGUI
from ..gui.mpl_canvas_dashboard import MplCanvasDashboard 
from ..tools.api_worker import ApiWorker
from ..gui.KpiCardWidget import KpiCard
from ..gui.CustomTreeWidget import CustomTreeWidget 
from .billing_dialog import CreateInvoiceDialog # <--- NUEVA IMPORTACIÓN
from ..gui.CampaniasComboBox import CampaniasComboBox # <--- NUEVA IMPORTACIÓN DEL COMPONENTE
from .billing_kit_digital_dialog import CreateKitDigitalInvoiceDialog

class AgraeDashboardWindow(QMainWindow):
    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("aGrae Dashboard General")
        self.resize(1024, 768)
        self.endpoint_url = 'http://142.93.41.109:8000'
        self.active_workers = []
        self.current_kpi_update_id = 0 

        # Valores numéricos para cálculos (se mantienen)
        self.lbl_total_hectareas_val = 0.0
        self.lbl_num_lotes_val = 0
        self.lbl_area_mapeada_val = 0.0
        self.lbl_num_lotes_mapeados_val = 0
        self.lbl_area_pendiente_val = 0.0 # Nuevo valor numérico para el área pendiente

        # Atributos para las tarjetas KPI
        self.card_total_hectareas: KpiCard
        self.card_num_lotes: KpiCard
        self.card_num_lotes_mapeados: KpiCard
        self.card_area_mapeada: KpiCard
        self.card_area_pendiente: KpiCard # Nueva tarjeta

        self._create_menu_bar() # Crear la barra de menús
        self.UIComponents()
        # self.load_campanias_data() # Ya no es necesario, CampaniasComboBox lo hace al instanciarse
        self.on_campania_changed_and_update_kpis()

    def _create_menu_bar(self):
        menu_bar = self.menuBar()

        # Menú Archivo (Ejemplo)
        # file_menu = menu_bar.addMenu("&Archivo")
        # exit_action = QAction("Salir", self)
        # exit_action.triggered.connect(self.close)
        # file_menu.addAction(exit_action)

        # Menú Módulos
        modules_menu = menu_bar.addMenu("&Módulos")

        # Submenú para Facturación
        billing_submenu = modules_menu.addMenu("&Facturación") # &F para atajo Alt+M -> F

        # Acción para Crear Factura dentro del submenú Facturación
        create_ordinary_invoice_action = QAction("&Crear Factura Ordinaria", self) # &C para atajo Alt+M -> F -> C
        create_ordinary_invoice_action.triggered.connect(lambda: self._open_create_billing_dialog(True))
        billing_submenu.addAction(create_ordinary_invoice_action)
        create_kd_invoice_action = QAction("&Crear Factura KD", self) # &C para atajo Alt+M -> F -> C
        create_kd_invoice_action.triggered.connect(lambda: self._open_create_billing_dialog(False))
        billing_submenu.addAction(create_kd_invoice_action)

    def _open_create_billing_dialog(self,ordinary:bool = True):
        # Aquí irá la lógica para abrir el diálogo o ventana de creación de facturas
        # Por ahora, mostramos un mensaje
        QgsMessageLog.logMessage("Abriendo diálogo para crear factura...", "Dashboard Menu", Qgis.Info)
        
        # Crear y mostrar el diálogo de facturación
        if ordinary:
            billing_dialog = CreateInvoiceDialog(self) # 'self' como padre para que se comporte como hijo de la ventana principal
            billing_dialog.exec_() # Usar exec_() para un diálogo modal (bloquea la ventana padre)
        else:
            billing_dialog = CreateKitDigitalInvoiceDialog(self)
            billing_dialog.exec_()
        # Si quieres un diálogo no modal, usa billing_dialog.show()
        # y considera guardar una referencia: self.current_billing_dialog = billing_dialog

    def _create_kpi_card(self, title_text: str) -> KpiCard:
        # Simplemente crea y devuelve la tarjeta.
        return KpiCard(title_text)

    def _create_kpi_section(self) -> QGroupBox:
        kpi_group = QGroupBox("Indicadores Clave (KPIs)")
        kpi_layout = QGridLayout(kpi_group)
        kpi_layout.setSpacing(15)

        # Crear las tarjetas
        self.card_total_hectareas = self._create_kpi_card("Total Hectáreas")
        self.card_num_lotes = self._create_kpi_card("Nº de Lotes")
        self.card_area_mapeada = self._create_kpi_card("Área Mapeada")
        self.card_num_lotes_mapeados = self._create_kpi_card("Nº de Lotes Mapeados")
        self.card_area_pendiente = self._create_kpi_card("Área Pendiente de Mapear") # Nueva tarjeta

        # Añadir las tarjetas al layout (ejemplo de layout 2x3)
        kpi_layout.addWidget(self.card_total_hectareas, 0, 0)
        kpi_layout.addWidget(self.card_num_lotes, 0, 1)
        kpi_layout.addWidget(self.card_num_lotes_mapeados, 0, 2) # Mover a la primera fila
        kpi_layout.addWidget(self.card_area_mapeada, 0, 2)
        # kpi_layout.addWidget(self.card_num_lotes_mapeados, 0, 3) # Esta línea parece un duplicado o error, la comento
        kpi_layout.addWidget(self.card_area_pendiente, 1, 0) # Nueva tarjeta en la segunda fila, ajustando layout
        
        # Ajustar el layout para 5 tarjetas, por ejemplo 2 filas (3 en la primera, 2 en la segunda)
        # Fila 0
        kpi_layout.addWidget(self.card_total_hectareas, 0, 0)
        kpi_layout.addWidget(self.card_num_lotes, 0, 1)
        kpi_layout.addWidget(self.card_area_mapeada, 0, 2)
        # Fila 1
        kpi_layout.addWidget(self.card_num_lotes_mapeados, 1, 0)
        kpi_layout.addWidget(self.card_area_pendiente, 1, 1)

        # Conectar señales de doble clic de las tarjetas aquí, después de crearlas
        self.card_total_hectareas.doubleClicked.connect(self._on_kpi_card_double_clicked)
        self.card_num_lotes.doubleClicked.connect(self._on_kpi_card_double_clicked)
        self.card_area_mapeada.doubleClicked.connect(self._on_kpi_card_double_clicked)
        self.card_num_lotes_mapeados.doubleClicked.connect(self._on_kpi_card_double_clicked)
        self.card_area_pendiente.doubleClicked.connect(self._on_kpi_card_double_clicked)

        kpi_layout.setColumnStretch(2, 1) # Ajustar el stretch a la última columna usada
        kpi_layout.setRowStretch(2, 1) # Para empujar las tarjetas hacia arriba si hay espacio vertical
        return kpi_group

    def _create_comparison_charts_section(self) -> QGroupBox:
        main_mapeo_group = QGroupBox("Información de Mapeo") 
        main_mapeo_layout = QVBoxLayout(main_mapeo_group) 

        splitter_info_mapeo = QSplitter(Qt.Horizontal)
        main_mapeo_layout.addWidget(splitter_info_mapeo) 

        donut_chart_group = QGroupBox("Progreso General") 
        donut_chart_layout = QVBoxLayout(donut_chart_group)
        self.comparison_chart_canvas = MplCanvasDashboard(self, width=4, height=3, dpi=90) 
        donut_chart_layout.addWidget(self.comparison_chart_canvas)
        splitter_info_mapeo.addWidget(donut_chart_group) 
        
        pendientes_table_group = QGroupBox("Lotes Pendientes de Mapear") 
        pendientes_table_layout = QVBoxLayout(pendientes_table_group)

        table_headers = ["ID Explotación", "Explotación", "Nº Lotes Pend.", "Área No Mapeada (ha)", "IDs Lotes"]
        hidden_cols = [0, 4] 
        self.table_lotes_pendientes = CustomTreeWidget(headers=table_headers, hidden_columns=hidden_cols, parent=self)
        # self.table_lotes_pendientes.itemDoubleClickedWithData.connect(self._on_pendiente_double_clicked) # Descomentar si se implementa
        
        pendientes_table_layout.addWidget(self.table_lotes_pendientes)
        splitter_info_mapeo.addWidget(pendientes_table_group) 
        
        splitter_info_mapeo.setSizes([int(self.width() * 0.4), int(self.width() * 0.6)]) 
        
        return main_mapeo_group

    def UIComponents(self): 
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget) 

        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        filter_group = QGroupBox("Filtros")
        filter_layout = QHBoxLayout(filter_group)
        
        self.combo_campania = CampaniasComboBox(self.endpoint_url, parent=self)
        self.combo_campania.setMinimumWidth(180)
        self.combo_campania.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.combo_explotacion = QComboBox()
        self.combo_explotacion.setMinimumWidth(180)
        self.combo_explotacion.setEditable(True)
        self.combo_explotacion.setInsertPolicy(QComboBox.NoInsert)
        self.combo_explotacion.completer().setCompletionMode(QCompleter.PopupCompletion)
        self.combo_explotacion.completer().setFilterMode(Qt.MatchContains)
        self.combo_explotacion.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        self.combo_chart_type = QComboBox()
        self.combo_chart_type.addItem("Distribución de Cultivos por Área", "area_cultivos_bar")
        self.btn_actualizar_dashboard = QPushButton("Actualizar")
        self.btn_actualizar_dashboard.setIcon(agraeGUI().getIcon('reload'))
        
        # Los QLabel de KPI individuales ya no se crean aquí

        filter_layout.addWidget(QLabel("Campaña:"))
        filter_layout.addWidget(self.combo_campania)
        filter_layout.addSpacing(20)
        filter_layout.addWidget(QLabel("Explotación:"))
        filter_layout.addWidget(self.combo_explotacion)
        filter_layout.addSpacing(20)
        filter_layout.addStretch(1)

        self.combo_campania.current_campaign_changed.connect(self.on_campania_changed_and_update_kpis)
        self.combo_explotacion.currentIndexChanged.connect(self.update_all_kpis)
        filter_layout.addWidget(self.btn_actualizar_dashboard)
        # Las conexiones de las tarjetas KPI se movieron a _create_kpi_section
        self.btn_actualizar_dashboard.clicked.connect(self.update_all_kpis)

        main_layout.addWidget(filter_group)

        main_splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(main_splitter)

        top_widget_container = QWidget() 
        top_layout = QVBoxLayout(top_widget_container) 
        top_layout.setContentsMargins(0,0,0,0)

        top_splitter = QSplitter(Qt.Horizontal)
        top_layout.addWidget(top_splitter) 
        
        kpi_section_widget = self._create_kpi_section()
        top_splitter.addWidget(kpi_section_widget)

        comparison_charts_section_widget = self._create_comparison_charts_section() 
        top_splitter.addWidget(comparison_charts_section_widget)

        top_splitter.setStretchFactor(0, 1) 
        top_splitter.setStretchFactor(1, 2) 
        main_splitter.addWidget(top_widget_container) 

        charts_group = QGroupBox("Gráficos") 
        charts_layout = QVBoxLayout(charts_group)
        
        chart_controls_layout = QHBoxLayout()
        chart_controls_layout.addWidget(QLabel("Tipo de Gráfico:"))
        chart_controls_layout.addWidget(self.combo_chart_type)
        chart_controls_layout.addStretch(1)
        self.btn_save_chart = QPushButton("Guardar Gráfico")
        self.btn_save_chart.setIcon(agraeGUI().getIcon('save'))
        chart_controls_layout.addWidget(self.btn_save_chart)
        charts_layout.addLayout(chart_controls_layout)

        self.chart_canvas1 = MplCanvasDashboard(self, width=7, height=3, dpi=100) 
        charts_layout.addWidget(self.chart_canvas1)
        self.combo_chart_type.currentIndexChanged.connect(self.update_all_kpis) 
        self.btn_save_chart.clicked.connect(self.save_chart_image)
        
        main_splitter.addWidget(charts_group) 

        main_splitter.setSizes([int(self.height() * 0.5), int(self.height() * 0.5)]) 
        main_layout.setStretchFactor(main_splitter, 1) 

    # def load_campanias_data(self):
    #     """
    #     Este método ya no es necesario aquí. CampaniasComboBox maneja su propia carga.
    #     """
    #     pass

    def load_explotaciones_data(self, idcampania=None):
        self.combo_explotacion.clear()
        self.combo_explotacion.addItem("Todas las Explotaciones", None)

        if idcampania is None:
            return

        endpoint_explotaciones = f'/api/explotaciones/?idcampania={idcampania}'
        explotaciones_data = self.fetch_data_synchronous(endpoint_explotaciones)

        if explotaciones_data:
            if isinstance(explotaciones_data, list):
                for explotacion in explotaciones_data:
                    if isinstance(explotacion, dict) and 'id' in explotacion and 'nombre' in explotacion:
                        self.combo_explotacion.addItem(f'{explotacion['id']}-{str(explotacion['nombre'])}', explotacion['id'])
                    else:
                        QgsMessageLog.logMessage(f"Formato de explotación inesperado: {explotacion}", "Dashboard API", Qgis.Warning)
            else:
                QgsMessageLog.logMessage(f"Respuesta de API para explotaciones no es una lista: {explotaciones_data}", "Dashboard API", Qgis.Warning)

    def on_campania_changed(self, id_campania_seleccionada: int | None):
        """Este método ahora es llamado por on_campania_changed_and_update_kpis."""
        self.load_explotaciones_data(id_campania_seleccionada)

    def on_campania_changed_and_update_kpis(self, id_campania_seleccionada: int | None = None):
        """Maneja el cambio de campaña y actualiza los KPIs y otros datos dependientes."""
        # Si id_campania_seleccionada no se proporciona (ej. llamada inicial), obtenerlo del combo.
        # La señal current_campaign_changed ya nos da el ID correcto.
        current_id_from_combo = id_campania_seleccionada if id_campania_seleccionada is not None else self.combo_campania.get_current_campaign_id()
        self.on_campania_changed(current_id_from_combo)
        self.update_all_kpis()

    def _start_kpi_fetch_worker(self, endpoint: str, params: dict, kpi_targets_config: list, update_id: int):
        if not kpi_targets_config:
            QgsMessageLog.logMessage("Error: kpi_targets_config está vacío.", "Dashboard Worker", Qgis.Critical)
            return

        target_type = None 
        card_widget_to_update: KpiCard = None

        for config_item in kpi_targets_config:
            target_type = config_item.get('target_type') 

            if 'card_widget' in config_item: # Clave cambiada de 'widget' a 'card_widget'
                card_widget_to_update = config_item['card_widget']
                if card_widget_to_update:
                    card_widget_to_update.update_value("Cargando...", "loading")
            elif config_item.get('target_type') == 'area_cultivos_bar': 
                canvas = config_item.get('canvas')
                if canvas:
                    base_title = config_item.get('default_title', "Gráfico")
                    loading_title = self._get_dynamic_chart_title(f"{base_title} - Cargando...")
                    canvas.plot_bar_chart([], [], title=loading_title, xlabel="Cultivo", ylabel="Área (ha)")
            elif config_item.get('target_type') == 'tabla_pendientes':
                table_widget = config_item.get('widget')
                if table_widget:
                    # Asegúrate de que CustomTreeWidget tenga este método
                    table_widget.show_loading_message()


        worker = ApiWorker(self.endpoint_url, endpoint, kpi_targets_config, update_id, params=params)
        worker.finished.connect(self._handle_kpi_response)
        worker.error.connect(self._handle_kpi_error)
        self.active_workers.append(worker)
        worker.start()

    # _apply_style_refresh ya no es necesario aquí

    def _handle_kpi_response(self, api_response: object, kpi_targets_config: list, worker_update_id: int):
        if worker_update_id != self.current_kpi_update_id:
            QgsMessageLog.logMessage(f"Respuesta de worker KPI/Tabla obsoleto (ID: {worker_update_id}, Actual: {self.current_kpi_update_id}). Descartando.", "Dashboard", Qgis.Info) 
            self._remove_worker_reference(self.sender()) 
            return

        table_config_item = next((item for item in kpi_targets_config if item.get('target_type') == 'tabla_pendientes'), None)
        if table_config_item:
            table_widget = table_config_item['widget']
            if isinstance(api_response, list):
                data_map = {
                    0: 'idexplotacion',
                    1: 'nombre_explotacion',
                    2: 'lotes_pendientes',
                    3: 'area_ha', 
                    4: 'idlotes_pendientes'
                }
                table_widget.populate_from_list(api_response, data_map) 
            else:
                QgsMessageLog.logMessage(f"Respuesta de API para tabla de pendientes no es una lista: {api_response}", "Dashboard", Qgis.Warning)
                table_widget.show_error_message("Respuesta API inválida") 
            self._remove_worker_reference(self.sender())
            return 

        chart_config_item = next((item for item in kpi_targets_config if item.get('target_type') == 'area_cultivos_bar'), None)
        if chart_config_item:
            canvas = chart_config_item['canvas']
            default_title = chart_config_item.get('default_title', "Distribución de Cultivos por Área")
            chart_type = chart_config_item.get('target_type')

            labels = []
            sizes = []
            if isinstance(api_response, list):
                for item_dict in api_response:
                    if isinstance(item_dict, dict):
                        for _id, details in item_dict.items(): 
                            if isinstance(details, dict) and 'nombre' in details and 'area' in details:
                                labels.append(str(details['nombre'])) 
                                try:
                                    sizes.append(float(details['area'])) 
                                except (ValueError, TypeError):
                                    QgsMessageLog.logMessage(f"Área inválida para cultivo {details['nombre']}: {details['area']}", "Dashboard", Qgis.Warning)
                            else:
                                 QgsMessageLog.logMessage(f"Estructura de item inesperada en datos de área de cultivo: {details}", "Dashboard", Qgis.Warning)
            else:
                QgsMessageLog.logMessage(f"Respuesta de API de área de cultivo no es una lista: {api_response}", "Dashboard", Qgis.Warning)

            dynamic_title = self._get_dynamic_chart_title(default_title)
            if chart_type == 'area_cultivos_bar':
                canvas.plot_bar_chart(labels, sizes, title=dynamic_title, xlabel="Cultivo", ylabel="Área (ha)")

            self._remove_worker_reference(self.sender())
            return

        if not isinstance(api_response, dict):
            error_msg = "Error Respuesta API"
            for config_item in kpi_targets_config:
                if 'card_widget' in config_item:
                    card_widget: KpiCard = config_item['card_widget']
                    if card_widget:
                        card_widget.update_value(error_msg, "error")
            self._remove_worker_reference(self.sender())
            return

        for config_item in kpi_targets_config:
            if 'card_widget' not in config_item: continue # Saltar si no es una config de tarjeta KPI

            card_widget: KpiCard = config_item['card_widget']
            key = config_item['key']
            unit = config_item.get('unit', '')
            default_val = config_item.get('default', "N/A")
            is_float = config_item.get('is_float', False)

            raw_value = api_response.get(key)
            status_to_set = "ok"
            value_to_display = str(default_val) # Valor por defecto si raw_value es None

            if raw_value is not None:
                if is_float:
                    try:
                        value_to_display = f"{float(raw_value):.2f}{unit}"
                    except (ValueError, TypeError):
                        value_to_display = f"Error Formato{unit}"
                        status_to_set = "error"
                else:
                    value_to_display = f"{str(raw_value)}{unit}"
            else: # raw_value es None
                status_to_set = "idle"
                if "Error" in str(default_val) or default_val == "N/A":
                    status_to_set = "error" if "Error" in str(default_val) else "idle"
            
            if card_widget:
                card_widget.update_value(value_to_display, status_to_set)

            numeric_val_to_store = 0.0 if is_float else 0
            if raw_value is not None and status_to_set != "error":
                try:
                    if is_float: numeric_val_to_store = float(raw_value)
                    else: numeric_val_to_store = int(raw_value)
                except (ValueError, TypeError): 
                    pass # Mantiene el valor numérico en 0 o 0.0

            if card_widget == self.card_total_hectareas: self.lbl_total_hectareas_val = numeric_val_to_store
            elif card_widget == self.card_num_lotes: self.lbl_num_lotes_val = numeric_val_to_store
            elif card_widget == self.card_area_mapeada: self.lbl_area_mapeada_val = numeric_val_to_store
            elif card_widget == self.card_num_lotes_mapeados: self.lbl_num_lotes_mapeados_val = numeric_val_to_store
            # La tarjeta de área pendiente se actualiza en update_comparison_chart_display
            
        self._remove_worker_reference(self.sender())
        
        kpis_updated_for_comparison = False
        for config_item_check in kpi_targets_config: 
            if 'card_widget' in config_item_check and \
               config_item_check['card_widget'] in [self.card_total_hectareas, self.card_num_lotes, self.card_area_mapeada, self.card_num_lotes_mapeados]:
                kpis_updated_for_comparison = True
                break
        if kpis_updated_for_comparison:
            self.update_comparison_chart_display()


    def _handle_kpi_error(self, error_message: str, kpi_targets_config: list, worker_update_id: int):
        if worker_update_id != self.current_kpi_update_id:
            QgsMessageLog.logMessage(f"Error de worker KPI/Tabla obsoleto (ID: {worker_update_id}, Actual: {self.current_kpi_update_id}). Descartando.", "Dashboard", Qgis.Info) 
            self._remove_worker_reference(self.sender())
            return

        table_config_item = next((item for item in kpi_targets_config if item.get('target_type') == 'tabla_pendientes'), None)
        if table_config_item:
            table_widget = table_config_item['widget']
            table_widget.show_error_message(error_message) 
            self._remove_worker_reference(self.sender())
            return 

        chart_config_item = next((item for item in kpi_targets_config if item.get('target_type') == 'area_cultivos_bar'), None)
        if chart_config_item:
            canvas = chart_config_item['canvas']
            error_title_base = chart_config_item.get('default_title', "Error Cargando Datos")
            error_title = self._get_dynamic_chart_title(f"{error_title_base}: {error_message.split(':')[0]}")
            
            chart_type = chart_config_item.get('target_type')
            canvas.plot_bar_chart([], [], title=error_title, xlabel="Cultivo", ylabel="Área (ha)")
            
            self._remove_worker_reference(self.sender())
            return

        for config_item in kpi_targets_config: # Solo afecta a las tarjetas KPI
            if 'card_widget' not in config_item: continue

            card_widget: KpiCard = config_item['card_widget']
            is_float = config_item.get('is_float', False) 

            if card_widget:
                card_widget.update_value(error_message.split(':')[0], "error") # Mostrar solo la primera parte del error

            if card_widget == self.card_total_hectareas: self.lbl_total_hectareas_val = 0.0 if is_float else 0
            elif card_widget == self.card_num_lotes: self.lbl_num_lotes_val = 0
            elif card_widget == self.card_area_mapeada: self.lbl_area_mapeada_val = 0.0 if is_float else 0
            elif card_widget == self.card_num_lotes_mapeados: self.lbl_num_lotes_mapeados_val = 0
            # La tarjeta de área pendiente se actualiza en update_comparison_chart_display

        self._remove_worker_reference(self.sender())

        kpis_affected_by_error = False
        for config_item_check in kpi_targets_config:
            if 'card_widget' in config_item_check and \
               config_item_check['card_widget'] in [self.card_total_hectareas, self.card_num_lotes, self.card_area_mapeada, self.card_num_lotes_mapeados]:
                kpis_affected_by_error = True
                break
        if kpis_affected_by_error:
            self.update_comparison_chart_display()

    def update_all_kpis(self):
        self.current_kpi_update_id += 1 

        idcampania = self.combo_campania.get_current_campaign_id()
        idexplotacion = self.combo_explotacion.currentData()
        params = {}
        if idcampania is not None:
            params['idcampania'] = idcampania
        if idexplotacion is not None:
            params['idexplotacion'] = idexplotacion

        kpi_total_hectareas_config = [{
            'card_widget': self.card_total_hectareas, 'key': 'area_ha', 
            'unit': ' ha', 'default': "0.00 ha", 'is_float': True
        }]
        self._start_kpi_fetch_worker('/api/area_lotes/', params.copy(), kpi_total_hectareas_config, self.current_kpi_update_id)

        kpi_num_lotes_config = [{
            'card_widget': self.card_num_lotes, 'key': 'num_lotes', 
            'unit': '', 'default': "0", 'is_float': False
        }]
        self._start_kpi_fetch_worker('/api/num_lotes/', params.copy(), kpi_num_lotes_config, self.current_kpi_update_id)

        kpi_area_mapeada_multiple_config = [
            {
                'card_widget': self.card_area_mapeada, 'key': 'area_mapeada',
                'unit': ' ha', 'default': "0.00 ha", 'is_float': True
            },
            {
                'card_widget': self.card_num_lotes_mapeados, 'key': 'lotes_mapeados',
                'unit': '', 'default': "0", 'is_float': False
            }
        ]
        self._start_kpi_fetch_worker('/api/area_mapeada/', params.copy(), kpi_area_mapeada_multiple_config, self.current_kpi_update_id)

        selected_chart_type = self.combo_chart_type.currentData() # Para el gráfico principal
        if selected_chart_type == "area_cultivos_bar": 
            kpi_chart_config = [{
                'target_type': selected_chart_type, 
                'canvas': self.chart_canvas1,
                'default_title': "Distribución de Cultivos por Área"
            }]
            self._start_kpi_fetch_worker('/api/area_cultivos/', params.copy(), kpi_chart_config, self.current_kpi_update_id)
        
        tabla_pendientes_config = [{
            'target_type': 'tabla_pendientes',
            'widget': self.table_lotes_pendientes,
        }]
        self._start_kpi_fetch_worker('/api/pend_mapeos/', params.copy(), tabla_pendientes_config, self.current_kpi_update_id)
        
        self.update_comparison_chart_display() 

    def update_comparison_chart_display(self):
        chart_type = "area_comparison" 
        canvas = self.comparison_chart_canvas

        title_suffix = ""
        kpi_statuses = [
            self.card_total_hectareas.status if hasattr(self, 'card_total_hectareas') and self.card_total_hectareas else "idle",
            self.card_area_mapeada.status if hasattr(self, 'card_area_mapeada') and self.card_area_mapeada else "idle",
            self.card_num_lotes.status if hasattr(self, 'card_num_lotes') and self.card_num_lotes else "idle", # Incluir otros KPIs si afectan la lógica
        ]

        if "loading" in kpi_statuses:
            title_suffix = " - Cargando..."
        elif "error" in kpi_statuses:
            title_suffix = " - Error de Carga"


        if chart_type == "area_comparison":
            # --- Lógica para la tarjeta de Área Pendiente ---
            area_total = self.lbl_total_hectareas_val
            area_mapeada = self.lbl_area_mapeada_val
            area_pendiente = area_total - area_mapeada
            self.lbl_area_pendiente_val = area_pendiente # Guardar el valor numérico

            pendiente_status = "idle" # Estado por defecto
            pendiente_text = "N/A"

            # Determinar el estado y texto de la tarjeta de área pendiente
            if "loading" in kpi_statuses:
                pendiente_status = "loading"
                pendiente_text = "Cargando..."
            elif "error" in kpi_statuses:
                 pendiente_status = "error"
                 pendiente_text = "Error"
            elif "idle" in kpi_statuses:
                 pendiente_status = "idle"
                 pendiente_text = "N/A"
            else: # Ambos KPIs fuente están 'ok'
                pendiente_text = f"{area_pendiente:.2f} ha"
                pendiente_status = "ok" if area_pendiente <= 0.01 else "error" # Verde si es <= 0.01, Rojo si es > 0.01

            self.card_area_pendiente.update_value(pendiente_text, pendiente_status)
            # --- Fin Lógica para la tarjeta de Área Pendiente ---

            area_mapeada = self.lbl_area_mapeada_val
            area_total = self.lbl_total_hectareas_val
            
            percentage_mapeada = 0.0

            if area_total > 0:
                if area_mapeada < 0: 
                    QgsMessageLog.logMessage(f"Advertencia: Área mapeada ({area_mapeada}) es negativa. Tratando como 0.", "Dashboard", Qgis.Warning)
                    area_mapeada_calc = 0.0
                elif area_mapeada > area_total: 
                    QgsMessageLog.logMessage(f"Advertencia: Área mapeada ({area_mapeada}) excede el área total ({area_total}). Usando área total para el porcentaje.", "Dashboard", Qgis.Warning)
                    area_mapeada_calc = area_total 
                else:
                    area_mapeada_calc = area_mapeada
                percentage_mapeada = (area_mapeada_calc / area_total) * 100
            elif area_total == 0: 
                if area_mapeada > 0: 
                    QgsMessageLog.logMessage(f"Advertencia: Área total es 0, pero área mapeada ({area_mapeada}) es positiva. Mostrando 0% y revisa datos.", "Dashboard", Qgis.Warning)
                percentage_mapeada = 0.0 
            else: 
                QgsMessageLog.logMessage(f"Advertencia: Área total ({area_total}) es negativa. Mostrando 0%.", "Dashboard", Qgis.Warning)
                percentage_mapeada = 0.0

            QgsMessageLog.logMessage(
                f"Gauge Input: AreaTotalVal={self.lbl_total_hectareas_val}, AreaMapeadaVal={self.lbl_area_mapeada_val}, CalculatedPercentage={percentage_mapeada}",
                "DashboardGaugeDebug", Qgis.Info
            )

            dynamic_title_for_plot = self._get_dynamic_chart_title("Área Mapeada" + title_suffix)
            canvas.plot_gauge_chart(percentage_mapeada, title=dynamic_title_for_plot, label="Área Mapeada", is_loading="Cargando..." in title_suffix) 
        else:
            canvas.clear_plot()

    def _on_kpi_card_double_clicked(self, card_title: str):
        """Maneja el doble clic en una tarjeta KPI."""
        QgsMessageLog.logMessage(f"Doble clic en tarjeta: {card_title}", "Dashboard Interacción", Qgis.Info)
        # Aquí podrías añadir lógica específica según el título de la tarjeta
    def save_chart_image(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getSaveFileName(self, "Guardar Gráfico", "dashboard_chart.png",
                                                  "PNG Files (*.png);;JPEG Files (*.jpg *.jpeg);;PDF Files (*.pdf)", options=options)
        if fileName:
            try:
                self.chart_canvas1.fig.savefig(fileName) 
                QgsMessageLog.logMessage(f"Gráfico guardado en: {fileName}", "Dashboard", Qgis.Info)
            except Exception as e:
                QgsMessageLog.logMessage(f"Error al guardar gráfico: {e}", "Dashboard", Qgis.Critical)
                QMessageBox.critical(self, "Error al Guardar", f"No se pudo guardar el gráfico:\n{e}")

    def _get_dynamic_chart_title(self, base_title: str) -> str:
        campania_text = self.combo_campania.currentText() # currentText() sigue siendo válido
        explotacion_text = self.combo_explotacion.currentText()

        if self.combo_explotacion.currentData() is not None:
            explotacion_nombre_display = explotacion_text.split('-', 1)[-1] if '-' in explotacion_text else explotacion_text
            title_chart = f"{base_title} para Explotación: {explotacion_nombre_display}"
        elif self.combo_campania.currentData() is not None:
            title_chart = f"{base_title} para Campaña: {campania_text}"
        else:
            title_chart = f"{base_title} (General)"
        return title_chart

    def _remove_worker_reference(self, worker_thread):
        if isinstance(worker_thread, QThread) and worker_thread in self.active_workers:
            self.active_workers.remove(worker_thread) 
            worker_thread.deleteLater() # <--- AÑADIDO: Programar el worker para eliminación

    def fetch_data_synchronous(self, endpoint, params=None, headers=None, method='GET', data=None) -> dict | list | None:
        try:
            url = self.endpoint_url + endpoint
            response = requests.request(method.upper(), url, params=params, headers=headers, json=data, timeout=10000)
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
        QgsMessageLog.logMessage("AgraeDashboardWindow closeEvent triggered.", "Dashboard Memory", Qgis.Info)
        # Limpiar workers activos
        for worker in list(self.active_workers):
            if worker.isRunning():
                QgsMessageLog.logMessage(f"Stopping worker: {worker}", "Dashboard Memory", Qgis.Info)
                worker.quit()
                worker.wait()
            worker.deleteLater() # <--- AÑADIDO: Asegurar la eliminación de todos los workers referenciados
        self.active_workers.clear()

        # Cerrar figuras de Matplotlib para liberar memoria
        QgsMessageLog.logMessage("Closing Matplotlib figures.", "Dashboard Memory", Qgis.Info)
        if hasattr(self, 'comparison_chart_canvas') and self.comparison_chart_canvas and hasattr(self.comparison_chart_canvas, 'fig'):
            plt.close(self.comparison_chart_canvas.fig)
            QgsMessageLog.logMessage("Closed comparison_chart_canvas figure.", "Dashboard Memory", Qgis.Info)
        if hasattr(self, 'chart_canvas1') and self.chart_canvas1 and hasattr(self.chart_canvas1, 'fig'):
            plt.close(self.chart_canvas1.fig)
            QgsMessageLog.logMessage("Closed chart_canvas1 figure.", "Dashboard Memory", Qgis.Info)

        self.closingPlugin.emit()
        self.hide()
        event.ignore()
        QgsMessageLog.logMessage("AgraeDashboardWindow hidden and event ignored.", "Dashboard Memory", Qgis.Info)
