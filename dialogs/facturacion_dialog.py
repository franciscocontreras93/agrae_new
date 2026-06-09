from decimal import Decimal, ROUND_HALF_UP


from qgis.PyQt import QtWidgets, QtCore
from qgis.PyQt.QtCore import Qt

from ..core.api import APIRequest
from ..gui.components.CustomComboBox import PlanesComboBox, SeriesComboBox
from ..dialogs.gestion.agricultor.agricultorSelectDialog import AgricultorSelectDialog


class FacturacionDialog(QtWidgets.QDialog):
    """
    Diálogo de facturación.

    Permite:
    - Seleccionar cliente.
    - Editar datos fiscales.
    - Seleccionar plan.
    - Calcular importes.
    - Emitir o generar borrador.
    - Descargar el PDF devuelto por el backend.
    """

    def __init__(
        self,
        idexplotacion: int,
        lotes: list | None = None,
        uid_factura: str | None = None,
        modo_edicion: bool = False,
        parent=None,
    ):
        super().__init__(parent)

        self.idexplotacion = idexplotacion
        self.lotes = lotes or []
        self.uid_factura = uid_factura
        self.modo_edicion = bool(modo_edicion)

        self._api_request = APIRequest()
        self._agricultor_payer = None
        self.idpersona = None
        self._current_plan = None

        self.setWindowTitle("aGrae | Editar factura" if self.modo_edicion else "aGrae | Facturación")
        self.resize(980, 680)

        self._build_ui()
        self._connect_signals()

        self._load_initial_data()

    # ------------------------------------------------------------------
    # Helpers UI
    # ------------------------------------------------------------------

    def _label(self, text: str):
        return QtWidgets.QLabel(text)

    def _line(self, placeholder: str = "", readonly: bool = False):
        line = QtWidgets.QLineEdit()
        line.setPlaceholderText(placeholder)
        line.setReadOnly(readonly)
        return line

    def _money_spin(self, suffix: str = "", enabled: bool = True, readonly: bool = False, maximum: float = 10_000_000):
        spin = QtWidgets.QDoubleSpinBox()
        spin.setDecimals(2)
        spin.setMaximum(maximum)
        spin.setSuffix(suffix)
        spin.setEnabled(enabled)
        spin.setReadOnly(readonly)
        return spin

    def _date_edit(self, date: QtCore.QDate):
        edit = QtWidgets.QDateEdit(date)
        edit.setCalendarPopup(True)
        return edit

    def _grid(self, parent):
        layout = QtWidgets.QGridLayout(parent)
        layout.setContentsMargins(8, 10, 8, 8)
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(5)
        return layout

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        main = QtWidgets.QVBoxLayout(self)
        main.setContentsMargins(8, 8, 8, 8)
        main.setSpacing(6)

        self._build_header(main)
        self._build_cliente_group(main)
        self._build_factura_group(main)
        self._build_plan_group(main)
        self._build_observaciones_group(main)
        self._build_lotes_resumen_group(main)
        self._build_bottom(main)

    def _build_header(self, main):
        header = QtWidgets.QHBoxLayout()

        title = QtWidgets.QLabel("Editar factura" if self.modo_edicion else "Facturación")
        font = title.font()
        font.setPointSize(12)
        font.setBold(True)
        title.setFont(font)

        self.lbl_explotacion = QtWidgets.QLabel(f"Explotación ID: {self.idexplotacion}")
        self.lbl_explotacion.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.lbl_explotacion)
        main.addLayout(header)

    def _build_cliente_group(self, main):
        gb = QtWidgets.QGroupBox("Datos del cliente")
        layout = self._grid(gb)

        payer_layout = QtWidgets.QHBoxLayout()
        payer_layout.setSpacing(6)

        self.txt_facturar_a = self._line("Seleccione agricultor/persona a facturar", readonly=True)
        self.btn_buscar_agricultor = QtWidgets.QPushButton("Buscar")
        self.btn_buscar_agricultor.setMaximumWidth(90)

        payer_layout.addWidget(self.txt_facturar_a)
        payer_layout.addWidget(self.btn_buscar_agricultor)

        self.line_razon_social = self._line()
        self.line_dni = self._line()
        self.line_direccion = self._line()
        self.line_provincia = self._line()
        self.line_municipio = self._line()
        self.line_cp = self._line()
        self.line_pais = self._line()
        self.line_pais.setText("ESP")
        self.line_email = self._line()
        self.line_telefono = self._line()

        self.combo_person_type = QtWidgets.QComboBox()
        self.combo_person_type.addItems(["Seleccionar...", "F", "J"])

        self.btn_guardar_cliente = QtWidgets.QPushButton("Guardar datos cliente")
        self.btn_guardar_cliente.setMaximumWidth(160)

        layout.addWidget(self._label("Facturar a:"), 0, 0)
        layout.addLayout(payer_layout, 0, 1, 1, 5)

        layout.addWidget(self._label("Razón social:"), 1, 0)
        layout.addWidget(self.line_razon_social, 1, 1, 1, 3)
        layout.addWidget(self._label("NIF/CIF:"), 1, 4)
        layout.addWidget(self.line_dni, 1, 5)

        layout.addWidget(self._label("Tipo:"), 2, 0)
        layout.addWidget(self.combo_person_type, 2, 1)
        layout.addWidget(self._label("Dirección:"), 2, 2)
        layout.addWidget(self.line_direccion, 2, 3, 1, 3)

        layout.addWidget(self._label("Provincia:"), 3, 0)
        layout.addWidget(self.line_provincia, 3, 1)
        layout.addWidget(self._label("Municipio:"), 3, 2)
        layout.addWidget(self.line_municipio, 3, 3)
        layout.addWidget(self._label("CP:"), 3, 4)
        layout.addWidget(self.line_cp, 3, 5)

        layout.addWidget(self._label("País:"), 4, 0)
        layout.addWidget(self.line_pais, 4, 1)
        layout.addWidget(self._label("Email:"), 4, 2)
        layout.addWidget(self.line_email, 4, 3)
        layout.addWidget(self._label("Teléfono:"), 4, 4)
        layout.addWidget(self.line_telefono, 4, 5)

        layout.addWidget(self.btn_guardar_cliente, 5, 4, 1, 2)

        main.addWidget(gb)

    def _build_factura_group(self, main):
        gb = QtWidgets.QGroupBox("Datos de factura")
        layout = self._grid(gb)

        self.cmb_serie = SeriesComboBox(auto_enable_on_load=True)
        # self.date_fecha_emision = self._date_edit(QtCore.QDate.currentDate())
        self.date_fecha_emision = QtWidgets.QDateEdit()
        # self.date_fecha_emision.setMinimumDate(self.cmb_serie.get_current_serie().get("ultima_fecha"))
        self.date_fecha_vencimiento = QtWidgets.QDateEdit()

        # self.date_fecha_vencimiento = self._date_edit(QtCore.QDate.currentDate().addMonths(1))

        self.spin_iva = self._money_spin(" %", maximum=100)
        self.spin_iva.setValue(21)

        self.chk_area_minima = QtWidgets.QCheckBox("Aplicar mínimo por lote")
        self.chk_area_minima.setChecked(True)

        self.spin_area_minima = self._money_spin(" ha", maximum=10_000)
        self.spin_area_minima.setValue(5.00)

        layout.addWidget(self._label("Serie:"), 0, 0)
        layout.addWidget(self.cmb_serie, 0, 1)
        layout.addWidget(self._label("Emisión:"), 0, 2)
        layout.addWidget(self.date_fecha_emision, 0, 3)
        layout.addWidget(self._label("Vencimiento:"), 0, 4)
        layout.addWidget(self.date_fecha_vencimiento, 0, 5)

        layout.addWidget(self._label("IVA:"), 1, 0)
        layout.addWidget(self.spin_iva, 1, 1)
        layout.addWidget(self.chk_area_minima, 1, 2)
        layout.addWidget(self.spin_area_minima, 1, 3)

        main.addWidget(gb)

    def _build_plan_group(self, main):
        gb = QtWidgets.QGroupBox("Plan y precio")
        layout = self._grid(gb)

        self.cmb_plan = PlanesComboBox(endpoint=f"billing/planes?idexplotacion={self.idexplotacion}", auto_enable_on_load=True)

        self.txt_concepto = self._line("Se tomará del nombre del plan", readonly=True)
        self.txt_pricing_model = self._line(readonly=True)

        self.spin_precio_ha_plan = self._money_spin(" €/ha", readonly=True)
        self.spin_precio_ha_aplicado = self._money_spin(" €/ha", enabled=False)
        self.spin_precio_paquete_aplicado = self._money_spin(" €", enabled=False)
        self.spin_max_ha_paquete = self._money_spin(" ha", readonly=True)
        self.spin_precio_ha_excedente = self._money_spin(" €/ha")
        self.spin_precio_ha_excedente.setValue(0)

        self.chk_precio_manual = QtWidgets.QCheckBox("Usar precio manual")

        layout.addWidget(self._label("Plan:"), 0, 0)
        layout.addWidget(self.cmb_plan, 0, 1, 1, 5)

        layout.addWidget(self._label("Concepto:"), 1, 0)
        layout.addWidget(self.txt_concepto, 1, 1, 1, 3)
        layout.addWidget(self._label("Modelo:"), 1, 4)
        layout.addWidget(self.txt_pricing_model, 1, 5)

        layout.addWidget(self._label("Base plan:"), 2, 0)
        layout.addWidget(self.spin_precio_ha_plan, 2, 1)
        layout.addWidget(self._label("€/ha aplicado:"), 2, 2)
        layout.addWidget(self.spin_precio_ha_aplicado, 2, 3)
        layout.addWidget(self._label("Paquete:"), 2, 4)
        layout.addWidget(self.spin_precio_paquete_aplicado, 2, 5)

        layout.addWidget(self._label("Máx. paquete:"), 3, 0)
        layout.addWidget(self.spin_max_ha_paquete, 3, 1)
        layout.addWidget(self._label("€/ha excedente:"), 3, 2)
        layout.addWidget(self.spin_precio_ha_excedente, 3, 3)
        layout.addWidget(self.chk_precio_manual, 3, 4, 1, 2)

        main.addWidget(gb)

    def _build_observaciones_group(self, main):
        gb = QtWidgets.QGroupBox("Observaciones")
        layout = QtWidgets.QVBoxLayout(gb)
        layout.setContentsMargins(8, 10, 8, 8)

        self.txt_observaciones = QtWidgets.QPlainTextEdit()
        self.txt_observaciones.setPlaceholderText("Observaciones...")
        self.txt_observaciones.setMaximumHeight(40)

        layout.addWidget(self.txt_observaciones)
        main.addWidget(gb)

    def _build_lotes_resumen_group(self, main):
        body = QtWidgets.QHBoxLayout()
        body.setSpacing(8)

        self._build_lotes_group(body)
        self._build_resumen_group(body)

        main.addLayout(body, 1)

    def _build_lotes_group(self, body):
        gb = QtWidgets.QGroupBox("Lotes / items a facturar")
        layout = QtWidgets.QVBoxLayout(gb)
        layout.setContentsMargins(8, 10, 8, 8)
        layout.setSpacing(5)

        self.tree_lotes = QtWidgets.QTreeWidget()
        self.tree_lotes.setColumnCount(6)
        self.tree_lotes.setHeaderLabels(["iddata", "Lote", "Cultivo", "Ha reales", "Ha facturadas", "Norma"])
        self.tree_lotes.setRootIsDecorated(False)
        self.tree_lotes.setAlternatingRowColors(True)
        self.tree_lotes.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.tree_lotes.setMinimumHeight(150)
        self.tree_lotes.setEditTriggers(
            QtWidgets.QAbstractItemView.DoubleClicked |
            QtWidgets.QAbstractItemView.SelectedClicked |
            QtWidgets.QAbstractItemView.EditKeyPressed
        )

        header = self.tree_lotes.header()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        for col in (2, 3, 4, 5):
            header.setSectionResizeMode(col, QtWidgets.QHeaderView.ResizeToContents)

        self.lbl_lotes_info = QtWidgets.QLabel(
            "Doble clic en 'Ha facturadas' para ajustar manualmente la superficie facturada."
        )
        self.lbl_lotes_info.setStyleSheet("color: #666;")

        layout.addWidget(self.tree_lotes)
        layout.addWidget(self.lbl_lotes_info)

        body.addWidget(gb, 3)

    def _build_resumen_group(self, body):
        gb = QtWidgets.QGroupBox("Resumen")
        form = QtWidgets.QFormLayout(gb)
        form.setContentsMargins(8, 10, 8, 8)
        form.setHorizontalSpacing(8)
        form.setVerticalSpacing(5)

        self.lbl_items = QtWidgets.QLabel("0")
        self.lbl_ha_real_total = QtWidgets.QLabel("0,00")
        self.lbl_ha_fact_total = QtWidgets.QLabel("0,00")
        self.lbl_ha_excedente = QtWidgets.QLabel("0,00")
        self.lbl_precio_ha = QtWidgets.QLabel("0,00 €/ha")
        self.lbl_precio_paquete = QtWidgets.QLabel("0,00 €")
        self.lbl_precio_excedente = QtWidgets.QLabel("0,00 €/ha")
        self.lbl_base_excedente = QtWidgets.QLabel("0,00 €")
        self.lbl_base = QtWidgets.QLabel("0,00 €")
        self.lbl_iva = QtWidgets.QLabel("0,00 €")
        self.lbl_total = QtWidgets.QLabel("0,00 €")

        font = self.lbl_total.font()
        font.setBold(True)
        self.lbl_total.setFont(font)

        for label, widget in [
            ("Items:", self.lbl_items),
            ("Ha reales:", self.lbl_ha_real_total),
            ("Ha facturadas:", self.lbl_ha_fact_total),
            ("Ha excedentes:", self.lbl_ha_excedente),
            ("Precio ha:", self.lbl_precio_ha),
            ("Precio paquete:", self.lbl_precio_paquete),
            ("Precio excedente:", self.lbl_precio_excedente),
            ("Base excedente:", self.lbl_base_excedente),
            ("Base imponible:", self.lbl_base),
            ("IVA:", self.lbl_iva),
            ("Total:", self.lbl_total),
        ]:
            form.addRow(label, widget)

        resumen_box = QtWidgets.QVBoxLayout()
        resumen_box.addWidget(gb)

        self.btn_guardar_borrador = QtWidgets.QPushButton("Guardar borrador")
        self.btn_emitir = QtWidgets.QPushButton("Guardar cambios" if self.modo_edicion else "Emitir factura")
        self.btn_guardar_borrador.setMinimumHeight(28)
        self.btn_emitir.setMinimumHeight(30)

        if self.modo_edicion:
            self.btn_guardar_borrador.setVisible(False)

        resumen_box.addWidget(self.btn_guardar_borrador)
        resumen_box.addWidget(self.btn_emitir)
        resumen_box.addStretch()

        body.addLayout(resumen_box, 1)

    def _build_bottom(self, main):
        bottom = QtWidgets.QHBoxLayout()
        self.btn_cerrar = QtWidgets.QPushButton("Cerrar")

        bottom.addStretch()
        bottom.addWidget(self.btn_cerrar)

        main.addLayout(bottom)

    # ------------------------------------------------------------------
    # Signals
    # ------------------------------------------------------------------

    def _connect_signals(self):
        self.btn_cerrar.clicked.connect(self.reject)
        self.btn_buscar_agricultor.clicked.connect(self._buscar_agricultor)
        self.btn_guardar_cliente.clicked.connect(self._guardar_datos_cliente)

        self.date_fecha_emision.dateChanged.connect(
            lambda date: self.date_fecha_vencimiento.setDate(date.addMonths(1))
        )

        self.cmb_serie.items_loaded.connect(self._on_series_loaded)
        self.cmb_serie.current_value_changed.connect(self._on_serie_changed)


        self.cmb_plan.plan_changed.connect(self._on_plan_changed)
        self.chk_precio_manual.toggled.connect(self._on_precio_manual_toggled)

        self.spin_precio_ha_aplicado.valueChanged.connect(self._recalcular_resumen)
        self.spin_precio_paquete_aplicado.valueChanged.connect(self._recalcular_resumen)
        self.spin_precio_ha_excedente.valueChanged.connect(self._recalcular_resumen)
        self.spin_iva.valueChanged.connect(self._recalcular_resumen)

        self.chk_area_minima.toggled.connect(self._reaplicar_area_minima)
        self.spin_area_minima.valueChanged.connect(self._reaplicar_area_minima)

        self.tree_lotes.itemChanged.connect(self._on_lote_item_changed)

        self.btn_guardar_borrador.clicked.connect(self._guardar_borrador)

        if self.modo_edicion:
            self.btn_emitir.clicked.connect(self._guardar_cambios_factura)
        else:
            self.btn_emitir.clicked.connect(self._emitir_factura)

    # ------------------------------------------------------------------
    # Carga inicial
    # ------------------------------------------------------------------

    def _load_initial_data(self):
        self._load_lotes(self.lotes)
        self._recalcular_resumen()


    def _load_lotes(self, lotes: list | None = None):
        self.tree_lotes.blockSignals(True)
        self.tree_lotes.clear()

        lotes = lotes or []

        for lote in lotes:
            lote_norm = self._normalizar_lote(lote)
            ha_real = Decimal(str(lote_norm["area_ha"]))
            ha_fact = self._calcular_ha_facturada_default(ha_real)

            item = QtWidgets.QTreeWidgetItem([
                str(lote_norm.get("iddata") or ""),
                str(lote_norm.get("nombre", "-")),
                str(lote_norm.get("cultivo", "-")),
                self._fmt_number(ha_real),
                self._fmt_number(ha_fact),
                self._get_norma_text(ha_real),
            ])

            item.setData(0, Qt.UserRole, lote_norm)
            item.setFlags(item.flags() | Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable)
            self.tree_lotes.addTopLevelItem(item)

        self.tree_lotes.blockSignals(False)
        self._recalcular_resumen()

    def _on_series_loaded(self, _items):
        self._on_serie_changed(self.cmb_serie.currentData())


    def _on_serie_changed(self, _value=None):
        serie = self.cmb_serie.get_current_serie()

        if not isinstance(serie, dict):
            return

        ultima_fecha = serie.get("ultima_fecha")

        fecha_ultima = self._parse_qdate(ultima_fecha)
        fecha_hoy = QtCore.QDate.currentDate()

        if fecha_ultima and fecha_ultima.isValid():
            fecha_base = fecha_ultima if fecha_ultima > fecha_hoy else fecha_hoy
        else:
            fecha_base = fecha_hoy

        self.date_fecha_emision.setCalendarPopup(True)
        self.date_fecha_vencimiento.setCalendarPopup(True)

        self.date_fecha_emision.setMinimumDate(fecha_base)
        self.date_fecha_emision.setDate(fecha_base)

        self.date_fecha_vencimiento.setMinimumDate(fecha_base)
        self.date_fecha_vencimiento.setDate(fecha_base.addMonths(1))


    def _parse_qdate(self, value):
        if value is None:
            return None

        if isinstance(value, QtCore.QDate):
            return value if value.isValid() else None

        # Si viene como date/datetime de Python
        if hasattr(value, "year") and hasattr(value, "month") and hasattr(value, "day"):
            return QtCore.QDate(value.year, value.month, value.day)

        text = str(value).strip()

        # Soporta "2026-06-01" o "2026-06-01T00:00:00"
        if len(text) >= 10:
            text = text[:10]

        qdate = QtCore.QDate.fromString(text, "yyyy-MM-dd")
        return qdate if qdate.isValid() else None
    # ------------------------------------------------------------------
    # Agricultor y cliente
    # ------------------------------------------------------------------

    def _buscar_agricultor(self):
        dlg = AgricultorSelectDialog(idexplotacion=self.idexplotacion, parent=self)

        try:
            dlg.table.rowDoubleClicked.disconnect(dlg._on_selected)
        except Exception:
            pass

        def on_selected(value, item):
            dlg.selected_value = value
            dlg.selected_item = item
            self._set_agricultor_payer(item)
            dlg.accept()

        dlg.table.rowDoubleClicked.connect(on_selected)
        dlg.exec_()

    def _set_agricultor_payer(self, agricultor):
        self._agricultor_payer = agricultor
        data = self._extract_cliente_data(agricultor)

        self.idpersona = data.get("idpersona")

        self.txt_facturar_a.setText(f"{data['nif']} - {data['razon_social']}".strip(" -"))
        self.line_razon_social.setText(data["razon_social"])
        self.line_dni.setText(data["nif"])
        self.line_direccion.setText(data["direccion"])
        self.line_provincia.setText(data["provincia"])
        self.line_municipio.setText(data["municipio"])
        self.line_cp.setText(data["codigo_postal"])
        self.line_email.setText(data["email"])
        self.line_telefono.setText(data["telefono"])

        if data["nif"] and data["nif"][0].isalpha() and data["nif"][0].upper() not in ("X", "Y", "Z"):
            self.combo_person_type.setCurrentText("J")
        elif data["nif"]:
            self.combo_person_type.setCurrentText("F")

    def _extract_cliente_data(self, agricultor) -> dict:
        if not isinstance(agricultor, dict):
            return {
                "idagricultor": getattr(agricultor, "idagricultor", None) or getattr(agricultor, "id", None),
                "razon_social": getattr(agricultor, "nombre_completo", "") or "",
                "nif": getattr(agricultor, "dni", "") or "",
                "direccion": getattr(agricultor, "direccion", "") or "",
                "provincia": getattr(agricultor, "provincia", "") or "",
                "municipio": getattr(agricultor, "municipio", "") or "",
                "codigo_postal": getattr(agricultor, "codigo_postal", "") or getattr(agricultor, "cp", "") or "",
                "email": getattr(agricultor, "email", "") or "",
                "telefono": getattr(agricultor, "telefono", "") or getattr(agricultor, "movil", "") or "",
            }

        persona = agricultor.get("persona") or {}
        explotacion = agricultor.get("explotacion") or {}

        return {
            "idpersona": persona.get("idpersona"),
            "idagricultor": agricultor.get("idagricultor"),
            "razon_social": persona.get("nombre_completo") or agricultor.get("nombre_completo") or agricultor.get("nombre") or "",
            "nif": persona.get("dni") or agricultor.get("dni") or "",
            "direccion": persona.get("direccion") or explotacion.get("direccion") or "",
            "provincia": persona.get("provincia") or explotacion.get("provincia") or "",
            "municipio": persona.get("municipio") or explotacion.get("municipio") or "",
            "codigo_postal": (
                persona.get("codigo_postal")
                or persona.get("cp")
                or explotacion.get("codigo_postal")
                or explotacion.get("cp")
                or ""
            ),
            "email": persona.get("email") or agricultor.get("email") or "",
            "telefono": (
                persona.get("telefono")
                or persona.get("movil")
                or agricultor.get("telefono")
                or agricultor.get("movil")
                or ""
            ),
        }

    def _get_idagricultor_payer(self):
        data = self._extract_cliente_data(self._agricultor_payer) if self._agricultor_payer else {}
        return data.get("idagricultor")

    def _guardar_datos_cliente(self):
        idagricultor = self._get_idagricultor_payer()

        if not idagricultor:
            QtWidgets.QMessageBox.warning(self, "Facturación", "Selecciona primero un agricultor/cliente.")
            return

        payload = self._cliente_payload()

        payload  = {
            "idpersona": payload.get("idpersona"),
            "dni": payload.get("nif"),
            "direccion": payload.get("direccion"),
            "provincia": payload.get("provincia"),
            "municipio": payload.get("municipio"),
            "codigo_postal": payload.get("codigo_postal"),
            "email": payload.get("email"),
            "telefono": payload.get("telefono")}

        if not payload['dni']:
            QtWidgets.QMessageBox.warning(self, "Facturación", "El DNI/CIF es obligatorio.")
            return


        r = self._api_request.put('/gis/personas/', payload)


        if r['http_status'] != 200:
            QtWidgets.QMessageBox.critical(self, f"Error: {r.get('http_status')}", f"Error al guardar datos del cliente: {r.get('data', {}).get('detail', 'Error desconocido')}")
            return
            
        QtWidgets.QMessageBox.information(self, "Facturación", "Datos del cliente preparados correctamente.")

    # ------------------------------------------------------------------
    # Lotes e items
    # ------------------------------------------------------------------

    def _normalizar_lote(self, lote):
        if isinstance(lote, dict):
            return {
                "iddata": lote.get("iddata"),
                "idlote": lote.get("idlote"),
                "nombre": lote.get("nombre") or lote.get("lote") or lote.get("name") or "-",
                "cultivo": lote.get("cultivo") or lote.get("nombre_cultivo") or "-",
                "area_ha": float(lote.get("area_ha") or lote.get("ha") or lote.get("area") or 0),
                "raw": lote,
            }

        attrs = lote.attributes()
        fields = lote.fields()

        def val(*names, default=None):
            for name in names:
                idx = fields.indexFromName(name)
                if idx >= 0:
                    return attrs[idx]
            return default

        return {
            "iddata": val("iddata", "IDDATA", "id_data"),
            "idlote": val("idlote", "IDLOTE", "id_lote"),
            "nombre": val("lote", "nombre", "name", "LOTE", "NOMBRE", default="-"),
            "cultivo": val("cultivo", "nombre_cultivo", "CULTIVO", default="-"),
            "area_ha": float(val("area_ha", "ha", "sup_ha", "AREA_HA", "area", default=0) or 0),
            "raw": None,
        }

    def _get_lotes_items(self):
        items = []

        for i in range(self.tree_lotes.topLevelItemCount()):
            item = self.tree_lotes.topLevelItem(i)
            lote = item.data(0, Qt.UserRole)

            if not isinstance(lote, dict):
                continue

            iddata = lote.get("iddata")

            items.append({
                "iddata": int(iddata) if iddata is not None and str(iddata).strip() else None,
                "area_ha_facturada": float(self._money_like(self._to_decimal(item.text(4)))),
            })

        return items

    def _sum_lote_decimal(self, source: str) -> Decimal:
        total = Decimal("0")

        for i in range(self.tree_lotes.topLevelItemCount()):
            item = self.tree_lotes.topLevelItem(i)

            if source == "real":
                lote = item.data(0, Qt.UserRole)
                if isinstance(lote, dict):
                    total += Decimal(str(lote.get("area_ha") or 0))
            else:
                total += self._to_decimal(item.text(4))

        return total

    # ------------------------------------------------------------------
    # Norma de área mínima
    # ------------------------------------------------------------------

    def _calcular_ha_facturada_default(self, ha_real: Decimal) -> Decimal:
        if not self.chk_area_minima.isChecked():
            return ha_real

        area_minima = Decimal(str(self.spin_area_minima.value()))
        return area_minima if ha_real < area_minima else ha_real

    def _get_norma_text(self, ha_real: Decimal) -> str:
        if not self.chk_area_minima.isChecked():
            return ""

        area_minima = Decimal(str(self.spin_area_minima.value()))
        return f"Mín. {self._fmt_number(area_minima)} ha" if ha_real < area_minima else ""

    def _reaplicar_area_minima(self):
        self.spin_area_minima.setEnabled(self.chk_area_minima.isChecked())
        self.tree_lotes.blockSignals(True)

        for i in range(self.tree_lotes.topLevelItemCount()):
            item = self.tree_lotes.topLevelItem(i)
            lote = item.data(0, Qt.UserRole)

            if not isinstance(lote, dict):
                continue

            ha_real = Decimal(str(lote.get("area_ha") or 0))
            item.setText(4, self._fmt_number(self._calcular_ha_facturada_default(ha_real)))
            item.setText(5, self._get_norma_text(ha_real))

        self.tree_lotes.blockSignals(False)
        self._recalcular_resumen()

    # ------------------------------------------------------------------
    # Plan y precio
    # ------------------------------------------------------------------

    def _on_plan_changed(self, plan):
        self._current_plan = plan if isinstance(plan, dict) else None

        if isinstance(plan, dict):
            nombre = plan.get("nombre", "")
            pricing_model = plan.get("pricing_model") or "PER_HA"
            precio_base = float(plan.get("precio_base") or 0)
            max_ha = float(plan.get("max_ha") or 0)
            precio_excedente = float(plan.get("precio_ha_excedente") or 0)
        else:
            nombre = self.cmb_plan.currentText() if plan else ""
            pricing_model = "PER_HA"
            precio_base = 0
            max_ha = 0
            precio_excedente = 0

        self._set_plan_values(nombre, pricing_model, precio_base, max_ha, precio_excedente)

    def _set_plan_values(self, nombre: str, pricing_model: str, precio_base: float, max_ha: float = 0, precio_excedente: float = 0):
        self.txt_concepto.setText(nombre)
        self.txt_pricing_model.setText(pricing_model)

        is_package = pricing_model == "PACKAGE"

        self.spin_precio_ha_plan.setValue(0 if is_package else precio_base)
        self.spin_precio_ha_aplicado.setValue(0 if is_package else precio_base)
        self.spin_precio_paquete_aplicado.setValue(precio_base if is_package else 0)
        self.spin_max_ha_paquete.setValue(max_ha if is_package else 0)
        self.spin_precio_ha_excedente.setValue(precio_excedente if is_package else 0)

        self.spin_max_ha_paquete.setEnabled(False)
        self.spin_precio_ha_excedente.setEnabled(is_package)

        self._aplicar_estado_precio_por_modelo()
        self._recalcular_resumen()

    def _on_precio_manual_toggled(self, checked: bool):
        self._aplicar_estado_precio_por_modelo()

        if checked:
            return

        plan = self._get_current_plan_dict()
        pricing_model = self.txt_pricing_model.text() or "PER_HA"

        precio_base = float((plan or {}).get("precio_base") or 0)
        max_ha = float((plan or {}).get("max_ha") or 0)
        precio_excedente = float((plan or {}).get("precio_ha_excedente") or 0)

        if pricing_model == "PACKAGE":
            self.spin_precio_paquete_aplicado.setValue(precio_base)
            self.spin_max_ha_paquete.setValue(max_ha)
            self.spin_precio_ha_excedente.setValue(precio_excedente)
        else:
            self.spin_precio_ha_aplicado.setValue(precio_base)

        self._recalcular_resumen()

    def _get_current_plan_dict(self):
        if isinstance(self._current_plan, dict):
            return self._current_plan

        data = self.cmb_plan.currentData()
        return data if isinstance(data, dict) else None

    def _aplicar_estado_precio_por_modelo(self):
        manual = self.chk_precio_manual.isChecked()
        pricing_model = self.txt_pricing_model.text() or "PER_HA"

        self.spin_precio_ha_aplicado.setEnabled(manual and pricing_model != "PACKAGE")
        self.spin_precio_paquete_aplicado.setEnabled(manual and pricing_model == "PACKAGE")
        self.spin_precio_ha_excedente.setEnabled(pricing_model == "PACKAGE")

    # ------------------------------------------------------------------
    # Edición de tabla
    # ------------------------------------------------------------------

    def _on_lote_item_changed(self, item: QtWidgets.QTreeWidgetItem, column: int):
        if column != 4:
            return

        value = max(self._to_decimal(item.text(4)), Decimal("0"))

        self.tree_lotes.blockSignals(True)
        item.setText(4, self._fmt_number(value))

        lote = item.data(0, Qt.UserRole)
        if isinstance(lote, dict):
            ha_real = Decimal(str(lote.get("area_ha") or 0))
            item.setText(5, self._get_norma_text(ha_real))

        self.tree_lotes.blockSignals(False)
        self._recalcular_resumen()

    # ------------------------------------------------------------------
    # Cálculos
    # ------------------------------------------------------------------

    def _calcular_importes(self):
        pricing_model = self.txt_pricing_model.text() or "PER_HA"

        ha_reales = self._money_like(self._sum_lote_decimal("real"))
        ha_facturadas = self._money_like(self._sum_lote_decimal("facturada"))

        precio_ha = self._money_like(Decimal(str(self.spin_precio_ha_aplicado.value())))
        precio_paquete = self._money_like(Decimal(str(self.spin_precio_paquete_aplicado.value())))
        precio_excedente = self._money_like(Decimal(str(self.spin_precio_ha_excedente.value())))
        max_ha = self._money_like(Decimal(str(self.spin_max_ha_paquete.value())))
        iva_pct = self._money_like(Decimal(str(self.spin_iva.value())))

        if pricing_model == "PACKAGE":
            ha_excedente = max(Decimal("0"), ha_facturadas - max_ha)
            base_excedente = ha_excedente * precio_excedente
            base = precio_paquete + base_excedente
        else:
            ha_excedente = Decimal("0")
            base_excedente = Decimal("0")
            base = ha_facturadas * precio_ha

        iva = base * iva_pct / Decimal("100")

        return {
            "pricing_model": pricing_model,
            "ha_reales": self._money_like(ha_reales),
            "ha_facturadas": self._money_like(ha_facturadas),
            "ha_excedente": self._money_like(ha_excedente),
            "max_ha_paquete": self._money_like(max_ha),
            "precio_ha": self._money_like(precio_ha),
            "precio_paquete": self._money_like(precio_paquete),
            "precio_ha_excedente": self._money_like(precio_excedente),
            "base_excedente": self._money_like(base_excedente),
            "iva_pct": self._money_like(iva_pct),
            "base": self._money_like(base),
            "iva": self._money_like(iva),
            "total": self._money_like(base + iva),
        }

    def _recalcular_resumen(self):
        calc = self._calcular_importes()

        self.lbl_items.setText(str(len(self._get_lotes_items())))
        self.lbl_ha_real_total.setText(self._fmt_number(calc["ha_reales"]))
        self.lbl_ha_fact_total.setText(self._fmt_number(calc["ha_facturadas"]))
        self.lbl_ha_excedente.setText(self._fmt_number(calc["ha_excedente"]))
        self.lbl_precio_ha.setText(f"{self._fmt_money(calc['precio_ha'])}/ha")
        self.lbl_precio_paquete.setText(self._fmt_money(calc["precio_paquete"]))
        self.lbl_precio_excedente.setText(f"{self._fmt_money(calc['precio_ha_excedente'])}/ha")
        self.lbl_base_excedente.setText(self._fmt_money(calc["base_excedente"]))
        self.lbl_base.setText(self._fmt_money(calc["base"]))
        self.lbl_iva.setText(self._fmt_money(calc["iva"]))
        self.lbl_total.setText(self._fmt_money(calc["total"]))

    # ------------------------------------------------------------------
    # Payload
    # ------------------------------------------------------------------

    def _cliente_payload(self) -> dict:
        return {
            "idpersona": self.idpersona,
            "razon_social": self.line_razon_social.text().strip(),
            "nif": self.line_dni.text().strip(),
            "person_type": self.combo_person_type.currentText() if self.combo_person_type.currentIndex() > 0 else None,
            "direccion": self.line_direccion.text().strip(),
            "provincia": self.line_provincia.text().strip(),
            "municipio": self.line_municipio.text().strip(),
            "codigo_postal": self.line_cp.text().strip(),
            "pais": self.line_pais.text().strip() or "ESP",
            "email": self.line_email.text().strip(),
            "telefono": self.line_telefono.text().strip(),
        }

    def _collect_data(self):
        calc = self._calcular_importes()
        pricing_model = calc["pricing_model"]

        return {
            "factura": {
                "idempresa": 1,
                "idexplotacion": int(self.idexplotacion),
                "idagricultor_payer": self._get_idagricultor_payer(),
                "modo": "UNICA",
                "idserie": self.cmb_serie.currentData(),
                "fecha_emision": self.date_fecha_emision.date().toString("yyyy-MM-dd"),
                "fecha_vencimiento": self.date_fecha_vencimiento.date().toString("yyyy-MM-dd"),
            },
            "cliente": self._cliente_payload(),
            "linea": {
                "idplan": self.cmb_plan.get_current_plan_id(),
                "concepto": self.txt_concepto.text().strip(),
                "pricing_model": pricing_model,
                "ha_facturadas": float(calc["ha_facturadas"]),
                "precio_ha_aplicado": float(calc["precio_ha"]) if pricing_model == "PER_HA" else None,
                "precio_paquete_aplicado": float(calc["precio_paquete"]) if pricing_model == "PACKAGE" else None,
                "iva_pct": float(calc["iva_pct"]),
                "anio_ipc_aplicado": None,
                "factor_ipc_aplicado": None,
            },
            "items": self._get_lotes_items(),
            "config": {
                "aplicar_area_minima": self.chk_area_minima.isChecked(),
                "area_minima_ha": float(Decimal(str(self.spin_area_minima.value()))),
                "aplicar_exceso_paquete": pricing_model == "PACKAGE",
                "max_ha_paquete": float(calc["max_ha_paquete"]) if pricing_model == "PACKAGE" else 0,
                "precio_exceso_ha": float(calc["precio_ha_excedente"]) if pricing_model == "PACKAGE" else 0,
            },
        }

    # ------------------------------------------------------------------
    # Validaciones y acciones
    # ------------------------------------------------------------------

    def _validar_payload(self, payload: dict) -> bool:
        factura = payload.get("factura") or {}
        cliente = payload.get("cliente") or {}
        linea = payload.get("linea") or {}
        items = payload.get("items") or []

        checks = [
            (factura.get("idagricultor_payer"), "Selecciona el agricultor/persona a facturar."),
            (factura.get("idserie"), "Selecciona una serie de facturación."),
            (cliente.get("razon_social"), "La razón social/nombre del cliente es obligatoria."),
            (cliente.get("nif"), "El NIF/CIF del cliente es obligatorio."),
            (cliente.get("person_type"), "Selecciona el tipo de persona: F o J."),
            (cliente.get("direccion"), "La dirección del cliente es obligatoria para FacturaE."),
            (
                cliente.get("provincia") and cliente.get("municipio") and cliente.get("codigo_postal"),
                "Provincia, municipio y código postal son obligatorios para FacturaE."
            ),
            (linea.get("idplan"), "Selecciona un plan."),
            (linea.get("concepto"), "El concepto está vacío."),
            (items, "No hay lotes/items para facturar."),
        ]

        for ok, message in checks:
            if not ok:
                QtWidgets.QMessageBox.warning(self, "Facturación", message)
                return False

        for item in items:
            if not item.get("iddata"):
                QtWidgets.QMessageBox.warning(self, "Facturación", "Hay un lote sin iddata. Revisa la capa seleccionada.")
                return False

            if float(item.get("area_ha_facturada") or 0) <= 0:
                QtWidgets.QMessageBox.warning(self, "Facturación", "Hay un item con área facturada menor o igual a 0.")
                return False

        if linea.get("pricing_model") == "PACKAGE":
            if float(linea.get("precio_paquete_aplicado") or 0) <= 0:
                QtWidgets.QMessageBox.warning(self, "Facturación", "El precio paquete debe ser mayor que 0.")
                return False
        else:
            if float(linea.get("precio_ha_aplicado") or 0) <= 0:
                QtWidgets.QMessageBox.warning(self, "Facturación", "El precio por hectárea debe ser mayor que 0.")
                return False

        return True

    def _guardar_borrador(self):
        if self.modo_edicion:
            self._guardar_cambios_factura()
            return

        self._solicitar_factura_pdf(emitir=False)

    def _emitir_factura(self):
        if self.modo_edicion:
            self._guardar_cambios_factura()
            return

        payload = self._collect_data()

        if not self._validar_payload(payload):
            return

        calc = self._calcular_importes()

        confirm = QtWidgets.QMessageBox.question(
            self,
            "Emitir factura",
            (
                "¿Confirma que desea emitir esta factura?\n\n"
                f"Cliente: {payload['cliente']['razon_social']}\n"
                f"Concepto: {payload['linea']['concepto']}\n"
                f"Items: {len(payload['items'])}\n"
                f"Ha facturadas: {payload['linea']['ha_facturadas']:.2f}\n"
                f"Base: {float(calc['base']):.2f} €\n"
                f"IVA: {float(calc['iva']):.2f} €\n"
                f"Total: {float(calc['total']):.2f} €"
            ),
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )

        if confirm != QtWidgets.QMessageBox.Yes:
            return

        self._solicitar_factura_pdf(emitir=True)

    def _collect_edit_data(self):
        """
        Payload para PATCH /billing/facturas/{uid}/editar.
        Usa la misma UI, pero adaptando la estructura al endpoint de edición.
        """
        calc = self._calcular_importes()
        pricing_model = calc["pricing_model"]

        factura = {
            "idexplotacion": int(self.idexplotacion),
            "idagricultor_payer": self._get_idagricultor_payer(),
            "modo": "UNICA",
            "fecha_vencimiento": self.date_fecha_vencimiento.date().toString("yyyy-MM-dd"),
            "cliente_razon_social": self.line_razon_social.text().strip(),
            "cliente_nif": self.line_dni.text().strip(),
            "cliente_person_type": self.combo_person_type.currentText() if self.combo_person_type.currentIndex() > 0 else None,
            "cliente_direccion": self.line_direccion.text().strip(),
            "cliente_provincia": self.line_provincia.text().strip(),
            "cliente_municipio": self.line_municipio.text().strip(),
            "cliente_codigo_postal": self.line_cp.text().strip(),
            "cliente_pais": self.line_pais.text().strip() or "ESP",
            "cliente_email": self.line_email.text().strip(),
            "cliente_telefono": self.line_telefono.text().strip(),
            "aplicar_area_minima": self.chk_area_minima.isChecked(),
            "area_minima_ha": float(Decimal(str(self.spin_area_minima.value()))),
            "aplicar_exceso_paquete": pricing_model == "PACKAGE",
            "max_ha_paquete": float(calc["max_ha_paquete"]) if pricing_model == "PACKAGE" else 0,
            "precio_exceso_ha": float(calc["precio_ha_excedente"]) if pricing_model == "PACKAGE" else 0,
        }

        lineas = [
            {
                "idplan": self.cmb_plan.get_current_plan_id(),
                "concepto": self.txt_concepto.text().strip(),
                "pricing_model": pricing_model,
                "ha_facturadas": float(calc["ha_facturadas"]),
                "precio_ha_aplicado": float(calc["precio_ha"]) if pricing_model == "PER_HA" else None,
                "precio_paquete_aplicado": float(calc["precio_paquete"]) if pricing_model == "PACKAGE" else None,
                "iva_pct": float(calc["iva_pct"]),
                "anio_ipc_aplicado": None,
                "factor_ipc_aplicado": None,
                "items": self._get_lotes_items(),
            }
        ]

        # Si es paquete con excedente, enviamos una segunda línea sin items.
        # Los iddata quedan vinculados a la línea principal del paquete.
        if pricing_model == "PACKAGE" and calc["ha_excedente"] > Decimal("0"):
            lineas.append(
                {
                    "idplan": self.cmb_plan.get_current_plan_id(),
                    "concepto": f"EXCESO {self.txt_concepto.text().strip()} SOBRE {self._fmt_number(calc['max_ha_paquete'])} HA",
                    "pricing_model": "PER_HA",
                    "ha_facturadas": float(calc["ha_excedente"]),
                    "precio_ha_aplicado": float(calc["precio_ha_excedente"]),
                    "precio_paquete_aplicado": None,
                    "iva_pct": float(calc["iva_pct"]),
                    "anio_ipc_aplicado": None,
                    "factor_ipc_aplicado": None,
                    "items": [],
                }
            )

        return {
            "factura": factura,
            "lineas": lineas,
        }

    def _guardar_cambios_factura(self):
        if not self.uid_factura:
            QtWidgets.QMessageBox.warning(
                self,
                "Facturación",
                "No se recibió el uid de la factura que se quiere editar."
            )
            return

        payload_validacion = self._collect_data()

        if not self._validar_payload(payload_validacion):
            return

        calc = self._calcular_importes()

        confirm = QtWidgets.QMessageBox.question(
            self,
            "Guardar cambios",
            (
                "¿Confirma que desea guardar los cambios de esta factura?\n\n"
                f"Cliente: {payload_validacion['cliente']['razon_social']}\n"
                f"Concepto: {payload_validacion['linea']['concepto']}\n"
                f"Items: {len(payload_validacion['items'])}\n"
                f"Ha facturadas: {payload_validacion['linea']['ha_facturadas']:.2f}\n"
                f"Base: {float(calc['base']):.2f} €\n"
                f"IVA: {float(calc['iva']):.2f} €\n"
                f"Total: {float(calc['total']):.2f} €"
            ),
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
        )

        if confirm != QtWidgets.QMessageBox.Yes:
            return

        response = self._api_request.patch(
            f"/billing/facturas/{self.uid_factura}/editar",
            self._collect_edit_data(),
        )

        if not response or not response.get("ok"):
            QtWidgets.QMessageBox.warning(
                self,
                "Facturación",
                f"No se pudo editar la factura.\n\n{self._format_api_error(response)}"
            )
            return

        data = self._extract_response_data(response)

        QtWidgets.QMessageBox.information(
            self,
            "Facturación",
            (
                "Factura actualizada correctamente.\n\n"
                f"Código: {(data or {}).get('codigo', '-')}\n"
                f"Total: {(data or {}).get('total', '-')}"
            )
        )

        self.accept()

    # ------------------------------------------------------------------
    # PDF
    # ------------------------------------------------------------------

    def _format_api_error(self, response) -> str:
        if not response:
            return "Sin respuesta del backend."

        status = response.get("http_status") if isinstance(response, dict) else None
        data = response.get("data") if isinstance(response, dict) else response

        if isinstance(data, dict):
            detail = data.get("detail")

            if isinstance(detail, dict):
                message = detail.get("message") or detail.get("detail") or str(detail)
            elif isinstance(detail, list):
                message = "\n".join(str(x) for x in detail)
            else:
                message = str(detail or data)

            if status:
                return f"HTTP {status}\n{message}"
            return message

        if status:
            return f"HTTP {status}\n{data}"

        return str(data)

    def _extract_response_data(self, response):
        """
        Acepta las dos estructuras durante la transición:
        1) JSON directo legacy: {"uid": ...}
        2) Envelope nuevo: {"ok": True, "http_status": 200, "data": {...}}
        """
        if not isinstance(response, dict):
            return None

        if "ok" in response and "data" in response:
            return response.get("data") or {}

        return response

    def _seleccionar_codigo_disponible(self):
        """
        Consulta códigos de facturas anuladas disponibles para la serie actual.
        Devuelve idcodigo o None si el usuario no quiere reutilizar ninguno.
        """
        idserie = self.cmb_serie.currentData()

        if not idserie:
            return None

        codigos = self._api_request.get(
            "/billing/facturas/codigos_disponibles",
            params={
                "idserie": idserie,
                "idempresa": 1,
            },
        )

        if not codigos:
            return None

        opciones = ["No reutilizar código"]

        for codigo in codigos:
            opciones.append(
                f"{codigo.get('codigo')} | fecha original: {codigo.get('fecha_emision_original', '-')}"
            )

        selected, ok = QtWidgets.QInputDialog.getItem(
            self,
            "Código disponible",
            "Hay códigos de facturas anuladas disponibles para esta serie.\nSelecciona uno si quieres reutilizarlo:",
            opciones,
            0,
            False,
        )

        if not ok or selected == "No reutilizar código":
            return None

        index = opciones.index(selected) - 1
        return codigos[index].get("idcodigo")

    def _solicitar_factura_pdf(self, emitir: bool):
        """
        Genera/emite la factura y descarga posteriormente el PDF.
        """

        payload = self._collect_data()

        if not self._validar_payload(payload):
            return

        endpoint = f"/billing/facturar_por_data?emitir={'true' if emitir else 'false'}"

        if emitir:
            idcodigo_disponible = self._seleccionar_codigo_disponible()
            if idcodigo_disponible:
                endpoint += f"&idcodigo_disponible={idcodigo_disponible}"

        response = self._api_request.post(endpoint, payload, full_response=True)

        if not response or not response.get("ok"):
            QtWidgets.QMessageBox.warning(
                self,
                "Facturación",
                f"No se pudo crear la factura.\n\n{self._format_api_error(response)}"
            )
            return

        data = self._extract_response_data(response)
        uid = (data or {}).get("uid")

        if not uid:
            QtWidgets.QMessageBox.warning(
                self,
                "Facturación",
                f"No se recibió uid de factura.\n\nRespuesta:\n{data}"
            )
            return

        pdf_response = self._api_request.get_binary(
            f"/billing/facturas/{uid}/pdf"
        )

        self._guardar_pdf_factura(pdf_response, emitir)

    def _guardar_pdf_factura(self, response: dict, emitir: bool):
        """
        Guarda el PDF devuelto por backend usando el filename enviado
        en Content-Disposition.
        """

        if not response or not response.get("ok"):
            QtWidgets.QMessageBox.warning(
                self,
                "Facturación",
                f"No se pudo descargar el PDF.\n\n{response}"
            )
            return

        content = response.get("content")

        if not content:
            QtWidgets.QMessageBox.warning(
                self,
                "Facturación",
                "El backend no devolvió contenido PDF."
            )
            return

        filename = self._get_pdf_filename(
            response.get("headers", {}) or {},
            emitir
        )

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
                "Facturación",
                f"Factura guardada correctamente:\n{path}"
            )

            self.cmb_serie.refresh()

        except Exception as ex:
            QtWidgets.QMessageBox.warning(
                self,
                "Facturación",
                f"No se pudo guardar el PDF.\n\n{ex}"
            )


    def _get_pdf_filename(self, headers: dict, emitir: bool) -> str:
        """
        Obtiene el nombre del PDF desde Content-Disposition.
        """

        disposition = ""

        for key, value in headers.items():
            if key.lower() == "content-disposition":
                disposition = value or ""
                break

        filename = None

        try:
            if "filename=" in disposition:
                filename = disposition.split("filename=")[-1]
                filename = filename.strip().strip('"').strip("'")
        except Exception:
            filename = None

        if filename:
            if not filename.lower().endswith(".pdf"):
                filename += ".pdf"

            return filename

        tipo = "factura_emitida" if emitir else "factura_borrador"

        return f"{tipo}.pdf"
    
    # ------------------------------------------------------------------
    # Formato y decimales
    # ------------------------------------------------------------------

    def _to_decimal(self, value) -> Decimal:
        txt = str(value or "0").strip()
        txt = txt.replace("€", "").replace("/ha", "").replace("ha", "").strip()
        txt = txt.replace(".", "").replace(",", ".")

        try:
            return Decimal(txt)
        except Exception:
            return Decimal("0")

    def _money_like(self, value: Decimal) -> Decimal:
        return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def _fmt_money(self, value: Decimal) -> str:
        return f"{self._money_like(value):,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")

    def _fmt_number(self, value: Decimal) -> str:
        return f"{self._money_like(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")