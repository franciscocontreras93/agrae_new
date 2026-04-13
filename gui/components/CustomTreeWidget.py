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