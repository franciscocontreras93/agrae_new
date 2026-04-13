# -*- coding: utf-8 -*-
"""
CustomTreeWidget.py
-------------------
Panel/Widget compuesto para QGIS (PyQt5) basado en el patrón de CustomComboBox:

- Consume un endpoint REST en un hilo separado (QThread) usando GenericApiWorker
- Barra superior: checkbox "Mostrar solo activos (según fechas)", botón "Ocultar/Mostrar detalle",
  y botones Expandir/Colapsar.
- Splitter horizontal: Tree (izquierda) + Panel de detalle (derecha).
- Señales:
    - items_loaded(list[dict])
    - load_error(str)
    - item_dict_selected(dict|None)
    - contrato_selected(dict|None)  (en ContratosTreePanel)

Notas:
- Respeta el orden exacto que entrega el backend (no aplica sorted()).
- El filtro "solo activos" únicamente filtra (no reordena).

Requisitos (como en CustomComboBox):
- aGraeTools().backend_url → URL base del backend (sin slash final).
- GenericApiWorker(api_config, request_context) con señales:
    - success(object, object), error(str, object), finished_signal()

Autor: aGrae
"""

from __future__ import annotations

from typing import Callable, Optional, Any, Dict, List

from qgis.PyQt import QtWidgets, QtCore
from qgis.PyQt.QtCore import Qt, QThread

from qgis.core import QgsMessageLog, Qgis

from ...tools import aGraeTools
from ...tools.api_worker import GenericApiWorker


# =============================================================================
# Panel base reusable (compuesto)
# =============================================================================
class CustomTreePanel(QtWidgets.QWidget):
    """
    Panel base reusable:
      - Barra superior (checkbox + toggle detalle + expand/collapse)
      - QSplitter: tree + detail_widget
      - Carga desde API (GET) en background usando GenericApiWorker
      - No reordena por defecto (respeta orden backend)
    """

    items_loaded = QtCore.pyqtSignal(list)          # list[dict]
    load_error = QtCore.pyqtSignal(str)
    item_dict_selected = QtCore.pyqtSignal(object)  # dict | None

    def __init__(
        self,
        parent=None,
        *,
        endpoint: str,
        columns: Optional[List[str]] = None,
        param_provider: Optional[Callable[[], dict]] = None,
        headers_provider: Optional[Callable[[], dict]] = None,
        items_transform: Optional[Callable[[List[dict]], List[dict]]] = None,
        auto_load: bool = True,
        expand_level: int = 1,
        show_only_active_checkbox: bool = True,
        checkbox_text: str = "Mostrar solo activos (según fechas)",
        detail_title: str = "Detalle",
        auto_enable_on_load: bool = True,
    ):
        super().__init__(parent)

        self._backend = aGraeTools().backend_url.rstrip("/")
        self.endpoint = endpoint if endpoint.startswith("/") else f"/{endpoint}"

        self.param_provider = param_provider or (lambda: {})
        self.headers_provider = headers_provider or (lambda: {})
        self.items_transform = items_transform or (lambda items: items)
        self._expand_level = int(expand_level)
        self._auto_enable_on_load = bool(auto_enable_on_load)

        self._items: List[dict] = []
        self._last_splitter_sizes: Optional[List[int]] = None

        # Thread/Worker (como en CustomComboBox)
        self.api_thread: QThread | None = None
        self.api_worker: GenericApiWorker | None = None

        # ---------------- UI ----------------
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        # Barra superior
        bar = QtWidgets.QHBoxLayout()
        bar.setContentsMargins(0, 0, 0, 0)
        bar.setSpacing(6)

        self.chk_only_active = QtWidgets.QCheckBox(checkbox_text)
        self.chk_only_active.setVisible(bool(show_only_active_checkbox))
        self.chk_only_active.setChecked(False)

        self.btn_toggle_detail = QtWidgets.QPushButton("Ocultar detalle")
        self.btn_refresh = QtWidgets.QPushButton('Recargar')
        self.btn_expand = QtWidgets.QPushButton("Expandir todo")
        self.btn_collapse = QtWidgets.QPushButton("Colapsar todo")

        bar.addWidget(self.chk_only_active)
        bar.addWidget(self.btn_toggle_detail)
        bar.addWidget(self.btn_refresh)
        bar.addStretch(1)
        bar.addWidget(self.btn_expand)
        bar.addWidget(self.btn_collapse)
        root.addLayout(bar)

        # Splitter: tree + detail
        self.splitter = QtWidgets.QSplitter(Qt.Horizontal)
        root.addWidget(self.splitter)

        # Tree
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setAlternatingRowColors(True)
        self.tree.setUniformRowHeights(True)
        self.tree.setRootIsDecorated(True)
        self.tree.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

        cols = columns or ["Item"]
        self.tree.setHeaderLabels(cols)
        self.splitter.addWidget(self.tree)

        # Detail panel
        self.detail_panel = QtWidgets.QGroupBox(detail_title)
        self.detail_panel.setMinimumWidth(240)
        self.splitter.addWidget(self.detail_panel)

        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 1)

        # ---------------- Signals ---------------- 
        self.btn_refresh.clicked.connect(self.refresh)
        self.btn_expand.clicked.connect(self.tree.expandAll)
        self.btn_collapse.clicked.connect(self.tree.collapseAll)
        self.btn_toggle_detail.clicked.connect(self.toggle_detail_panel)

        self.tree.currentItemChanged.connect(self._on_current_item_changed)
        self.chk_only_active.toggled.connect(self.rebuild)

        if auto_load:
            self.refresh()

    # ---------------- API pública ----------------s
    def refresh(self) -> None:
        """Recarga los datos del endpoint con los parámetros actuales."""
        self.load_items()

    def load_items(self) -> None:
        """Lanza la petición en QThread usando GenericApiWorker. Evita cargas concurrentes."""
        if self.api_thread and self.api_thread.isRunning():
            QgsMessageLog.logMessage(
                "[CustomTreePanel] Carga ya en progreso, se omite.",
                "CustomTreePanel",
                Qgis.Info,
            )
            return

        if self._auto_enable_on_load:
            self.setEnabled(False)

        api_config = self._make_api_config()

        self.api_thread = QThread(self)
        self.api_worker = GenericApiWorker(api_config, request_context="load_items")
        self.api_worker.moveToThread(self.api_thread)

        self.api_worker.success.connect(self._handle_api_success)
        self.api_worker.error.connect(self._handle_api_error)

        self.api_worker.finished_signal.connect(self.api_thread.quit)
        self.api_worker.finished_signal.connect(self.api_worker.deleteLater)
        self.api_thread.finished.connect(self.api_thread.deleteLater)
        self.api_thread.finished.connect(self._on_load_finished)

        self.api_thread.started.connect(self.api_worker.run)
        self.api_thread.start()

    def set_endpoint(self, endpoint: str, *, refresh: bool = True) -> None:
        self.endpoint = endpoint if endpoint.startswith("/") else f"/{endpoint}"
        if refresh:
            self.refresh()

    def set_columns(self, columns: List[str], *, rebuild: bool = True) -> None:
        self.tree.setHeaderLabels(columns or ["Item"])
        if rebuild:
            self.rebuild()

    def items(self) -> List[dict]:
        return self._items

    def selected_item_dict(self) -> Optional[dict]:
        it = self.tree.currentItem()
        if not it:
            return None
        data = it.data(0, Qt.UserRole)
        return data if isinstance(data, dict) else None

    def toggle_detail_panel(self) -> None:
        """Oculta/muestra el panel derecho, recordando tamaños."""
        if self.detail_panel.isVisible():
            self._last_splitter_sizes = self.splitter.sizes()
            self.detail_panel.setVisible(False)
            self.btn_toggle_detail.setText("Mostrar detalle")
        else:
            self.detail_panel.setVisible(True)
            self.btn_toggle_detail.setText("Ocultar detalle")
            if self._last_splitter_sizes:
                self.splitter.setSizes(self._last_splitter_sizes)
            else:
                w = max(self.splitter.width(), 600)
                self.splitter.setSizes([int(w * 0.72), int(w * 0.28)])

    def rebuild(self) -> None:
        """Reconstruye el tree desde caché (sin pegarle al backend)."""
        self.tree.clear()

        items = self.filter_items(self._items)
        self.build_tree(items)
        self.tree.expandToDepth(self._expand_level)

        # NUEVO: autoselección post-build
        self.select_default_item()

        # refrescar detalle según selección
        self.item_dict_selected.emit(self.selected_item_dict())


    # ---------------- Hooks para heredar ----------------
    def filter_items(self, items: List[dict]) -> List[dict]:
        """Filtro UI (por defecto: checkbox 'solo activos' si existe). No reordena."""
        if not self.chk_only_active.isVisible() or not self.chk_only_active.isChecked():
            return items

        out: List[dict] = []
        for d in items:
            if not isinstance(d, dict):
                continue
            if d.get("active", d.get("activo", False)) is True:
                out.append(d)
        return out

    def build_tree(self, items: List[dict]) -> None:
        """Construcción por defecto: lista plana."""
        for d in items:
            label = str(d.get("nombre") or d.get("codigo") or d.get("id") or "-")
            node = QtWidgets.QTreeWidgetItem(self.tree, [label])
            node.setData(0, Qt.UserRole, d)

    # ---------------- Internals (estilo CustomComboBox) ----------------
    def _make_api_config(self) -> dict[str, Any]:
        """Crea el dict de config para GenericApiWorker."""
        params: dict[str, Any] = {}
        headers: dict[str, Any] = {}

        if callable(self.param_provider):
            try:
                params = self.param_provider() or {}
            except Exception as e:
                QgsMessageLog.logMessage(
                    f"[CustomTreePanel] param_provider error: {e}",
                    "CustomTreePanel",
                    Qgis.Warning,
                )
                params = {}

        if callable(self.headers_provider):
            try:
                headers = self.headers_provider() or {}
            except Exception as e:
                QgsMessageLog.logMessage(
                    f"[CustomTreePanel] headers_provider error: {e}",
                    "CustomTreePanel",
                    Qgis.Warning,
                )
                headers = {}

        return {"url": f"{self._backend}{self.endpoint}", "params": params, "headers": headers}

    def _handle_api_success(self, response_data: object, request_context: object) -> None:
        if request_context != "load_items":
            return

        if not isinstance(response_data, list):
            self._handle_api_error("Respuesta API inválida (no es lista)", request_context)
            return

        # Transformación previa (si se definió)
        if callable(self.items_transform):
            try:
                response_data = self.items_transform(response_data) or []
            except Exception as e:
                QgsMessageLog.logMessage(
                    f"[CustomTreePanel] items_transform error: {e}",
                    "CustomTreePanel",
                    Qgis.Warning,
                )

        # Cache (SIN ordenar)
        self._items = [it for it in response_data if isinstance(it, dict)]

        if self._auto_enable_on_load:
            self.setEnabled(True)

        self.rebuild()
        self.items_loaded.emit(self._items)

    def _handle_api_error(self, error_message: str, request_context: object) -> None:
        if request_context != "load_items":
            return
        QgsMessageLog.logMessage(
            f"[CustomTreePanel] Error al cargar: {error_message}",
            "CustomTreePanel",
            Qgis.Critical,
        )
        if self._auto_enable_on_load:
            self.setEnabled(True)
        self.load_error.emit(error_message)

    def _on_load_finished(self) -> None:
        self.api_thread = None
        self.api_worker = None

    def _on_current_item_changed(self, current, previous) -> None:
        self.item_dict_selected.emit(self.selected_item_dict())


    def _first_leaf_item(self) -> QtWidgets.QTreeWidgetItem | None:
        """Devuelve el primer item 'hoja' (no raíz) del tree."""
        root_count = self.tree.topLevelItemCount()
        for i in range(root_count):
            root = self.tree.topLevelItem(i)
            if not root:
                continue
            # Si root tiene hijos, devolvemos el primero
            if root.childCount() > 0:
                return root.child(0)
            # Si root no tiene hijos, root ya es leaf
            data = root.data(0, Qt.UserRole)
            if isinstance(data, dict):
                return root
        return None
    
    def select_default_item(self) -> None:
        """
        Hook: seleccionar un item por defecto después de rebuild().
        Base: primer leaf disponible.
        """
        item = self._first_leaf_item()
        if item:
            self.tree.setCurrentItem(item)
            self.tree.scrollToItem(item)



# =============================================================================
# Contratos (especialización)
# =============================================================================
class ContratosTreePanel(CustomTreePanel):
    """
    Especialización:
      - Agrupa contratos por año (vigencia_desde)
      - Respeta el orden EXACTO de items recibido (backend: reciente -> antiguo)
      - Panel detalle integrado en la derecha (rellena al seleccionar)
    """

    contrato_selected = QtCore.pyqtSignal(object)  # dict | None

    def __init__(self, parent=None, **kwargs):
        super().__init__(
            parent=parent,
            endpoint="/billing/contratos",
            columns=["Periodo / Contrato", "Plan", "Precio", "Max ha"],
            expand_level=1,
            show_only_active_checkbox=True,
            checkbox_text="Mostrar solo activos (según fechas)",
            detail_title="Detalle",
            **kwargs
        )

        self._item_by_idcontrato = {}

        self.tree.setColumnWidth(0, 340)
        self._build_detail_ui()

        self.item_dict_selected.connect(self._on_item_selected)
    # --------------------------------------------------------------------
    # HELPERS
    #---------------------------------------------------------------------
    def _na(self, v) -> str:
        if v is None:
            return "N/A"
        if isinstance(v, str) and v.strip() == "":
            return "N/A"
        return str(v)

    def _precio_efectivo(self, contrato: dict) -> object:
        plan = contrato.get("plan") or {}
        return contrato.get("precio_contratado") if contrato.get("precio_contratado") is not None else plan.get("precio_base")

    def _origen_precio(self, contrato: dict) -> str:
        return "Contratado" if contrato.get("precio_contratado") is not None else "Base"
    
    # --------------------------------------------------------------------------- # 
    # --------------------------------------------------------------------------- # 


    def build_tree(self, items: List[dict]) -> None:
        self._item_by_idcontrato = {}
        year_nodes: Dict[str, QtWidgets.QTreeWidgetItem] = {}

        for c in items:

            desde = str(c.get("vigencia_desde") or "")
            year = desde[:4] if len(desde) >= 4 else "Sin fecha"

            root = year_nodes.get(year)
            if root is None:
                # 5 columnas -> 5 strings
                root = QtWidgets.QTreeWidgetItem(self.tree, [year, "", "", ""])
                root.setData(0, Qt.UserRole, None)
                year_nodes[year] = root

            plan = c.get("plan") or {}
            label = f"{c.get('explotacion').get('nombre','-')} {self._na(c.get('vigencia_desde'))} → {self._na(c.get('vigencia_hasta'))}  (#{self._na(c.get('idcontrato'))})"

            precio = self._precio_efectivo(c)

            row = [
                label,
                self._na(plan.get("nombre")),
                # self._na(plan.get("pricing_model")),
                self._na(precio),                 # ✅ solo 1 precio
                self._na(plan.get("max_ha")),      # ✅ ahora sí se ve
            ]

            node = QtWidgets.QTreeWidgetItem(root, row)
            node.setData(0, Qt.UserRole, c)

            cid = c.get("idcontrato")
            if cid is not None:
                self._item_by_idcontrato[cid] = node

            # Opcional: tooltip para saber de dónde sale el precio
            node.setToolTip(3, f"Origen: {self._origen_precio(c)}")

    # --------- Detail panel ---------
    def _build_detail_ui(self) -> None:
        lay = QtWidgets.QVBoxLayout(self.detail_panel)
        lay.setContentsMargins(10, 12, 10, 10)
        lay.setSpacing(10)

        form = QtWidgets.QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft)
        form.setFormAlignment(Qt.AlignTop)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)

        self.lbl_id = QtWidgets.QLabel("-")
        self.lbl_vig = QtWidgets.QLabel("-")
        self.lbl_explot = QtWidgets.QLabel("-")
        self.lbl_plan = QtWidgets.QLabel("-")
        self.lbl_model = QtWidgets.QLabel("-")
        self.lbl_precio = QtWidgets.QLabel("-")
        self.lbl_maxha = QtWidgets.QLabel("-")

        # form.addRow("ID contrato:", self.lbl_id)
        form.addRow("Vigencia:", self.lbl_vig)
        form.addRow("Explotación:", self.lbl_explot)
        form.addRow("Plan:", self.lbl_plan)
        form.addRow("Modelo:", self.lbl_model)
        form.addRow("Precio:", self.lbl_precio)
        form.addRow("Max ha:", self.lbl_maxha)

        lay.addLayout(form)

        btns = QtWidgets.QHBoxLayout()
        self.btn_duplicar = QtWidgets.QPushButton("Duplicar")
        self.btn_editar = QtWidgets.QPushButton("Editar…")
        self.btn_editar.setEnabled(True)
        self.btn_eliminar = QtWidgets.QPushButton("Eliminar")
        self.btn_eliminar.setEnabled(True)
        btns.addWidget(self.btn_duplicar)
        btns.addWidget(self.btn_editar)
        btns.addWidget(self.btn_eliminar)
        btns.addStretch(1)
        lay.addLayout(btns)

        lay.addStretch(1)

    def _on_item_selected(self, contrato: Optional[dict]) -> None:
        self.contrato_selected.emit(contrato)

        if not contrato:
            self._clear_detail()
            return

        plan = contrato.get("plan") or {}
        explot = contrato.get("explotacion") or {}
        precio = self._precio_efectivo(contrato)

        # self.lbl_id.setText(str(contrato.get("idcontrato", "-")))
        self.lbl_vig.setText(f"{contrato.get('vigencia_desde','-')} → {contrato.get('vigencia_hasta','-')}")
        self.lbl_explot.setText(str(explot.get("nombre", "-")))
        self.lbl_plan.setText(str(plan.get("nombre", "-")))
        self.lbl_model.setText(str(plan.get("pricing_model", "-")))
        self.lbl_precio.setText(self._na(precio))
        self.lbl_maxha.setText(self._na(plan.get("max_ha")))

    def _clear_detail(self) -> None:
        for lbl in (
            self.lbl_id, self.lbl_vig, self.lbl_explot,
            self.lbl_plan, self.lbl_model, self.lbl_precio, self.lbl_maxha
        ):
            lbl.setText("-")

    def select_default_item(self) -> None:
        """
        Selecciona por defecto el contrato vigente (active=True).
        Si no hay, selecciona el primer leaf.
        Respeta el orden backend: toma el primero active=True.
        """
        # Primero intentamos encontrar el idcontrato activo en el orden original del backend
        active_id = None
        for c in self._items:
            if isinstance(c, dict) and c.get("active") is True:
                active_id = c.get("idcontrato")
                break

        if active_id is not None:
            item = self._item_by_idcontrato.get(active_id)
            if item is not None:
                # Asegura que se vea
                parent = item.parent()
                if parent:
                    parent.setExpanded(True)
                self.tree.setCurrentItem(item)
                self.tree.scrollToItem(item)
                return

        # Fallback
        super().select_default_item()


    # --------------------------------------------------------------------------- #
    # ACTIONS
    # --------------------------------------------------------------------------- #

    def _get_selected_contrato_id(self) -> Optional[int]:
        contrato = self.selected_item_dict()
        if contrato and isinstance(contrato, dict):
            return contrato.get("idcontrato")
        return None
    
    def _get_selected_contrato(self) -> Optional[dict]:
        contrato = self.selected_item_dict()
        if contrato and isinstance(contrato, dict):
            return contrato
        return None


class FacturacionTreePanel(CustomTreePanel):
    """
    Panel de líneas de facturación LOCAL, compatible con el uso actual del diálogo.

    Objetivos:
      - Componente compuesto (tree + detalle + resumen)
      - Mantener líneas locales de facturación
      - Permitir futura integración con selección de lotes / map canvas
      - Ser compatible con llamadas tipo QTreeWidget usadas por el diálogo:
            clear()
            addTopLevelItem(...)
            topLevelItemCount()
            topLevelItem(...)
            selectedItems()
            indexOfTopLevelItem(...)
            takeTopLevelItem(...)

    Notas:
      - addTopLevelItem(QTreeWidgetItem) se soporta como compatibilidad.
      - Internamente convertimos cada item a una línea local.
      - Para uso nuevo, preferir add_contrato_line / add_plan_line / set_line_lotes.
    """

    factura_selected = QtCore.pyqtSignal(object)          # dict | None
    lineas_changed = QtCore.pyqtSignal(list)              # list[dict]
    resumen_changed = QtCore.pyqtSignal(object)           # dict
    request_select_lotes = QtCore.pyqtSignal(object)      # dict linea
    request_edit_linea = QtCore.pyqtSignal(object)        # dict linea
    request_remove_linea = QtCore.pyqtSignal(object)      # dict linea

    def __init__(self, parent=None, **kwargs):
        super().__init__(
            parent=parent,
            endpoint="/billing/facturas",   # reservado, no usado por ahora
            columns=["Concepto", "Plan", "Modelo", "Precio", "Max ha", "Ha sel.", "Lotes", "Estado"],
            expand_level=0,
            show_only_active_checkbox=False,
            detail_title="Detalle de línea",
            auto_load=False,
            **kwargs
        )

        self._lineas: List[dict] = []
        self._item_by_temp_id: Dict[object, QtWidgets.QTreeWidgetItem] = {}
        self._next_temp_id = 1

        self.tree.setRootIsDecorated(False)
        self.tree.setColumnWidth(0, 260)

        self._build_detail_ui()
        self._build_extra_toolbar()
        self.item_dict_selected.connect(self._on_item_selected)

        self._refresh_actions()
        self._emit_resumen_changed()

    # ------------------------------------------------------------------
    # UI adicional
    # ------------------------------------------------------------------
    def _build_extra_toolbar(self) -> None:
        root_layout = self.layout()
        if root_layout is None or root_layout.count() == 0:
            return

        top_item = root_layout.itemAt(0)
        if top_item is None:
            return

        top_layout = top_item.layout()
        if top_layout is None:
            return

        self.btn_add_demo = QtWidgets.QPushButton("Añadir demo")
        self.btn_select_lotes = QtWidgets.QPushButton("Seleccionar lotes…")
        self.btn_edit_linea = QtWidgets.QPushButton("Editar línea")
        self.btn_remove_linea = QtWidgets.QPushButton("Quitar línea")
        self.btn_clear = QtWidgets.QPushButton("Limpiar")

        insert_pos = 3
        top_layout.insertWidget(insert_pos, self.btn_add_demo)
        top_layout.insertWidget(insert_pos + 1, self.btn_select_lotes)
        top_layout.insertWidget(insert_pos + 2, self.btn_edit_linea)
        top_layout.insertWidget(insert_pos + 3, self.btn_remove_linea)
        top_layout.insertWidget(insert_pos + 4, self.btn_clear)

        self.btn_refresh.setVisible(False)
        self.btn_expand.setVisible(False)
        self.btn_collapse.setVisible(False)
        self.chk_only_active.setVisible(False)

        self.btn_add_demo.clicked.connect(self._add_demo_line)
        self.btn_select_lotes.clicked.connect(self._emit_request_select_lotes)
        self.btn_edit_linea.clicked.connect(self._emit_request_edit_linea)
        self.btn_remove_linea.clicked.connect(self._emit_request_remove_linea)
        self.btn_clear.clicked.connect(self.clear)

    def _build_detail_ui(self) -> None:
        lay = QtWidgets.QVBoxLayout(self.detail_panel)
        lay.setContentsMargins(10, 12, 10, 10)
        lay.setSpacing(10)

        form = QtWidgets.QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft)
        form.setFormAlignment(Qt.AlignTop)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)

        self.lbl_concepto = QtWidgets.QLabel("-")
        self.lbl_contrato = QtWidgets.QLabel("-")
        self.lbl_plan = QtWidgets.QLabel("-")
        self.lbl_modelo = QtWidgets.QLabel("-")
        self.lbl_precio = QtWidgets.QLabel("-")
        self.lbl_maxha = QtWidgets.QLabel("-")
        self.lbl_hasel = QtWidgets.QLabel("-")
        self.lbl_nlotes = QtWidgets.QLabel("-")
        self.lbl_estado = QtWidgets.QLabel("-")

        form.addRow("Concepto:", self.lbl_concepto)
        form.addRow("Contrato:", self.lbl_contrato)
        form.addRow("Plan:", self.lbl_plan)
        form.addRow("Modelo:", self.lbl_modelo)
        form.addRow("Precio:", self.lbl_precio)
        form.addRow("Max ha:", self.lbl_maxha)
        form.addRow("Ha seleccionadas:", self.lbl_hasel)
        form.addRow("Nº lotes:", self.lbl_nlotes)
        form.addRow("Estado:", self.lbl_estado)

        lay.addLayout(form)

        self.lotes_tree = QtWidgets.QTreeWidget()
        self.lotes_tree.setColumnCount(3)
        self.lotes_tree.setHeaderLabels(["Lote", "Área ha", "Estado"])
        self.lotes_tree.setRootIsDecorated(False)
        self.lotes_tree.setAlternatingRowColors(True)
        self.lotes_tree.setMinimumHeight(180)

        hh = self.lotes_tree.header()
        hh.setStretchLastSection(False)
        hh.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        hh.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)

        lay.addWidget(self.lotes_tree)

        self.gb_resumen = QtWidgets.QGroupBox("Resumen")
        resumen = QtWidgets.QFormLayout(self.gb_resumen)
        resumen.setLabelAlignment(Qt.AlignLeft)
        resumen.setFormAlignment(Qt.AlignTop)
        resumen.setHorizontalSpacing(12)
        resumen.setVerticalSpacing(8)

        self.lbl_total_lineas = QtWidgets.QLabel("0")
        self.lbl_total_lotes = QtWidgets.QLabel("0")
        self.lbl_total_ha = QtWidgets.QLabel("0.00")
        self.lbl_total_importe = QtWidgets.QLabel("0.00 €")

        resumen.addRow("Líneas:", self.lbl_total_lineas)
        resumen.addRow("Lotes:", self.lbl_total_lotes)
        resumen.addRow("Ha totales:", self.lbl_total_ha)
        resumen.addRow("Importe est.:", self.lbl_total_importe)

        lay.addWidget(self.gb_resumen)
        lay.addStretch(1)

    # ------------------------------------------------------------------
    # Compatibilidad con QTreeWidget para el diálogo actual
    # ------------------------------------------------------------------
    def clear(self) -> None:
        self._lineas.clear()
        self._item_by_temp_id.clear()
        self.rebuild()
        self._clear_detail()
        self._emit_lineas_changed()
        self._emit_resumen_changed()
        self._refresh_actions()

    def addTopLevelItem(self, item: QtWidgets.QTreeWidgetItem) -> None:
        """
        Compatibilidad con el diálogo viejo.
        Espera un QTreeWidgetItem con:
            0 concepto
            1 cantidad
            2 precio_unitario
            3 importe
            4 estado
        """
        if item is None:
            return

        concepto = item.text(0)
        cantidad = item.text(1)
        precio_unit = item.text(2)
        importe = item.text(3)
        estado = item.text(4) or "PENDIENTE"

        linea = {
            "_temp_id": self._next_temp_id,
            "source_type": "manual",
            "idcontrato": None,
            "idplan": None,
            "concepto": concepto or "Concepto",
            "contrato": None,
            "plan": {
                "idplan": None,
                "nombre": "-",
            },
            "pricing_model": "PACKAGE",
            "precio": self._to_float(importe) if importe else self._to_float(precio_unit),
            "max_ha": None,
            "ha_seleccionadas": 0.0,
            "lotes": [],
            "estado": estado,
            # compat con diálogo viejo
            "_legacy_cantidad": cantidad or "1",
            "_legacy_precio_unitario": precio_unit or "0.00",
            "_legacy_importe": importe or "0.00",
        }
        self._next_temp_id += 1

        self._lineas.append(linea)
        self.rebuild()
        self._select_by_temp_id(linea["_temp_id"])
        self._emit_lineas_changed()
        self._emit_resumen_changed()
        self._refresh_actions()

    def topLevelItemCount(self) -> int:
        return len(self._lineas)

    def topLevelItem(self, index: int) -> Optional[QtWidgets.QTreeWidgetItem]:
        return self.tree.topLevelItem(index)

    def selectedItems(self) -> List[QtWidgets.QTreeWidgetItem]:
        return self.tree.selectedItems()

    def indexOfTopLevelItem(self, item: QtWidgets.QTreeWidgetItem) -> int:
        return self.tree.indexOfTopLevelItem(item)

    def takeTopLevelItem(self, index: int) -> Optional[QtWidgets.QTreeWidgetItem]:
        item = self.tree.topLevelItem(index)
        if item is None:
            return None

        data = item.data(0, Qt.UserRole)
        if isinstance(data, dict):
            temp_id = data.get("_temp_id")
            self._lineas = [ln for ln in self._lineas if ln.get("_temp_id") != temp_id]
            self.rebuild()
            self._emit_lineas_changed()
            self._emit_resumen_changed()
            self._refresh_actions()

        return item

    # ------------------------------------------------------------------
    # API pública nueva
    # ------------------------------------------------------------------
    def items(self) -> List[dict]:
        return list(self._lineas)

    def selected_line(self) -> Optional[dict]:
        return self.selected_item_dict()

    def remove_line(self, temp_id: object) -> None:
        self._lineas = [ln for ln in self._lineas if ln.get("_temp_id") != temp_id]
        self.rebuild()
        self._emit_lineas_changed()
        self._emit_resumen_changed()
        self._refresh_actions()

    def add_contrato_line(self, contrato: dict, *, concepto: Optional[str] = None) -> dict:
        if not isinstance(contrato, dict):
            raise ValueError("contrato inválido")

        plan = contrato.get("plan") or {}
        precio = contrato.get("precio_contratado")
        if precio is None:
            precio = plan.get("precio_base")

        linea = {
            "_temp_id": self._next_temp_id,
            "source_type": "contrato",
            "idcontrato": contrato.get("idcontrato"),
            "idplan": plan.get("idplan"),
            "concepto": concepto or f"{plan.get('nombre', 'Concepto')}",
            "contrato": contrato,
            "plan": plan,
            "pricing_model": plan.get("pricing_model"),
            "precio": precio,
            "max_ha": plan.get("max_ha"),
            "ha_seleccionadas": 0.0,
            "lotes": [],
            "estado": "SIN_LOTES",
            "_legacy_cantidad": "1",
            "_legacy_precio_unitario": f"{self._to_float(precio):.2f}",
            "_legacy_importe": f"{self._estimate_importe_from_values(plan.get('pricing_model'), precio, 0.0):.2f}",
        }
        self._next_temp_id += 1

        self._lineas.append(linea)
        self.rebuild()
        self._select_by_temp_id(linea["_temp_id"])
        self._emit_lineas_changed()
        self._emit_resumen_changed()
        self._refresh_actions()
        return linea

    def add_plan_line(self, plan: dict, *, concepto: Optional[str] = None) -> dict:
        if not isinstance(plan, dict):
            raise ValueError("plan inválido")

        precio = plan.get("precio_base")
        linea = {
            "_temp_id": self._next_temp_id,
            "source_type": "plan",
            "idcontrato": None,
            "idplan": plan.get("idplan"),
            "concepto": concepto or f"{plan.get('nombre', 'Concepto')}",
            "contrato": None,
            "plan": plan,
            "pricing_model": plan.get("pricing_model"),
            "precio": precio,
            "max_ha": plan.get("max_ha"),
            "ha_seleccionadas": 0.0,
            "lotes": [],
            "estado": "SIN_LOTES",
            "_legacy_cantidad": "1",
            "_legacy_precio_unitario": f"{self._to_float(precio):.2f}",
            "_legacy_importe": f"{self._estimate_importe_from_values(plan.get('pricing_model'), precio, 0.0):.2f}",
        }
        self._next_temp_id += 1

        self._lineas.append(linea)
        self.rebuild()
        self._select_by_temp_id(linea["_temp_id"])
        self._emit_lineas_changed()
        self._emit_resumen_changed()
        self._refresh_actions()
        return linea

    def set_line_lotes(self, temp_id: object, lotes: List[dict]) -> None:
        linea = self._find_line(temp_id)
        if not linea:
            return

        cleaned: List[dict] = []
        total_ha = 0.0

        for lote in lotes or []:
            if not isinstance(lote, dict):
                continue

            area = self._to_float(lote.get("area_ha"))
            total_ha += area

            cleaned.append({
                "idlote": lote.get("idlote"),
                "nombre": lote.get("nombre", "-"),
                "area_ha": area,
                "estado": lote.get("estado", "OK"),
            })

        linea["lotes"] = cleaned
        linea["ha_seleccionadas"] = total_ha
        linea["estado"] = self._compute_estado(linea)

        precio_unit = self._to_float(linea.get("precio"))
        linea["_legacy_cantidad"] = f"{total_ha:.2f}" if (linea.get("pricing_model") == "PER_HA") else "1"
        linea["_legacy_precio_unitario"] = f"{precio_unit:.2f}"
        linea["_legacy_importe"] = f"{self._estimate_importe(linea):.2f}"

        self.rebuild()
        self._select_by_temp_id(temp_id)
        self._emit_lineas_changed()
        self._emit_resumen_changed()
        self._refresh_actions()

    # ------------------------------------------------------------------
    # Overrides
    # ------------------------------------------------------------------
    def rebuild(self) -> None:
        self.tree.clear()
        self._item_by_temp_id.clear()
        self.build_tree(self._lineas)
        self.select_default_item()
        self.item_dict_selected.emit(self.selected_item_dict())

    def build_tree(self, items: List[dict]) -> None:
        for linea in items:
            plan = linea.get("plan") or {}
            row = [
                self._na(linea.get("concepto")),
                self._na(plan.get("nombre")),
                self._na(linea.get("pricing_model")),
                self._fmt_money(linea.get("precio")),
                self._fmt_ha(linea.get("max_ha")),
                self._fmt_ha(linea.get("ha_seleccionadas")),
                str(len(linea.get("lotes") or [])),
                self._na(linea.get("estado")),
            ]

            node = QtWidgets.QTreeWidgetItem(self.tree, row)
            node.setData(0, Qt.UserRole, linea)

            temp_id = linea.get("_temp_id")
            if temp_id is not None:
                self._item_by_temp_id[temp_id] = node

            if linea.get("estado") == "EXCEDE_MAX_HA":
                node.setToolTip(7, "La suma de hectáreas seleccionadas supera el máximo del plan.")

    def select_default_item(self) -> None:
        if self.tree.topLevelItemCount() > 0:
            item = self.tree.topLevelItem(0)
            self.tree.setCurrentItem(item)
            self.tree.scrollToItem(item)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _na(self, v) -> str:
        if v is None:
            return "-"
        if isinstance(v, str) and not v.strip():
            return "-"
        return str(v)

    def _to_float(self, value: Any) -> float:
        if value is None:
            return 0.0
        txt = str(value).strip().replace("€", "").replace(",", ".")
        if not txt:
            return 0.0
        try:
            return float(txt)
        except Exception:
            return 0.0

    def _fmt_money(self, value: Any) -> str:
        return f"{self._to_float(value):.2f}"

    def _fmt_ha(self, value: Any) -> str:
        if value is None:
            return "-"
        return f"{self._to_float(value):.2f}"

    def _compute_estado(self, linea: dict) -> str:
        lotes = linea.get("lotes") or []
        if not lotes:
            return "SIN_LOTES"

        ha = self._to_float(linea.get("ha_seleccionadas"))
        max_ha = linea.get("max_ha")

        if max_ha is not None and ha > self._to_float(max_ha):
            return "EXCEDE_MAX_HA"

        return "OK"

    def _estimate_importe_from_values(self, pricing_model: Any, precio: Any, ha: float) -> float:
        precio_f = self._to_float(precio)
        if pricing_model == "PER_HA":
            return precio_f * ha
        if pricing_model == "PACKAGE":
            return precio_f
        return precio_f

    def _estimate_importe(self, linea: dict) -> float:
        return self._estimate_importe_from_values(
            linea.get("pricing_model"),
            linea.get("precio"),
            self._to_float(linea.get("ha_seleccionadas")),
        )

    def _find_line(self, temp_id: object) -> Optional[dict]:
        for linea in self._lineas:
            if linea.get("_temp_id") == temp_id:
                return linea
        return None

    def _select_by_temp_id(self, temp_id: object) -> None:
        item = self._item_by_temp_id.get(temp_id)
        if item is not None:
            self.tree.setCurrentItem(item)
            self.tree.scrollToItem(item)

    def _refresh_actions(self) -> None:
        has_selection = self.selected_line() is not None
        has_items = len(self._lineas) > 0

        self.btn_select_lotes.setEnabled(has_selection)
        self.btn_edit_linea.setEnabled(has_selection)
        self.btn_remove_linea.setEnabled(has_selection)
        self.btn_clear.setEnabled(has_items)

    # ------------------------------------------------------------------
    # Detail
    # ------------------------------------------------------------------
    def _on_item_selected(self, linea: Optional[dict]) -> None:
        self.factura_selected.emit(linea)

        if not linea:
            self._clear_detail()
            self._refresh_actions()
            return

        self._fill_detail(linea)
        self._refresh_actions()

    def _fill_detail(self, linea: dict) -> None:
        self.lotes_tree.clear()

        contrato = linea.get("contrato") or {}
        plan = linea.get("plan") or {}

        self.lbl_concepto.setText(self._na(linea.get("concepto")))
        self.lbl_contrato.setText(self._na(contrato.get("idcontrato")) if contrato else "-")
        self.lbl_plan.setText(self._na(plan.get("nombre")))
        self.lbl_modelo.setText(self._na(linea.get("pricing_model")))
        self.lbl_precio.setText(f"{self._fmt_money(linea.get('precio'))} €")
        self.lbl_maxha.setText(self._fmt_ha(linea.get("max_ha")))
        self.lbl_hasel.setText(self._fmt_ha(linea.get("ha_seleccionadas")))
        self.lbl_nlotes.setText(str(len(linea.get("lotes") or [])))
        self.lbl_estado.setText(self._na(linea.get("estado")))

        for lote in linea.get("lotes") or []:
            row = [
                self._na(lote.get("nombre")),
                self._fmt_ha(lote.get("area_ha")),
                self._na(lote.get("estado")),
            ]
            QtWidgets.QTreeWidgetItem(self.lotes_tree, row)

    def _clear_detail(self) -> None:
        self.lbl_concepto.setText("-")
        self.lbl_contrato.setText("-")
        self.lbl_plan.setText("-")
        self.lbl_modelo.setText("-")
        self.lbl_precio.setText("-")
        self.lbl_maxha.setText("-")
        self.lbl_hasel.setText("-")
        self.lbl_nlotes.setText("-")
        self.lbl_estado.setText("-")
        self.lotes_tree.clear()

    # ------------------------------------------------------------------
    # Señales y resumen
    # ------------------------------------------------------------------
    def _emit_lineas_changed(self) -> None:
        self.lineas_changed.emit(self.items())

    def _emit_resumen_changed(self) -> None:
        total_lineas = len(self._lineas)
        total_lotes = sum(len(ln.get("lotes") or []) for ln in self._lineas)
        total_ha = sum(self._to_float(ln.get("ha_seleccionadas")) for ln in self._lineas)
        total_importe = sum(
            self._to_float(ln.get("_legacy_importe")) if ln.get("source_type") == "manual"
            else self._estimate_importe(ln)
            for ln in self._lineas
        )
        has_errors = any((ln.get("estado") == "EXCEDE_MAX_HA") for ln in self._lineas)

        self.lbl_total_lineas.setText(str(total_lineas))
        self.lbl_total_lotes.setText(str(total_lotes))
        self.lbl_total_ha.setText(f"{total_ha:.2f}")
        self.lbl_total_importe.setText(f"{total_importe:.2f} €")

        self.resumen_changed.emit({
            "total_lineas": total_lineas,
            "total_lotes": total_lotes,
            "total_ha": total_ha,
            "total_importe": total_importe,
            "has_errors": has_errors,
        })

    def _emit_request_select_lotes(self) -> None:
        linea = self.selected_line()
        if not linea:
            return
        self.request_select_lotes.emit(linea)

    def _emit_request_edit_linea(self) -> None:
        linea = self.selected_line()
        if not linea:
            return
        self.request_edit_linea.emit(linea)

    def _emit_request_remove_linea(self) -> None:
        linea = self.selected_line()
        if not linea:
            return
        self.request_remove_linea.emit(linea)
        self.remove_line(linea.get("_temp_id"))

    # ------------------------------------------------------------------
    # Demo
    # ------------------------------------------------------------------
    def _add_demo_line(self) -> None:
        contrato = {
            "idcontrato": "demo-1",
            "precio_contratado": "85.00",
            "plan": {
                "idplan": 1,
                "nombre": "Plan abonado variable",
                "pricing_model": "PER_HA",
                "precio_base": "90.00",
                "max_ha": "12.50",
            }
        }

        linea = self.add_contrato_line(contrato)
        self.set_line_lotes(linea["_temp_id"], [
            {"idlote": 101, "nombre": "Lote Norte", "area_ha": 4.20},
            {"idlote": 102, "nombre": "Lote Sur", "area_ha": 3.10},
        ])