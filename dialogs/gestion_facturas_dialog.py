from qgis.PyQt import QtWidgets
from qgis.PyQt.QtCore import Qt

from ..core.api import APIRequest
from ..gui.components.searchTableWidget import FacturasSearchTable


class FacturasConsultaDialog(QtWidgets.QDialog):
    """
    Consulta y gestión básica de facturas.
    Puede abrirse general o filtrada por explotación.
    """

    ENDPOINT_LIST = "/billing/facturas"
    ENDPOINT_DETAIL = "/billing/facturas/{uid}"
    ENDPOINT_PDF = "/billing/facturas/{uid}/pdf"
    ENDPOINT_EMITIR = "/billing/facturas/{uid}/emitir"

    def __init__(self, idexplotacion: int | None = None, parent=None):
        super().__init__(parent)

        self.idexplotacion = idexplotacion
        self.api = APIRequest()

        self.setWindowTitle("aGrae | Consulta de facturas")
        self.resize(950, 580)

        self._build_ui()
        self._connect_signals()
        self._buscar()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        main = QtWidgets.QVBoxLayout(self)
        main.setContentsMargins(10, 10, 10, 10)
        main.setSpacing(8)

        main.addLayout(self._header_layout())
        main.addWidget(self._filters_group())

        self.facturas_table = FacturasSearchTable(parent=self)
        # self.facturas_table.endpoint = self.ENDPOINT_LIST
        main.addWidget(self.facturas_table)

        main.addLayout(self._actions_layout())

    def _header_layout(self):
        layout = QtWidgets.QHBoxLayout()

        title = QtWidgets.QLabel("Consulta de facturas")
        font = title.font()
        font.setPointSize(12)
        font.setBold(True)
        title.setFont(font)

        scope = f"Explotación ID: {self.idexplotacion}" if self.idexplotacion else "Todas las explotaciones"
        self.lbl_scope = QtWidgets.QLabel(scope)
        self.lbl_scope.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(self.lbl_scope)

        return layout

    def _filters_group(self):
        gb = QtWidgets.QGroupBox("Filtros")
        layout = QtWidgets.QGridLayout(gb)
        layout.setContentsMargins(10, 12, 10, 10)
        layout.setHorizontalSpacing(8)

        self.combo_estado = QtWidgets.QComboBox()
        self.combo_estado.addItem("Todas", None)
        self.combo_estado.addItem("Borrador", "BORRADOR")
        self.combo_estado.addItem("Emitida", "EMITIDA")
        self.combo_estado.addItem("Pagada", "PAGADA")
        self.combo_estado.addItem("Anulada", "ANULADA")

        self.spin_idagricultor = QtWidgets.QSpinBox()
        self.spin_idagricultor.setMinimum(0)
        self.spin_idagricultor.setMaximum(999999999)
        self.spin_idagricultor.setSpecialValueText("Todos")

        self.btn_buscar = QtWidgets.QPushButton("Buscar")
        self.btn_limpiar = QtWidgets.QPushButton("Limpiar")

        layout.addWidget(QtWidgets.QLabel("Estado:"), 0, 0)
        layout.addWidget(self.combo_estado, 0, 1)
        layout.addWidget(QtWidgets.QLabel("Agricultor payer:"), 0, 2)
        layout.addWidget(self.spin_idagricultor, 0, 3)
        layout.addWidget(self.btn_buscar, 0, 4)
        layout.addWidget(self.btn_limpiar, 0, 5)
        layout.setColumnStretch(6, 1)

        return gb

    def _actions_layout(self):
        layout = QtWidgets.QHBoxLayout()

        self.btn_ver_detalle = QtWidgets.QPushButton("Ver detalle")
        self.btn_descargar_pdf = QtWidgets.QPushButton("Descargar PDF")
        self.btn_emitir = QtWidgets.QPushButton("Emitir factura")
        self.btn_refrescar = QtWidgets.QPushButton("Refrescar")
        self.btn_cerrar = QtWidgets.QPushButton("Cerrar")

        layout.addWidget(self.btn_ver_detalle)
        layout.addWidget(self.btn_descargar_pdf)
        layout.addWidget(self.btn_emitir)
        layout.addWidget(self.btn_refrescar)
        layout.addStretch()
        layout.addWidget(self.btn_cerrar)

        return layout

    # ------------------------------------------------------------------
    # Signals
    # ------------------------------------------------------------------

    def _connect_signals(self):
        self.btn_cerrar.clicked.connect(self.reject)
        self.btn_buscar.clicked.connect(self._buscar)
        self.btn_limpiar.clicked.connect(self._limpiar_filtros)
        self.btn_refrescar.clicked.connect(self._buscar)

        self.btn_ver_detalle.clicked.connect(self._ver_detalle)
        self.btn_descargar_pdf.clicked.connect(self._descargar_pdf)
        self.btn_emitir.clicked.connect(self._emitir_factura)

    # ------------------------------------------------------------------
    # Filtros y carga
    # ------------------------------------------------------------------

    def _build_params(self) -> dict:
        params = {}

        if self.idexplotacion:
            params["idexplotacion"] = self.idexplotacion

        estado = self.combo_estado.currentData()
        if estado:
            params["estado"] = estado

        idagricultor = self.spin_idagricultor.value()
        if idagricultor > 0:
            params["idagricultor_payer"] = idagricultor

        return params

    def _buscar(self):
        self.facturas_table.reload(params=self._build_params())

    def _limpiar_filtros(self):
        self.combo_estado.setCurrentIndex(0)
        self.spin_idagricultor.setValue(0)
        self._buscar()

    # ------------------------------------------------------------------
    # Selección
    # ------------------------------------------------------------------

    def _selected(self) -> dict | None:
        factura = self.facturas_table.selected_item()

        if not factura:
            QtWidgets.QMessageBox.warning(self, "Facturas", "Selecciona una factura.")
            return None

        return factura

    def _value(self, factura: dict, *keys):
        for key in keys:
            if key in factura:
                return factura.get(key)
        return None

    def _uid(self, factura: dict):
        return self._value(factura, "uid")

    def _idfactura(self, factura: dict):
        return self._value(factura, "idfactura", "id")

    def _estado(self, factura: dict):
        return self._value(factura, "estado")

    # ------------------------------------------------------------------
    # Acciones
    # ------------------------------------------------------------------

    def _ver_detalle(self):
        factura = self._selected()
        if not factura:
            return

        uid = self._uid(factura)
        if not uid:
            QtWidgets.QMessageBox.warning(self, "Facturas", f"La factura seleccionada no tiene UID.\n\n{factura}")
            return

        response = self.api.get(self.ENDPOINT_DETAIL.format(uid=uid))

        if not response:
            QtWidgets.QMessageBox.warning(self, "Facturas", "No se pudo obtener el detalle de la factura.")
            return

        self._show_detalle(response)

    def _descargar_pdf(self):
        factura = self._selected()
        if not factura:
            return

        idfactura = self._uid(factura)
        if not idfactura:
            QtWidgets.QMessageBox.warning(self, "Facturas", f"La factura seleccionada no tiene idfactura.\n\n{factura}")
            return

        response = self.api.get_binary(self.ENDPOINT_PDF.format(idfactura=idfactura))
        self._guardar_pdf(response)

    def _emitir_factura(self):
        factura = self._selected()
        if not factura:
            return

        uid = self._uid(factura)
        estado = str(self._estado(factura) or "").upper()

        if not uid:
            QtWidgets.QMessageBox.warning(self, "Facturas", f"La factura seleccionada no tiene UID.\n\n{factura}")
            return

        if estado == "EMITIDA":
            QtWidgets.QMessageBox.information(self, "Facturas", "La factura seleccionada ya está emitida.")
            return

        confirm = QtWidgets.QMessageBox.question(
            self,
            "Emitir factura",
            "¿Confirma que desea emitir la factura seleccionada?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )

        if confirm != QtWidgets.QMessageBox.Yes:
            return

        response = self.api.post(self.ENDPOINT_EMITIR.format(uid=uid))

        if not response or response.get("status") == "error":
            QtWidgets.QMessageBox.warning(
                self,
                "Facturas",
                f"No se pudo emitir la factura.\n\nRespuesta:\n{response}"
            )
            return

        QtWidgets.QMessageBox.information(self, "Facturas", "Factura emitida correctamente.")
        self._buscar()

    # ------------------------------------------------------------------
    # Detalle
    # ------------------------------------------------------------------

    def _show_detalle(self, factura: dict):
        lines = [
            f"Número: {factura.get('codigo') or factura.get('numero') or '-'}",
            f"Estado: {factura.get('estado') or '-'}",
            f"Fecha emisión: {factura.get('fecha_emision') or '-'}",
            f"Fecha vencimiento: {factura.get('fecha_vencimiento') or '-'}",
            f"Total: {factura.get('total') or factura.get('total_factura') or '-'}",
        ]

        QtWidgets.QMessageBox.information(self, "Detalle factura", "\n".join(lines))

    # ------------------------------------------------------------------
    # PDF
    # ------------------------------------------------------------------

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
            QtWidgets.QMessageBox.warning(self, "Facturas", "El backend no devolvió contenido PDF.")
            return

        filename = self._filename_from_headers(response.get("headers", {}) or {})

        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Guardar factura PDF",
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
                f"Factura guardada correctamente:\n{path}"
            )

        except Exception as ex:
            QtWidgets.QMessageBox.warning(
                self,
                "Facturas",
                f"No se pudo guardar el PDF.\n\n{ex}"
            )

    def _filename_from_headers(self, headers: dict) -> str:
        disposition = ""

        for key, value in headers.items():
            if key.lower() == "content-disposition":
                disposition = value or ""
                break

        if "filename=" in disposition:
            filename = disposition.split("filename=")[-1].strip().strip('"').strip("'")
            return filename if filename.lower().endswith(".pdf") else f"{filename}.pdf"

        return "factura.pdf"