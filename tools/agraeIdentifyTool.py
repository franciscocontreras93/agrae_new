# -*- coding: utf-8 -*-
# agrae/tools/agraeIdentifyTool.py

from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtGui import QColor, QCursor, QGuiApplication
from qgis.PyQt.QtWidgets import QMenu, QAction
from qgis.gui import QgsMapToolIdentify, QgsHighlight
from qgis.core import QgsProject, QgsFeature, Qgis
from qgis.utils import iface

from ..dialogs import aGraeGEEDialog
from ..dialogs.integral_termica_detail_dialog import IntegralTermicaDialog


from ..core.api import APIRequest


class aGraeSelectTool(QgsMapToolIdentify):
    """
    Map tool con highlight propio y menú contextual integrado.
    - IZQ: resalta (Shift acumula, Ctrl limpia y deja solo la nueva).
    - DER sobre feature: abre menú contextual con herramientas (implementadas aquí).
    - DER sobre vacío: limpia todos los highlights.
    - Limpia automáticamente al remover la capa o cambiar/limpiar proyecto.
    """

    featureSelected = pyqtSignal(object)  # emite QgsFeature al click IZQ (por si quieres seguir usándolo)

    def __init__(
        self,
        layer,
        *,
        edge_color="#7B61FF",
        fill_color="#7B61FF",
        edge_alpha=220,
        fill_alpha=70,
        also_clear_native_selection=True,   # si limpiamos highlights, ¿limpiamos selección nativa?
        parent=None,
    ):
        super().__init__(iface.mapCanvas())
        self.api = APIRequest()

        self.layer = layer
        self.canvas = iface.mapCanvas()

        self._edge_color = QColor(edge_color)
        self._fill_color = QColor(fill_color)
        self._edge_alpha = edge_alpha
        self._fill_alpha = fill_alpha

        self._highlights: dict[int, QgsHighlight] = {}   # fid -> highlight
        self._custom_ids: set[int] = set()
        self._also_clear_native = also_clear_native_selection

        # Hooks de proyecto/capa para limpiar si desaparecen
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

    # ----------------- Eventos de canvas -----------------
    def canvasPressEvent(self, event):
        if not self._layer_ok():
            self.clearCustomSelection()
            return

        # Clic derecho: menú contextual o limpiar
        if event.button() == Qt.RightButton:
            self._on_right_click(event)
            return

        if event.button() != Qt.LeftButton:
            return

        results = self.identify(event.x(), event.y(), [self.layer], QgsMapToolIdentify.TopDownAll)
        if not results:
            return

        f = results[0].mFeature

        # Ctrl → limpiar todo; Shift → acumular; click simple → reemplazar
        if event.modifiers() & Qt.ControlModifier:
            self.clearCustomSelection()
        elif not (event.modifiers() & Qt.ShiftModifier):
            self.clearCustomSelection()

        self._custom_ids.add(f.id())
        self._add_highlight(f)

        # Si quieres la selección amarilla nativa además del highlight, descomenta:
        # self.layer.select(f.id())

        self.featureSelected.emit(f)

    # ----------------- Clic derecho: menú contextual -----------------
    def _on_right_click(self, event):
        if not self._layer_ok():
            self.clearCustomSelection()
            return

        results = self.identify(event.x(), event.y(), [self.layer], QgsMapToolIdentify.TopDownAll)
        if not results:
            # clic derecho en vacío ⇒ limpiar todo
            self.clearCustomSelection()
            return

        f = results[0].mFeature
        self._show_context_menu(f)

    def _show_context_menu(self, feature: QgsFeature):
        menu = QMenu(self.canvas)

        act_select_lote = QAction("Seleccionar Lote", menu)
        act_it_dialog = QAction("Zoom al lote", menu)
        act_select_lote.triggered.connect(lambda _, f=feature: self._toggle_native_selection(f))

        menu.addAction(act_select_lote)
        menu.addSeparator()

        # Submenú: Herramientas básicas
        menu_basicas = menu.addMenu("aGrae")


        # # Opción 1: crear QAction y conectarla
        act_it_dialog = QAction("Detalle Integral Térmica", menu_basicas)
        # # triggered(bool) -> capturamos el bool con "_" y fijamos 'feature' en el closure
        act_it_dialog.triggered.connect(lambda _, f=feature: self._open_integral_termica_dialog(f.id()))
        act_pan_lote = QAction("Centrar en lote", menu_basicas)
        act_pan_lote.triggered.connect(lambda _, f=feature: self._pan_to_feature(f))


        menu_basicas.addAction(act_it_dialog)

        menu_economicas = menu.addMenu("Facturación")
        act_facturacion = QAction("Asignar prescripción", menu_economicas)
        act_facturacion.triggered.connect(self._post_facturacion_action)

        menu_economicas.addAction(act_facturacion)
        # IMPORTANTE: añadir el submenú al menú principal (ya lo hicimos con addMenu arriba)
        # NO añadas la acción al menú raíz con menu.addAction(act_zoom_lote),
        # eso saca la acción fuera del submenú.

        # Mostrar menú contextual
        menu.exec_(QCursor.pos())







        
        # acts = {}
        # # Acciones integradas (sin necesidad de tocar el dock)
        # acts[menu.addAction("Zoom al lote")]          = ("zoom", feature)
        # acts[menu.addAction("Centrar en lote")]       = ("pan", feature)
        # menu.addSeparator()
        # acts[menu.addAction("Copiar ID")]             = ("copy_id", feature)
        # acts[menu.addAction("Copiar atributos")]      = ("copy_attrs", feature)
        # menu.addSeparator()
        # acts[menu.addAction("Seleccionar Lote")]  = ("native_select", feature)
        # acts[menu.addAction("Quitar highlight")]      = ("remove_highlight", feature)
        # acts[menu.addAction("Limpiar todo")]          = ("clear_all", None)
        # menu.addSeparator()
        # acts[menu.addAction("Abrir formulario")]      = ("open_form", feature)
        # acts[menu.addAction("Abrir GEE")]             = ("open_gee", feature)

        # chosen = menu.exec_(QCursor.pos())
        # if not chosen:
        #     return

        # key, f = acts[chosen]
        # # Ejecutamos aquí mismo (no hace falta que el dock haga nada)
        # try:
        #     if key == "zoom":
        #         self._zoom_to_feature(f)
        #     elif key == "pan":
        #         self._pan_to_feature(f)
        #     elif key == "copy_id":
        #         self._copy_to_clipboard(self._preferred_id_value(f))
        #     elif key == "copy_attrs":
        #         self._copy_to_clipboard(self._attrs_as_text(f))
        #     elif key == "native_select":
        #         self._toggle_native_selection(f)
        #     elif key == "remove_highlight":
        #         self._remove_highlight(f.id())
        #         self._custom_ids.discard(f.id())
        #     elif key == "clear_all":
        #         self.clearCustomSelection()
        #     elif key == "open_form":
        #         self._open_attribute_form(f)
        #     elif key == "open_gee":
        #         self._open_gee_dialog()
        # except Exception as e:
        #     # no rompemos la herramienta por un error en una acción
        #     pass

    # ----------------- Helpers de highlight -----------------
    def _add_highlight(self, feature: QgsFeature):
        fid = feature.id()
        if fid in self._highlights:
            self._remove_highlight(fid)

        h = QgsHighlight(self.canvas, feature.geometry(), self.layer)

        edge = QColor(self._edge_color); edge.setAlpha(self._edge_alpha)
        fill = QColor(self._fill_color); fill.setAlpha(self._fill_alpha)

        h.setColor(edge)
        h.setFillColor(fill)
        h.setWidth(2)
        h.show()
        self._highlights[fid] = h

    def _remove_highlight(self, fid: int):
        h = self._highlights.pop(fid, None)
        if h:
            try:
                h.hide()
                h.deleteLater()
            except Exception:
                pass

    def clearCustomSelection(self):
        for fid in list(self._highlights.keys()):
            self._remove_highlight(fid)
        self._custom_ids.clear()

        if self._also_clear_native and self._layer_ok():
            try:
                self.layer.removeSelection()
            except Exception:
                pass

    # ----------------- Acciones integradas -----------------
    def _zoom_to_feature(self, feature: QgsFeature):
        g = feature.geometry()
        if not g or g.isEmpty():
            return
        rect = g.boundingBox()
        rect.grow(0.10 * max(rect.width(), rect.height()))  # margen
        self.canvas.setExtent(rect)
        self.canvas.refresh()

    def _pan_to_feature(self, feature: QgsFeature):
        g = feature.geometry()
        if not g or g.isEmpty():
            return
        self.canvas.setCenter(g.boundingBox().center())
        self.canvas.refresh()

    def _toggle_native_selection(self, feature: QgsFeature):
        # Alterna selección nativa de la capa para ese FID
        try:
            if feature.id() in self.layer.selectedFeatureIds():
                self.layer.deselect(feature.id())
            else:
                self.layer.select(feature.id())
        except Exception:
            pass

    def _open_attribute_form(self, feature: QgsFeature):
        try:
            iface.openFeatureForm(self.layer, feature, showModal=True)
        except Exception:
            pass

    def _preferred_id_value(self, feature: QgsFeature) -> str:
        # intenta campos comunes; si no, usa FID
        for k in ("iddata"):
            if k in feature.fields().names():
                v = feature[k]
                return "" if v is None else str(v)
        return str(feature.id())

    def _attrs_as_text(self, feature: QgsFeature) -> str:
        # texto simple clave=valor (puedes cambiar a JSON si prefieres)
        parts = []
        flds = feature.fields()
        for i in range(flds.count()):
            if not 'id' in flds.at(i).name().lower():
                name = flds.at(i).name()
                val = feature[name]
                parts.append(f"{name}={val}")
        return "\n".join(parts)

    def _copy_to_clipboard(self, text: str):
        try:
            QGuiApplication.clipboard().setText(text or "")
        except Exception:
            pass
    
    def _open_gee_dialog(self):
        dlg = aGraeGEEDialog()
        dlg.exec()

    def _open_integral_termica_dialog(self, iddata):
        # print(iddata)
        dlg = IntegralTermicaDialog(iddata=iddata)
        dlg.exec()

    def _post_facturacion_action(self):
        features = self.layer.getSelectedFeatures()
        if not features:
            return
        iddata = [f["iddata"] if "iddata" in f.fields().names() else f.id() for f in features]

        data = {
            "iddata": iddata
        }
        try:
            r = self.api.post("billing/data_estado/prescripcion_ejecutada",data) 
            if r['status'] == 'success':
                iface.messageBar().pushMessage("Correcto", f" {r['message']}", level=Qgis.Success)
        except Exception as e:
            iface.messageBar().pushMessage("Error", f"No se pudo asignar la prescripción: {e}", level=Qgis.Critical)    
        
    # ----------------- Hooks proyecto/capa -----------------
    def _on_project_change(self, *args, **kwargs):
        self.clearCustomSelection()

    def _on_layer_destroyed(self, *args):
        self.clearCustomSelection()
        self.layer = None

    def _layer_ok(self) -> bool:
        return self.layer is not None

    def deactivate(self):
        self.clearCustomSelection()
        super().deactivate()

    # opcional: leer ids resaltados por la herramienta
    def customSelectedIds(self):
        return list(self._custom_ids)
    
    
