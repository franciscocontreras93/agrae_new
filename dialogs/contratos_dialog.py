import http
import rlcompleter

from qgis.PyQt import QtWidgets, QtCore

from ..gui.components.CustomComboBox import PlanesComboBox
from ..gui.components.CustomTreeWidget import ContratosTreePanel

from ..core.api import APIRequest




class ContratosDialog(QtWidgets.QDialog):
    """
    Diálogo base (Opción C):
      - Tab 1: Contrato activo (detalle read-only)
      - Tab 2: Histórico (TreeWidget por Año -> Contrato)
      - Tab 3: Nuevo contrato (formulario)
    """

    def __init__(self, idexplotacion:int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("aGrae | Gestión de contratos")
        self.resize(900, 520)

        self._api_request = APIRequest()  # para llamadas a endpoints (puedes pasar backend_url si quieres)

        self._contratos = []  # lista cruda del endpoint (dicts)

        main = QtWidgets.QVBoxLayout(self)
        main.setContentsMargins(10, 10, 10, 10)
        main.setSpacing(10)

        self.idexplotacion = idexplotacion

        # Tabs
        self.tabs = QtWidgets.QTabWidget()
        main.addWidget(self.tabs)

        # ----------------------------
        # TAB 1: ACTIVO
        # ----------------------------
        # self.tab_activo = QtWidgets.QWidget()
        # self.tabs.addTab(self.tab_activo, "Contrato activo")
        # self._build_tab_activo()

        # ----------------------------
        # TAB 2: HISTORICO (TREE)
        # ----------------------------
        self.tab_historico = QtWidgets.QWidget()
        self.tabs.addTab(self.tab_historico, "Histórico")
        self._build_tab_historico()

        # ----------------------------
        # TAB 3: NUEVO
        # ----------------------------
        self.tab_nuevo = QtWidgets.QWidget()
        self.tabs.addTab(self.tab_nuevo, "Crear o Editar contratos")
        self._build_tab_nuevo()

        # Botonera inferior
        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Close)
        btns.rejected.connect(self.reject)
        btns.accepted.connect(self.accept)
        main.addWidget(btns)

    # ------------------------------------------------------------------
    # Construcción UI
    # ------------------------------------------------------------------
    def _build_tab_activo(self):
        lay = QtWidgets.QVBoxLayout(self.tab_activo)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(10)

        gb = QtWidgets.QGroupBox("Detalle del contrato activo")
        form = QtWidgets.QFormLayout(gb)
        form.setContentsMargins(10, 12, 10, 10)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)

        self.lbl_act_id = QtWidgets.QLabel("-")
        self.lbl_act_vig = QtWidgets.QLabel("-")
        self.lbl_act_explot = QtWidgets.QLabel("-")
        self.lbl_act_plan = QtWidgets.QLabel("-")
        self.lbl_act_model = QtWidgets.QLabel("-")
        self.lbl_act_precio = QtWidgets.QLabel("-")
        self.lbl_act_maxha = QtWidgets.QLabel("-")

        form.addRow("ID contrato:", self.lbl_act_id)
        form.addRow("Vigencia:", self.lbl_act_vig)
        form.addRow("Explotación:", self.lbl_act_explot)
        form.addRow("Plan:", self.lbl_act_plan)
        form.addRow("Modelo:", self.lbl_act_model)
        form.addRow("Precio contratado:", self.lbl_act_precio)
        form.addRow("Max ha:", self.lbl_act_maxha)

        lay.addWidget(gb)

        # Acciones rápidas
        actions = QtWidgets.QHBoxLayout()
        self.btn_nuevo_desde_activo = QtWidgets.QPushButton("Crear nuevo contrato…")
        self.btn_duplicar_activo = QtWidgets.QPushButton("Duplicar contrato activo")
        actions.addWidget(self.btn_nuevo_desde_activo)
        actions.addWidget(self.btn_duplicar_activo)
        actions.addStretch(1)
        lay.addLayout(actions)

        # (Opcional) nota/estado
        self.lbl_act_estado = QtWidgets.QLabel("")
        self.lbl_act_estado.setStyleSheet("color: #666;")
        lay.addWidget(self.lbl_act_estado)

        lay.addStretch(1)

        # Conexiones básicas (sin lógica todavía)
        self.btn_nuevo_desde_activo.clicked.connect(lambda: self.tabs.setCurrentWidget(self.tab_nuevo))

    def _build_tab_historico(self):
        
        lay = QtWidgets.QVBoxLayout(self.tab_historico)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(10)

        # Panel completo (checkbox + expand/collapse + toggle detalle + splitter + tree + detalle)
        self.contratos_panel = ContratosTreePanel(
            parent=self.tab_historico,
            # endpoint="/billing/contratos",  # si en la clase ya viene por defecto, lo podés omitir
            param_provider=lambda: {"idexplotacion": self.idexplotacion},
            # headers_provider=lambda: {"Authorization": f"Bearer {self.token}"},  # si aplica
            auto_load=True,
        )
        self.contratos_panel.btn_duplicar.setEnabled(False)   #TODO DEFINIR SI SE VA A PERMITIR MODIFICAR O ELIMINAR Y CREAR UNO NUEVO.
        self.contratos_panel.btn_editar.setEnabled(False)  #TODO DEFINIR SI SE VA A PERMITIR MODIFICAR O ELIMINAR Y CREAR UNO NUEVO.
        self.contratos_panel.btn_editar.clicked.connect(self._on_update_activo_clicked)
        self.contratos_panel.btn_eliminar.clicked.connect(self._on_delete_clicked)

        # Si querés reaccionar cuando el usuario seleccione un contrato:
        # self.contratos_panel.contrato_selected.connect(self._on_contrato_selected)

        # Manejo de errores (opcional)
        self.contratos_panel.load_error.connect(
            lambda msg: QtWidgets.QMessageBox.warning(self, "Contratos", msg)
        )

        lay.addWidget(self.contratos_panel)

    def _build_tab_nuevo(self):
        lay = QtWidgets.QVBoxLayout(self.tab_nuevo)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(10)

        gb = QtWidgets.QGroupBox("Crear o Editar contrato")
        form = QtWidgets.QFormLayout(gb)
        form.setContentsMargins(10, 12, 10, 10)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)

        #! ESTO LO VAMOS A QUITAR
        self.txt_explot = QtWidgets.QLineEdit()
        self.txt_explot.setReadOnly(True)
        #! --------------------------------------- #

        self.cmb_plan = PlanesComboBox(auto_enable_on_load=True)
        self.cmb_plan.plan_changed.connect(self._on_plan_changed)  # luego lo cargas con endpoint /plans
        # self.cmb_plan.addItem("Seleccione un plan…", None)

        self.date_desde = QtWidgets.QDateEdit(QtCore.QDate.currentDate())
        self.date_desde.setCalendarPopup(True)

        self.date_hasta = QtWidgets.QDateEdit(QtCore.QDate.currentDate().addYears(1))
        self.date_hasta.setCalendarPopup(True)

        self.date_desde.dateChanged.connect(self._on_fecha_desde_changed)

        self.spin_precio_plan = QtWidgets.QDoubleSpinBox()
        self.spin_precio_plan.setDecimals(2)
        self.spin_precio_plan.setMaximum(10_000_000)
        self.spin_precio_plan.setSuffix(" €")

        self.spin_precio_plan.setReadOnly(True)



        self.spin_precio = QtWidgets.QDoubleSpinBox()
        self.spin_precio.setDecimals(2)
        self.spin_precio.setMaximum(10_000_000)
        self.spin_precio.setSuffix(" €")
        self.spin_precio.setEnabled(False)

        self.chk_usar_precio = QtWidgets.QCheckBox("Usar precio base del plan")
        self.chk_usar_precio.setChecked(True)
        # self.chk_usar_precio.setEnabled(False)
        self.chk_usar_precio.toggled.connect(self._on_chk_usar_precio_toggled)



        #! form.addRow("Explotación:", self.txt_explot)

        form.addRow("Plan:", self.cmb_plan)
        form.addRow("Precio base:", self.spin_precio_plan)
        form.addRow("Vigencia desde:", self.date_desde)
        form.addRow("Vigencia hasta:", self.date_hasta)
        form.addRow("Precio contratado:", self.spin_precio)
        form.addRow("", self.chk_usar_precio)

        lay.addWidget(gb)

        actions = QtWidgets.QHBoxLayout()
        self.btn_guardar = QtWidgets.QPushButton("Guardar")
        self.btn_guardar.clicked.connect(self._on_guardar_clicked)
        self.btn_cancelar = QtWidgets.QPushButton("Cancelar")
        actions.addWidget(self.btn_guardar)
        actions.addWidget(self.btn_cancelar)
        actions.addStretch(1)
        lay.addLayout(actions)

        lay.addStretch(1)

        self.btn_cancelar.clicked.connect(lambda: self.tabs.setCurrentWidget(self.tab_activo))

    # ------------------------------------------------------------------
    # API de carga de datos (para cuando pegues endpoint)
    # ------------------------------------------------------------------
    
    def set_contratos(self, contratos: list, nombre_explotacion: str = ""):
        """
        contratos: lista de dicts como el JSON que mostraste.
        """
        self._contratos = contratos or []
        self.txt_explot.setText(nombre_explotacion or "")
        self._update_activo()
        self._rebuild_tree()

    def _update_activo(self):
        """
        Selecciona el contrato 'activo' según fechas (si existe) y rellena labels del tab activo.
        """
        hoy = QtCore.QDate.currentDate()

        activo = None
        for c in self._contratos:
            d = QtCore.QDate.fromString(c.get("vigencia_desde", ""), "yyyy-MM-dd")
            h = QtCore.QDate.fromString(c.get("vigencia_hasta", ""), "yyyy-MM-dd")
            if d.isValid() and h.isValid() and (d <= hoy <= h):
                activo = c
                break

        if not activo:
            self.lbl_act_id.setText("-")
            self.lbl_act_vig.setText("-")
            self.lbl_act_explot.setText("-")
            self.lbl_act_plan.setText("-")
            self.lbl_act_model.setText("-")
            self.lbl_act_precio.setText("-")
            self.lbl_act_maxha.setText("-")
            self.lbl_act_estado.setText("No hay contrato activo para la fecha actual.")
            return

        self.lbl_act_id.setText(str(activo.get("idcontrato", "-")))
        self.lbl_act_vig.setText(f"{activo.get('vigencia_desde','-')} → {activo.get('vigencia_hasta','-')}")
        exp = (activo.get("explotacion") or {}).get("nombre", "-")
        self.lbl_act_explot.setText(exp)
        plan = (activo.get("plan") or {}).get("nombre", "-")
        self.lbl_act_plan.setText(plan)
        model = (activo.get("plan") or {}).get("pricing_model", "-")
        self.lbl_act_model.setText(model)
        self.lbl_act_precio.setText(str(activo.get("precio_contratado", "-")))
        self.lbl_act_maxha.setText(str((activo.get("plan") or {}).get("max_ha", "-")))
        self.lbl_act_estado.setText("Contrato activo detectado.")

    def _rebuild_tree(self):
        self.tree.clear()

        hoy = QtCore.QDate.currentDate()
        solo_activos = self.chk_solo_activos.isChecked()

        # Agrupar por año (desde)
        buckets = {}  # year -> list
        for c in self._contratos:
            d = QtCore.QDate.fromString(c.get("vigencia_desde", ""), "yyyy-MM-dd")
            h = QtCore.QDate.fromString(c.get("vigencia_hasta", ""), "yyyy-MM-dd")

            if solo_activos and not (d.isValid() and h.isValid() and (d <= hoy <= h)):
                continue

            year = d.year() if d.isValid() else 0
            buckets.setdefault(year, []).append(c)

        # Orden descendente por año (0 al final)
        for year in sorted(buckets.keys(), reverse=True):
            year_label = str(year) if year != 0 else "Sin fecha"
            root = QtWidgets.QTreeWidgetItem(self.tree, [year_label])
            root.setFirstColumnSpanned(False)
            root.setExpanded(True)

            # Orden por vigencia_desde desc
            def key_fn(c):
                qd = QtCore.QDate.fromString(c.get("vigencia_desde", ""), "yyyy-MM-dd")
                return qd.toJulianDay() if qd.isValid() else -1

            for c in sorted(buckets[year], key=key_fn, reverse=True):
                plan = c.get("plan") or {}
                label = f"{c.get('vigencia_desde','-')} → {c.get('vigencia_hasta','-')}  (#{c.get('idcontrato','-')})"
                item = QtWidgets.QTreeWidgetItem(root, [
                    label,
                    plan.get("nombre", "-"),
                    plan.get("pricing_model", "-"),
                    str(c.get("precio_contratado", "-")),
                    str(plan.get("max_ha", "-")),
                ])
                # Guardar el dict completo en el item
                item.setData(0, QtCore.Qt.UserRole, c)

        self.tree.expandToDepth(0)

    def _on_tree_selection_changed(self, current: QtWidgets.QTreeWidgetItem, previous: QtWidgets.QTreeWidgetItem):
        if not current:
            return

        data = current.data(0, QtCore.Qt.UserRole)
        if not isinstance(data, dict):
            # es un nodo de año
            self._clear_detail()
            return

        self._fill_detail(data)

    def _clear_detail(self):
        for lbl in (
            self.lbl_det_id, self.lbl_det_vig, self.lbl_det_explot, self.lbl_det_plan,
            self.lbl_det_model, self.lbl_det_precio, self.lbl_det_maxha
        ):
            lbl.setText("-")

    def _fill_detail(self, c: dict):
        self.lbl_det_id.setText(str(c.get("idcontrato", "-")))
        self.lbl_det_vig.setText(f"{c.get('vigencia_desde','-')} → {c.get('vigencia_hasta','-')}")
        exp = (c.get("explotacion") or {}).get("nombre", "-")
        self.lbl_det_explot.setText(exp)
        plan = (c.get("plan") or {})
        self.lbl_det_plan.setText(plan.get("nombre", "-"))
        self.lbl_det_model.setText(plan.get("pricing_model", "-"))
        self.lbl_det_precio.setText(str(c.get("precio_contratado", "-")))
        self.lbl_det_maxha.setText(str(plan.get("max_ha", "-")))


    # ==================================================================================================
    # HELPERS
    # ==================================================================================================

    def _on_plan_changed(self, plan: dict):
        print(plan)
        if plan is None:
            return
        self.spin_precio_plan.setValue(float(plan.get("precio_base", 0)))


    def _on_fecha_desde_changed(self, Date: QtCore.QDate):
        
        date = Date.addYears(1)
        # 1) Setear fecha por defecto
        self.date_hasta.setDate(date)
        # 2) Limitar mínimo permitido
        self.date_hasta.setMinimumDate(date)


    def _on_chk_usar_precio_toggled(self, checked: bool):
        self.spin_precio.setEnabled(not checked)


    
    
    # =================================================================================================
    # ACCIONES (guardar, duplicar, nuevo desde activo, etc)
    # =================================================================================================

    def _on_guardar_clicked(self):
        """ 
        Aquí iría la lógica para validar el formulario y llamar al endpoint de creación de contrato.
         - Validar que plan esté seleccionado
         - Validar que vigencia_desde < vigencia_hasta
         - Validar que precio_contratado > 0 (si no se usa precio base)
         - Mostrar mensajes de error si algo no está bien
         - Si todo es correcto, llamar al endpoint (con requests o similar) y pasar los datos necesarios
         - Manejar la respuesta: si es éxito, mostrar mensaje y recargar contratos; si es error, mostrar mensaje.
         - Opcional: bloquear UI mientras se hace la petición para evitar múltiples clicks.
        """

        payload = {}

        payload["idexplotacion"] = int(self.idexplotacion)
        payload["idplan"] = int(self.cmb_plan.get_current_plan_id())
        payload["vigencia_desde"] = self.date_desde.date().toString("yyyy-MM-dd")
        payload["vigencia_hasta"] = self.date_hasta.date().toString("yyyy-MM-dd")
        if self.chk_usar_precio.isChecked():
            payload["precio_contratado"] = self.spin_precio_plan.value()
        else:
            payload["precio_contratado"] = self.spin_precio.value()
        
        # print(payload)
        confirm = QtWidgets.QMessageBox.question(
            self, "Confirmar creación", f"¿Confirma que desea crear este contrato?\n\nPlan: {self.cmb_plan.currentText()}\nVigencia: {payload['vigencia_desde']} → {payload['vigencia_hasta']}\nPrecio: {payload['precio_contratado']} €",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        if confirm == QtWidgets.QMessageBox.Yes:
            r = self._api_request.post("billing/contratos", data=payload)
            # print("Respuesta del endpoint de creación:", r)
            if not r:
                QtWidgets.QMessageBox.warning(self, "Error de conexión", "No se pudo conectar al servidor. Por favor, intenta nuevamente.")
                return
            if r["http_status"] == 201:
                QtWidgets.QMessageBox.information(self, "Contrato creado", r.get("data", {}).get("message", "El contrato ha sido creado exitosamente."))
                self.contratos_panel.load_items()  # recargar la lista de contratos
                self.tabs.setCurrentWidget(self.tab_historico)  # ir al histórico para ver el nuevo contrato
                return
            if r["http_status"] != 201:
               QtWidgets.QMessageBox.warning(self, "Error al crear", f"No se pudo crear el contrato: {r.get('data', {}).get('message', 'Error desconocido')}")
            

    def _on_update_activo_clicked(self):
        """
        Maneja la acción de actualización para un contrato seleccionado.
        
        Recupera el contrato actualmente seleccionado del panel de contratos y completa
        el formulario de edición con sus datos. Configura los campos del formulario con
        los detalles del contrato incluyendo:
        - Plan (mediante selección en combo box)
        - Precio del contrato (con opción de anulación de precio personalizado)
        - Fechas de vigencia (desde y hasta)
        
        Muestra un mensaje de advertencia si no hay ningún contrato seleccionado.
        Cambia la interfaz a la pestaña de edición después de cargar exitosamente
        los datos del contrato.
        
        Lanza:
            QtWidgets.QMessageBox.warning: Si no hay contrato seleccionado para editar.
        """
        contrato = self.contratos_panel._get_selected_contrato()
        print("Contrato seleccionado para editar:", contrato)
        if not contrato:
            QtWidgets.QMessageBox.warning(self, "Editar contrato", "Por favor, selecciona un contrato para editar.")
            return
        
        idplan = (contrato.get("plan") or {}).get("idplan")
        precioContratado = float(contrato.get("precio_contratado", 0))
        fechaDesde = QtCore.QDate.fromString(contrato.get("vigencia_desde", ""), "yyyy-MM-dd")
        fechaHasta = QtCore.QDate.fromString(contrato.get("vigencia_hasta", ""), "yyyy-MM-dd")

        if idplan:
            self.cmb_plan.select_by_id(idplan)
        else:
            self.cmb_plan.setCurrentIndex(-1)

        self.date_desde.setDate(fechaDesde if fechaDesde.isValid() else QtCore.QDate.currentDate())
        self.date_hasta.setDate(fechaHasta if fechaHasta.isValid() else QtCore.QDate.currentDate().addYears(1))

        if precioContratado != self.spin_precio_plan.value():
            self.chk_usar_precio.setChecked(False)
            self.spin_precio.setValue(precioContratado)
        

        
        # self.tab_nuevo.setTitle("Editar contrato")
        # self.tabs.getTabBar().setTabText(self.tabs.indexOf(self.tab_nuevo), "Editar contrato")
        self.tabs.setCurrentWidget(self.tab_nuevo)
        # Aquí podrías cargar los datos del contrato seleccionado en el formulario de edición (similar a _fill_detail pero con campos editables)
        # Luego, al guardar, llamarías a un endpoint de actualización (PUT/PATCH) en lugar de creación.

    def _on_delete_clicked(self):
        """
        Lógica para eliminar un contrato.
        Debería pedir confirmación al usuario antes de eliminar.
        Luego llamar al endpoint de eliminación y manejar la respuesta similar a guardar.
        """

        idcontrato = self.contratos_panel._get_selected_contrato_id()
        if idcontrato is None:
            QtWidgets.QMessageBox.warning(self, "Eliminar contrato", "Por favor, selecciona un contrato para eliminar.")
            return
        confirm = QtWidgets.QMessageBox.question(
            self, "Confirmar eliminación", "¿Estás seguro de que deseas eliminar el contrato seleccionado?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        if confirm == QtWidgets.QMessageBox.Yes:
            # Llamar al endpoint de eliminación y manejar la respuesta
            r = self._api_request.delete(f"billing/contratos/{idcontrato}")
            # print("Respuesta del endpoint de eliminación:", r)
            if r['http_status'] == 200:
                QtWidgets.QMessageBox.information(self, "Contrato eliminado", "{}".format(r.get('data', {}).get('message', '')))
                self.contratos_panel.load_items()  # recargar la lista de contratos
            else:
                QtWidgets.QMessageBox.warning(self, "Error al eliminar", f"No se pudo eliminar el contrato: {r.get('data', {}).get('message', 'Error desconocido')}")
