from decimal import Decimal, InvalidOperation

from qgis.PyQt import QtWidgets, QtCore
from qgis.PyQt.QtCore import Qt

from ..gui.components.CustomComboBox import SeriesComboBox
from ..gui.components.CustomTreeWidget import FacturacionTreePanel

from ..core.api import APIRequest


class FacturacionDialog(QtWidgets.QDialog):
    IVA_DEFAULT = Decimal("21.00")

    def __init__(self, idexplotacion: int, parent=None):
        super().__init__(parent)

        self.idexplotacion = idexplotacion
        self.api = APIRequest()

        self.datos_contrato = {}

        self.setWindowTitle("Facturación")
        self.resize(980, 640)
        self.setModal(True)


        self._get_contrato_data()

        self._setup_ui()
        self._connect_signals()

        self._init_state()
        self._load_initial_data()
    
    # ============================
    # CONFIGURACION DE LA API INICIAL
    # ============================

    

    def _setup_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # ===== Cabecera =====
        header_layout = QtWidgets.QHBoxLayout()

        self.lbl_title = QtWidgets.QLabel("Gestión de Facturación")
        title_font = self.lbl_title.font()
        title_font.setPointSize(12)
        title_font.setBold(True)
        self.lbl_title.setFont(title_font)

        self.lbl_explotacion = QtWidgets.QLabel(f"Explotación ID: {self.idexplotacion}")
        self.lbl_explotacion.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        header_layout.addWidget(self.lbl_title)
        header_layout.addStretch()
        header_layout.addWidget(self.lbl_explotacion)

        main_layout.addLayout(header_layout)

        # ===== Datos de facturación =====
        gb_info = QtWidgets.QGroupBox("Datos de facturación")
        info_layout = QtWidgets.QFormLayout(gb_info)
        info_layout.setLabelAlignment(Qt.AlignLeft)
        info_layout.setFormAlignment(Qt.AlignTop)
        info_layout.setHorizontalSpacing(12)
        info_layout.setVerticalSpacing(8)

        self.le_num_factura = QtWidgets.QLineEdit()
        self.le_num_factura.setReadOnly(True)
        self.le_num_factura.setPlaceholderText("Se asignará al emitir")
        self.le_num_factura.setText("Se asignará al emitir")

        self.cb_serie = SeriesComboBox()
        self.cb_serie.setMinimumWidth(180)

        self.de_fecha = QtWidgets.QDateEdit()
        self.de_fecha.setCalendarPopup(True)
        self.de_fecha.setDate(QtCore.QDate.currentDate())
        self.de_fecha.setDisplayFormat("dd/MM/yyyy")

        self.cb_estado = QtWidgets.QComboBox()
        self.cb_estado.addItem("BORRADOR", "BORRADOR")
        self.cb_estado.addItem("EMITIDA", "EMITIDA")
        self.cb_estado.addItem("ANULADA", "ANULADA")
        self.cb_estado.addItem("PAGADA", "PAGADA")
        self.cb_estado.setCurrentIndex(0)
        self.cb_estado.setEnabled(False)

        self.te_observaciones = QtWidgets.QPlainTextEdit()
        self.te_observaciones.setPlaceholderText("Observaciones...")
        self.te_observaciones.setMaximumHeight(90)

        info_layout.addRow("Nº factura:", self.le_num_factura)
        info_layout.addRow("Serie:", self.cb_serie)
        info_layout.addRow("Fecha:", self.de_fecha)
        info_layout.addRow("Estado:", self.cb_estado)
        info_layout.addRow("Observaciones:", self.te_observaciones)

        main_layout.addWidget(gb_info)

        # ===== Zona central =====
        central_layout = QtWidgets.QHBoxLayout()
        central_layout.setSpacing(10)

        # ---- Líneas ----
        gb_lineas = QtWidgets.QGroupBox("Conceptos a facturar")
        gb_lineas_layout = QtWidgets.QVBoxLayout(gb_lineas)
        gb_lineas_layout.setContentsMargins(8, 10, 8, 8)

        self.tree_facturacion = QtWidgets.QTreeWidget()
        self.tree_facturacion.setColumnCount(5)
        self.tree_facturacion.setHeaderLabels([
            "Concepto",
            "Cantidad",
            "Precio Unit.",
            "Importe",
            "Estado"
        ])
        self.tree_facturacion.setRootIsDecorated(False)
        self.tree_facturacion.setAlternatingRowColors(True)
        self.tree_facturacion.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.tree_facturacion.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tree_facturacion.setUniformRowHeights(True)

        header = self.tree_facturacion.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeToContents)

        self.tree_facturacion = FacturacionTreePanel()


        gb_lineas_layout.addWidget(self.tree_facturacion)

        lineas_btn_layout = QtWidgets.QHBoxLayout()

        self.btn_add_linea = QtWidgets.QPushButton("Añadir")
        self.btn_edit_linea = QtWidgets.QPushButton("Editar")
        self.btn_remove_linea = QtWidgets.QPushButton("Quitar")
        self.btn_refresh = QtWidgets.QPushButton("Recargar")

        lineas_btn_layout.addWidget(self.btn_add_linea)
        lineas_btn_layout.addWidget(self.btn_edit_linea)
        lineas_btn_layout.addWidget(self.btn_remove_linea)
        lineas_btn_layout.addStretch()
        lineas_btn_layout.addWidget(self.btn_refresh)

        gb_lineas_layout.addLayout(lineas_btn_layout)

        central_layout.addWidget(gb_lineas, 3)

        # ---- Resumen ----
        resumen_box_layout = QtWidgets.QVBoxLayout()

        gb_resumen = QtWidgets.QGroupBox("Resumen")
        resumen_layout = QtWidgets.QFormLayout(gb_resumen)
        resumen_layout.setLabelAlignment(Qt.AlignLeft)
        resumen_layout.setFormAlignment(Qt.AlignTop)
        resumen_layout.setHorizontalSpacing(12)
        resumen_layout.setVerticalSpacing(10)

        self.lbl_items = QtWidgets.QLabel("0")
        self.lbl_subtotal = QtWidgets.QLabel("0.00 €")
        self.lbl_iva = QtWidgets.QLabel("0.00 €")
        self.lbl_total = QtWidgets.QLabel("0.00 €")

        total_font = self.lbl_total.font()
        total_font.setBold(True)
        self.lbl_total.setFont(total_font)

        resumen_layout.addRow("Ítems:", self.lbl_items)
        resumen_layout.addRow("Subtotal:", self.lbl_subtotal)
        resumen_layout.addRow("IVA:", self.lbl_iva)
        resumen_layout.addRow("Total:", self.lbl_total)

        self.btn_generar = QtWidgets.QPushButton("Emitir factura")
        self.btn_generar.setMinimumHeight(34)

        resumen_box_layout.addWidget(gb_resumen)
        resumen_box_layout.addWidget(self.btn_generar)
        resumen_box_layout.addStretch()

        central_layout.addLayout(resumen_box_layout, 1)

        main_layout.addLayout(central_layout)

        # ===== Botonera inferior =====
        bottom_layout = QtWidgets.QHBoxLayout()

        self.btn_guardar = QtWidgets.QPushButton("Guardar borrador")
        self.btn_cancelar = QtWidgets.QPushButton("Cerrar")

        bottom_layout.addStretch()
        bottom_layout.addWidget(self.btn_guardar)
        bottom_layout.addWidget(self.btn_cancelar)

        main_layout.addLayout(bottom_layout)

    def _connect_signals(self):
        self.btn_cancelar.clicked.connect(self.reject)
        self.btn_guardar.clicked.connect(self._guardar_factura)
        self.btn_generar.clicked.connect(self._generar_factura)

        self.btn_add_linea.clicked.connect(self._add_linea)
        self.btn_edit_linea.clicked.connect(self._edit_linea)
        self.btn_remove_linea.clicked.connect(self._remove_linea)
        self.btn_refresh.clicked.connect(self._refresh_lineas)

        self.cb_serie.currentIndexChanged.connect(self._update_numero_preview)

    def _init_state(self):
        self._set_factura_borrador_mode()

    def _set_factura_borrador_mode(self):
        self.cb_estado.setCurrentIndex(0)
        self.le_num_factura.setText("Se asignará al emitir")

    def _load_initial_data(self):
        # self._load_series()
        self.datos_contrato = self._get_contrato_data()
        self._load_demo_data()
        self._recalcular_totales()

    def _get_contrato_data(self):
        try:
            response = self.api.get(f"billing/contratos?idexplotacion={self.idexplotacion}")
            return response 


        except Exception as e:
            print(f"[FacturacionDialog] Error cargando datos de contrato: {e}")
            return {}
    def _update_numero_preview(self):
        data = self.cb_serie.currentData()
        if not data:
            self.le_num_factura.setText("Se asignará al emitir")
            return

        activo = data.get("activo", True)
        letra = data.get("letra")
        anio = data.get("anio")
        next_num = data.get("next_num")

        if not activo:
            self.le_num_factura.setText("Serie inactiva")
            return

        if letra and anio and next_num is not None:
            self.le_num_factura.setText(f"Próximo estimado: {letra}-{anio}-{int(next_num):06d}")
        else:
            self.le_num_factura.setText("Se asignará al emitir")

    def _load_demo_data(self):
        self.tree_facturacion.clear()

        demo_items = [
            ("Plan abonado variable", "1", "250.00", "250.00", "PENDIENTE"),
            ("Muestreo de suelo", "2", "45.00", "90.00", "PENDIENTE"),
            ("Procesado NDVI", "1", "75.00", "75.00", "PENDIENTE"),
        ]

        for item_data in demo_items:
            item = QtWidgets.QTreeWidgetItem(item_data)
            self.tree_facturacion.addTopLevelItem(item)

    def _recalcular_totales(self):
        subtotal = Decimal("0")
        total_items = self.tree_facturacion.topLevelItemCount()

        for i in range(total_items):
            item = self.tree_facturacion.topLevelItem(i)
            subtotal += self._to_decimal(item.text(3))

        iva = (subtotal * self.IVA_DEFAULT) / Decimal("100")
        total = subtotal + iva

        self.lbl_items.setText(str(total_items))
        self.lbl_subtotal.setText(self._format_eur(subtotal))
        self.lbl_iva.setText(self._format_eur(iva))
        self.lbl_total.setText(self._format_eur(total))

    def _to_decimal(self, value):
        if value is None:
            return Decimal("0")

        txt = str(value).strip().replace("€", "").replace(",", ".")
        if not txt:
            return Decimal("0")

        try:
            return Decimal(txt)
        except (InvalidOperation, ValueError):
            return Decimal("0")

    def _format_eur(self, value: Decimal) -> str:
        return f"{value.quantize(Decimal('0.01'))} €"

    def _get_selected_item(self):
        items = self.tree_facturacion.selectedItems()
        return items[0] if items else None

    def _add_linea(self):
        item = QtWidgets.QTreeWidgetItem([
            "Nuevo concepto",
            "1",
            "0.00",
            "0.00",
            "PENDIENTE"
        ])
        self.tree_facturacion.addTopLevelItem(item)
        self.tree_facturacion.setCurrentItem(item)
        self._recalcular_totales()

    def _edit_linea(self):
        item = self._get_selected_item()
        if not item:
            QtWidgets.QMessageBox.warning(self, "Facturación", "Selecciona una línea para editar.")
            return

        QtWidgets.QMessageBox.information(
            self,
            "Facturación",
            f"Edición pendiente de implementar.\n\nConcepto actual: {item.text(0)}"
        )

    def _remove_linea(self):
        item = self._get_selected_item()
        if not item:
            QtWidgets.QMessageBox.warning(self, "Facturación", "Selecciona una línea para quitar.")
            return

        index = self.tree_facturacion.indexOfTopLevelItem(item)
        self.tree_facturacion.takeTopLevelItem(index)
        self._recalcular_totales()

    def _refresh_lineas(self):
        QtWidgets.QMessageBox.information(
            self,
            "Facturación",
            "Recarga pendiente de implementar."
        )

    def _guardar_factura(self):
        payload = self._collect_data()
        print("[GUARDAR BORRADOR]", payload)

        QtWidgets.QMessageBox.information(
            self,
            "Facturación",
            "Guardado como borrador pendiente de integración con API."
        )

    def _generar_factura(self):
        serie_data = self.cb_serie.currentData()
        if not serie_data or not serie_data.get("idserie"):
            QtWidgets.QMessageBox.warning(
                self,
                "Facturación",
                "Debes seleccionar una serie válida antes de emitir."
            )
            return

        if not serie_data.get("activo", True):
            QtWidgets.QMessageBox.warning(
                self,
                "Facturación",
                "La serie seleccionada está inactiva."
            )
            return

        if self.tree_facturacion.topLevelItemCount() == 0:
            QtWidgets.QMessageBox.warning(
                self,
                "Facturación",
                "La factura no tiene líneas."
            )
            return

        payload = self._collect_data()
        print("[EMITIR FACTURA]", payload)

        QtWidgets.QMessageBox.information(
            self,
            "Facturación",
            "Emisión pendiente de integrar con API."
        )

        # print(self.datos_contrato)

    def _collect_data(self):
        lineas = []

        for i in range(self.tree_facturacion.topLevelItemCount()):
            item = self.tree_facturacion.topLevelItem(i)
            lineas.append({
                "concepto": item.text(0),
                "cantidad": item.text(1),
                "precio_unitario": item.text(2),
                "importe": item.text(3),
                "estado": item.text(4),
            })

        serie_data = self.cb_serie.currentData() or {}

        return {
            "idexplotacion": self.idexplotacion,
            "idserie": serie_data.get("idserie"),
            "serie_label": self.cb_serie.currentText(),
            "numero_factura_preview": self.le_num_factura.text().strip(),
            "fecha": self.de_fecha.date().toString("yyyy-MM-dd"),
            "estado": self.cb_estado.currentData(),
            "observaciones": self.te_observaciones.toPlainText().strip(),
            "lineas": lineas,
        }