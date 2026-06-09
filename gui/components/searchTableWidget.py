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
from qgis.PyQt import sip
from qgis.core import QgsNetworkAccessManager, QgsMessageLog, Qgis

from ...tools import aGraeTools

from ...core.models import (
    # MODELOS
    AgricultoresTableModel, 
    PersonasTableModel,
    ExplotacionesTableModel,
    AsesoresTableModel,
    DistribuidoresTableModel,
    FacturasTableModel,
    # MAPPERS
    map_agricultores, 
    map_personas, 
    map_explotacion,
    map_asesores,
    map_distribuidores,
    map_facturas,
    )


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
        self.base_url = aGraeTools().backend_url 
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
        # self.table.setColumnHidden(0, True)  # ocultar columna ID por defecto, se asume que es la primera. Ajusta según tu modelo.

        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(True)

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

        if self.local_filter:
            self.proxy.invalidate()

        self.table.clearSelection()
        self.table.viewport().update()

    def reload(self, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None):
        """
        Hace GET y carga el modelo con map_func.
        """
        url = self._full_url(params)
        req = QNetworkRequest(url)

        if headers:
            for k, v in headers.items():
                req.setRawHeader(QByteArray(k.encode("utf-8")), QByteArray(str(v).encode("utf-8")))

        # Cancelar request anterior si sigue vivo
        if self._reply is not None:
            try:
                if not sip.isdeleted(self._reply) and self._reply.isRunning():
                    self._reply.abort()
            except RuntimeError:
                pass
            except Exception:
                pass
            finally:
                self._reply = None

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
            Qgis.Info
        )

        r.deleteLater()

        if not text:
            QgsMessageLog.logMessage(
                f"Respuesta vacía en {url}",
                "aGrae",
                Qgis.Warning
            )
            self.set_items([])
            return

        try:
            raw = json.loads(text)
        except Exception as e:
            msg = f"Respuesta no-JSON en {url}: {e} | body={text[:500]}"
            QgsMessageLog.logMessage(msg, "aGrae", Qgis.Warning)
            self.set_items([])
            return

        try:
            items = self.map_func(raw)
        except Exception as e:
            msg = f"Error mapeando respuesta ({url}): {e}"
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



# AGRICULTORES

class AgricultorSearchTable(SearchTableWidget):
    def __init__(self ,parent=None):
        super().__init__(
            model=AgricultoresTableModel(),
            endpoint='/gis/agricultores/',
            map_func=map_agricultores,
            placeholder="Buscar agricultor...",
            local_filter=True,
            emit_field="idagricultor",
            parent=parent
        )


        # self.table.setColumnHidden(0, True)  # ocultar columna ID

class AsignarAgricultorSearchTable(SearchTableWidget):
    def __init__(self, idexplotacion: int ,parent=None):
        super().__init__(
            model=AgricultoresTableModel(),
            endpoint='/gis/agricultores/exp/{}'.format(idexplotacion),
            map_func=map_agricultores,
            placeholder="Buscar agricultor...",
            local_filter=True,
            emit_field="idagricultor",
            parent=parent
        )


# PERSONAS
class PersonaSearchTable(SearchTableWidget):
    def __init__(self ,parent=None):
        super().__init__(
            model=PersonasTableModel(),
            endpoint='/gis/personas/',
            map_func=map_personas,
            placeholder="Buscar persona...",
            local_filter=True,
            emit_field="idpersona",
            parent=parent
        )


        self.table.setColumnHidden(0, True)  # ocultar columna ID


# EXPLOTACIONES
class ExplotacionSearchTable(SearchTableWidget):
    def __init__(self , idvisible = True, parent=None):
        super().__init__(
            model=ExplotacionesTableModel(),
            endpoint='/gis/explotaciones/',
            map_func=map_explotacion,
            placeholder="Buscar explotación...",
            local_filter=True,
            emit_field="idexplotacion",
            parent=parent
        )


        self.setColumnHidden(0, not idvisible)  # ocultar columna ID según idvisible

        # self.table.setColumnHidden(0, idvisible)  # ocultar columna ID

    def setColumnHidden(self, column: int, hide: bool):
        self.table.setColumnHidden(column, hide)
        
# ASESORES
class AsesorSearchTable(SearchTableWidget):
    def __init__(self ,parent=None):
        super().__init__(
            model=AsesoresTableModel(),
            endpoint='/gis/asesores/',
            map_func=map_asesores,
            placeholder="Buscar asesor...",
            local_filter=True,
            emit_field="idasesor",
            parent=parent
        )


        self.table.setColumnHidden(0, True)  # ocultar columna ID

class DistribuidorSearchTable(SearchTableWidget):
    def __init__(self ,parent=None):
        super().__init__(
            model=DistribuidoresTableModel(),
            endpoint='/gis/distribuidores/',
            map_func=map_distribuidores,
            placeholder="Buscar distribuidor...",
            local_filter=True,
            emit_field="iddistribuidor",
            parent=parent
        )


        self.table.setColumnHidden(0, True)  # ocultar columna ID

# FACTURACION

class FacturasSearchTable(SearchTableWidget):
    def __init__(self ,parent=None):
        super().__init__(
            model=FacturasTableModel(),
            endpoint='/billing/facturas/consulta',
            map_func=map_facturas,
            placeholder="Buscar factura...",
            local_filter=True,
            emit_field="uid",
            parent=parent
        )


        self.table.setColumnHidden(0, True)  # ocultar columna ID
        # self.table.setColumnHidden(1, True)  # ocultar columna UID

   