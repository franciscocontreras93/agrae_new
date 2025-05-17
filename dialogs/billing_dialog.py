from qgis.PyQt.QtWidgets import (  # type: ignore
    QDialog, QVBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QDateEdit, QDialogButtonBox, QDoubleSpinBox, QMessageBox, QAction,
    QHBoxLayout, QFileDialog, QComboBox # QCompleter ya no es necesario aquí directamente
)
from qgis.PyQt.QtGui import QIcon, QBrush, QColor # type: ignore # Añadido QIcon, QBrush, QColor
from qgis.PyQt.QtCore import QDate, Qt, QStringListModel # type: ignore # Añadido QStringListModel
import os

from ..tools.pdf_utils import create_invoice_pdf_document, REPORTLAB_AVAILABLE

from .select_client_dialog import SelectClientDialog # Importar el diálogo de selección de cliente
from ..gui.billing.product_selection_combobox import ProductSelectionComboBox # Importar el nuevo componente


class CreateInvoiceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Crear Nueva Factura")
        self.setMinimumSize(700, 600) # Ajustado para más espacio y el PDF
        # Lista de productos/servicios (simulación de BD)
        self.product_items_list_master = ["Producto Ejemplo 1", "Servicio Ejemplo A", "Otro Item Inicial"] # Lista maestra
        self.endpoint_url = 'http://localhost:8000'
        
        # Lista para almacenar los datos completos de los ítems de la factura
        self.invoice_items_data_objects = []

        self.init_ui()
        self._update_product_models() # Carga inicial de modelos
        if self.table_items.rowCount() == 0: # Añadir una fila solo si no hay ninguna
            self.add_item_row() 


        

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # --- Sección de Información General de la Factura ---
        general_info_layout = QFormLayout()
        self.txt_cliente = QLineEdit()
        self.txt_cliente.setPlaceholderText("Nombre o Razón Social del Cliente (o buscar)")

        # Crear la acción para el botón de búsqueda dentro del QLineEdit
        current_script_path = os.path.dirname(__file__) # .../dialogs/
        plugin_agrae_dir = os.path.dirname(current_script_path) # .../agrae/
        search_icon_path = os.path.join(plugin_agrae_dir, "gui", "icons", "search.svg")
        
        self.search_client_action = QAction(self)
        if os.path.exists(search_icon_path):
            self.search_client_action.setIcon(QIcon(search_icon_path))
        self.txt_cliente.addAction(self.search_client_action, QLineEdit.TrailingPosition)
        self.txt_cliente.setPlaceholderText("Nombre o Razón Social del Cliente")
        self.date_fecha_factura = QDateEdit(QDate.currentDate())
        self.date_fecha_factura.setCalendarPopup(True)
        self.date_fecha_factura.setDisplayFormat("dd/MM/yyyy")
        self.txt_numero_factura = QLineEdit()
        self.txt_numero_factura.setPlaceholderText("Se generará al guardar (ej: F2025-0001)")
        self.txt_numero_factura.setReadOnly(True) # Mantenido como ReadOnly

        self.spin_global_iva = QDoubleSpinBox()
        self.spin_global_iva.setMinimum(0)
        self.spin_global_iva.setMaximum(100)
        self.spin_global_iva.setValue(21.0) # Default IVA
        self.spin_global_iva.setSuffix(" %")

        general_info_layout.addRow("Cliente:", self.txt_cliente)
        general_info_layout.addRow("Fecha Factura:", self.date_fecha_factura)
        general_info_layout.addRow("Número Factura:", self.txt_numero_factura)
        main_layout.addLayout(general_info_layout)

        # --- Sección de Ítems de la Factura ---
        main_layout.addWidget(QLabel("Ítems de la Factura:"))
        self.table_items = QTableWidget()
        self.table_items.setColumnCount(4) 
        self.table_items.setHorizontalHeaderLabels(["Descripción", "Cantidad", "Precio Unit.", "Subtotal"]) # type: ignore
        self.table_items.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch) # Descripción
        self.table_items.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table_items.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table_items.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents) # Subtotal

        # Layout para la tabla y los botones de añadir/eliminar a su derecha
        table_with_buttons_layout = QHBoxLayout()
        table_with_buttons_layout.addWidget(self.table_items, 1) # La tabla ocupa la mayor parte del espacio

        # Botones de acción para la tabla (Añadir, Eliminar)
        table_action_buttons_layout = QVBoxLayout()
        table_action_buttons_layout.setAlignment(Qt.AlignTop) # Alinea los botones arriba

        current_script_path = os.path.dirname(__file__)
        plugin_agrae_dir = os.path.dirname(current_script_path)
        
        self.btn_add_item_to_table = QPushButton()
        add_icon_path = os.path.join(plugin_agrae_dir, "gui", "icons", "plus-solid.svg")
        if os.path.exists(add_icon_path):
            self.btn_add_item_to_table.setIcon(QIcon(add_icon_path))
            self.btn_add_item_to_table.setToolTip("Añadir ítem a la factura")
        else:
            self.btn_add_item_to_table.setText("+")
            print(f"Advertencia: No se encontró el icono en {add_icon_path}.")
        table_action_buttons_layout.addWidget(self.btn_add_item_to_table)

        self.btn_remove_item_from_table = QPushButton()
        remove_icon_path = os.path.join(plugin_agrae_dir, "gui", "icons", "minus-solid.svg")
        if os.path.exists(remove_icon_path):
            self.btn_remove_item_from_table.setIcon(QIcon(remove_icon_path))
            self.btn_remove_item_from_table.setToolTip("Eliminar ítem seleccionado de la factura")
        else:
            self.btn_remove_item_from_table.setText("-")
            print(f"Advertencia: No se encontró el icono en {remove_icon_path}.")
        table_action_buttons_layout.addWidget(self.btn_remove_item_from_table)
        
        table_with_buttons_layout.addLayout(table_action_buttons_layout)
        main_layout.addLayout(table_with_buttons_layout)

        # Botón para añadir nuevos productos a la lista maestra (debajo de la tabla)
        items_button_layout = QHBoxLayout()
        self.btn_add_new_product = QPushButton("Gestionar Productos/Servicios") # Texto más genérico
        items_button_layout.addWidget(self.btn_add_new_product)
        items_button_layout.addStretch()
        main_layout.addLayout(items_button_layout)


        # --- Sección de Totales ---
        totals_layout = QFormLayout()
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
        totals_layout.addRow("IVA Global:", self.spin_global_iva) # Moved here for better layout with totals
        totals_layout.addRow("IVA Total:", self.lbl_iva_total)
        totals_layout.addRow("TOTAL:", self.lbl_total_factura)
        main_layout.addLayout(totals_layout)

        # --- Botones de Acción (Guardar, Cancelar) ---
        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.button_box.button(QDialogButtonBox.Save).setText("Guardar Factura y Exportar PDF")
        self.button_box.accepted.connect(self.accept_invoice)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

        self.setLayout(main_layout)
        
        # Conexiones para botones de ítems (después de que existan los botones)
        self.btn_add_item_to_table.clicked.connect(self.add_item_row)
        self.btn_remove_item_from_table.clicked.connect(self.remove_item_row)
        self.btn_add_new_product.clicked.connect(self.open_add_new_product_dialog)
        self.search_client_action.triggered.connect(self.open_select_client_dialog) # Conectar la acción


        # Connect global IVA spinbox to recalculate totals when changed
        self.spin_global_iva.valueChanged.connect(self.calculate_totals)

    def _update_product_models(self):
        """Actualiza el modelo de productos para las celdas y el ComboBox de añadir."""
        self.product_items_list_master.sort(key=lambda x: x.lower())
        # Actualizar todos los combobox de descripción en la tabla
        for row in range(self.table_items.rowCount()):
            widget = self.table_items.cellWidget(row, 0)
            if isinstance(widget, ProductSelectionComboBox):
                widget.update_product_list(self.product_items_list_master)
        print(f"[DEBUG] _update_product_models: Lista maestra actualizada: {self.product_items_list_master}")

    def add_item_row(self): # Eliminado description_text
        row_position = self.table_items.rowCount()
        self.table_items.insertRow(row_position)
        # print(f"[DEBUG] add_item_row: Iniciando para fila {row_position}. El modelo de productos ahora es interno a ProductSelectionComboBox.")

        # Asegurarse de que no haya un item preexistente en la celda de descripción que pueda interferir
        existing_item_at_desc_col = self.table_items.item(row_position, 0)
        if existing_item_at_desc_col:
            print(f"[DEBUG] add_item_row (fila {row_position}): ADVERTENCIA - Había un QTableWidgetItem en ( {row_position}, 0) antes de setCellWidget. Texto: '{existing_item_at_desc_col.text()}'. Eliminándolo.")
            self.table_items.takeItem(row_position, 0) # Eliminarlo si existe
        api_items_config = {
            "url": f"{self.endpoint_url}/api/billing/items/", # Reemplaza con tu URL base
            "params": {}, # Parámetros GET adicionales si los necesitas
            "headers": {} # Cabeceras adicionales (ej: para autenticación)
        }
        desc_combo = ProductSelectionComboBox(api_items_config, self)
        desc_combo.setObjectName(f"desc_combo_row_{row_position}") # Para identificarlo unívocamente en los logs
        print(f"[DEBUG] add_item_row (fila {row_position}): ProductSelectionComboBox '{desc_combo.objectName()}' creado.")

        # Conectar la señal del nuevo combobox para actualizar la lista maestra
        desc_combo.product_list_updated.connect(self.handle_master_product_list_update)
        # Conectar la nueva señal para manejar la selección de un producto
        desc_combo.product_selected_data.connect(lambda product_data, r=row_position: self.handle_product_selected_in_row(r, product_data))

        self.table_items.setCellWidget(row_position, 0, desc_combo)
        print(f"[DEBUG] add_item_row (fila {row_position}): setCellWidget( {row_position}, 0, '{desc_combo.objectName()}') LLAMADO.")

        # VERIFICACIÓN INMEDIATA después de setCellWidget:
        retrieved_widget = self.table_items.cellWidget(row_position, 0)
        if retrieved_widget:
            print(f"[DEBUG] add_item_row (fila {row_position}): VERIFICACIÓN - Widget en ( {row_position}, 0) es {type(retrieved_widget)}, objectName: {retrieved_widget.objectName()}")
            if isinstance(retrieved_widget, ProductSelectionComboBox):
                current_model = retrieved_widget.model()
                if hasattr(current_model, 'stringList'):
                    print(f"[DEBUG] add_item_row (fila {row_position}):   ¡ÉXITO! Es un ProductSelectionComboBox. Modelo ({type(current_model)}): {current_model.stringList()}")
                else:
                    print(f"[DEBUG] add_item_row (fila {row_position}):   ¡ÉXITO PARCIAL! Es un ProductSelectionComboBox, pero su modelo ({type(current_model)}) no tiene stringList(). Items: {[current_model.item(i).text() if current_model.item(i) else 'None' for i in range(current_model.rowCount())] if hasattr(current_model, 'rowCount') and hasattr(current_model, 'item') else 'No se pudo obtener lista de items'}")
            else:
                print(f"[DEBUG] add_item_row (fila {row_position}):   ¡FALLO CRÍTICO! NO ES UN QCOMBOBOX. Esto es un problema grave.")
        else:
            print(f"[DEBUG] add_item_row (fila {row_position}): ¡FALLO CRÍTICO! No se recuperó ningún widget de ( {row_position}, 0) después de setCellWidget.")

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
        self.table_items.setItem(row_position, 3, subtotal_item) # Subtotal is now in column 3

        # Conexiones para actualizar subtotales
        desc_combo.currentTextChanged.connect(self.on_description_text_changed) # Conectado a un método dedicado
        qty_spinbox.valueChanged.connect(lambda value, r=row_position: self.update_item_subtotal(r, 1))
        price_spinbox.valueChanged.connect(lambda value, r=row_position: self.update_item_subtotal(r, 2))
        # No IVA per item, so no connection for column 3's old IVA spinbox

        # Enfocar el nuevo combobox de descripción si es la primera fila absoluta o la única fila
        if self.table_items.rowCount() == 1 and row_position == 0 : 
            print(f"[DEBUG] add_item_row (fila {row_position}): Intentando enfocar QComboBox en la primera fila absoluta.")
            self.table_items.setCurrentCell(0,0)
            desc_combo.setFocus()

    def handle_master_product_list_update(self, updated_list):
        """Manejador para cuando un ProductSelectionComboBox actualiza la lista maestra."""
        print(f"[DEBUG] handle_master_product_list_update: Lista maestra recibida: {updated_list}")
        self.product_items_list_master = updated_list
        self._update_product_models() # Propagar la actualización a otros combos

    def open_select_client_dialog(self):
        dialog = SelectClientDialog(self.endpoint_url,self)
        dialog.client_selected.connect(self.handle_client_dialog_selection)
        # dialog.exec_() # Modal
        if dialog.exec_() == QDialog.Accepted:
            print("Diálogo de selección de cliente aceptado.")
        else:
            print("Diálogo de selección de cliente cancelado.")

    def handle_client_dialog_selection(self, client_data):
        if client_data:
            self.txt_cliente.setText(client_data.get("nombre", ""))
            self.selected_client_id = client_data.get("id") 
            print(f"Cliente seleccionado: ID {self.selected_client_id}, Nombre: {client_data.get('nombre')}")

    def handle_product_selected_in_row(self, row: int, product_data: object):
        """
        Manejador para cuando se selecciona un producto en un ProductSelectionComboBox de una fila.
        Actualiza el precio en la tabla y almacena los datos del ítem.
        """
        print(f"[DEBUG] handle_product_selected_in_row: Fila {row}, Datos del producto: {product_data}")
        if not isinstance(product_data, dict):
            print(f"[DEBUG] handle_product_selected_in_row: Datos del producto no son un diccionario. Tipo: {type(product_data)}")
            # Podrías querer limpiar el precio si el producto no es válido o es el placeholder
            price_widget = self.table_items.cellWidget(row, 2)
            if price_widget:
                price_widget.setValue(0.0)
            return

        precio_1 = product_data.get('precio_1', 0.0)
        try:
            precio_1_float = float(precio_1)
        except (ValueError, TypeError):
            precio_1_float = 0.0
            print(f"[DEBUG] handle_product_selected_in_row: No se pudo convertir precio_1 ('{precio_1}') a float.")

        price_widget = self.table_items.cellWidget(row, 2) # Columna del Precio Unit.
        if price_widget and isinstance(price_widget, QDoubleSpinBox):
            price_widget.setValue(precio_1_float)
        
        # Aquí actualizaremos o añadiremos el objeto a self.invoice_items_data_objects
        # Por ahora, solo imprimimos. La lógica de almacenamiento se desarrollará más adelante.
        print(f"[DEBUG] Fila {row}: Precio unitario establecido a {precio_1_float} desde producto.")
        # self.update_item_subtotal(row, 0) # El cambio de precio ya dispara la actualización del subtotal

    def on_description_text_changed(self, text: str):
        """
        Manejador para la señal currentTextChanged del QComboBox de descripción.
        Identifica la fila del QComboBox que emitió la señal y llama a update_item_subtotal.
        NOTA: La lógica de "Añadir nuevo producto" ahora está dentro de ProductSelectionComboBox.
        Este método solo se preocupa de actualizar el subtotal si el texto cambia a un producto real.
        """
        sender_combo = self.sender() # Sigue siendo ProductSelectionComboBox
        if not isinstance(sender_combo, ProductSelectionComboBox):
            return

        for row in range(self.table_items.rowCount()):
            widget = self.table_items.cellWidget(row, 0)
            if widget == sender_combo:
                print(f"[DEBUG] on_description_text_changed: Fila {row} (widget '{widget.objectName()}'), Texto: '{text}'")
                # Si el texto es el placeholder o "agregar nuevo", no actualizamos subtotal basado en esto.
                # La actualización del precio (y por ende subtotal) se maneja en handle_product_selected_in_row
                if text != sender_combo.PLACEHOLDER_CHOOSE_SERVICE_TEXT and \
                   text != sender_combo.ADD_NEW_PRODUCT_SYSTEM_TEXT:
                    self.update_item_subtotal(row, 0) # Columna 0 (descripción) cambió
                return

    def remove_item_row(self):
        current_row = self.table_items.currentRow()
        if current_row >= 0:
            self.table_items.removeRow(current_row)
            self.calculate_totals()
        else:
            QMessageBox.warning(self, "Eliminar Ítem", "Por favor, seleccione una fila para eliminar.")

    def open_add_new_product_dialog(self):
        # Este método ahora es llamado por el botón "Gestionar Productos/Servicios"
        # y no directamente por la selección del combo.
        dialog = AddNewProductDialog(self.product_items_list_master, self)
        if dialog.exec_() == QDialog.Accepted:
            new_product_name = dialog.get_new_product_name()
            if new_product_name: # Nombre ya validado en AddNewProductDialog
                self.product_items_list_master.append(new_product_name)
                self._update_product_models() # Esto actualiza la lista, la ordena y refresca los modelos
                print(f"[DEBUG] open_add_new_product_dialog: Lista de productos y modelos actualizados tras añadir '{new_product_name}'.")

    def update_item_subtotal(self, row, column_changed):
        try:
            # La descripción (col 0) no afecta directamente el subtotal, pero su cambio puede ser un trigger
            qty_widget = self.table_items.cellWidget(row, 1)
            price_widget = self.table_items.cellWidget(row, 2)
            subtotal_item = self.table_items.item(row, 3) # El subtotal está en la columna 3

            if qty_widget and price_widget and subtotal_item: # Asegurarse que todos los widgets/items existen
                cantidad = qty_widget.value()
                precio_unit = price_widget.value()
                subtotal_linea = cantidad * precio_unit
                subtotal_item.setText(f"€ {subtotal_linea:.2f}")
            else:
                if subtotal_item:
                    subtotal_item.setText("€ 0.00")
        except Exception as e:
            print(f"Error actualizando subtotal de ítem (fila {row}): {e}")
            if self.table_items.item(row, 3): # Column 3 for subtotal
                self.table_items.item(row, 3).setText("Error")
        
        self.calculate_totals()

    def calculate_totals(self):
        subtotal_general_val = 0.0
        iva_total_acumulado_val = 0.0

        for row in range(self.table_items.rowCount()):
            try:
                subtotal_item_text = self.table_items.item(row, 3).text().replace("€ ", "") # Subtotal from column 3
                line_subtotal = float(subtotal_item_text)
                subtotal_general_val += line_subtotal
            except (ValueError, AttributeError, TypeError) as e:
                print(f"Error calculando totales para fila {row}: {e}")
                continue
        
        global_iva_rate = self.spin_global_iva.value() / 100.0
        iva_total_acumulado_val = subtotal_general_val * global_iva_rate
        total_factura_val = subtotal_general_val + iva_total_acumulado_val
        self.lbl_subtotal_general.setText(f"€ {subtotal_general_val:.2f}")
        self.lbl_iva_total.setText(f"€ {iva_total_acumulado_val:.2f}")
        self.lbl_total_factura.setText(f"€ {total_factura_val:.2f}")

    def accept_invoice(self):
        cliente = self.txt_cliente.text().strip()
        if not cliente:
            QMessageBox.warning(self, "Validación", "El campo 'Cliente' no puede estar vacío.")
            self.txt_cliente.setFocus()
            return

        if self.table_items.rowCount() == 0:
            QMessageBox.warning(self, "Validación", "La factura debe tener al menos un ítem.")
            self.btn_add_item_to_table.setFocus() # type: ignore
            return

        for row in range(self.table_items.rowCount()):
            desc_widget = self.table_items.cellWidget(row, 0) # Ahora es un QComboBox
            qty_widget = self.table_items.cellWidget(row, 1)

            if not desc_widget or not desc_widget.currentText().strip():
                QMessageBox.warning(self, "Validación", f"El ítem en la fila {row + 1} no tiene descripción.")
                self.table_items.setCurrentCell(row, 0)
                if desc_widget:
                    desc_widget.setFocus()
                return
            if qty_widget and qty_widget.value() <= 0:
                QMessageBox.warning(self, "Validación", f"La cantidad para el ítem en la fila {row + 1} debe ser mayor que cero.")
                self.table_items.setCurrentCell(row, 1)
                qty_widget.setFocus()
                return
        
        # Simulación de guardado en consola
        print("--- Factura a Guardar (Simulación) ---")
        print(f"Cliente: {cliente}")
        print(f"Fecha: {self.date_fecha_factura.date().toString('yyyy-MM-dd')}")
        num_factura_text = self.txt_numero_factura.text()
        if not num_factura_text or num_factura_text == self.txt_numero_factura.placeholderText():
            num_factura_display = "PENDIENTE (automático)"
        else:
            num_factura_display = num_factura_text
        print(f"Número Factura (campo): {num_factura_display}")
        print("Ítems:")
        for row in range(self.table_items.rowCount()):
            desc = self.table_items.cellWidget(row, 0).currentText() if self.table_items.cellWidget(row, 0) else ""
            qty = self.table_items.cellWidget(row, 1).value()
            price = self.table_items.cellWidget(row, 2).value()
            sub = self.table_items.item(row, 3).text() # Subtotal from column 3
            print(f"  - Desc: {desc}, Cant: {qty:.2f}, Precio: €{price:.2f}, Subtotal: {sub}")
        
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
            super().accept() # Aceptar simulación sin PDF
            return

        # Recopilar datos para el PDF
        items_data_for_pdf = []
        for row in range(self.table_items.rowCount()):
            items_data_for_pdf.append({
                "description": self.table_items.cellWidget(row, 0).currentText() if self.table_items.cellWidget(row, 0) else "",
                "quantity_str": f"{self.table_items.cellWidget(row, 1).value():.2f}",
                "unit_price_str": f"€ {self.table_items.cellWidget(row, 2).value():.2f}",
                "subtotal_str": self.table_items.item(row, 3).text() # Subtotal from column 3
            })

        invoice_data_for_pdf = {
            "client_name": cliente,
            "invoice_date_str": self.date_fecha_factura.date().toString('dd/MM/yyyy'),
            "invoice_number_display": num_factura_display, # Ya calculado arriba
            "items": items_data_for_pdf,
            "subtotal_general_str": self.lbl_subtotal_general.text(),
            "global_iva_rate_str": f"{self.spin_global_iva.value():.2f}%",
            "iva_total_str": self.lbl_iva_total.text(),
            "total_factura_str": self.lbl_total_factura.text()
        }

        # Preguntar dónde guardar el PDF
        options = QFileDialog.Options()
        # options |= QFileDialog.DontUseNativeDialog # Descomentar si el diálogo nativo da problemas
        
        # Sugerir un nombre de archivo
        clean_cliente_name = "".join(c if c.isalnum() or c in (' ', '_') else '' for c in cliente).rstrip()
        default_filename = f"Factura_{clean_cliente_name.replace(' ', '_')}_{self.date_fecha_factura.date().toString('yyyyMMdd')}.pdf"
        
        filepath, _ = QFileDialog.getSaveFileName(self, "Guardar Factura PDF", default_filename,
                                                  "Archivos PDF (*.pdf);;Todos los archivos (*)", options=options)
        if filepath:
            # Llamar a la función externa para generar el PDF
            if create_invoice_pdf_document(filepath, invoice_data_for_pdf, parent_widget=self):
                QMessageBox.information(self, "Factura Guardada y Exportada", 
                                        f"La factura se ha 'guardado' (simulación) y exportado a PDF:\n{filepath}")
                super().accept() # Cierra el diálogo con resultado aceptado
            else:
                # El error ya se mostró en create_invoice_pdf_document
                # No cerramos el diálogo para que el usuario pueda intentarlo de nuevo o cancelar.
                return 
        else:
            # Usuario canceló el guardado del PDF
            reply = QMessageBox.question(self, "Guardado de PDF Cancelado", 
                                       "La generación del PDF fue cancelada por el usuario.\n"
                                       "¿Desea continuar guardando la factura (simulación en consola) sin generar el PDF?",
                                       QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                QMessageBox.information(self, "Factura 'Guardada' (Simulación)", 
                                        "La factura se ha 'guardado' (simulación).\nLos detalles se han impreso en la consola de Python.")
                super().accept()
            else:
                return # No cerrar el diálogo, el usuario eligió no guardar nada


# Para probar el diálogo de forma independiente (opcional):
if __name__ == '__main__':
    import sys
    from qgis.PyQt.QtWidgets import QApplication
    
    # Para la prueba standalone, intentamos importar ReportLab directamente
    # para el mensaje de advertencia inicial. La clase CreateInvoiceDialog usará
    # la importación relativa que funcionará dentro de QGIS.
    reportlab_available_for_test = False
    try:
        from reportlab.lib.pagesizes import A4 # Solo para verificar si ReportLab está instalado
        reportlab_available_for_test = True
    except ImportError:
        pass # Mantenemos reportlab_available_for_test como False

    app = QApplication(sys.argv)
    
    if not reportlab_available_for_test:
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle("Advertencia de Dependencia (Prueba Standalone)")
        msg_box.setText("La librería ReportLab no está instalada o no se pudo importar.\n"
                        "La funcionalidad de generar PDF podría no estar disponible en esta prueba si el módulo 'tools.pdf_utils' no se carga correctamente.")
        msg_box.setInformativeText("Puede instalarla con: pip install reportlab")
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()

    dialog = CreateInvoiceDialog()
    dialog.show()
    sys.exit(app.exec_())
