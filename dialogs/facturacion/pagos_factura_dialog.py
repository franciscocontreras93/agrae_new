# -*- coding: utf-8 -*-

from decimal import Decimal

from qgis.PyQt import QtWidgets
from qgis.PyQt.QtCore import QDate

from ...core.api import APIRequest


class PagosFacturaDialog(QtWidgets.QDialog):

    METODOS_PAGO = [
        ("Transferencia", "TRANSFERENCIA"),
        ("Domiciliación SEPA", "DOMICILIACION_SEPA"),
        ("Efectivo", "EFECTIVO"),
    ]

    def __init__(self, factura: dict, parent=None):
        super().__init__(parent)

        self.factura = factura or {}
        self.api = APIRequest()

        self.total_factura = self._to_decimal(self.factura.get("total", 0))
        self.saldo_pendiente = self._to_decimal(self.factura.get("saldo_pendiente", 0))

        self.setWindowTitle("Registrar pago de factura")
        self.resize(760, 460)

        self._build_ui()
        self._load_factura_data()
        self._connect_signals()
        self._actualizar_saldo_visual()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)

        factura_group = QtWidgets.QGroupBox("Detalle de la factura")
        factura_layout = QtWidgets.QGridLayout(factura_group)

        self.lbl_codigo = QtWidgets.QLabel()
        self.lbl_estado = QtWidgets.QLabel()
        self.lbl_fecha_emision = QtWidgets.QLabel()
        self.lbl_fecha_vencimiento = QtWidgets.QLabel()
        self.lbl_total = QtWidgets.QLabel()

        self.lbl_saldo = QtWidgets.QLabel()


        factura_layout.addWidget(QtWidgets.QLabel("Código:"), 0, 0)
        factura_layout.addWidget(self.lbl_codigo, 0, 1)

        factura_layout.addWidget(QtWidgets.QLabel("Estado:"), 0, 2)
        factura_layout.addWidget(self.lbl_estado, 0, 3)

        factura_layout.addWidget(QtWidgets.QLabel("Fecha emisión:"), 1, 0)
        factura_layout.addWidget(self.lbl_fecha_emision, 1, 1)

        factura_layout.addWidget(QtWidgets.QLabel("Fecha vencimiento:"), 1, 2)
        factura_layout.addWidget(self.lbl_fecha_vencimiento, 1, 3)

        factura_layout.addWidget(QtWidgets.QLabel("Total factura:"), 2, 0)
        factura_layout.addWidget(self.lbl_total, 2, 1)

        factura_layout.addWidget(QtWidgets.QLabel("Saldo pendiente:"), 2, 2)
        factura_layout.addWidget(self.lbl_saldo, 2, 3)

        main_layout.addWidget(factura_group)

        pago_group = QtWidgets.QGroupBox("Registrar pago")
        pago_layout = QtWidgets.QGridLayout(pago_group)

        self.input_importe = QtWidgets.QDoubleSpinBox()
        self.input_importe.setDecimals(2)
        self.input_importe.setMinimum(0.00)
        self.input_importe.setMaximum(999999999.99)
        self.input_importe.setSingleStep(0.01)
        self.input_importe.setValue(0.00)
        self.input_importe.setSuffix(" €")
        self.input_importe.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.input_importe.setKeyboardTracking(True)

        self.input_saldo = QtWidgets.QLineEdit()
        self.input_saldo.setReadOnly(True)

        self.combo_metodo = QtWidgets.QComboBox()
        for label, value in self.METODOS_PAGO:
            self.combo_metodo.addItem(label, value)

        self.input_fecha_pago = QtWidgets.QDateEdit()
        self.input_fecha_pago.setCalendarPopup(True)
        self.input_fecha_pago.setDate(QDate.currentDate())
        self.input_fecha_pago.setDisplayFormat("yyyy-MM-dd")

        self.input_referencia = QtWidgets.QLineEdit()
        self.input_referencia.setPlaceholderText("Referencia bancaria, recibo, etc.")

        self.input_observaciones = QtWidgets.QPlainTextEdit()
        self.input_observaciones.setPlaceholderText("Observaciones del pago...")
        self.input_observaciones.setFixedHeight(90)

        pago_layout.addWidget(QtWidgets.QLabel("Importe pagado:"), 0, 0)
        pago_layout.addWidget(self.input_importe, 0, 1)

        pago_layout.addWidget(QtWidgets.QLabel("Saldo:"), 0, 2)
        pago_layout.addWidget(self.input_saldo, 0, 3)

        pago_layout.addWidget(QtWidgets.QLabel("Método de pago:"), 1, 0)
        pago_layout.addWidget(self.combo_metodo, 1, 1)

        pago_layout.addWidget(QtWidgets.QLabel("Fecha pago:"), 1, 2)
        pago_layout.addWidget(self.input_fecha_pago, 1, 3)

        pago_layout.addWidget(QtWidgets.QLabel("Referencia:"), 2, 0)
        pago_layout.addWidget(self.input_referencia, 2, 1, 1, 3)

        pago_layout.addWidget(QtWidgets.QLabel("Observaciones:"), 3, 0)
        pago_layout.addWidget(self.input_observaciones, 3, 1, 1, 3)

        main_layout.addWidget(pago_group)

        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.addStretch()

        self.btn_cancelar = QtWidgets.QPushButton("Cancelar")
        self.btn_guardar = QtWidgets.QPushButton("Registrar pago")

        self.btn_cancelar.clicked.connect(self.reject)
        self.btn_guardar.clicked.connect(self.registrar_pago)

        btn_layout.addWidget(self.btn_cancelar)
        btn_layout.addWidget(self.btn_guardar)

        main_layout.addLayout(btn_layout)

    def _connect_signals(self):
        self.input_importe.valueChanged.connect(self._actualizar_saldo_visual)

    # ------------------------------------------------------------------
    # DATOS
    # ------------------------------------------------------------------

    def _load_factura_data(self):
        self.lbl_codigo.setText(str(self.factura.get("codigo", "")))
        self.lbl_estado.setText(str(self.factura.get("estado", "")))
        self.lbl_fecha_emision.setText(str(self.factura.get("fecha_emision", "")))
        self.lbl_fecha_vencimiento.setText(str(self.factura.get("fecha_vencimiento", "")))
        self.lbl_total.setText(self._money(self.total_factura))
        self.lbl_saldo.setText(self._money(self.saldo_pendiente))

    # ------------------------------------------------------------------
    # SALDO VISUAL
    # ------------------------------------------------------------------

    def _actualizar_saldo_visual(self):
        importe = self._importe_actual()
        saldo = self.saldo_pendiente - importe

        if saldo > 0:
            self.input_saldo.setText(self._money(saldo))
            self.input_saldo.setStyleSheet(
                "color: red; font-weight: bold;"
            )

        elif saldo == 0:
            self.input_saldo.setText("0,00 €")
            self.input_saldo.setStyleSheet(
                "color: green; font-weight: bold;"
            )

        else:
            self.input_saldo.setText(f"+ {self._money(abs(saldo))}")
            self.input_saldo.setStyleSheet(
                "color: green; font-weight: bold;"
            )

    def _importe_actual(self) -> Decimal:
        return self._to_decimal(self.input_importe.value())

    # ------------------------------------------------------------------
    # PAYLOAD
    # ------------------------------------------------------------------

    def _build_payload(self) -> dict:
        uid = self.factura.get("uid")

        if not uid:
            raise ValueError("La factura no tiene UID.")

        importe = self._importe_actual()

        if importe <= 0:
            raise ValueError("El importe debe ser mayor que cero.")

        return {
            "uid": str(uid),
            "importe": float(importe),
            "metodo_pago": self.combo_metodo.currentData(),
            "fecha_pago": self.input_fecha_pago.date().toString("yyyy-MM-dd"),
            "referencia": self.input_referencia.text().strip() or None,
            "observaciones": self.input_observaciones.toPlainText().strip() or None,
        }

    # ------------------------------------------------------------------
    # ACCIONES
    # ------------------------------------------------------------------

    def registrar_pago(self):
        try:
            payload = self._build_payload()
        except ValueError as e:
            QtWidgets.QMessageBox.warning(
                self,
                "Validación del pago",
                str(e)
            )
            return

        saldo = self.saldo_pendiente - self._to_decimal(payload["importe"])

        if saldo < 0:
            msg_saldo = f"Saldo a favor: + {self._money(abs(saldo))}"
        elif saldo > 0:
            msg_saldo = f"Saldo pendiente: {self._money(saldo)}"
        else:
            msg_saldo = "Factura saldada completamente."

        confirm = QtWidgets.QMessageBox.question(
            self,
            "Confirmar pago",
            (
                "¿Deseas registrar este pago?\n\n"
                f"Importe: {self._money(payload['importe'])}\n"
                f"Método: {payload['metodo_pago']}\n"
                f"Fecha: {payload['fecha_pago']}\n"
                f"{msg_saldo}"
            ),
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No,
        )

        if confirm != QtWidgets.QMessageBox.Yes:
            return

        try:
            self.btn_guardar.setEnabled(False)

            self.api.post(
                "/billing/facturas/pagar",
                data=payload,
            )

            QtWidgets.QMessageBox.information(
                self,
                "Pago registrado",
                "El pago se ha registrado correctamente."
            )

            self.accept()

        except Exception as e:
            self.btn_guardar.setEnabled(True)

            QtWidgets.QMessageBox.critical(
                self,
                "Error al registrar pago",
                str(e)
            )

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------

    def _to_decimal(self, value) -> Decimal:
        if value in (None, ""):
            return Decimal("0.00")

        try:
            return Decimal(str(value)).quantize(Decimal("0.01"))
        except Exception:
            return Decimal("0.00")

    def _money(self, value) -> str:
        value = self._to_decimal(value)
        txt = f"{value:,.2f}"
        txt = txt.replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{txt} €"