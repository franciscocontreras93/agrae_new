from qgis.PyQt.QtWidgets import (  # type: ignore
    QDialog, QVBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QDateEdit, QDialogButtonBox, QDoubleSpinBox, QMessageBox,
    QHBoxLayout, QFileDialog
)
from qgis.PyQt.QtCore import QDate, Qt # type: ignore

from ..tools.pdf_utils import create_invoice_pdf_document, REPORTLAB_AVAILABLE, INVOICE_TYPE_KIT_DIGITAL

class CreateKitDigitalInvoiceDialog(QDialog): # Nombre de clase cambiado
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Crear Nueva Factura - Kit Digital") # Título cambiado
        self.setMinimumSize(700, 650) # Un poco más alto para el nuevo campo
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # --- Sección de Información General de la Factura ---
        general_info_layout = QFormLayout()
        self.txt_cliente = QLineEdit()
        self.txt_cliente.setPlaceholderText("Nombre o Razón Social del Cliente")
        self.date_fecha_factura = QDateEdit(QDate.currentDate())
        self.date_fecha_factura.setCalendarPopup(True)
        self.date_fecha_factura.setDisplayFormat("dd/MM/yyyy")
        self.txt_numero_factura = QLineEdit()
        self.txt_numero_factura.setPlaceholderText("Se generará al guardar (ej: FKD2025-0001)") # Placeholder ajustado
        self.txt_numero_factura.setReadOnly(True)

        # --- Nuevo campo para Código de Convenio ---
        self.txt_codigo_convenio = QLineEdit()
        self.txt_codigo_convenio.setPlaceholderText("Ej: C033/22-ED")
        # --- Fin nuevo campo ---

        general_info_layout.addRow("Cliente:", self.txt_cliente)
        general_info_layout.addRow("Fecha Factura:", self.date_fecha_factura)
        general_info_layout.addRow("Número Factura:", self.txt_numero_factura)
        general_info_layout.addRow("Código de Convenio:", self.txt_codigo_convenio) # Añadido al layout
        main_layout.addLayout(general_info_layout)

        # --- Sección de Ítems de la Factura ---
        main_layout.addWidget(QLabel("Ítems de la Factura:"))
        self.table_items = QTableWidget()
        self.table_items.setColumnCount(5)
        self.table_items.setHorizontalHeaderLabels(["Descripción", "Cantidad", "Precio Unit.", "IVA (%)", "Subtotal"])
        self.table_items.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table_items.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table_items.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table_items.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table_items.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        main_layout.addWidget(self.table_items)

        items_button_layout = QHBoxLayout()
        self.btn_add_item = QPushButton("Añadir Ítem")
        self.btn_remove_item = QPushButton("Eliminar Ítem Seleccionado")
        items_button_layout.addWidget(self.btn_add_item)
        items_button_layout.addWidget(self.btn_remove_item)
        items_button_layout.addStretch()
        main_layout.addLayout(items_button_layout)

        self.btn_add_item.clicked.connect(self.add_item_row)
        self.btn_remove_item.clicked.connect(self.remove_item_row)

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
        totals_layout.addRow("IVA Total:", self.lbl_iva_total)
        totals_layout.addRow("TOTAL:", self.lbl_total_factura)
        main_layout.addLayout(totals_layout)

        # --- Botones de Acción ---
        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.button_box.button(QDialogButtonBox.Save).setText("Guardar Factura Kit Digital y PDF")
        self.button_box.accepted.connect(self.accept_invoice)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

        self.setLayout(main_layout)
        self.add_item_row()

    def add_item_row(self):
        row_position = self.table_items.rowCount()
        self.table_items.insertRow(row_position)

        desc_item = QTableWidgetItem("")
        self.table_items.setItem(row_position, 0, desc_item)

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

        iva_spinbox = QDoubleSpinBox()
        iva_spinbox.setMinimum(0)
        iva_spinbox.setMaximum(100)
        iva_spinbox.setValue(21.0) # O el IVA que aplique al Kit Digital
        iva_spinbox.setSuffix(" %")
        self.table_items.setCellWidget(row_position, 3, iva_spinbox)

        subtotal_item = QTableWidgetItem("€ 0.00")
        subtotal_item.setFlags(subtotal_item.flags() & ~Qt.ItemIsEditable)
        subtotal_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table_items.setItem(row_position, 4, subtotal_item)

        desc_item.setData(Qt.UserRole, row_position)
        qty_spinbox.valueChanged.connect(lambda value, r=row_position: self.update_item_subtotal(r, 1))
        price_spinbox.valueChanged.connect(lambda value, r=row_position: self.update_item_subtotal(r, 2))
        iva_spinbox.valueChanged.connect(lambda value, r=row_position: self.update_item_subtotal(r, 3))
        self.table_items.itemChanged.connect(self.handle_item_changed)

        if row_position == 0:
            self.table_items.setCurrentCell(0,0)
            self.table_items.editItem(desc_item)

    def handle_item_changed(self, item):
        if item.column() == 0:
            row = item.row()
            self.update_item_subtotal(row, 0)

    def remove_item_row(self):
        current_row = self.table_items.currentRow()
        if current_row >= 0:
            self.table_items.removeRow(current_row)
            self.calculate_totals()
        else:
            QMessageBox.warning(self, "Eliminar Ítem", "Por favor, seleccione una fila para eliminar.")

    def update_item_subtotal(self, row, column_changed):
        try:
            qty_widget = self.table_items.cellWidget(row, 1)
            price_widget = self.table_items.cellWidget(row, 2)
            subtotal_item = self.table_items.item(row, 4)

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
            if self.table_items.item(row, 4):
                self.table_items.item(row, 4).setText("Error")
        
        self.calculate_totals()

    def calculate_totals(self):
        subtotal_general_val = 0.0
        iva_total_acumulado_val = 0.0

        for row in range(self.table_items.rowCount()):
            try:
                subtotal_item_text = self.table_items.item(row, 4).text().replace("€ ", "")
                line_subtotal = float(subtotal_item_text)
                subtotal_general_val += line_subtotal

                iva_percent_widget = self.table_items.cellWidget(row, 3)
                if iva_percent_widget:
                    iva_percent = iva_percent_widget.value() / 100.0
                    iva_de_linea = line_subtotal * iva_percent
                    iva_total_acumulado_val += iva_de_linea
            except (ValueError, AttributeError, TypeError) as e:
                print(f"Error calculando totales para fila {row}: {e}")
                continue

        total_factura_val = subtotal_general_val + iva_total_acumulado_val

        self.lbl_subtotal_general.setText(f"€ {subtotal_general_val:.2f}")
        self.lbl_iva_total.setText(f"€ {iva_total_acumulado_val:.2f}")
        self.lbl_total_factura.setText(f"€ {total_factura_val:.2f}")

    def accept_invoice(self):
        cliente = self.txt_cliente.text().strip()
        codigo_convenio = self.txt_codigo_convenio.text().strip() # Obtener código de convenio

        if not cliente:
            QMessageBox.warning(self, "Validación", "El campo 'Cliente' no puede estar vacío.")
            self.txt_cliente.setFocus()
            return
        
        # Validación para el código de convenio (opcional, pero recomendable)
        if not codigo_convenio:
            QMessageBox.warning(self, "Validación", "El campo 'Código de Convenio' no puede estar vacío para facturas Kit Digital.")
            self.txt_codigo_convenio.setFocus()
            return

        if self.table_items.rowCount() == 0:
            QMessageBox.warning(self, "Validación", "La factura debe tener al menos un ítem.")
            self.btn_add_item.setFocus()
            return

        for row in range(self.table_items.rowCount()):
            desc_item = self.table_items.item(row, 0)
            qty_widget = self.table_items.cellWidget(row, 1)

            if not desc_item or not desc_item.text().strip():
                QMessageBox.warning(self, "Validación", f"El ítem en la fila {row + 1} no tiene descripción.")
                self.table_items.setCurrentCell(row, 0)
                self.table_items.editItem(desc_item)
                return
            if qty_widget and qty_widget.value() <= 0:
                QMessageBox.warning(self, "Validación", f"La cantidad para el ítem en la fila {row + 1} debe ser mayor que cero.")
                self.table_items.setCurrentCell(row, 1)
                qty_widget.setFocus()
                return
        
        print("--- Factura Kit Digital a Guardar (Simulación) ---")
        print(f"Cliente: {cliente}")
        print(f"Código Convenio: {codigo_convenio}") # Imprimir código de convenio
        print(f"Fecha: {self.date_fecha_factura.date().toString('yyyy-MM-dd')}")
        num_factura_text = self.txt_numero_factura.text()
        if not num_factura_text or num_factura_text == self.txt_numero_factura.placeholderText():
            num_factura_display = "PENDIENTE (automático)"
        else:
            num_factura_display = num_factura_text
        print(f"Número Factura (campo): {num_factura_display}")
        print("Ítems:")
        for row in range(self.table_items.rowCount()):
            desc = self.table_items.item(row, 0).text()
            qty = self.table_items.cellWidget(row, 1).value()
            price = self.table_items.cellWidget(row, 2).value()
            iva_p = self.table_items.cellWidget(row, 3).value()
            sub = self.table_items.item(row, 4).text()
            print(f"  - Desc: {desc}, Cant: {qty:.2f}, Precio: €{price:.2f}, IVA: {iva_p:.2f}%, Subtotal: {sub}")
        
        print(f"Subtotal General: {self.lbl_subtotal_general.text()}")
        print(f"IVA Total: {self.lbl_iva_total.text()}")
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
            items_data_for_pdf.append({
                "description": self.table_items.item(row, 0).text(),
                "quantity_str": f"{self.table_items.cellWidget(row, 1).value():.2f}",
                "unit_price_str": f"€ {self.table_items.cellWidget(row, 2).value():.2f}",
                "vat_str": f"{self.table_items.cellWidget(row, 3).value():.2f}%",
                "subtotal_str": self.table_items.item(row, 4).text()
            })

        invoice_data_for_pdf = {
            "client_name": cliente,
            "invoice_date_str": self.date_fecha_factura.date().toString('dd/MM/yyyy'),
            "invoice_number_display": num_factura_display,
            "items": items_data_for_pdf,
            "subtotal_general_str": self.lbl_subtotal_general.text(),
            "iva_total_str": self.lbl_iva_total.text(),
            "total_factura_str": self.lbl_total_factura.text(),
            # Podríamos añadir el código de convenio aquí si pdf_utils lo fuera a usar
            # "codigo_convenio": codigo_convenio 
        }

        options = QFileDialog.Options()
        clean_cliente_name = "".join(c if c.isalnum() or c in (' ', '_') else '' for c in cliente).rstrip()
        default_filename = f"Factura_KitDigital_{clean_cliente_name.replace(' ', '_')}_{self.date_fecha_factura.date().toString('yyyyMMdd')}.pdf"
        
        filepath, _ = QFileDialog.getSaveFileName(self, "Guardar Factura Kit Digital PDF", default_filename,
                                                  "Archivos PDF (*.pdf);;Todos los archivos (*)", options=options)
        if filepath:
            # Usar INVOICE_TYPE_KIT_DIGITAL
            if create_invoice_pdf_document(filepath, invoice_data_for_pdf, invoice_type=INVOICE_TYPE_KIT_DIGITAL, parent_widget=self):
                QMessageBox.information(self, "Factura Kit Digital Guardada y Exportada", 
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
                QMessageBox.information(self, "Factura Kit Digital 'Guardada' (Simulación)", 
                                        "La factura se ha 'guardado' (simulación).\nLos detalles se han impreso en la consola.")
                super().accept()
            else:
                return

