from qgis.PyQt.QtWidgets import (  # type: ignore
    QDialog, QVBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QWidget,
    QHeaderView, QDateEdit, QDialogButtonBox, QDoubleSpinBox, QMessageBox, QAction, QGroupBox,
    QHBoxLayout, QFileDialog, QComboBox, QFrame # QCompleter ya no es necesario aquí directamente
)
from qgis.PyQt.QtGui import QIcon, QBrush, QColor # type: ignore # Añadido QIcon, QBrush, QColor
from qgis.PyQt.QtCore import QDate, Qt, QStringListModel, QThread # type: ignore # Añadido QStringListModel y QThread
import os
from qgis.core import QgsMessageLog, Qgis # Para logging

from ..tools.pdf_utils import create_invoice_pdf_document, REPORTLAB_AVAILABLE
from ..tools.api_worker import GenericApiWorker # Importar GenericApiWorker

from .select_client_dialog import SelectClientDialog # Importar el diálogo de selección de cliente
from ..gui.billing.product_selection_combobox import ProductSelectionComboBox # Importar el nuevo componente
from ..gui.CampaniasComboBox import CampaniasComboBox # Importar CampaniasComboBox


class CreateInvoiceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Crear Nueva Factura")
        self.setAttribute(Qt.WA_DeleteOnClose) # Asegurar la eliminación del diálogo al cerrarse
        self.setMinimumSize(700, 800) # Ajustado para más espacio y el PDF, y la nueva tabla
        self.endpoint_url = 'http://localhost:8000'
        
        self.invoice_items_data_objects = []
        self.active_item_price_for_cultivos = 0.0 
        self.cultivos_data_for_campaign = [] 
        
        self.selected_client_idexplotacion = None 
        self.cultivos_api_thread = None
        self.cultivos_api_worker = None

        self.init_ui()
        if self.table_items.rowCount() == 0: 
            self.add_item_row() 
        

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # --- Sección de Información General de la Factura ---
        general_info_layout = QFormLayout()

        client_info_widget = QWidget()
        client_info_layout = QHBoxLayout(client_info_widget)
        client_info_layout.setContentsMargins(0, 0, 0, 0) 

        self.txt_cliente_cif = QLineEdit()
        self.txt_cliente_cif.setPlaceholderText("DNI/CIF")
        self.txt_cliente_cif.setReadOnly(True)
        self.txt_cliente_cif.setStyleSheet("color: red; font-weight: bold;") 
        client_info_layout.addWidget(self.txt_cliente_cif)

        client_info_layout.addWidget(QLabel("-"))

        self.txt_cliente_nombre = QLineEdit()
        self.txt_cliente_nombre.setPlaceholderText("Nombre o Razón Social (buscar)")
        self.txt_cliente_nombre.setReadOnly(True) 
        self.txt_cliente_nombre.setStyleSheet("color: black; font-weight: bold;") 
        current_script_path = os.path.dirname(__file__) 
        plugin_agrae_dir = os.path.dirname(current_script_path) 
        search_icon_path = os.path.join(plugin_agrae_dir, "gui", "icons", "search.svg")
        self.search_client_action = QAction(self)
        if os.path.exists(search_icon_path):
            self.search_client_action.setIcon(QIcon(search_icon_path))
        self.txt_cliente_nombre.addAction(self.search_client_action, QLineEdit.TrailingPosition)
        client_info_layout.addWidget(self.txt_cliente_nombre, 1) 

        general_info_layout.addRow("Cliente:", client_info_widget)

        self.date_fecha_factura = QDateEdit(QDate.currentDate())
        self.date_fecha_factura.setCalendarPopup(True)
        self.date_fecha_factura.setDisplayFormat("dd/MM/yyyy")
        self.txt_numero_factura = QLineEdit()
        self.txt_numero_factura.setPlaceholderText("Se generará al guardar (ej: F2025-0001)")
        self.txt_numero_factura.setReadOnly(True) 

        general_info_layout.addRow("Fecha Factura:", self.date_fecha_factura)
        general_info_layout.addRow("Número Factura:", self.txt_numero_factura)
        main_layout.addLayout(general_info_layout)

        # --- Sección de Ítems de la Factura ---
        main_layout.addWidget(QLabel("Ítems de la Factura:"))
        self.table_items = QTableWidget()
        self.table_items.setColumnCount(4) 
        self.table_items.setHorizontalHeaderLabels(["Descripción", "Cantidad", "Precio Unit.", "Subtotal"]) 
        self.table_items.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch) 
        self.table_items.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table_items.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table_items.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents) 
        self.table_items.setSelectionMode(QTableWidget.SingleSelection) 
        self.table_items.setSelectionBehavior(QTableWidget.SelectRows)

        table_with_buttons_layout = QHBoxLayout()
        table_with_buttons_layout.addWidget(self.table_items, 1) 

        table_action_buttons_layout = QVBoxLayout()
        table_action_buttons_layout.setAlignment(Qt.AlignTop) 
        
        self.btn_add_item_to_table = QPushButton()
        add_icon_path = os.path.join(plugin_agrae_dir, "gui", "icons", "plus-solid.svg")
        if os.path.exists(add_icon_path):
            self.btn_add_item_to_table.setIcon(QIcon(add_icon_path))
            self.btn_add_item_to_table.setToolTip("Añadir ítem a la factura")
        else:
            self.btn_add_item_to_table.setText("+I") 
            print(f"Advertencia: No se encontró el icono en {add_icon_path}.")
        table_action_buttons_layout.addWidget(self.btn_add_item_to_table)

        self.btn_remove_item_from_table = QPushButton()
        remove_icon_path = os.path.join(plugin_agrae_dir, "gui", "icons", "minus-solid.svg")
        if os.path.exists(remove_icon_path):
            self.btn_remove_item_from_table.setIcon(QIcon(remove_icon_path))
            self.btn_remove_item_from_table.setToolTip("Eliminar ítem seleccionado de la factura")
        else:
            self.btn_remove_item_from_table.setText("-I") 
            print(f"Advertencia: No se encontró el icono en {remove_icon_path}.")
        table_action_buttons_layout.addWidget(self.btn_remove_item_from_table)
        
        table_with_buttons_layout.addLayout(table_action_buttons_layout)
        main_layout.addLayout(table_with_buttons_layout)

        # --- Sección de Cultivos Facturables ---
        cultivos_group = QGroupBox("Cultivos Facturables")
        cultivos_main_layout = QVBoxLayout(cultivos_group)

        self.combo_campania_factura = CampaniasComboBox(self.endpoint_url, parent=self)
        self.combo_campania_factura.setMinimumWidth(250)
        cultivos_main_layout.addWidget(self.combo_campania_factura)

        self.lbl_active_price_for_cultivos = QLabel("Precio de ítem de referencia: € 0.00")
        main_layout.addWidget(self.lbl_active_price_for_cultivos) 

        self.table_cultivos = QTableWidget()
        self.table_cultivos.setColumnCount(5) 
        self.table_cultivos.setHorizontalHeaderLabels(["Cultivo", "Sup. Mapeada (ha)", "Sup. Facturable (ha)", "Precio (€/ha)", "Base Imponible (€)"])
        self.table_cultivos.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch) 
        self.table_cultivos.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table_cultivos.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table_cultivos.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents) 
        self.table_cultivos.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents) 

        cultivos_table_with_buttons_layout = QHBoxLayout()
        cultivos_table_with_buttons_layout.addWidget(self.table_cultivos, 1)

        cultivos_action_buttons_layout = QVBoxLayout()
        cultivos_action_buttons_layout.setAlignment(Qt.AlignTop)

        

        self.btn_remove_cultivo_from_table = QPushButton()
        if os.path.exists(remove_icon_path): 
            self.btn_remove_cultivo_from_table.setIcon(QIcon(remove_icon_path))
            self.btn_remove_cultivo_from_table.setToolTip("Eliminar cultivo seleccionado")
        else:
            self.btn_remove_cultivo_from_table.setText("-C") 
        cultivos_action_buttons_layout.addWidget(self.btn_remove_cultivo_from_table)

        cultivos_table_with_buttons_layout.addLayout(cultivos_action_buttons_layout)
        cultivos_main_layout.addLayout(cultivos_table_with_buttons_layout) 
        main_layout.addWidget(cultivos_group) 

        main_layout.addSpacing(10)

        line_separator = QFrame()
        line_separator.setFrameShape(QFrame.HLine)
        line_separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line_separator)
        main_layout.addSpacing(10)

        totals_layout = QFormLayout()
        self.spin_global_iva = QDoubleSpinBox() 
        self.spin_global_iva.setMinimum(0)
        self.spin_global_iva.setMaximum(100)
        self.spin_global_iva.setValue(21.0) 
        self.spin_global_iva.setSuffix(" %")

        self.lbl_subtotal_general = QLineEdit("0.00")
        self.lbl_subtotal_general.setReadOnly(True)
        self.lbl_subtotal_general.setAlignment(Qt.AlignRight)
        self.lbl_iva_total = QLineEdit("0.00")
        self.lbl_iva_total.setReadOnly(True)
        self.lbl_iva_total.setAlignment(Qt.AlignRight)
        self.lbl_total_factura = QLineEdit("0.00")
        self.lbl_total_factura.setReadOnly(True)
        self.lbl_total_factura.setAlignment(Qt.AlignRight)
        font = self.lbl_total_factura.font()
        font.setBold(True)
        self.lbl_total_factura.setFont(font)
        self.lbl_total_factura.setStyleSheet("QLineEdit { font-size: 14pt; }")

        totals_layout.addRow("Subtotal:", self.lbl_subtotal_general)
        totals_layout.addRow("IVA Global:", self.spin_global_iva) 
        totals_layout.addRow("IVA Total:", self.lbl_iva_total)
        totals_layout.addRow("TOTAL:", self.lbl_total_factura)
        main_layout.addLayout(totals_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.button_box.button(QDialogButtonBox.Save).setText("Guardar Factura y Exportar PDF")
        self.button_box.accepted.connect(self.accept_invoice)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

        self.setLayout(main_layout)
        
        self.btn_add_item_to_table.clicked.connect(self.add_item_row)
        self.btn_remove_item_from_table.clicked.connect(self.remove_item_row)
        self.search_client_action.triggered.connect(self.open_select_client_dialog) 
        
        self.btn_remove_cultivo_from_table.clicked.connect(self.remove_cultivo_row)
        self.table_items.itemSelectionChanged.connect(self.update_active_price_for_cultivos) 

        self.spin_global_iva.valueChanged.connect(self.calculate_totals)

        self.combo_campania_factura.current_campaign_changed.connect(self._trigger_cultivos_load_on_campaign_change)

    def _update_product_models(self):
        pass

    def add_item_row(self): 
        row_position = self.table_items.rowCount()
        self.table_items.insertRow(row_position)
        
        api_items_config = {
            "url": f"{self.endpoint_url}/api/billing/items/", 
            "params": {}, 
            "headers": {} 
        }
        desc_combo = ProductSelectionComboBox(api_items_config, self)
        desc_combo.setObjectName(f"desc_combo_row_{row_position}") 

        desc_combo.product_selected_data.connect(
            lambda product_data, combo=desc_combo: self.handle_product_selected_in_row(combo, product_data)
        )

        self.table_items.setCellWidget(row_position, 0, desc_combo)

        qty_spinbox = QDoubleSpinBox()
        qty_spinbox.setMinimum(0.01)
        qty_spinbox.setMaximum(999999.99)
        qty_spinbox.setValue(1.0)
        qty_spinbox.setDecimals(2)
        self.table_items.setCellWidget(row_position, 1, qty_spinbox)
        
        price_spinbox = QDoubleSpinBox()
        price_spinbox.setMinimum(0)
        price_spinbox.setMaximum(9999999.99)
        price_spinbox.setDecimals(2)
        price_spinbox.setPrefix("€ ")
        self.table_items.setCellWidget(row_position, 2, price_spinbox)

        subtotal_item = QTableWidgetItem("€ 0.00")
        subtotal_item.setFlags(subtotal_item.flags() & ~Qt.ItemIsEditable)
        subtotal_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table_items.setItem(row_position, 3, subtotal_item) 

        qty_spinbox.valueChanged.connect(lambda value, r=row_position: self.update_item_subtotal(r))
        price_spinbox.valueChanged.connect(lambda value, r=row_position: self.update_item_subtotal(r))
        
        if self.table_items.rowCount() == 1 and row_position == 0 : 
            self.table_items.setCurrentCell(0,0)
            desc_combo.setFocus()

    def add_cultivo_row(self):
        # Antes de añadir, restaurar el número de columnas si se mostró un mensaje
        if self.table_cultivos.columnCount() == 1 and self.table_cultivos.rowCount() == 1:
            if "Cargando" in self.table_cultivos.item(0,0).text() or \
               "Seleccione" in self.table_cultivos.item(0,0).text() or \
               "Error" in self.table_cultivos.item(0,0).text() or \
               "No se encontraron" in self.table_cultivos.item(0,0).text():
                self.table_cultivos.setRowCount(0) # Limpiar el mensaje
        
        self.table_cultivos.setColumnCount(5) # Asegurar 5 columnas
        self.table_cultivos.setHorizontalHeaderLabels(["Cultivo", "Sup. Mapeada (ha)", "Sup. Facturable (ha)", "Precio (€/ha)", "Base Imponible (€)"])
        self.table_cultivos.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch) 
        self.table_cultivos.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table_cultivos.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table_cultivos.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents) 
        self.table_cultivos.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)

        row_position = self.table_cultivos.rowCount()
        self.table_cultivos.insertRow(row_position)

        cultivo_combo = QComboBox()
        if not self.cultivos_data_for_campaign:
            cultivo_combo.addItem("Seleccione campaña y cliente", None)
            cultivo_combo.setEnabled(False)
        else:
            self._populate_cultivo_combo(cultivo_combo, self.cultivos_data_for_campaign)
        self.table_cultivos.setCellWidget(row_position, 0, cultivo_combo)

        sup_mapeada_spin = QDoubleSpinBox()
        sup_mapeada_spin.setMinimum(0.00)
        sup_mapeada_spin.setMaximum(999999.99)
        sup_mapeada_spin.setDecimals(2)
        sup_mapeada_spin.setReadOnly(True) 
        sup_mapeada_spin.setValue(0.00) 
        sup_mapeada_spin.setSuffix(" ha")
        self.table_cultivos.setCellWidget(row_position, 1, sup_mapeada_spin)

        sup_facturable_spin = QDoubleSpinBox()
        sup_facturable_spin.setMinimum(0.00)
        sup_facturable_spin.setMaximum(999999.99)
        sup_facturable_spin.setDecimals(2)
        sup_facturable_spin.setValue(0.00)
        sup_facturable_spin.setSuffix(" ha")
        self.table_cultivos.setCellWidget(row_position, 2, sup_facturable_spin)

        precio_cultivo_spin = QDoubleSpinBox()
        precio_cultivo_spin.setMinimum(0.00)
        precio_cultivo_spin.setMaximum(99999.99) 
        precio_cultivo_spin.setDecimals(2)
        precio_cultivo_spin.setPrefix("€ ")
        precio_cultivo_spin.setValue(0.00) 
        self.table_cultivos.setCellWidget(row_position, 3, precio_cultivo_spin)

        base_imponible_item = QTableWidgetItem("€ 0.00")
        base_imponible_item.setFlags(base_imponible_item.flags() & ~Qt.ItemIsEditable)
        base_imponible_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table_cultivos.setItem(row_position, 4, base_imponible_item)

        cultivo_combo.currentIndexChanged.connect(
            lambda index, r=row_position, c=cultivo_combo: self._on_cultivo_selected_in_row(r, c.itemData(index))
        )
        sup_facturable_spin.valueChanged.connect(lambda value, r=row_position: self.update_cultivo_base_imponible(r))
        precio_cultivo_spin.valueChanged.connect(lambda value, r=row_position: self.update_cultivo_base_imponible(r))
        
        self.update_cultivo_base_imponible(row_position) 

    def remove_cultivo_row(self):
        current_row = self.table_cultivos.currentRow()
        if current_row >= 0:
            self.table_cultivos.removeRow(current_row)
            self.calculate_totals()
            if self.table_cultivos.rowCount() == 0 and not self.cultivos_data_for_campaign:
                 if not self.combo_campania_factura.get_current_campaign_id():
                     self._show_message_in_cultivos_table("Seleccione una campaña.")
                 elif not self.selected_client_idexplotacion:
                     self._show_message_in_cultivos_table("Seleccione un cliente con explotación.")
                 else: # Si hay campaña y explotación pero no datos, o la API falló
                     self._show_message_in_cultivos_table("No hay cultivos para añadir o hubo un error.")

        else:
            QMessageBox.warning(self, "Eliminar Cultivo", "Por favor, seleccione una fila de cultivo para eliminar.")

    def _populate_cultivo_combo(self, combo: QComboBox, cultivos_data: list):
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("--- Elegir Cultivo ---", None)
        if cultivos_data:
            # Usar la clave "nombre" de la API para ordenar y mostrar
            sorted_cultivos = sorted(cultivos_data, key=lambda x: x.get("nombre", "").lower())
            for cultivo_obj in sorted_cultivos:
                # Usar la clave "nombre" para el texto del ítem
                combo.addItem(cultivo_obj.get("nombre", "N/A"), cultivo_obj)
        combo.setEnabled(bool(cultivos_data))
        combo.setCurrentIndex(0)
        combo.blockSignals(False)

    def update_active_price_for_cultivos(self):
        selected_items_rows = self.table_items.selectionModel().selectedRows()
        if not selected_items_rows:
            self.active_item_price_for_cultivos = 0.0
        else:
            current_row = selected_items_rows[0].row()
            if self.is_description_row(current_row): 
                if current_row > 0 and not self.is_description_row(current_row -1):
                    current_row -= 1
                else: 
                    self.active_item_price_for_cultivos = 0.0
                    self.lbl_active_price_for_cultivos.setText(f"Precio de ítem de referencia: € {self.active_item_price_for_cultivos:.2f}")
                    return

            price_widget = self.table_items.cellWidget(current_row, 2) 
            if isinstance(price_widget, QDoubleSpinBox):
                self.active_item_price_for_cultivos = price_widget.value()
            else:
                self.active_item_price_for_cultivos = 0.0
        
        self.lbl_active_price_for_cultivos.setText(f"Precio de ítem de referencia: € {self.active_item_price_for_cultivos:.2f}")

    def update_cultivo_base_imponible(self, row):
        try:
            sup_facturable_widget = self.table_cultivos.cellWidget(row, 2) 
            precio_cultivo_widget = self.table_cultivos.cellWidget(row, 3) 
            base_imponible_item_cultivo = self.table_cultivos.item(row, 4) 

            if sup_facturable_widget and precio_cultivo_widget and base_imponible_item_cultivo:
                sup_facturable = sup_facturable_widget.value()
                precio_cultivo = precio_cultivo_widget.value()
                base_calculada = sup_facturable * precio_cultivo
                base_imponible_item_cultivo.setText(f"€ {base_calculada:.2f}")
            else:
                if base_imponible_item_cultivo:
                    base_imponible_item_cultivo.setText("€ 0.00")
        except Exception as e:
            print(f"Error actualizando base imponible de cultivo (fila {row}): {e}")
            base_item_error = self.table_cultivos.item(row, 4)
            if base_item_error:
                base_item_error.setText("Error")
        
        self.calculate_totals()

    def _trigger_cultivos_load_on_campaign_change(self, campaign_id: int | None):
        QgsMessageLog.logMessage(f"Cambio de campaña detectado, ID: {campaign_id}. ID Explotación cliente: {self.selected_client_idexplotacion}", "BillingDialog", Qgis.Info)
        if campaign_id is not None and self.selected_client_idexplotacion is not None:
            self._load_cultivos_for_campaign_and_explotacion(campaign_id, self.selected_client_idexplotacion)
        else:
            self.cultivos_data_for_campaign = []
            self.table_cultivos.setRowCount(0)
            if campaign_id is None:
                self._show_message_in_cultivos_table("Seleccione una campaña.")
            elif self.selected_client_idexplotacion is None:
                self._show_message_in_cultivos_table("Seleccione un cliente con explotación asignada.")

    def _load_cultivos_for_campaign_and_explotacion(self, campaign_id: int, explotacion_id: int):
        QgsMessageLog.logMessage(f"Iniciando carga de cultivos para Campaña ID: {campaign_id}, Explotación ID: {explotacion_id}", "BillingDialog", Qgis.Info)
        
        self.cultivos_data_for_campaign = [] 
        self.table_cultivos.setRowCount(0) 
        self._show_message_in_cultivos_table("Cargando cultivos...")

        if self.cultivos_api_thread and self.cultivos_api_thread.isRunning():
            QgsMessageLog.logMessage("Carga de API de cultivos ya en progreso. Cancelando anterior.", "BillingDialog", Qgis.Warning)
            if self.cultivos_api_worker:
                self.cultivos_api_worker.stop() 

        api_config = {
            "url": f"{self.endpoint_url}/api/billing/cultivo_items/",
            "params": {"idcampania": campaign_id, "idexplotacion": explotacion_id},
            "headers": {} 
        }

        self.cultivos_api_thread = QThread(self)
        self.cultivos_api_worker = GenericApiWorker(api_config, request_context="load_cultivos_factura")
        self.cultivos_api_worker.moveToThread(self.cultivos_api_thread)

        self.cultivos_api_worker.success.connect(self._handle_cultivos_api_success)
        self.cultivos_api_worker.error.connect(self._handle_cultivos_api_error)
        
        self.cultivos_api_worker.finished_signal.connect(self.cultivos_api_thread.quit)
        self.cultivos_api_worker.finished_signal.connect(self.cultivos_api_worker.deleteLater)
        self.cultivos_api_thread.finished.connect(self.cultivos_api_thread.deleteLater)
        self.cultivos_api_thread.finished.connect(self._on_cultivos_load_finished)
        
        self.cultivos_api_thread.started.connect(self.cultivos_api_worker.run)
        self.cultivos_api_thread.start()

    def _handle_cultivos_api_success(self, response_data: object, request_context: object):
        if request_context == "load_cultivos_factura":
            self.table_cultivos.setRowCount(0) 
            if isinstance(response_data, list):
                QgsMessageLog.logMessage(f"Cultivos recibidos de API: {len(response_data)} ítems", "BillingDialog", Qgis.Info)
                self.cultivos_data_for_campaign = response_data
                if not response_data:
                    self._show_message_in_cultivos_table("No se encontraron cultivos para esta campaña/explotación.")
            else:
                error_msg = f"Respuesta de API inesperada para cultivos: {type(response_data)}"
                QgsMessageLog.logMessage(error_msg, "BillingDialog", Qgis.Warning)
                self._handle_cultivos_api_error(error_msg, request_context)
                return 
            
            if self.cultivos_data_for_campaign:
                for cultivo_obj_from_api in self.cultivos_data_for_campaign:
                    self.add_cultivo_row() # Añade una fila con el combo poblado
                    new_row_index = self.table_cultivos.rowCount() - 1
                    cultivo_combo_widget = self.table_cultivos.cellWidget(new_row_index, 0)
                    if isinstance(cultivo_combo_widget, QComboBox):
                        # Encontrar y seleccionar el cultivo_obj_from_api en el combo
                        for i in range(cultivo_combo_widget.count()):
                            item_data_in_combo = cultivo_combo_widget.itemData(i)
                            # Comparar por un identificador único si está disponible, o por el objeto mismo.
                            # Asumiendo que los objetos son los mismos o comparables.
                            if item_data_in_combo == cultivo_obj_from_api:
                                cultivo_combo_widget.setCurrentIndex(i)
                                break # Salir del bucle una vez encontrado y seleccionado


    def _handle_cultivos_api_error(self, error_message: str, request_context: object):
        if request_context == "load_cultivos_factura":
            QgsMessageLog.logMessage(f"Error cargando cultivos de API: {error_message}", "BillingDialog", Qgis.Critical)
            self.cultivos_data_for_campaign = []
            self.table_cultivos.setRowCount(0)
            self._show_message_in_cultivos_table(f"Error al cargar cultivos: {error_message.split(':')[0]}")
            QMessageBox.warning(self, "Error de API Cultivos", f"No se pudieron cargar los cultivos:\n{error_message}")

    def _on_cultivos_load_finished(self):
        QgsMessageLog.logMessage("Carga de API de cultivos finalizada.", "BillingDialog", Qgis.Info)
        self.cultivos_api_thread = None
        self.cultivos_api_worker = None
        if self.table_cultivos.rowCount() == 0 and not self.cultivos_data_for_campaign:
             if not self.combo_campania_factura.get_current_campaign_id():
                 self._show_message_in_cultivos_table("Seleccione una campaña.")
             elif not self.selected_client_idexplotacion:
                 self._show_message_in_cultivos_table("Seleccione un cliente con explotación.")

    def _show_message_in_cultivos_table(self, message: str):
        self.table_cultivos.setRowCount(1)
        self.table_cultivos.setColumnCount(1) 
        item = QTableWidgetItem(message)
        item.setTextAlignment(Qt.AlignCenter)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable & ~Qt.ItemIsSelectable)
        self.table_cultivos.setItem(0, 0, item)
        self.table_cultivos.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        # No restaurar columnas aquí, se hará en add_cultivo_row si es necesario

    def _on_cultivo_selected_in_row(self, row: int, cultivo_data: object | None):
        sup_mapeada_widget = self.table_cultivos.cellWidget(row, 1) 
        sup_facturable_widget = self.table_cultivos.cellWidget(row, 2) 
        precio_cultivo_widget = self.table_cultivos.cellWidget(row, 3)

        if isinstance(cultivo_data, dict) and sup_mapeada_widget and sup_facturable_widget and precio_cultivo_widget:
            # Usar "area_ha" para la superficie mapeada
            sup_mapeada_api = cultivo_data.get("area_ha", 0.0)
            try:
                sup_mapeada_widget.setValue(float(sup_mapeada_api))
                sup_facturable_widget.setValue(float(sup_mapeada_api)) # Por defecto, facturable = mapeada
            except (ValueError, TypeError):
                sup_mapeada_widget.setValue(0.0)
                sup_facturable_widget.setValue(0.0)

            # Usar "precio_facturable" para el precio del cultivo
            precio_api = cultivo_data.get("precio_facturable", 0.0)
            precio_cultivo_widget.setValue(float(precio_api))
        elif sup_mapeada_widget and sup_facturable_widget and precio_cultivo_widget: 
            sup_mapeada_widget.setValue(0.0)
            sup_facturable_widget.setValue(0.0)
            precio_cultivo_widget.setValue(0.0)
        self.update_cultivo_base_imponible(row) 

    def recalculate_all_cultivo_bases_imponibles(self):
        for row in range(self.table_cultivos.rowCount()):
            self.update_cultivo_base_imponible(row)

    def open_select_client_dialog(self):
        dialog = SelectClientDialog(self.endpoint_url,self)
        dialog.client_selected.connect(self.handle_client_dialog_selection)
        if dialog.exec_() == QDialog.Accepted:
            print("Diálogo de selección de cliente aceptado.")
        else:
            print("Diálogo de selección de cliente cancelado.")

    def handle_client_dialog_selection(self, client_data):
        if client_data:
            self.txt_cliente_nombre.setText(f"{client_data.get('nombre', 'N/A')} {client_data.get('apellidos', '')}".strip())
            self.txt_cliente_cif.setText(client_data.get("dni_cif", "N/A"))
            self.selected_client_id = client_data.get("id") 
            self.selected_client_idexplotacion = client_data.get("idexplotacion", None) # Asegúrate que esta clave exista
            QgsMessageLog.logMessage(f"Cliente seleccionado: ID {self.selected_client_id}, ID Explotación: {self.selected_client_idexplotacion}", "BillingDialog", Qgis.Info)

            current_campaign_id = self.combo_campania_factura.get_current_campaign_id()
            if current_campaign_id is not None and self.selected_client_idexplotacion is not None:
                self._load_cultivos_for_campaign_and_explotacion(current_campaign_id, self.selected_client_idexplotacion)
            elif current_campaign_id is not None and self.selected_client_idexplotacion is None:
                self._show_message_in_cultivos_table("Cliente seleccionado no tiene explotación asignada para cargar cultivos.")
            elif current_campaign_id is None and self.selected_client_idexplotacion is not None:
                 self._show_message_in_cultivos_table("Seleccione una campaña para cargar cultivos.")


    def handle_product_selected_in_row(self, sender_combo: ProductSelectionComboBox, product_data: object):
        item_row_index = -1
        for r in range(self.table_items.rowCount()):
            if self.table_items.cellWidget(r, 0) == sender_combo:
                item_row_index = r
                break
        
        if item_row_index == -1:
            print("[CreateInvoiceDialog] Error: No se encontró el sender_combo en la tabla.")
            return

        potential_desc_row_index = item_row_index + 1
        if potential_desc_row_index < self.table_items.rowCount() and \
           self.is_description_row(potential_desc_row_index):
            self.table_items.removeRow(potential_desc_row_index)

        if not isinstance(product_data, dict):
            price_widget = self.table_items.cellWidget(item_row_index, 2)
            if price_widget:
                price_widget.setValue(0.0)
        else:
            precio_1 = product_data.get('precio_1', 0.0)
            try:
                precio_1_float = float(precio_1)
            except (ValueError, TypeError):
                precio_1_float = 0.0

            price_widget = self.table_items.cellWidget(item_row_index, 2) 
            if price_widget and isinstance(price_widget, QDoubleSpinBox):
                price_widget.setValue(precio_1_float)

        description_text = product_data.get("descripcion") if isinstance(product_data, dict) else None

        if description_text and description_text.strip():
            desc_row_to_insert_at = item_row_index + 1
            self.table_items.insertRow(desc_row_to_insert_at)

            desc_label = QLabel(description_text)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("padding-left: 25px; padding-top: 2px; padding-bottom: 2px; font-style: italic; color: #555555; background-color: #f9f9f9;")
            desc_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)

            self.table_items.setCellWidget(desc_row_to_insert_at, 0, desc_label)
            self.table_items.setSpan(desc_row_to_insert_at, 0, 1, self.table_items.columnCount())

            for col in range(self.table_items.columnCount()):
                item = self.table_items.item(desc_row_to_insert_at, col)
                if not item:
                    item = QTableWidgetItem()
                    self.table_items.setItem(desc_row_to_insert_at, col, item)
                item.setFlags(Qt.ItemIsEnabled) 
            
            self.table_items.resizeRowToContents(desc_row_to_insert_at)

    def is_description_row(self, row_index: int) -> bool:
        if row_index < 0 or row_index >= self.table_items.rowCount():
            return False
        return (isinstance(self.table_items.cellWidget(row_index, 0), QLabel) and
                self.table_items.cellWidget(row_index, 1) is None and
                self.table_items.cellWidget(row_index, 2) is None)

    def remove_item_row(self):
        current_row = self.table_items.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Eliminar Ítem", "Por favor, seleccione una fila para eliminar.")
            return

        if self.is_description_row(current_row):
            QMessageBox.warning(self, "Eliminar Ítem", "No puede eliminar una fila de descripción. Seleccione el ítem asociado.")
            return

        potential_desc_row = current_row + 1
        if potential_desc_row < self.table_items.rowCount() and self.is_description_row(potential_desc_row):
            self.table_items.removeRow(potential_desc_row)
        
        self.table_items.removeRow(current_row) 
        self.calculate_totals()

    def update_item_subtotal(self, row): 
        try:
            qty_widget = self.table_items.cellWidget(row, 1)
            price_widget = self.table_items.cellWidget(row, 2)
            subtotal_item = self.table_items.item(row, 3) 

            if qty_widget and price_widget and subtotal_item: 
                cantidad = qty_widget.value()
                precio_unit = price_widget.value()
                subtotal_linea = cantidad * precio_unit
                subtotal_item.setText(f"€ {subtotal_linea:.2f}")
            else:
                if subtotal_item:
                    subtotal_item.setText("€ 0.00")
        except Exception as e:
            print(f"Error actualizando subtotal de ítem (fila {row}): {e}")
            if self.table_items.item(row, 3): 
                self.table_items.item(row, 3).setText("Error")
        
        self.calculate_totals()

    def calculate_totals(self):
        subtotal_general_val = 0.0
        
        for row in range(self.table_items.rowCount()):
            if self.is_description_row(row): 
                continue
            try:
                subtotal_item_text = self.table_items.item(row, 3).text().replace("€ ", "") 
                line_subtotal = float(subtotal_item_text)
                subtotal_general_val += line_subtotal
            except (ValueError, AttributeError, TypeError) as e:
                print(f"Error calculando totales para fila de ítems {row}: {e}")
                continue
        
        # Solo sumar si la tabla de cultivos tiene las columnas correctas (no es un mensaje)
        if self.table_cultivos.columnCount() == 5:
            for row in range(self.table_cultivos.rowCount()):
                try:
                    base_imponible_cultivo_text = self.table_cultivos.item(row, 4).text().replace("€ ", "") 
                    subtotal_general_val += float(base_imponible_cultivo_text)
                except (ValueError, AttributeError, TypeError) as e:
                    print(f"Error sumando base imponible de cultivo (fila {row}): {e}")

        global_iva_rate = self.spin_global_iva.value() / 100.0
        iva_total_acumulado_val = subtotal_general_val * global_iva_rate
        total_factura_val = subtotal_general_val + iva_total_acumulado_val
        self.lbl_subtotal_general.setText(f"€ {subtotal_general_val:.2f}")
        self.lbl_iva_total.setText(f"€ {iva_total_acumulado_val:.2f}")
        self.lbl_total_factura.setText(f"€ {total_factura_val:.2f}")

    def accept_invoice(self):
        cliente_nombre = self.txt_cliente_nombre.text().strip()
        if not cliente_nombre or not hasattr(self, 'selected_client_id') or not self.selected_client_id: 
            QMessageBox.warning(self, "Validación", "Debe seleccionar un cliente utilizando el botón de búsqueda.")
            return

        # Solo validar si hay filas que no sean mensajes
        has_actual_items = False
        for r in range(self.table_items.rowCount()):
            if not self.is_description_row(r):
                has_actual_items = True
                break
        
        has_actual_cultivos = False
        if self.table_cultivos.columnCount() == 5: # Solo si no es un mensaje
            if self.table_cultivos.rowCount() > 0:
                has_actual_cultivos = True

        if not has_actual_items and not has_actual_cultivos:
            QMessageBox.warning(self, "Validación", "La factura debe tener al menos un ítem o un cultivo.")
            self.btn_add_item_to_table.setFocus() 
            return

        for row in range(self.table_items.rowCount()):
            if self.is_description_row(row): 
                continue
            desc_widget = self.table_items.cellWidget(row, 0) 
            qty_widget = self.table_items.cellWidget(row, 1)

            if not desc_widget or desc_widget.currentText() == desc_widget.PLACEHOLDER_CHOOSE_SERVICE_TEXT or not desc_widget.currentText().strip():
                QMessageBox.warning(self, "Validación", f"El ítem en la fila {row + 1} de la tabla de ítems no tiene descripción válida.")
                self.table_items.setCurrentCell(row, 0)
                if desc_widget:
                    desc_widget.setFocus()
                return
            if qty_widget and qty_widget.value() <= 0:
                QMessageBox.warning(self, "Validación", f"La cantidad para el ítem en la fila {row + 1} debe ser mayor que cero.")
                self.table_items.setCurrentCell(row, 1)
                if qty_widget: qty_widget.setFocus()
                return
        
        if self.table_cultivos.columnCount() == 5: # Solo validar si no es un mensaje
            for row in range(self.table_cultivos.rowCount()):
                cultivo_widget = self.table_cultivos.cellWidget(row, 0) 
                sup_facturable_widget = self.table_cultivos.cellWidget(row, 2)
                precio_cultivo_widget = self.table_cultivos.cellWidget(row, 3)

                if not cultivo_widget or cultivo_widget.currentIndex() == 0: 
                    QMessageBox.warning(self, "Validación", f"El cultivo en la fila {row + 1} de la tabla de cultivos no ha sido seleccionado.")
                    self.table_cultivos.setCurrentCell(row, 0)
                    if cultivo_widget: cultivo_widget.setFocus()
                    return
                if sup_facturable_widget and sup_facturable_widget.value() <= 0:
                    QMessageBox.warning(self, "Validación", f"La superficie facturable para el cultivo en la fila {row + 1} debe ser mayor que cero.")
                    self.table_cultivos.setCurrentCell(row, 2)
                    if sup_facturable_widget: sup_facturable_widget.setFocus()
                    return
                if precio_cultivo_widget and precio_cultivo_widget.value() <= 0:
                    QMessageBox.warning(self, "Validación", f"El precio para el cultivo en la fila {row + 1} debe ser mayor que cero.")
                    self.table_cultivos.setCurrentCell(row, 3)
                    if precio_cultivo_widget: precio_cultivo_widget.setFocus()
                    return
        
        print("--- Factura a Guardar (Simulación) ---")
        print(f"Cliente (Nombre): {self.txt_cliente_nombre.text()}")
        print(f"Cliente (DNI/CIF): {self.txt_cliente_cif.text()}")
        print(f"Campaña Factura: {self.combo_campania_factura.currentText()} (ID: {self.combo_campania_factura.get_current_campaign_id()})")
        print(f"Fecha: {self.date_fecha_factura.date().toString('yyyy-MM-dd')}")
        num_factura_text = self.txt_numero_factura.text()
        if not num_factura_text or num_factura_text == self.txt_numero_factura.placeholderText():
            num_factura_display = "PENDIENTE (automático)"
        else:
            num_factura_display = num_factura_text
        print(f"Número Factura (campo): {num_factura_display}")
        
        print("Ítems:")
        for row in range(self.table_items.rowCount()):
            if self.is_description_row(row): 
                continue
            desc = self.table_items.cellWidget(row, 0).currentText() if self.table_items.cellWidget(row, 0) else ""
            qty = self.table_items.cellWidget(row, 1).value()
            price = self.table_items.cellWidget(row, 2).value()
            sub = self.table_items.item(row, 3).text() 
            print(f"  - Desc: {desc}, Cant: {qty:.2f}, Precio: €{price:.2f}, Subtotal: {sub}")
        
        print("Cultivos Facturables:")
        if self.table_cultivos.columnCount() == 5: # Solo si no es un mensaje
            for row in range(self.table_cultivos.rowCount()):
                cultivo = self.table_cultivos.cellWidget(row, 0).currentText()
                sup_map = self.table_cultivos.cellWidget(row, 1).value()
                sup_fact = self.table_cultivos.cellWidget(row, 2).value()
                precio_cult = self.table_cultivos.cellWidget(row, 3).value()
                base_imp = self.table_cultivos.item(row, 4).text()
                print(f"  - Cultivo: {cultivo}, Sup.Mapeada: {sup_map:.2f} ha, Sup.Facturable: {sup_fact:.2f} ha, Precio: €{precio_cult:.2f}/ha, Base Imp.: {base_imp}")

        print(f"Subtotal General: {self.lbl_subtotal_general.text()}")
        print(f"IVA Global: {self.spin_global_iva.value():.2f}%")
        print(f"IVA Total Calculado: {self.lbl_iva_total.text()}")
        print(f"Total Factura: {self.lbl_total_factura.text()}")
        print("------------------------------------")

        if not REPORTLAB_AVAILABLE:
            QMessageBox.warning(self, "Funcionalidad Limitada", 
                                "La librería ReportLab no está instalada. No se puede generar el PDF.\n"
                                "La factura se 'guardará' solo en simulación (consola).\n"
                                "Por favor, instale ReportLab (ej: pip install reportlab) para la exportación a PDF.")
            super().accept() 
            return

        items_data_for_pdf = []
        for row in range(self.table_items.rowCount()):
            if self.is_description_row(row): 
                continue
            items_data_for_pdf.append({
                "description": self.table_items.cellWidget(row, 0).currentText() if self.table_items.cellWidget(row, 0) else "",
                "quantity_str": f"{self.table_items.cellWidget(row, 1).value():.2f}",
                "unit_price_str": f"€ {self.table_items.cellWidget(row, 2).value():.2f}",
                "subtotal_str": self.table_items.item(row, 3).text() 
            })

        cultivos_data_for_pdf = []
        if self.table_cultivos.columnCount() == 5: # Solo si no es un mensaje
            for row in range(self.table_cultivos.rowCount()):
                cultivos_data_for_pdf.append({
                    "cultivo": self.table_cultivos.cellWidget(row, 0).currentText(),
                    "sup_mapeada_str": f"{self.table_cultivos.cellWidget(row, 1).value():.2f} ha",
                    "sup_facturable_str": f"{self.table_cultivos.cellWidget(row, 2).value():.2f} ha",
                    "precio_cultivo_str": f"€ {self.table_cultivos.cellWidget(row, 3).value():.2f}", 
                    "base_imponible_str": self.table_cultivos.item(row, 4).text()
                })

        invoice_data_for_pdf = {
            "client_name": self.txt_cliente_nombre.text(),
            "client_cif": self.txt_cliente_cif.text(),
            "campaign_name": self.combo_campania_factura.currentText(), 
            "campaign_id": self.combo_campania_factura.get_current_campaign_id(), 
            "invoice_date_str": self.date_fecha_factura.date().toString('dd/MM/yyyy'),
            "invoice_number_display": num_factura_display, 
            "items": items_data_for_pdf,
            "cultivos": cultivos_data_for_pdf, 
            "subtotal_general_str": self.lbl_subtotal_general.text(),
            "global_iva_rate_str": f"{self.spin_global_iva.value():.2f}%",
            "iva_total_str": self.lbl_iva_total.text(),
            "total_factura_str": self.lbl_total_factura.text()
        }

        options = QFileDialog.Options()
        clean_cliente_name_pdf = "".join(c if c.isalnum() or c in (' ', '_') else '' for c in self.txt_cliente_nombre.text()).rstrip()
        default_filename = f"Factura_{clean_cliente_name_pdf.replace(' ', '_')}_{self.date_fecha_factura.date().toString('yyyyMMdd')}.pdf"
        
        filepath, _ = QFileDialog.getSaveFileName(self, "Guardar Factura PDF", default_filename,
                                                  "Archivos PDF (*.pdf);;Todos los archivos (*)", options=options)
        if filepath:
            if create_invoice_pdf_document(filepath, invoice_data_for_pdf, parent_widget=self):
                QMessageBox.information(self, "Factura Guardada y Exportada", 
                                        f"La factura se ha 'guardado' (simulación) y exportado a PDF:\n{filepath}")
                super().accept() 
            else:
                return 
        else:
            reply = QMessageBox.question(self, "Guardado de PDF Cancelado", 
                                       "La generación del PDF fue cancelada por el usuario.\n"
                                       "¿Desea continuar guardando la factura (simulación en consola) sin generar el PDF?",
                                       QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                QMessageBox.information(self, "Factura 'Guardada' (Simulación)", 
                                        "La factura se ha 'guardado' (simulación).\nLos detalles se han impreso en la consola de Python.")
                super().accept()
            else:
                return 
