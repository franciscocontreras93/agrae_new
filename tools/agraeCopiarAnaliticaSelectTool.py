# -*- coding: utf-8 -*-
# agrae/tools/agraeCopiarAnaliticaSelectTool.py

from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtGui import QColor, QCursor, QPixmap
from qgis.PyQt.QtWidgets import QMenu, QAction
from qgis.gui import QgsMapToolIdentify, QgsHighlight
from qgis.core import QgsProject, QgsFeature
from qgis.utils import iface

from qgis.PyQt.QtCore import QUrl, QByteArray
from qgis.PyQt.QtNetwork import QNetworkRequest
import json
import os


class aGraeCopiarAnaliticaSelectTool(QgsMapToolIdentify):
    """
    Custom select tool con cursor propio + 2 selecciones:
      - Receptores (muchos) color A
      - Donante (uno) color B

    UX:
      - Click IZQ: toggle receptor (Shift acumula / click simple reemplaza)
      - Ctrl + click IZQ: set donante
      - Click DER: menú contextual (set/toggle/enviar/limpiar)
      - DER vacío: limpiar
    """

    requestFinished = pyqtSignal(object)

    IDL_FIELD = "idlote"

    MODE_RECEPTOR = "receptor"
    MODE_DONANTE = "donante"

    def __init__(
        self,
        layer,
        *,
        endpoint_url: str,
        idcampania: int,
        idexplotacion: int,
        cursor_png: str | None = None,   # ruta a png para cursor
        hotspot=(1, 1),                  # punto “click” del cursor
        # colores receptores
        rec_edge="#00AAFF", rec_fill="#00AAFF", rec_edge_alpha=220, rec_fill_alpha=70,
        # colores donante
        don_edge="#FF0078", don_fill="#FF0078", don_edge_alpha=240, don_fill_alpha=70,
        parent=None,
    ):
        super().__init__(iface.mapCanvas())
        self.layer = layer
        self.canvas = iface.mapCanvas()

        self.endpoint_url = endpoint_url
        self.idcampania = int(idcampania)
        self.idexplotacion = int(idexplotacion)

        # modo (por si luego querés toggle desde UI)
        self._mode = self.MODE_RECEPTOR

        # estado por idlote
        self._receptores: set[int] = set()
        self._donante: int | None = None

        # highlights por fid
        self._h_rec: dict[int, QgsHighlight] = {}
        self._h_don: dict[int, QgsHighlight] = {}

        # colores
        self._rec_edge = QColor(rec_edge); self._rec_edge.setAlpha(rec_edge_alpha)
        self._rec_fill = QColor(rec_fill); self._rec_fill.setAlpha(rec_fill_alpha)
        self._don_edge = QColor(don_edge); self._don_edge.setAlpha(don_edge_alpha)
        self._don_fill = QColor(don_fill); self._don_fill.setAlpha(don_fill_alpha)

        # cursor personalizado
        self._apply_custom_cursor(cursor_png, hotspot)

        # hooks proyecto/capa
        self._project = QgsProject.instance()
        for sig_name in ("cleared", "layerWillBeRemoved", "layersWillBeRemoved"):
            try:
                getattr(self._project, sig_name).connect(self._on_project_change)
            except Exception:
                pass
        try:
            self.layer.destroyed.connect(self._on_layer_destroyed)
        except Exception:
            pass

        # network manager
        self.nam = iface.networkAccessManager()
        self._pending_reply = None

    # ---------- Cursor ----------
    def _apply_custom_cursor(self, cursor_png: str | None, hotspot=(1, 1)):
        if not cursor_png:
            # fallback: cursor “cross” (ya se nota diferente)
            self.setCursor(Qt.CrossCursor)
            return

        try:
            if not os.path.exists(cursor_png):
                self.setCursor(Qt.CrossCursor)
                return
            px = QPixmap(cursor_png)
            if px.isNull():
                self.setCursor(Qt.CrossCursor)
                return
            self.setCursor(QCursor(px, hotspot[0], hotspot[1]))
        except Exception:
            self.setCursor(Qt.CrossCursor)

    def setMode(self, mode: str):
        if mode in (self.MODE_RECEPTOR, self.MODE_DONANTE):
            self._mode = mode
            iface.statusBarIface().showMessage(f"Modo herramienta: {mode}")

    # ---------- Eventos ----------
    def canvasPressEvent(self, event):
        if not self._layer_ok():
            self.clearAll()
            return

        if event.button() == Qt.RightButton:
            self._on_right_click(event)
            return

        if event.button() != Qt.LeftButton:
            return

        f = self._identify_top_feature(event)
        if not f:
            return

        idlote = self._get_idlote(f)
        if idlote is None:
            iface.messageBar().pushWarning("Copiar analítica", f"No existe/castea campo {self.IDL_FIELD}.")
            return

        # Ctrl fuerza donante
        if (event.modifiers() & Qt.ControlModifier) or self._mode == self.MODE_DONANTE:
            self.setDonante(f, idlote)
            return

        # receptores
        if not (event.modifiers() & Qt.ShiftModifier):
            self.clearReceptores()
        self.toggleReceptor(f, idlote)

    def _on_right_click(self, event):
        f = self._identify_top_feature(event)
        if not f:
            self.clearAll()
            return
        self._show_context_menu(f)

    # ---------- Identify ----------
    def _identify_top_feature(self, event):
        results = self.identify(event.x(), event.y(), [self.layer], QgsMapToolIdentify.TopDownAll)
        if not results:
            return None
        return results[0].mFeature

    def _get_idlote(self, feature: QgsFeature) -> int | None:
        if self.IDL_FIELD not in feature.fields().names():
            return None
        v = feature[self.IDL_FIELD]
        if v is None:
            return None
        try:
            return int(v)
        except Exception:
            return None

    # ---------- Menú ----------
    def _show_context_menu(self, feature: QgsFeature):
        idlote = self._get_idlote(feature)

        menu = QMenu(self.canvas)

        act_rec = QAction("Toggle receptor", menu)
        act_don = QAction("Marcar como DONANTE", menu)
        act_send = QAction("Enviar (copiar analítica)", menu)
        act_clear = QAction("Limpiar todo", menu)

        act_rec.triggered.connect(lambda _, f=feature, i=idlote: self._ctx_toggle_rec(f, i))
        act_don.triggered.connect(lambda _, f=feature, i=idlote: self._ctx_set_don(f, i))
        act_send.triggered.connect(lambda _: self.sendRequest())
        act_clear.triggered.connect(lambda _: self.clearAll())

        menu.addAction(act_rec)
        menu.addAction(act_don)
        menu.addSeparator()
        menu.addAction(act_send)
        menu.addSeparator()
        menu.addAction(act_clear)

        if idlote is None:
            act_rec.setEnabled(False)
            act_don.setEnabled(False)

        menu.exec_(QCursor.pos())

    def _ctx_toggle_rec(self, feature, idlote):
        if idlote is None:
            return
        self.toggleReceptor(feature, idlote)

    def _ctx_set_don(self, feature, idlote):
        if idlote is None:
            return
        self.setDonante(feature, idlote)

    # ---------- Selección custom ----------
    def toggleReceptor(self, feature: QgsFeature, idlote: int):
        if self._donante is not None and idlote == self._donante:
            iface.messageBar().pushWarning("Copiar analítica", "Ese lote ya es DONANTE.")
            return

        if idlote in self._receptores:
            self._receptores.remove(idlote)
            self._remove_highlight(self._h_rec, feature.id())
        else:
            self._receptores.add(idlote)
            self._add_highlight(self._h_rec, feature, edge=self._rec_edge, fill=self._rec_fill, width=2)

        self._status_msg()

    def setDonante(self, feature: QgsFeature, idlote: int):
        self.clearDonante()

        if idlote in self._receptores:
            self._receptores.remove(idlote)
            self._remove_highlight(self._h_rec, feature.id())

        self._donante = idlote
        self._add_highlight(self._h_don, feature, edge=self._don_edge, fill=self._don_fill, width=3)
        self._status_msg()

    def clearReceptores(self):
        self._receptores.clear()
        for fid in list(self._h_rec.keys()):
            self._remove_highlight(self._h_rec, fid)
        self._status_msg()

    def clearDonante(self):
        self._donante = None
        for fid in list(self._h_don.keys()):
            self._remove_highlight(self._h_don, fid)
        self._status_msg()

    def clearAll(self):
        self.clearReceptores()
        self.clearDonante()

    # ---------- Highlight ----------
    def _add_highlight(self, store, feature, *, edge: QColor, fill: QColor, width: int):
        fid = feature.id()
        if fid in store:
            self._remove_highlight(store, fid)

        h = QgsHighlight(self.canvas, feature.geometry(), self.layer)
        h.setColor(edge)
        h.setFillColor(fill)
        h.setWidth(width)
        h.show()
        store[fid] = h

    def _remove_highlight(self, store, fid: int):
        h = store.pop(fid, None)
        if h:
            try:
                h.hide()
                h.deleteLater()
            except Exception:
                pass

    # ---------- Request ----------
    def buildPayload(self):
        if self._donante is None:
            iface.messageBar().pushWarning("Copiar analítica", "Falta DONANTE (Ctrl+click o modo donante).")
            return None
        if not self._receptores:
            iface.messageBar().pushWarning("Copiar analítica", "Faltan receptores.")
            return None

        return {
            "idcampania": self.idcampania,
            "idexplotacion": self.idexplotacion,
            "idlote_origen": int(self._donante),
            "idlotes_destino": [int(x) for x in sorted(self._receptores)],
        }

    def sendRequest(self):
        payload = self.buildPayload()
        if payload is None:
            return

        data = QByteArray(json.dumps(payload).encode("utf-8"))
        req = QNetworkRequest(QUrl(self.endpoint_url))
        req.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")
        # req.setRawHeader(b"Authorization", b"Bearer TU_TOKEN")

        reply = self.nam.post(req, data)
        self._pending_reply = reply
        reply.finished.connect(lambda: self._on_reply_finished(reply))

        iface.messageBar().pushInfo(
            "Copiar analítica",
            f"Enviando donante={payload['idlote_origen']} -> {len(payload['idlotes_destino'])} receptores"
        )

    def _on_reply_finished(self, reply):
        info = {"ok": False, "status": None, "body": None, "message": None}
        try:
            try:
                info["status"] = int(reply.attribute(QNetworkRequest.HttpStatusCodeAttribute) or 0)
            except Exception:
                info["status"] = None

            body = bytes(reply.readAll()).decode("utf-8", errors="replace")
            info["body"] = body

            if reply.error():
                info["message"] = reply.errorString()
                iface.messageBar().pushCritical("Copiar analítica", f"Error: {info['message']}")
                self.requestFinished.emit(info)
                return

            msg = body
            try:
                j = json.loads(body) if body else {}
                msg = j.get("message") or j.get("detail") or msg
            except Exception:
                pass

            info["ok"] = True
            info["message"] = msg
            iface.messageBar().pushSuccess("Copiar analítica", msg)
            self.requestFinished.emit(info)

        finally:
            reply.deleteLater()
            self._pending_reply = None

    # ---------- Estado / hooks ----------
    def _status_msg(self):
        d = self._donante if self._donante is not None else "—"
        r = len(self._receptores)
        iface.statusBarIface().showMessage(f"Copiar analítica | Donante: {d} | Receptores: {r}")

    def _on_project_change(self, *args, **kwargs):
        self.clearAll()

    def _on_layer_destroyed(self, *args):
        self.clearAll()
        self.layer = None

    def _layer_ok(self) -> bool:
        return self.layer is not None

    def deactivate(self):
        self.clearAll()
        super().deactivate()
