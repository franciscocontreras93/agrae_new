# agrae/tools/agraeCopyAnaliticaSelectTool.py
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import QMenu, QAction

from qgis.gui import QgsMapToolIdentify, QgsHighlight
from qgis.core import QgsProject, QgsFeature, QgsVectorLayer
from qgis.utils import iface

from ..dialogs.copiar_analitica_dialog import CopyAnaliticaWizardDialog

from . import aGraeTools

import requests
import asyncio



class aGraeCopyAnaliticaSelectTool(QgsMapToolIdentify):
    """
    Tool 2 pasos:
      - Selección de PADRE (1 feature)
      - Selección de HIJOS (N features)
    Colorea highlights distintos y usa click derecho para confirmar/ejecutar.
    """

    # Señales para que el plugin conecte ejecución del endpoint
    execute_endpoint = pyqtSignal(int, list)  # padre_idlote, hijos_idlote_list

    STEP_PADRE = 1
    STEP_HIJOS = 2

    def __init__(self, canvas, lotes_layer: QgsVectorLayer, idcampania:int, idexplotacion:int, id_field="idlote"):
        super().__init__(canvas)
        self.canvas = canvas
        self.layer = lotes_layer
        self.id_field = id_field
        self.idcampania = idcampania
        self.idexplotacion = idexplotacion
        # colores (ajustá a tu paleta)
        self.color_padre = QColor(0, 0, 0, 180)       # negro semi
        self.color_hijos = QColor(0, 160, 255, 180)   # azul
        self.width_padre = 3
        self.width_hijos = 2

        self.step = self.STEP_PADRE
        self.padre_feat = None
        self.hijos = {}  # id -> feature

        self.hl_padre = None
        self.hl_hijos = {}  # id -> highlight
        self.tools = aGraeTools()

        self.dlg = None

    # -------------------------
    # Ciclo de vida
    # -------------------------
    def activate(self):
        super().activate()
        self._ensure_dialog()
        self._reset_all(keep_dialog=True)
        self.dlg.show()
        self.dlg.raise_()
        self.dlg.activateWindow()

    def deactivate(self):
        super().deactivate()
        self._clear_highlights()
        if self.dlg:
            self.dlg.close()
            self.dlg = None

    # -------------------------
    # Dialog wiring
    # -------------------------
    def _ensure_dialog(self):
        if self.dlg:
            return
        self.dlg = CopyAnaliticaWizardDialog(parent=iface.mainWindow())
        self.dlg.cancelled.connect(self._on_cancelled)
        self.dlg.confirm_requested.connect(self.confirm_padre if self.step == self.STEP_PADRE else self.confirm_hijos)
        self.dlg.reset_requested.connect(lambda: self._reset_all(keep_dialog=True))
        self.dlg.execute_requested.connect(self.on_execute_requested)

    def _on_cancelled(self):
        iface.mapCanvas().unsetMapTool(self)

    # -------------------------
    # Eventos de mouse
    # -------------------------
    def canvasReleaseEvent(self, e):
        if not self.layer or not self.layer.isValid():
            iface.messageBar().pushWarning("aGrae", "Capa de lotes inválida.")
            return

        if e.button() == Qt.LeftButton:
            self._handle_left_click(e)
        elif e.button() == Qt.RightButton:
            self._open_context_menu(e)

    def _handle_left_click(self, e):
        feat = self._identify_feature(e)
        if not feat:
            return

        if self.step == self.STEP_PADRE:
            self._set_padre(feat)

        elif self.step == self.STEP_HIJOS:
            self._toggle_hijo(feat)

        self._update_execute_state()

    def _open_context_menu(self, e):
        menu = QMenu()

        if self.step == self.STEP_PADRE:
            a_confirm = QAction("Confirmar padre", menu)
            a_confirm.setEnabled(self.padre_feat is not None)
            a_confirm.triggered.connect(self.confirm_padre)

            a_reset = QAction("Reset", menu)
            a_reset.triggered.connect(lambda: self._reset_all(keep_dialog=True))

            menu.addAction(a_confirm)
            menu.addSeparator()
            menu.addAction(a_reset)

        elif self.step == self.STEP_HIJOS:
            a_confirm_h = QAction("Confirmar hijos", menu)
            a_confirm_h.setEnabled(len(self.hijos) > 0)
            a_confirm_h.triggered.connect(self.confirm_hijos)

            a_exec = QAction("Ejecutar endpoint", menu)
            a_exec.setEnabled(self._can_execute())
            a_exec.triggered.connect(self.on_execute_requested)

            a_reset_h = QAction("Reset hijos", menu)
            a_reset_h.triggered.connect(self._reset_hijos_only)

            a_reset_all = QAction("Reset todo", menu)
            a_reset_all.triggered.connect(lambda: self._reset_all(keep_dialog=True))

            menu.addAction(a_confirm_h)
            menu.addAction(a_exec)
            menu.addSeparator()
            menu.addAction(a_reset_h)
            menu.addAction(a_reset_all)

        menu.exec_(e.globalPos())

    # -------------------------
    # Lógica selección
    # -------------------------
    def _identify_feature(self, e) -> QgsFeature | None:
        res = self.identify(
            e.x(), e.y(),
            [self.layer],
            QgsMapToolIdentify.TopDownStopAtFirst
        )
        if not res:
            return None
        return res[0].mFeature

    def _feat_id(self, feat: QgsFeature) -> int:
        val = feat[self.id_field]
        try:
            return int(val)
        except Exception:
            # fallback: id interno
            return int(feat.id())

    def _set_padre(self, feat: QgsFeature):
        self.padre_feat = feat
        self._draw_padre_highlight(feat)

    def _toggle_hijo(self, feat: QgsFeature):
        fid = self._feat_id(feat)

        # Evitar seleccionar el mismo lote que padre
        if self.padre_feat and fid == self._feat_id(self.padre_feat):
            iface.messageBar().pushWarning("aGrae", "El hijo no puede ser el mismo lote que el padre.")
            return

        if fid in self.hijos:
            # quitar
            self.hijos.pop(fid, None)
            self._remove_hijo_highlight(fid)
        else:
            # agregar
            self.hijos[fid] = feat
            self._add_hijo_highlight(fid, feat)

    # -------------------------
    # Confirmaciones
    # -------------------------
    def confirm_padre(self):
        if not self.padre_feat:
            return
        self.step = self.STEP_HIJOS
        self.dlg.btn_confirm.setText("Confirmar hijos")
        self.dlg.set_step_hijos()
        self._update_execute_state()

    def confirm_hijos(self):
        # acá podrías “bloquear” selección o sólo informar
        if len(self.hijos) == 0:
            return
        iface.messageBar().pushInfo("aGrae", f"Hijos confirmados: {len(self.hijos)}")

    def on_execute_requested(self):
        if not self._can_execute():
            iface.messageBar().pushWarning("aGrae", "Falta seleccionar padre y al menos 1 hijo.")
            return

        padre_id = self._feat_id(self.padre_feat)
        hijos_ids = sorted(list(self.hijos.keys()))

        try:

            # Ejecuta el helper del tools (async) desde un contexto sync
            resp = asyncio.run(
                self.tools.copiar_analitica(
                    self.idcampania,
                    self.idexplotacion,
                    padre_id,
                    hijos_ids
                )
            )

            # Manejo estándar de respuesta
            if resp.get("ok"):
                iface.messageBar().pushSuccess(
                    "aGrae",
                    f"Analítica copiada OK ({resp.get('status_code')}): {resp.get('message','')}"
                )
            else:
                iface.messageBar().pushCritical(
                    "aGrae",
                    f"Error ({resp.get('status_code')}): {resp.get('message','')}"
                )

        except Exception as ex:
            iface.messageBar().pushCritical("aGrae", f"Excepción ejecutando endpoint: {ex}")
        
        self._reset_all(keep_dialog=True)

    def _can_execute(self) -> bool:
        return self.padre_feat is not None and len(self.hijos) > 0 and self.step == self.STEP_HIJOS

    def _update_execute_state(self):
        if self.dlg:
            self.dlg.set_execute_enabled(self._can_execute())

    # -------------------------
    # Highlights
    # -------------------------
    def _draw_padre_highlight(self, feat: QgsFeature):
        if self.hl_padre:
            self.hl_padre.hide()
            self.hl_padre = None

        self.hl_padre = QgsHighlight(self.canvas, feat.geometry(), self.layer)
        self.hl_padre.setColor(self.color_padre)
        self.hl_padre.setWidth(self.width_padre)
        self.hl_padre.show()

    def _add_hijo_highlight(self, fid: int, feat: QgsFeature):
        hl = QgsHighlight(self.canvas, feat.geometry(), self.layer)
        hl.setColor(self.color_hijos)
        hl.setWidth(self.width_hijos)
        hl.show()
        self.hl_hijos[fid] = hl

    def _remove_hijo_highlight(self, fid: int):
        hl = self.hl_hijos.pop(fid, None)
        if hl:
            hl.hide()

    def _clear_highlights(self):
        if self.hl_padre:
            self.hl_padre.hide()
            self.hl_padre = None
        for hl in self.hl_hijos.values():
            hl.hide()
        self.hl_hijos = {}

    # -------------------------
    # Reset
    # -------------------------
    def _reset_hijos_only(self):
        for fid in list(self.hijos.keys()):
            self._remove_hijo_highlight(fid)
        self.hijos = {}
        self._update_execute_state()

    def _reset_all(self, keep_dialog=False):
        self.step = self.STEP_PADRE
        self.padre_feat = None
        self.hijos = {}
        self._clear_highlights()
        if self.dlg and keep_dialog:
            self.dlg.set_step_padre()
            self.dlg.set_execute_enabled(False)
