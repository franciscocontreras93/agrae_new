from decimal import Decimal, InvalidOperation

from qgis.PyQt import QtWidgets
from qgis.PyQt.QtCore import Qt, QDate

from ...core.api import APIRequest

from . import PagosFacturaDialog

from ...gui.components.CustomTableWidget import PagosTableWidget

ENDPOINT_DETAIL_FACTURA = "/billing/facturas/{uid}"
ENDPOINT_PDF = "/billing/facturas/recibo_pagos/pdf/{idpago}"




class DetalleFacturaDialog(QtWidgets.QDialog):


    def __init__(self, factura: dict, parent=None):
        super().__init__(parent)

        self.factura = factura
        self.factura_uid = factura.get("uid")
        self.idfactura = factura.get("idfactura")

        self.api = APIRequest()

        self.setWindowTitle("Detalle de factura")
        self.resize(850, 620)

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setSpacing(12)

        self.load_factura_details()

    def load_factura_details(self):
        response = self.api.get(ENDPOINT_DETAIL_FACTURA.format(uid=self.factura_uid))

        if response:
            factura_data = response

            self.factura = factura_data
            self.idfactura = factura_data.get("idfactura") or self.idfactura

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

    def _build_factura_group(self, factura):
        group = QtWidgets.QGroupBox("Información de la factura")
        layout = QtWidgets.QGridLayout(group)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(3, 1)

        codigo = factura.get("codigo") or "-"
        estado = factura.get("estado") or "-"
        explotacion = factura.get("explotacion", {})
        agricultor = factura.get("agricultor", {})

        row = 0
        self._add_readonly_line(layout, row, 0, "Código", codigo)
        self._add_readonly_line(layout, row, 2, "Estado", estado)

        row += 1
        self._add_readonly_line(
            layout, row, 0, "Fecha emisión",
            self._format_date(factura.get("fecha_emision"))
        )
        self._add_readonly_line(
            layout, row, 2, "Fecha vencimiento",
            self._format_date(factura.get("fecha_vencimiento"))
        )

        row += 1
        self._add_readonly_line(
            layout, row, 0, "Explotación",
            explotacion.get("nombre") or "-"
        )
        self._add_readonly_line(
            layout, row, 2, "ID explotación",
            str(explotacion.get("idexplotacion") or "-")
        )

        row += 1
        self._add_readonly_line(
            layout, row, 0, "Agricultor",
            agricultor.get("nombre_completo") or "-"
        )
        self._add_readonly_line(
            layout, row, 2, "DNI/NIF",
            agricultor.get("dni") or "-"
        )

        return group

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
        self._add_money_line(layout, row, 0, "Base imponible", base_total)
        self._add_money_line(layout, row, 2, "IVA", iva_total)

        row += 1
        self._add_money_line(layout, row, 0, "Total factura", total, bold=True)
        self._add_money_line(layout, row, 2, "Total pagado", pagado_total)

        row += 1
        pendiente_widget = self._add_money_line(
            layout, row, 0, "Saldo pendiente", saldo_pendiente, bold=True
        )

        favor_widget = self._add_money_line(
            layout, row, 2, "Saldo a favor", saldo_a_favor, bold=True
        )

        if saldo_pendiente > 0:
            pendiente_widget.setStyleSheet("color: #b00020; font-weight: bold;")
        else:
            pendiente_widget.setStyleSheet("color: #2e7d32; font-weight: bold;")

        if saldo_a_favor > 0:
            favor_widget.setStyleSheet("color: #2e7d32; font-weight: bold;")
        else:
            favor_widget.setStyleSheet("font-weight: bold;")

        return group

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

        self.pagos_table.actionTriggered.connect(self._on_pago_action_triggered)

        if not pagos:
            empty_label = QtWidgets.QLabel("No hay pagos registrados para esta factura.")
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
        # print(f"Generando recibo para el pago ID: {idpago}")
        # luego aquí puedes llamar a:
        self._descargar_pdf(idpago)

    def _agregar_pago(self):
        dlg = PagosFacturaDialog(self.factura_uid, parent=self)

        if dlg.exec() == QtWidgets.QDialog.Accepted:
            self.load_factura_details()

    def _descargar_pdf(self, idpago):
        response = self.api.get_binary(ENDPOINT_PDF.format(idpago=idpago))
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

        filename = response.get("filename") or f"recibo_pago_{self.factura.get('codigo')}_{QDate.currentDate().toString('yyyyMMdd')}.pdf"

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

    def _add_readonly_line(self, layout, row, col, label_text, value):
        label = QtWidgets.QLabel(label_text)

        line = QtWidgets.QLineEdit(str(value))
        line.setReadOnly(True)

        layout.addWidget(label, row, col)
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

    def _to_decimal(self, value):
        if value is None or value == "":
            return Decimal("0.00")

        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError):
            return Decimal("0.00")

    def _format_money(self, value):
        value = self._to_decimal(value)
        return f"{value:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")

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