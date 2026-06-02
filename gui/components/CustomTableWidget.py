# -*- coding: utf-8 -*-

from typing import Callable, Optional, Any, List, Dict
import json

from qgis.PyQt.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableView,
    QHeaderView,
    QPushButton,
)
from qgis.PyQt.QtCore import Qt, QUrl, QByteArray, pyqtSignal
from qgis.PyQt.QtNetwork import QNetworkRequest
from qgis.PyQt import sip
from qgis.core import QgsNetworkAccessManager, QgsMessageLog, Qgis

from ...tools import aGraeTools

from ...core.models.facturacion.FacturasModel import (
    PagosTableModel,
    map_pagos,
)


def safe_get(d: dict, path: str, default=None):
    cur = d or {}
    for k in (path or "").split("."):
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur.get(k)
    return default if cur is None else cur


class CustomTableWidget(QWidget):
    rowDoubleClicked = pyqtSignal(object, dict)
    actionTriggered = pyqtSignal(str, object)

    def __init__(
        self,
        model,
        endpoint: str,
        map_func: Callable[[Any], List[dict]],
        default_params: Optional[Dict[str, Any]] = None,
        emit_field: str = "",
        emit_func: Optional[Callable[[dict], Any]] = None,
        actions: Optional[List[Dict[str, Any]]] = None,
        parent=None,
    ):
        super().__init__(parent)

        self.model = model
        self.endpoint = endpoint or ""
        self.map_func = map_func
        self.default_params = default_params or {}

        self.emit_field = emit_field
        self.emit_func = emit_func

        self.base_url = aGraeTools().backend_url

        self.nam = QgsNetworkAccessManager.instance()
        self._reply = None

        self.action_buttons = {}

        self.table = QTableView()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)
        self.table.setSortingEnabled(True)
        self.table.setModel(self.model)

        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.Stretch)

        self.table.verticalHeader().setVisible(True)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(6, 6, 6, 6)
        self.main_layout.setSpacing(6)

        self.toolbar_layout = QHBoxLayout()
        self.toolbar_layout.setContentsMargins(0, 0, 0, 0)
        self.toolbar_layout.setSpacing(6)
        self.toolbar_layout.addStretch()

        self.main_layout.addLayout(self.toolbar_layout)
        self.main_layout.addWidget(self.table)

        if actions:
            for action in actions:
                self.add_action_button(**action)

        self.table.doubleClicked.connect(self._on_table_double_clicked)

    def add_action_button(
        self,
        text: str,
        callback: Optional[Callable[[Optional[dict]], None]] = None,
        tooltip: str = "",
        enabled_without_selection: bool = True,
        action_name: Optional[str] = None,
    ):
        button = QPushButton(text, self)
        button.setToolTip(tooltip or text)

        name = action_name or text

        if not enabled_without_selection:
            button.setEnabled(False)

            def update_enabled():
                button.setEnabled(self.selected_item() is not None)

            self.table.selectionModel().selectionChanged.connect(update_enabled)

        if callback:
            button.clicked.connect(lambda: callback(self.selected_item()))
        else:
            button.clicked.connect(lambda: self.actionTriggered.emit(name, self.selected_item()))

        self.toolbar_layout.insertWidget(
            self.toolbar_layout.count() - 1,
            button
        )

        self.action_buttons[name] = button
        return button

    def _full_url(self, params: Optional[Dict[str, Any]] = None) -> QUrl:
        endpoint = self.endpoint.strip()

        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            url = QUrl(endpoint)
        else:
            if self.base_url:
                url = QUrl(f"{self.base_url}/{endpoint.lstrip('/')}")
            else:
                url = QUrl(endpoint)

        from qgis.PyQt.QtCore import QUrlQuery

        query = QUrlQuery(url)

        merged = dict(self.default_params)
        if params:
            merged.update({k: v for k, v in params.items() if v is not None})

        for k, v in merged.items():
            query.addQueryItem(str(k), str(v))

        url.setQuery(query)
        return url

    def reload(
        self,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        url = self._full_url(params)
        req = QNetworkRequest(url)

        if headers:
            for k, v in headers.items():
                req.setRawHeader(
                    QByteArray(k.encode("utf-8")),
                    QByteArray(str(v).encode("utf-8")),
                )

        if self._reply is not None:
            try:
                if not sip.isdeleted(self._reply) and self._reply.isRunning():
                    self._reply.abort()
            except Exception:
                pass
            finally:
                self._reply = None

        self._reply = self.nam.get(req)
        self._reply.finished.connect(self._on_reply_finished)

    def set_items(self, items: List[dict]):
        if not hasattr(self.model, "set_items"):
            raise AttributeError("El modelo no implementa set_items(items).")

        self.model.set_items(items or [])
        self.table.clearSelection()
        self.table.viewport().update()

    def selected_item(self) -> Optional[dict]:
        sel = self.table.selectionModel()

        if not sel or not sel.hasSelection():
            return None

        idx = sel.selectedRows()[0]
        return self.model.data(idx, Qt.UserRole)

    def setColumnHidden(self, column: int, hide: bool):
        self.table.setColumnHidden(column, hide)

    def sort_by_column(self, column: int, order=Qt.DescendingOrder):
        self.table.sortByColumn(column, order)

    def resize_columns_stretch(self):
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def resize_columns_to_contents(self):
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

    def _on_reply_finished(self):
        r = self._reply
        self._reply = None

        if r is None:
            return

        try:
            if sip.isdeleted(r):
                return
        except Exception:
            return

        url = r.url().toString()
        status_code = r.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        reason = r.attribute(QNetworkRequest.HttpReasonPhraseAttribute)
        content_type = r.header(QNetworkRequest.ContentTypeHeader)

        data = bytes(r.readAll())
        text = data.decode("utf-8", errors="replace").strip()

        if r.error():
            msg = (
                f"Error GET {url}: {r.errorString()} | "
                f"status={status_code} reason={reason} | "
                f"content-type={content_type} | body={text[:500]}"
            )
            QgsMessageLog.logMessage(msg, "aGrae", Qgis.Warning)
            self.set_items([])
            r.deleteLater()
            return

        QgsMessageLog.logMessage(
            f"GET {url} | status={status_code}",
            "aGrae",
            Qgis.Info,
        )

        r.deleteLater()

        if not text:
            QgsMessageLog.logMessage(
                f"Respuesta vacía en {url}",
                "aGrae",
                Qgis.Warning,
            )
            self.set_items([])
            return

        try:
            raw = json.loads(text)
        except Exception as e:
            QgsMessageLog.logMessage(
                f"Respuesta no-JSON en {url}: {e} | body={text[:500]}",
                "aGrae",
                Qgis.Warning,
            )
            self.set_items([])
            return

        try:
            items = self.map_func(raw)
        except Exception as e:
            QgsMessageLog.logMessage(
                f"Error mapeando respuesta ({url}): {e}",
                "aGrae",
                Qgis.Warning,
            )
            self.set_items([])
            return

        self.set_items(items)

    def _on_table_double_clicked(self, view_index):
        item = self.model.data(view_index, Qt.UserRole)

        if not item:
            return

        if callable(self.emit_func):
            value = self.emit_func(item)
        elif self.emit_field:
            value = safe_get(item, self.emit_field, None)
        else:
            value = item

        self.rowDoubleClicked.emit(value, item)


class PagosTableWidget(CustomTableWidget):
    def __init__(self, idfactura, parent=None):
        self.idfactura = idfactura

        model = PagosTableModel()

        super().__init__(
            model=model,
            endpoint=f"/billing/facturas/pagos/{idfactura}",
            map_func=map_pagos,
            emit_field="idpago",
            actions=[
                {
                    "text": "Generar recibo",
                    "tooltip": "Generar recibo para el pago seleccionado",
                    "enabled_without_selection": False,
                    "action_name": "generar_recibo",
                },
            ],
            parent=parent,
        )

        self.setColumnHidden(0, True)
        self.sort_by_column(1, Qt.DescendingOrder)