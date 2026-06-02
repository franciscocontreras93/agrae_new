import time

from qgis.PyQt import QtWidgets
from qgis.PyQt.QtCore import Qt

from ...core.api import APIRequest
from ...gui.components.searchTableWidget import FacturasSearchTable

from . import PagosFacturaDialog, DetalleFacturaDialog


class FacturasConsultaDialog(QtWidgets.QDialog):
    """
    Consulta y gestión básica de facturas.
    Puede abrirse general o filtrada por explotación.
    """

    ENDPOINT_LIST = "/billing/facturas"
    ENDPOINT_DETAIL = "/billing/facturas/{uid}"
    ENDPOINT_PDF = "/billing/facturas/{uid}/pdf"
    ENDPOINT_XML = "/billing/facturas/{uid}/xml"
    ENDPOINT_EMITIR = "/billing/facturas/{uid}/emitir"
    ENDPOINT_CSV = "/billing/facturas/resumen/csv"

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


        self.combo_estado.currentIndexChanged.connect(self._buscar)

        # self.spin_idagricultor = QtWidgets.QSpinBox()
        # self.spin_idagricultor.setMinimum(0)
        # self.spin_idagricultor.setMaximum(999999999)
        # self.spin_idagricultor.setSpecialValueText("Todos")

        # self.btn_buscar = QtWidgets.QPushButton("Buscar")
        # self.btn_limpiar = QtWidgets.QPushButton("Limpiar")

        layout.addWidget(QtWidgets.QLabel("Estado:"), 0, 0)
        layout.addWidget(self.combo_estado, 0, 1)
        # layout.addWidget(QtWidgets.QLabel("Agricultor payer:"), 0, 2)
        # layout.addWidget(self.spin_idagricultor, 0, 3)
        # layout.addWidget(self.btn_buscar, 0, 4)
        # layout.addWidget(self.btn_limpiar, 0, 5)
        layout.setColumnStretch(6, 1)

        return gb

    def _actions_layout(self):
        layout = QtWidgets.QHBoxLayout()

        self.btn_ver_detalle = QtWidgets.QPushButton("Ver detalle")
        self.btn_ver_detalle.setToolTip("Ver el detalle de la factura seleccionada")
        self.btn_descargar_pdf = QtWidgets.QPushButton("Descargar PDF")
        self.btn_descargar_pdf.setToolTip("Descargar la factura en formato PDF")
        self.btn_descargar_xml = QtWidgets.QPushButton("Descargar XML")
        self.btn_descargar_xml.setToolTip("Descargar la factura en formato XML")
        self.btn_facturas_csv = QtWidgets.QPushButton("Descargar CSV")
        self.btn_facturas_csv.setToolTip("Descargar las facturas en formato CSV")

        self.btn_emitir = QtWidgets.QPushButton("Emitir factura")
        self.btn_emitir.setToolTip("Emitir la factura seleccionada (si no está emitida)")
        self.btn_anular = QtWidgets.QPushButton("Anular factura")
        self.btn_anular.setToolTip("Anular la factura seleccionada (si no está anulada)")

        self.btn_pagar = QtWidgets.QPushButton("Registrar pago")
        self.btn_pagar.setToolTip("Registrar el pago de la factura seleccionada")

        self.btn_cargar_pagos = QtWidgets.QPushButton("Cargar pagos")
        self.btn_cargar_pagos.setToolTip("Cargar pagos desde el banco y asociarlos a las facturas")

        self.btn_refrescar = QtWidgets.QPushButton("Refrescar")
        self.btn_cerrar = QtWidgets.QPushButton("Cerrar")

        layout.addWidget(self.btn_ver_detalle)
        layout.addWidget(self.btn_descargar_pdf)
        layout.addWidget(self.btn_descargar_xml)
        layout.addWidget(self.btn_facturas_csv)
        layout.addStretch()
        layout.addWidget(self.btn_emitir)
        layout.addWidget(self.btn_anular)
        layout.addWidget(self.btn_refrescar)
        layout.addStretch()
        layout.addWidget(self.btn_cargar_pagos)
        layout.addWidget(self.btn_cerrar)

        return layout

    # ------------------------------------------------------------------
    # Signals
    # ------------------------------------------------------------------

    def _connect_signals(self):
        self.btn_cerrar.clicked.connect(self.reject)
        # self.btn_buscar.clicked.connect(self._buscar)
        # self.btn_limpiar.clicked.connect(self._limpiar_filtros)
        self.btn_refrescar.clicked.connect(self._buscar)

        self.btn_ver_detalle.clicked.connect(self._ver_detalle)
        self.btn_descargar_pdf.clicked.connect(self._descargar_pdf)
        self.btn_descargar_xml.clicked.connect(self._descargar_xml)
        self.btn_facturas_csv.clicked.connect(self._descargar_csv)
        self.btn_emitir.clicked.connect(self._emitir_factura)
        self.btn_anular.clicked.connect(self._anular_factura)
        self.btn_cargar_pagos.clicked.connect(self._cargar_pagos) 

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

        return params

    def _buscar(self):
        self.facturas_table.reload(params=self._build_params())

    

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

        dlg = DetalleFacturaDialog(factura, parent=self)
        dlg.exec()

    def _descargar_pdf(self):
        factura = self._selected()
        if not factura:
            return

        uid = self._uid(factura)
        if not uid:
            QtWidgets.QMessageBox.warning(self, "Facturas", f"La factura seleccionada no tiene UID.\n\n{factura}")
            return

        response = self.api.get_binary(self.ENDPOINT_PDF.format(uid=uid))
        self._guardar_pdf(response)

    def _descargar_xml(self):
        factura = self._selected()
        if not factura:
            return
        uid = self._uid(factura)
        if not uid:
            QtWidgets.QMessageBox.warning(self, "Facturas", f"La factura seleccionada no tiene UID.\n\n{factura}")
            return
        response = self.api.get_binary(self.ENDPOINT_XML.format(uid=uid))
        if not response or not response.get("ok"):
            QtWidgets.QMessageBox.warning(
                self,
                "Facturas",
                f"No se pudo descargar el XML.\n\nRespuesta:\n{response}"
            )
            return
        self._guardar_xml(response)

    def _descargar_csv(self):
       
        
        response = self.api.get_binary(self.ENDPOINT_CSV, headers={"Accept": "text/csv"})
        self._guardar_csv(response)
        
        # QtWidgets.QMessageBox.information(self, "Facturas", f"Guardando facturas en:\n{path}")
        
    
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

    def _anular_factura(self):
        factura = self._selected()
        if not factura:
            return

        uid = self._uid(factura)
        estado = str(self._estado(factura) or "").upper()

        if not uid:
            QtWidgets.QMessageBox.warning(self, "Facturas", f"La factura seleccionada no tiene UID.\n\n{factura}")
            return
        if estado == "PAGADA":
            QtWidgets.QMessageBox.information(self, "Facturas", "La factura seleccionada está pagada y no se puede anular.")
            return
        
        if estado == "ANULADA":
            QtWidgets.QMessageBox.information(self, "Facturas", "La factura seleccionada ya está anulada.")
            return

        password = QtWidgets.QInputDialog.getText(
            self,"Anular factura", "Introduce tu contraseña para confirmar la anulación:", QtWidgets.QLineEdit.Password)
        if not password or not password[0]:
            QtWidgets.QMessageBox.warning(self, "Anular factura", "La anulación de la factura requiere una contraseña.")
            return
    

        confirm = QtWidgets.QMessageBox.question(
            self,
            "Anular factura",
            "¿Confirma que desea anular la factura seleccionada?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        if confirm != QtWidgets.QMessageBox.Yes:
            return
        response = self.api.post(f"/billing/facturas/{uid}/anular")
        # response = self.api.post(f"/billing/facturas/{uid}/anular", data={"password": password[0]})
        if not response or response.get("status") == "error":
            QtWidgets.QMessageBox.warning(
                self,
                "Facturas",
                f"No se pudo anular la factura.\n\nRespuesta:\n{response}"
            )
            return
        QtWidgets.QMessageBox.information(self, "Facturas", "Factura anulada correctamente.")
        self._buscar()
    


    def _cargar_pagos(self):
        dlg = QtWidgets.QFileDialog(self)
        dlg.setWindowTitle("Seleccionar archivo de pagos")
        dlg.setNameFilter("Archivos CSV (*.csv)")
        dlg.setFileMode(QtWidgets.QFileDialog.ExistingFile)
        if dlg.exec() != QtWidgets.QDialog.Accepted:
            return
        file_path = dlg.selectedFiles()[0]
        r = self.api.post_file("/billing/facturas/pagar/by_csv", file_path)
        if not r or r.get("status") == "error":
            QtWidgets.QMessageBox.warning(
                self,
                "Cargar pagos",
                f"No se pudieron cargar los pagos.\n\nRespuesta:\n{r}"
            )
            return
        QtWidgets.QMessageBox.information(
            self,
            "Cargar pagos",
            f"Pagos cargados correctamente.\n\nRespuesta:\n{r}"
        )

    def _pagar_factura(self):
        factura = self._selected()
        if not factura:
            return

        uid = self._uid(factura)
        estado = str(self._estado(factura) or "").upper()

        if not uid:
            QtWidgets.QMessageBox.warning(self, "Facturas", f"La factura seleccionada no tiene UID.\n\n{factura}")
            return
        if estado == "PAGADA":
            QtWidgets.QMessageBox.information(self, "Facturas", "La factura seleccionada ya está pagada.")
            return
        if estado != "EMITIDA":
            QtWidgets.QMessageBox.information(self, "Facturas", "Solo las facturas emitidas pueden ser pagadas.")
            return

        self._pagar_factura_dialog(factura)
    
    # ------------------------------------------------------------------
    # Dialogs
    # ------------------------------------------------------------------

    def _pagar_factura_dialog(self, factura: dict):
        dialog = PagosFacturaDialog(factura, parent=self)
        dialog.exec()
        self._buscar()  # Refrescar la lista de facturas después de cerrar el diálogo de pagos
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

    def _guardar_csv(self, response: dict):
            if not response or not response.get("ok"):
                QtWidgets.QMessageBox.warning(
                    self,
                    "Facturas",
                    f"No se pudo descargar el CSV.\n\nRespuesta:\n{response}"
                )
                return
            content = response.get("content")
            if not content:
                QtWidgets.QMessageBox.warning(self, "Facturas", "El backend no devolvió contenido CSV.")
                return
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"facturas_{timestamp}.csv"
            path, _ = QtWidgets.QFileDialog.getSaveFileName(self,"Guardar facturas CSV",filename,"CSV (*.csv)") 
            if not path:
                return
            if not path.lower().endswith(".csv"):
                path += ".csv"
            try:
                with open(path, "wb") as f:
                    f.write(content)
                QtWidgets.QMessageBox.information(self,"Facturas",f"Facturas guardadas correctamente:\n{path}")
            except Exception as ex:
                QtWidgets.QMessageBox.warning(self,"Facturas",f"No se pudo guardar el CSV.\n\n{ex}")
                return

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

    def _guardar_xml(self, response: dict):
        if not response or not response.get("ok"):
            QtWidgets.QMessageBox.warning(
                self,
                "Facturas",
                f"No se pudo descargar el XML.\n\nRespuesta:\n{response}"
            )
            return
        content = response.get("content")
        if not content:
            QtWidgets.QMessageBox.warning(self, "Facturas", "El backend no devolvió contenido XML.")
            return
        filename = self._filename_from_headers(response.get("headers", {}) or {}).replace(".pdf", "")
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self,"Guardar factura XML",filename,"XML (*.xml)") 
        if not path:
            return
        if not path.lower().endswith(".xml"):
            path += ".xml"
        try:
            with open(path, "wb") as f:
                f.write(content)
            QtWidgets.QMessageBox.information(self,"Facturas",f"Factura guardada correctamente:\n{path}")
        except Exception as ex:
            QtWidgets.QMessageBox.warning(self,"Facturas",f"No se pudo guardar el XML.\n\n{ex}")


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