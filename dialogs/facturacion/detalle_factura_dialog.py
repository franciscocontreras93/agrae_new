from decimal import Decimal, InvalidOperation

from qgis.PyQt import QtWidgets
from qgis.PyQt.QtCore import Qt, QDate

from ...core.api import APIRequest

from . import PagosFacturaDialog

from ...gui.components.CustomTableWidget import PagosTableWidget


ENDPOINT_DETAIL_FACTURA = "/billing/facturas/{uid}"
ENDPOINT_UPDATE_FACTURA = "/billing/facturas/{uid}/editar"
ENDPOINT_PDF = "/billing/facturas/recibo_pagos/pdf/{idpago}"


class DetalleFacturaDialog(QtWidgets.QDialog):

    def __init__(self, factura: dict, parent=None):
        super().__init__(parent)

        self.factura = factura or {}
        self.factura_uid = self.factura.get("uid")
        self.idfactura = self.factura.get("idfactura")

        self.api = APIRequest()

        self.editando_header = False
        self._header_original_values = {}

        self.setWindowTitle("Detalle de factura")
        self.resize(950, 720)

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setSpacing(12)

        self.load_factura_details()

    # ==========================================================
    # CARGA / REFRESCO
    # ==========================================================

    def load_factura_details(self):
        response = self.api.get(
            ENDPOINT_DETAIL_FACTURA.format(uid=self.factura_uid)
        )

        if response:
            factura_data = response

            self.factura = factura_data
            self.idfactura = factura_data.get("idfactura") or self.idfactura
            self.editando_header = False

            self.display_factura_details(factura_data)
        else:
            QtWidgets.QMessageBox.critical(
                self,
                "Error",
                "No se pudo cargar el detalle de la factura."
            )
            self.reject()

    def display_factura_details(self, factura):
        self.clear_layout(self.main_layout)

        self.main_layout.addWidget(self._build_factura_group(factura))
        self.main_layout.addWidget(self._build_importes_group(factura))
        self.main_layout.addWidget(self._build_pagos_group(factura))

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)
        self.main_layout.addWidget(button_box)

    # ==========================================================
    # BLOQUE INFORMACIÓN FACTURA / ENCABEZADO
    # ==========================================================

    def _build_factura_group(self, factura):
        group = QtWidgets.QGroupBox("Información de la factura")
        outer_layout = QtWidgets.QVBoxLayout(group)

        # ------------------------------------------------------
        # Barra superior del bloque
        # ------------------------------------------------------
        header_bar = QtWidgets.QHBoxLayout()

        title_label = QtWidgets.QLabel("Datos de facturación")
        title_label.setStyleSheet("font-weight: bold;")

        header_bar.addWidget(title_label)
        header_bar.addStretch()

        self.btn_editar_header = QtWidgets.QPushButton("Editar")
        self.btn_guardar_header = QtWidgets.QPushButton("Guardar")
        self.btn_cancelar_header = QtWidgets.QPushButton("Cancelar")

        self.btn_editar_header.clicked.connect(self._activar_edicion_header)
        self.btn_guardar_header.clicked.connect(self._guardar_header_factura)
        self.btn_cancelar_header.clicked.connect(self._cancelar_edicion_header)

        header_bar.addWidget(self.btn_editar_header)
        header_bar.addWidget(self.btn_guardar_header)
        header_bar.addWidget(self.btn_cancelar_header)

        outer_layout.addLayout(header_bar)

        # ------------------------------------------------------
        # Formulario
        # ------------------------------------------------------
        layout = QtWidgets.QGridLayout()
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(3, 1)

        outer_layout.addLayout(layout)

        codigo = factura.get("codigo") or "-"
        estado = factura.get("estado") or "-"
        explotacion = factura.get("explotacion", {}) or {}
        agricultor = factura.get("agricultor", {}) or {}

        row = 0

        self._add_readonly_line(
            layout,
            row,
            0,
            "Código",
            codigo
        )

        self._add_readonly_line(
            layout,
            row,
            2,
            "Estado",
            estado
        )

        row += 1

        self._add_readonly_line(
            layout,
            row,
            0,
            "Fecha emisión",
            self._format_date(factura.get("fecha_emision"))
        )

        self._add_date_edit(
            layout,
            row,
            2,
            "Fecha vencimiento",
            factura.get("fecha_vencimiento")
        )

        row += 1

        self._add_readonly_line(
            layout,
            row,
            0,
            "Explotación",
            explotacion.get("nombre") or "-"
        )

        self.cliente_razon_social_edit = self._add_editable_line(
            layout,
            row,
            2,
            "Razón social",
            factura.get("cliente_razon_social")
            or agricultor.get("nombre_completo")
            or ""
        )

        row += 1

        self.cliente_nif_edit = self._add_editable_line(
            layout,
            row,
            0,
            "DNI/NIF",
            factura.get("cliente_nif")
            or agricultor.get("dni")
            or ""
        )

        layout.addWidget(QtWidgets.QLabel("Tipo persona"), row, 2)

        self.cliente_person_type_combo = QtWidgets.QComboBox()
        self.cliente_person_type_combo.addItem("Persona física", "F")
        self.cliente_person_type_combo.addItem("Persona jurídica", "J")

        person_type = factura.get("cliente_person_type") or "F"
        index = self.cliente_person_type_combo.findData(person_type)

        if index >= 0:
            self.cliente_person_type_combo.setCurrentIndex(index)

        layout.addWidget(self.cliente_person_type_combo, row, 3)

        row += 1

        self.cliente_direccion_edit = self._add_editable_line(
            layout,
            row,
            0,
            "Dirección",
            factura.get("cliente_direccion") or "",
            colspan=3
        )

        row += 1

        self.cliente_municipio_edit = self._add_editable_line(
            layout,
            row,
            0,
            "Municipio",
            factura.get("cliente_municipio") or ""
        )

        self.cliente_provincia_edit = self._add_editable_line(
            layout,
            row,
            2,
            "Provincia",
            factura.get("cliente_provincia") or ""
        )

        row += 1

        self.cliente_codigo_postal_edit = self._add_editable_line(
            layout,
            row,
            0,
            "Código postal",
            factura.get("cliente_codigo_postal") or ""
        )

        self.cliente_pais_edit = self._add_editable_line(
            layout,
            row,
            2,
            "País",
            factura.get("cliente_pais") or "España"
        )

        row += 1

        self.cliente_email_edit = self._add_editable_line(
            layout,
            row,
            0,
            "Email",
            factura.get("cliente_email") or ""
        )

        self.cliente_telefono_edit = self._add_editable_line(
            layout,
            row,
            2,
            "Teléfono",
            factura.get("cliente_telefono") or ""
        )

        self._set_header_edit_mode(False)
        self._capture_header_original_values()

        return group

    def _add_date_edit(self, layout, row, col, label_text, value):
        label = QtWidgets.QLabel(label_text)

        self.fecha_vencimiento_edit = QtWidgets.QDateEdit()
        self.fecha_vencimiento_edit.setCalendarPopup(True)
        self.fecha_vencimiento_edit.setDisplayFormat("dd/MM/yyyy")

        date = QDate.fromString(str(value or ""), "yyyy-MM-dd")

        if date.isValid():
            self.fecha_vencimiento_edit.setDate(date)
        else:
            self.fecha_vencimiento_edit.setDate(QDate.currentDate())

        layout.addWidget(label, row, col)
        layout.addWidget(self.fecha_vencimiento_edit, row, col + 1)

        return self.fecha_vencimiento_edit

    # ==========================================================
    # MODO EDICIÓN HEADER
    # ==========================================================

    def _get_header_edit_widgets(self):
        return [
            self.fecha_vencimiento_edit,
            self.cliente_razon_social_edit,
            self.cliente_nif_edit,
            self.cliente_person_type_combo,
            self.cliente_direccion_edit,
            self.cliente_provincia_edit,
            self.cliente_municipio_edit,
            self.cliente_codigo_postal_edit,
            self.cliente_pais_edit,
            self.cliente_email_edit,
            self.cliente_telefono_edit,
        ]

    def _set_header_edit_mode(self, enabled: bool):
        self.editando_header = enabled

        for widget in self._get_header_edit_widgets():
            widget.setEnabled(enabled)

            if isinstance(widget, QtWidgets.QLineEdit):
                widget.setReadOnly(not enabled)

        self.btn_editar_header.setVisible(not enabled)
        self.btn_guardar_header.setVisible(enabled)
        self.btn_cancelar_header.setVisible(enabled)

    def _activar_edicion_header(self):
        self._capture_header_original_values()
        self._set_header_edit_mode(True)

    def _cancelar_edicion_header(self):
        self._restore_header_original_values()
        self._set_header_edit_mode(False)

    def _capture_header_original_values(self):
        self._header_original_values = {
            "fecha_vencimiento": self.fecha_vencimiento_edit.date(),
            "cliente_razon_social": self.cliente_razon_social_edit.text(),
            "cliente_nif": self.cliente_nif_edit.text(),
            "cliente_person_type": self.cliente_person_type_combo.currentData(),
            "cliente_direccion": self.cliente_direccion_edit.text(),
            "cliente_provincia": self.cliente_provincia_edit.text(),
            "cliente_municipio": self.cliente_municipio_edit.text(),
            "cliente_codigo_postal": self.cliente_codigo_postal_edit.text(),
            "cliente_pais": self.cliente_pais_edit.text(),
            "cliente_email": self.cliente_email_edit.text(),
            "cliente_telefono": self.cliente_telefono_edit.text(),
        }

    def _restore_header_original_values(self):
        values = self._header_original_values or {}

        fecha = values.get("fecha_vencimiento")
        if fecha and fecha.isValid():
            self.fecha_vencimiento_edit.setDate(fecha)

        self.cliente_razon_social_edit.setText(
            values.get("cliente_razon_social", "")
        )
        self.cliente_nif_edit.setText(
            values.get("cliente_nif", "")
        )
        self.cliente_direccion_edit.setText(
            values.get("cliente_direccion", "")
        )
        self.cliente_provincia_edit.setText(
            values.get("cliente_provincia", "")
        )
        self.cliente_municipio_edit.setText(
            values.get("cliente_municipio", "")
        )
        self.cliente_codigo_postal_edit.setText(
            values.get("cliente_codigo_postal", "")
        )
        self.cliente_pais_edit.setText(
            values.get("cliente_pais", "")
        )
        self.cliente_email_edit.setText(
            values.get("cliente_email", "")
        )
        self.cliente_telefono_edit.setText(
            values.get("cliente_telefono", "")
        )

        person_type = values.get("cliente_person_type") or "F"
        index = self.cliente_person_type_combo.findData(person_type)

        if index >= 0:
            self.cliente_person_type_combo.setCurrentIndex(index)

    # ==========================================================
    # GUARDAR ENCABEZADO
    # ==========================================================

    def _guardar_header_factura(self):
        if not self.factura_uid:
            QtWidgets.QMessageBox.warning(
                self,
                "Facturas",
                "No se pudo identificar la factura."
            )
            return

        payload = {
            "factura": {
                "fecha_vencimiento": self.fecha_vencimiento_edit.date().toString("yyyy-MM-dd"),

                "cliente_razon_social": self._line_text_or_none(
                    self.cliente_razon_social_edit
                ),
                "cliente_nif": self._line_text_or_none(
                    self.cliente_nif_edit
                ),
                "cliente_person_type": self.cliente_person_type_combo.currentData(),
                "cliente_direccion": self._line_text_or_none(
                    self.cliente_direccion_edit
                ),
                "cliente_provincia": self._line_text_or_none(
                    self.cliente_provincia_edit
                ),
                "cliente_municipio": self._line_text_or_none(
                    self.cliente_municipio_edit
                ),
                "cliente_codigo_postal": self._line_text_or_none(
                    self.cliente_codigo_postal_edit
                ),
                "cliente_pais": self._line_text_or_none(
                    self.cliente_pais_edit
                ),
                "cliente_email": self._line_text_or_none(
                    self.cliente_email_edit
                ),
                "cliente_telefono": self._line_text_or_none(
                    self.cliente_telefono_edit
                ),
            }
        }

        response = self.api.patch(
            ENDPOINT_UPDATE_FACTURA.format(uid=self.factura_uid),
            data=payload
        )

        if response:
            QtWidgets.QMessageBox.information(
                self,
                "Facturas",
                "Encabezado de factura actualizado correctamente."
            )

            self.editando_header = False
            self.load_factura_details()

        else:
            QtWidgets.QMessageBox.warning(
                self,
                "Facturas",
                "No se pudo actualizar el encabezado de la factura."
            )

    def _line_text_or_none(self, line_edit):
        if not line_edit:
            return None

        value = line_edit.text().strip()
        return value or None

    # ==========================================================
    # BLOQUE IMPORTES
    # ==========================================================

    def _build_importes_group(self, factura):
        group = QtWidgets.QGroupBox("Resumen económico")
        layout = QtWidgets.QGridLayout(group)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(3, 1)

        base_total = self._to_decimal(factura.get("base_total"))
        iva_total = self._to_decimal(factura.get("iva_total"))
        total = self._to_decimal(factura.get("total"))
        pagado_total = self._to_decimal(factura.get("pagado_total"))
        saldo_pendiente = self._to_decimal(factura.get("saldo_pendiente"))
        saldo_a_favor = self._to_decimal(factura.get("saldo_a_favor"))

        row = 0

        self._add_money_line(
            layout,
            row,
            0,
            "Base imponible",
            base_total
        )

        self._add_money_line(
            layout,
            row,
            2,
            "IVA",
            iva_total
        )

        row += 1

        self._add_money_line(
            layout,
            row,
            0,
            "Total factura",
            total,
            bold=True
        )

        self._add_money_line(
            layout,
            row,
            2,
            "Total pagado",
            pagado_total
        )

        row += 1

        pendiente_widget = self._add_money_line(
            layout,
            row,
            0,
            "Saldo pendiente",
            saldo_pendiente,
            bold=True
        )

        favor_widget = self._add_money_line(
            layout,
            row,
            2,
            "Saldo a favor",
            saldo_a_favor,
            bold=True
        )

        if saldo_pendiente > 0:
            pendiente_widget.setStyleSheet(
                "color: #b00020; font-weight: bold;"
            )
        else:
            pendiente_widget.setStyleSheet(
                "color: #2e7d32; font-weight: bold;"
            )

        if saldo_a_favor > 0:
            favor_widget.setStyleSheet(
                "color: #2e7d32; font-weight: bold;"
            )
        else:
            favor_widget.setStyleSheet(
                "font-weight: bold;"
            )

        return group

    # ==========================================================
    # BLOQUE PAGOS
    # ==========================================================

    def _build_pagos_group(self, factura):
        group = QtWidgets.QGroupBox("Pagos registrados")
        layout = QtWidgets.QVBoxLayout(group)

        pagos = factura.get("pagos") or []
        idfactura = factura.get("idfactura") or self.idfactura

        self.pagos_table = PagosTableWidget(
            idfactura=idfactura,
            parent=self,
        )

        self.pagos_table.set_items(pagos)
        self.pagos_table.table.verticalHeader().setVisible(False)
        self.pagos_table.resize_columns_to_contents()

        self.pagos_table.actionTriggered.connect(
            self._on_pago_action_triggered
        )

        if not pagos:
            empty_label = QtWidgets.QLabel(
                "No hay pagos registrados para esta factura."
            )
            empty_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(empty_label)
        else:
            layout.addWidget(self.pagos_table)

        return group

    def _on_pago_action_triggered(self, action_name, item):
        if action_name == "generar_recibo":
            if not item:
                return

            idpago = item.get("idpago")
            self._generar_recibo_pago(idpago)

    def _generar_recibo_pago(self, idpago):
        self._descargar_pdf(idpago)

    def _agregar_pago(self):
        dlg = PagosFacturaDialog(self.factura_uid, parent=self)

        if dlg.exec() == QtWidgets.QDialog.Accepted:
            self.load_factura_details()

    # ==========================================================
    # DESCARGA PDF
    # ==========================================================

    def _descargar_pdf(self, idpago):
        response = self.api.get_binary(
            ENDPOINT_PDF.format(idpago=idpago)
        )
        self._guardar_pdf(response)

    def _guardar_pdf(self, response: dict):
        if not response or not response.get("ok"):
            QtWidgets.QMessageBox.warning(
                self,
                "Facturas",
                f"No se pudo descargar el PDF.\n\nRespuesta:\n{response}"
            )
            return

        content = response.get("content")

        if not content:
            QtWidgets.QMessageBox.warning(
                self,
                "Facturas",
                "El backend no devolvió contenido PDF."
            )
            return

        filename = response.get("filename") or (
            f"recibo_pago_"
            f"{self.factura.get('codigo')}_"
            f"{QDate.currentDate().toString('yyyyMMdd')}.pdf"
        )

        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Guardar recibo PDF",
            filename,
            "PDF (*.pdf)"
        )

        if not path:
            return

        if not path.lower().endswith(".pdf"):
            path += ".pdf"

        try:
            with open(path, "wb") as f:
                f.write(content)

            QtWidgets.QMessageBox.information(
                self,
                "Facturas",
                f"Recibo guardado correctamente:\n{path}"
            )

        except Exception as ex:
            QtWidgets.QMessageBox.warning(
                self,
                "Facturas",
                f"No se pudo guardar el PDF.\n\n{ex}"
            )

    # ==========================================================
    # HELPERS UI
    # ==========================================================

    def _add_readonly_line(self, layout, row, col, label_text, value):
        label = QtWidgets.QLabel(label_text)

        line = QtWidgets.QLineEdit(str(value))
        line.setReadOnly(True)

        layout.addWidget(label, row, col)
        layout.addWidget(line, row, col + 1)

        return line

    def _add_editable_line(self, layout, row, col, label_text, value, colspan=1):
        label = QtWidgets.QLabel(label_text)

        line = QtWidgets.QLineEdit(str(value or ""))
        line.setReadOnly(True)
        line.setEnabled(False)

        layout.addWidget(label, row, col)

        if colspan > 1:
            layout.addWidget(line, row, col + 1, 1, colspan)
        else:
            layout.addWidget(line, row, col + 1)

        return line

    def _add_money_line(self, layout, row, col, label_text, value, bold=False):
        label = QtWidgets.QLabel(label_text)

        line = QtWidgets.QLineEdit(self._format_money(value))
        line.setReadOnly(True)
        line.setAlignment(Qt.AlignRight)

        if bold:
            line.setStyleSheet("font-weight: bold;")

        layout.addWidget(label, row, col)
        layout.addWidget(line, row, col + 1)

        return line

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)

            widget = item.widget()
            child_layout = item.layout()

            if widget:
                widget.deleteLater()

            if child_layout:
                self.clear_layout(child_layout)

    # ==========================================================
    # HELPERS FORMATO
    # ==========================================================

    def _to_decimal(self, value):
        if value is None or value == "":
            return Decimal("0.00")

        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError):
            return Decimal("0.00")

    def _format_money(self, value):
        value = self._to_decimal(value)
        return (
            f"{value:,.2f} €"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

    def _format_date(self, value):
        if not value:
            return "-"

        date = QDate.fromString(str(value), "yyyy-MM-dd")

        if not date.isValid():
            return str(value)

        return date.toString("dd/MM/yyyy")

    def _format_datetime(self, value):
        if not value:
            return "-"

        value = str(value)
        date_part = value.split("T")[0]

        return self._format_date(date_part)