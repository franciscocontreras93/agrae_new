from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtGui import QColor
from qgis.gui import QgsMapToolIdentify, QgsHighlight
from qgis.utils import iface

class aGraeSelectTool(QgsMapToolIdentify):
    featureSelected = pyqtSignal(object)  # QgsFeature

    def __init__(
        self,
        layer,
        edge_color="#8843E2",
        fill_color="#7B61FF",
        edge_alpha=220,
        fill_alpha=70,
        right_click_mode="clear_one",      # "clear_one" | "clear_all"
        also_clear_native_selection=True,  # si borramos highlights, ¿quitamos también la selección nativa?
        parent=None
    ):
        super().__init__(iface.mapCanvas())
        self.layer = layer
        self.canvas = iface.mapCanvas()

        self._edge_color = QColor(edge_color)
        self._fill_color = QColor(fill_color)
        self._edge_alpha = edge_alpha
        self._fill_alpha = fill_alpha

        self._rc_mode = right_click_mode
        self._also_clear_native = also_clear_native_selection

        self._highlights = {}   # fid -> QgsHighlight
        self._custom_ids = set()

    # ---------- eventos ----------
    def canvasPressEvent(self, event):
        if event.button() == Qt.RightButton:
            self._handle_right_click(event)
            return

        if event.button() != Qt.LeftButton:
            return

        results = self.identify(event.x(), event.y(), [self.layer], QgsMapToolIdentify.TopDownAll)
        if not results:
            return

        f = results[0].mFeature

        # Ctrl → limpiar todo primero; Shift → acumular; click simple → reemplazar
        if event.modifiers() & Qt.ControlModifier:
            self.clearCustomSelection()
        elif not (event.modifiers() & Qt.ShiftModifier):
            self.clearCustomSelection()

        self._custom_ids.add(f.id())
        self._addHighlight(f)

        # Si quieres evitar la selección amarilla, comenta esta línea:
        # self.layer.select(f.id())

        self.featureSelected.emit(f)

    # ---------- clic derecho ----------
    def _handle_right_click(self, event):
        if self._rc_mode == "clear_all":
            self.clearCustomSelection()
            return

        # clear_one: intenta borrar SOLO la feature bajo el cursor;
        # si no hay nada bajo el cursor, limpia todo.
        results = self.identify(event.x(), event.y(), [self.layer], QgsMapToolIdentify.TopDownAll)
        if results:
            fid = results[0].mFeature.id()
            if fid in self._highlights:
                self._removeHighlight(fid)
                self._custom_ids.discard(fid)
                if self._also_clear_native:
                    try:
                        self.layer.deselect(fid)
                    except Exception:
                        pass
                return

        # si no había feature bajo el cursor, limpia todo
        self.clearCustomSelection()

    # ---------- helpers de highlight ----------
    def _addHighlight(self, feature):
        fid = feature.id()
        # si ya existía, primero lo quitamos
        if fid in self._highlights:
            self._removeHighlight(fid)

        h = QgsHighlight(self.canvas, feature.geometry(), self.layer)

        c = QColor(self._edge_color); c.setAlpha(self._edge_alpha)
        h.setColor(c)

        fc = QColor(self._fill_color); fc.setAlpha(self._fill_alpha)
        h.setFillColor(fc)

        h.setWidth(2)
        h.show()

        self._highlights[fid] = h

    def _removeHighlight(self, fid):
        h = self._highlights.pop(fid, None)
        if h:
            try:
                h.hide()
                h.deleteLater()
            except Exception:
                pass

    def clearCustomSelection(self):
        # limpiar highlights
        for fid in list(self._highlights.keys()):
            self._removeHighlight(fid)
        self._custom_ids.clear()

        # limpiar selección nativa si procede
        if self._also_clear_native:
            try:
                self.layer.removeSelection()
            except Exception:
                pass

    def deactivate(self):
        self.clearCustomSelection()
        super().deactivate()

    # opcional: para leer ids resaltados por esta herramienta
    def customSelectedIds(self):
        return list(self._custom_ids)
