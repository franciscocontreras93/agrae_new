# -*- coding: utf-8 -*-
"""
searchTableWidget.py

Widget reutilizable con:
- QLineEdit (buscador)
- QTableView (tabla)
- Fetch GET incluido (QgsNetworkAccessManager)
- Proxy de filtro multi-columna opcional (local)
- Mapper para normalizar respuesta raw -> items para model.set_items()

Requisitos:
- model debe implementar set_items(list[dict])
- map_func(raw_json) -> list[dict]
"""

from typing import Callable, Optional, Any, List, Dict

import json

from qgis.PyQt.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QTableView, QHeaderView
from qgis.PyQt.QtCore import Qt, QTimer, QUrl, QByteArray, pyqtSignal
from qgis.PyQt.QtNetwork import QNetworkRequest

from qgis.core import QgsNetworkAccessManager, QgsMessageLog, Qgis

from ...tools import aGraeTools


from ...core.proxies import MultiColumnFilterProxy

def safe_get(d: dict, path: str, default=None):
    cur = d or {}
    for k in (path or "").split("."):
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur.get(k)
    return default if cur is None else cur


class SearchTableWidget(QWidget):

    rowDoubleClicked = pyqtSignal(object,dict)

    def __init__(
        self,
        model,
        endpoint: str,
        map_func: Callable[[Any], List[dict]],
        placeholder: str = "Buscar...",
        local_filter: bool = True,
        debounce_ms: int = 0,
        default_params: Optional[Dict[str, Any]] = None,
        emit_field: str = "",
        emit_func: Optional[Callable[[dict], Any]] = None,
        parent=None,
    ):
        """
        model: QAbstractTableModel con set_items(items)
        endpoint: ruta o url completa (ej: "/api/agricultores" o "https://host/api/agricultores")
        map_func: normaliza raw_json -> items para el modelo
        base_url: si endpoint es relativo, se concatena base_url + endpoint
        local_filter: si True filtra local con proxy
        debounce_ms: si >0, aplica debounce al tecleo (útil si luego haces server-side)
        default_params: params que siempre se mandan (ej: {"active": 1})
        """
        super().__init__(parent)

        self.model = model
        self.map_func = map_func
        self.base_url = aGraeTools().backend_endpoint 
        self.endpoint = endpoint or ""
        self.local_filter = local_filter
        self.default_params = default_params or {}
        self.emit_field = emit_field
        self.emit_func = emit_func

        # ---------------- UI ----------------
        self.search = QLineEdit()
        self.search.setPlaceholderText(placeholder)
        self.search.setClearButtonEnabled(True)

        self.table = QTableView()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)
        self.table.setSortingEnabled(True)

        self.proxy = MultiColumnFilterProxy(self)
        self.proxy.setSourceModel(self.model)

        self.table.setModel(self.proxy if self.local_filter else self.model)

        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.addWidget(self.search)
        lay.addWidget(self.table)

        # -------------- Debounce -------------
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(max(0, int(debounce_ms)))
        self._last_text = ""

        if debounce_ms and debounce_ms > 0:
            self.search.textChanged.connect(self._on_text_changed_debounced)
            self._debounce.timeout.connect(self._on_debounced_timeout)
        else:
            self.search.textChanged.connect(self._on_text_changed_now)

        # -------------- Network --------------
        self.nam = QgsNetworkAccessManager.instance()
        self._reply = None  # para evitar GC

        # -------------- Signals --------------
        self.table.doubleClicked.connect(self._on_table_double_clicked)

    # -----------------------------
    # URL building
    # -----------------------------
    def _full_url(self, params: Optional[Dict[str, Any]] = None) -> QUrl:
        endpoint = self.endpoint.strip()

        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            url = QUrl(endpoint)
        else:
            # endpoint relativo
            if not self.base_url:
                # si no hay base_url, igual intentamos
                url = QUrl(endpoint)
            else:
                url = QUrl(f"{self.base_url}/{endpoint.lstrip('/')}")

        # query params
        q = url.query()
        # reconstruimos con QUrlQuery (simplemente setQueryItems vía string manual es más feo)
        from qgis.PyQt.QtCore import QUrlQuery
        query = QUrlQuery(url)

        merged = dict(self.default_params)
        if params:
            merged.update({k: v for k, v in params.items() if v is not None})

        for k, v in merged.items():
            query.addQueryItem(str(k), str(v))

        url.setQuery(query)
        return url

    # -----------------------------
    # Búsqueda local / futura remota
    # -----------------------------
    def _on_text_changed_now(self, text: str):
        if self.local_filter:
            self.proxy.set_needle(text)
        else:
            # server-side (lo activamos luego):
            # self.reload(params={"q": text})
            pass

    def _on_text_changed_debounced(self, text: str):
        self._last_text = text
        self._debounce.start()

    def _on_debounced_timeout(self):
        text = self._last_text
        if self.local_filter:
            self.proxy.set_needle(text)
        else:
            # server-side:
            # self.reload(params={"q": text})
            pass

    # -----------------------------
    # API pública
    # -----------------------------
    def set_items(self, items: List[dict]):
        if not hasattr(self.model, "set_items"):
            raise AttributeError("El modelo no implementa set_items(items).")
        self.model.set_items(items or [])

    def reload(self, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None):
        """
        Hace GET y carga el modelo con map_func.
        """
        url = self._full_url(params)
        req = QNetworkRequest(url)

        # headers opcionales
        if headers:
            for k, v in headers.items():
                req.setRawHeader(QByteArray(k.encode("utf-8")), QByteArray(str(v).encode("utf-8")))

        # Cancelar request anterior si sigue vivo
        if self._reply and self._reply.isRunning():
            try:
                self._reply.abort()
            except Exception:
                pass

        self._reply = self.nam.get(req)
        self._reply.finished.connect(self._on_reply_finished)

    def selected_item(self) -> Optional[dict]:
        sel = self.table.selectionModel()
        if not sel or not sel.hasSelection():
            return None

        idx = sel.selectedRows()[0]
        if self.local_filter:
            idx = self.proxy.mapToSource(idx)

        return self.model.data(idx, Qt.UserRole)

    # -----------------------------
    # Network callbacks
    # -----------------------------
    def _on_reply_finished(self):
        r = self._reply
        if r is None:
            return

        if r.error():
            msg = f"Error GET {r.url().toString()}: {r.errorString()}"
            QgsMessageLog.logMessage(msg, "aGrae", Qgis.Warning)
            self.set_items([])
            r.deleteLater()
            return

        data = bytes(r.readAll())
        r.deleteLater()

        try:
            raw = json.loads(data.decode("utf-8"))
        except Exception as e:
            msg = f"Respuesta no-JSON en {r.url().toString()}: {e}"
            QgsMessageLog.logMessage(msg, "aGrae", Qgis.Warning)
            self.set_items([])
            return

        try:
            items = self.map_func(raw)
        except Exception as e:
            msg = f"Error mapeando respuesta ({r.url().toString()}): {e}"
            QgsMessageLog.logMessage(msg, "aGrae", Qgis.Warning)
            self.set_items([])
            return

        self.set_items(items)

    # -----------------------------
    # UI Callbacks
    # -----------------------------
    def _on_table_double_clicked(self, view_index):
        # view_index es del modelo que está en la vista (proxy o model)
        idx = view_index
        if self.local_filter:
            idx = self.proxy.mapToSource(view_index)

        # item completo del modelo (tu model devuelve dict en Qt.UserRole)
        item = self.model.data(idx, Qt.UserRole)
        if not item:
            return

        # valor a emitir: prioridad a emit_func, si no, emit_field, si no, item completo
        if callable(self.emit_func):
            value = self.emit_func(item)
        elif self.emit_field:
            value = safe_get(item, self.emit_field, None)
        else:
            value = item

        self.rowDoubleClicked.emit(value, item)

