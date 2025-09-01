from math import exp
from qgis.PyQt.QtWidgets import * 
from qgis.PyQt.QtCore import * 
from qgis.PyQt.QtGui import * 

from qgis.PyQt.QtCore import pyqtSignal, QSize, QDate
from qgis.core import *
from qgis.gui import * 
from qgis.PyQt import uic

from ..gui import agraeGUI
from ..gui.components import CampaniasComboBox, ExplotacionesComboBox
from ..db import agraeDataBaseDriver
from ..sql import aGraeSQLTools
from ..tools import aGraeTools

from ..core.workers import WorkerGenerarPuntosMuestreo

import asyncio


class MuestreoDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.agraeSql = aGraeSQLTools()
        self.tools = aGraeTools()
        self.setWindowTitle('aGrae | Generar Puntos de Muestreo')
        self.resize(720, 520)

        self.UIComponents()

    def UIComponents(self): 
        # ====== MAIN LAYOUT + TABS ======
        main_layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget(self)

        # -- Pestañas
        self.tab_muestreo = QWidget(self.tab_widget)
        self.tab_remuestreo = QWidget(self.tab_widget)

        # ====== TAB: MUESTREO ======
        tab_muestreo_v = QVBoxLayout(self.tab_muestreo)
        tab_muestreo_v.setContentsMargins(8, 8, 8, 8)
        tab_muestreo_v.setSpacing(10)

        group_muestreo = QGroupBox('Generar Puntos de Muestreo en Lotes', self.tab_muestreo)
        group_muestreo_g = QGridLayout(group_muestreo)
        group_muestreo_g.setContentsMargins(10, 10, 10, 10)
        group_muestreo_g.setHorizontalSpacing(8)
        group_muestreo_g.setVerticalSpacing(6)

        # Controles principales
        self.combo_layer_lotes = QgsMapLayerComboBox(self.tab_muestreo)
        self.check_seleccionados = QCheckBox('Lotes seleccionados', self.tab_muestreo)
        self.check_seleccionados.setChecked(True)
        self.check_seguimiento = QCheckBox('Muestra de Seguimiento', self.tab_muestreo)
        self.check_seguimiento.setChecked(False)

        # Sub-group: segmentos
        group_segmentos = QGroupBox('Generar Muestras en Segmentos', group_muestreo)
        group_segmentos_h = QHBoxLayout(group_segmentos)
        group_segmentos_h.setContentsMargins(10, 8, 10, 8)
        group_segmentos_h.setSpacing(12)

        self.check_segmento_1 = QCheckBox('Segmento 1', group_segmentos)
        self.check_segmento_1.setChecked(True)
        self.check_segmento_2 = QCheckBox('Segmento 2', group_segmentos)
        self.check_segmento_2.setChecked(True)
        self.check_segmento_3 = QCheckBox('Segmento 3', group_segmentos)
        self.check_segmento_3.setChecked(True)

        group_segmentos_h.addWidget(self.check_segmento_1)
        group_segmentos_h.addWidget(self.check_segmento_2)
        group_segmentos_h.addWidget(self.check_segmento_3)
        group_segmentos_h.addStretch(1)

        # Botón MUestreo
        self.btn_create_muestreo = QPushButton('Generar', self.tab_muestreo)
        # Importante: conectar al slot correcto (no a self.create)
        self.btn_create_muestreo.clicked.connect(self.createMuestreoPoints)

        # Colocar en la grilla del group principal
        row = 0
        group_muestreo_g.addWidget(QLabel('Selecciona la Capa con los Lotes'), row, 0, 1, 1)
        group_muestreo_g.addWidget(self.combo_layer_lotes, row, 1, 1, 1)
        row += 1
        group_muestreo_g.addWidget(self.check_seleccionados, row, 0, 1, 1)
        group_muestreo_g.addWidget(self.check_seguimiento, row, 1, 1, 1)
        row += 1
        group_muestreo_g.addWidget(group_segmentos, row, 0, 1, 2)
        row += 1
        group_muestreo_g.addWidget(self.btn_create_muestreo, row, 0, 1, 2)

        tab_muestreo_v.addWidget(group_muestreo)
        tab_muestreo_v.addStretch(1)

        # ====== TAB: REMUESTREO ======
        tab_remuestreo_v = QVBoxLayout(self.tab_remuestreo)
        tab_remuestreo_v.setContentsMargins(8, 8, 8, 8)
        tab_remuestreo_v.setSpacing(10)

        group_remuestreo = QGroupBox('Generar Puntos de Remuestreo', self.tab_remuestreo)
        group_remuestreo_g = QGridLayout(group_remuestreo)
        group_remuestreo_g.setContentsMargins(10, 10, 10, 10)
        group_remuestreo_g.setHorizontalSpacing(8)
        group_remuestreo_g.setVerticalSpacing(6)

        # Controles Remuestreo
        self.combo_campania = CampaniasComboBox(parent=group_remuestreo,exclude_latest=True)
        self.combo_campania.setPlaceholderText('Selecciona una campaña')

        self.combo_explotacion = ExplotacionesComboBox(parent=group_remuestreo)
        self.combo_explotacion.setPlaceholderText('Selecciona una explotación')
        self.combo_explotacion.bind_to_campaigns(self.combo_campania)

        self.combo_segmentos_remuestreo = QgsMapLayerComboBox(group_remuestreo)
        self.combo_segmentos_remuestreo.setPlaceholderText('Selecciona la capa de Segmentos de Remuestreo')
        self.combo_segmentos_remuestreo.setFilters(QgsMapLayerProxyModel.PolygonLayer)

        # Botón Remuestreo
        self.btn_create_remuestreo = QPushButton('Generar', self.tab_remuestreo)
        self.btn_create_remuestreo.clicked.connect(self.createRemuestreoPoints)

        # Distribución Remuestreo con contador local
        row_r = 0
        group_remuestreo_g.addWidget(QLabel('Remuestrear desde la Campaña'), row_r, 0)
        group_remuestreo_g.addWidget(self.combo_campania, row_r, 1); row_r += 1

        group_remuestreo_g.addWidget(QLabel('Remuestrear desde  la Explotación'), row_r, 0)
        group_remuestreo_g.addWidget(self.combo_explotacion, row_r, 1); row_r += 1

        group_remuestreo_g.addWidget(QLabel('Remuestrear desde  la capa de\nSegmentos de Remuestreo'), row_r, 0)
        group_remuestreo_g.addWidget(self.combo_segmentos_remuestreo, row_r, 1); row_r += 1

        group_remuestreo_g.addWidget(self.btn_create_remuestreo, row_r, 0, 1, 2)

        tab_remuestreo_v.addWidget(group_remuestreo)
        tab_remuestreo_v.addStretch(1)

        # Validación reactiva de la capa de remuestreo (UX: deshabilita botón si falta schema)
        if hasattr(self.combo_segmentos_remuestreo, "layerChanged"):
            self.combo_segmentos_remuestreo.layerChanged.connect(self._validate_remuestreo_layer)
        # Validación inicial
        self._validate_remuestreo_layer(self.combo_segmentos_remuestreo.currentLayer())

        # ====== ENSAMBLAR TABS ======
        self.tab_widget.addTab(self.tab_muestreo, 'Muestreo')
        self.tab_widget.addTab(self.tab_remuestreo, 'Remuestreo')
        main_layout.addWidget(self.tab_widget)

    # ------------------ helpers UX ------------------
    def _validate_remuestreo_layer(self, layer: QgsMapLayer | None):
        """
        Habilita/Deshabilita el botón de remuestreo según que la capa tenga
        los campos 'idlote' e 'idsegmento'. Coloca un tooltip explicativo.
        """
        ok = False
        if layer is not None and isinstance(layer, QgsVectorLayer):
            names = {f.name() for f in layer.fields()}
            ok = ("idlote" in names) and ("idsegmento" in names)
        self.btn_create_remuestreo.setEnabled(ok)
        tip = "" if ok else "La capa debe tener los campos 'idlote' e 'idsegmento'."
        self.btn_create_remuestreo.setToolTip(tip)

    # ================== LÓGICA ==================
    def createMuestreoPoints(self):
        """
        Mantiene tu lógica tal cual, pero con una mejora de UX:
        si está marcado 'Lotes seleccionados' y no hay selección,
        ofrece procesar todos los lotes o cancelar para que seleccione.
        """
        layer = self.combo_layer_lotes.currentLayer()
        if layer is None:
            QMessageBox.warning(self, 'aGrae Toolbox', 'Selecciona una capa de lotes válida.')
            return

        segmentos = [1, 2, 3]
        selected = []

        if self.check_segmento_1.isChecked():
            selected.append(1)
        if self.check_segmento_2.isChecked():
            selected.append(2)
        if self.check_segmento_3.isChecked():
            selected.append(3)

        # UX mejorada para "Lotes seleccionados"
        if self.check_seleccionados.isChecked():
            sel_feats = list(layer.getSelectedFeatures())
            if not sel_feats:
                ask = QMessageBox.question(
                    self,
                    'aGrae Toolbox',
                    'No hay lotes seleccionados.\n\n¿Quieres procesar TODOS los lotes de la capa?',
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if ask == QMessageBox.Yes:
                    ids = [f['iddata'] for f in layer.getFeatures()]
                else:
                    QMessageBox.information(self, 'aGrae Toolbox', 'Debes seleccionar uno o más lotes y volver a intentarlo.')
                    return
            else:
                ids = [f['iddata'] for f in sel_feats]
        else:
            ids = [f['iddata'] for f in layer.getFeatures()]

        # Calcular segmentos a derivar (MISMA LÓGICA)
        for x in selected:
            if x in segmentos:
                segmentos.remove(x)
        if len(selected) == 3:
            segmentos = [0]

        segmento_derivar = segmentos
        segmento_remuestreo = selected

        tipo = 3 if self.check_seguimiento.isChecked() else 1

        if not ids:
            QMessageBox.information(self, 'aGrae Toolbox', 'No hay lotes para procesar.')
            return

        reply = QMessageBox.question(
            self,
            'aGrae Toolbox',
            f'¿Quieres generar los puntos de muestreo para:\n{len(ids)} lotes?',
            QMessageBox.Yes, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            data = asyncio.run(self.tools.crearPuntosMuestreo(ids, segmento_remuestreo, segmento_derivar, tipo))
            if data:
                # Acepta contrato nuevo (ok/status_code/message) o el anterior
                ok = data.get('ok', None)
                status = data.get('status_code')
                message = data.get('message', '')

                if ok is True or status == 200:
                    self.tools.messages(
                        'Puntos de Muestreo',
                        f'Se han generado los puntos de muestreo correctamente.\n{message}',
                        3,
                        alert=True
                    )
                elif status == 409:
                    self.tools.messages(
                        'Puntos de Muestreo',
                        f'No se han podido generar los puntos de muestreo.\n{message}',
                        1,
                        alert=True
                    )
                else:
                    self.tools.messages(
                        'Puntos de Muestreo',
                        f'Respuesta del servidor ({status}).\n{message}',
                        2,
                        alert=True
                    )

    def createRemuestreoPoints(self):
        """
        Genera puntos de RE-muestreo con validación de esquema de capa.
        Evita KeyError si la capa no contiene 'idlote' o 'idsegmento'.
        """
        # 1) Campaña y Explotación
        idcamp = self.combo_campania.get_current_campaign_id() if hasattr(self.combo_campania, "get_current_campaign_id") else self.combo_campania.currentData()
        idexpl = self.combo_explotacion.get_current_explotacion_id() if hasattr(self.combo_explotacion, "get_current_explotacion_id") else self.combo_explotacion.currentData()

        campania_name = self.combo_campania.get_current_campaign_name() if hasattr(self.combo_campania, "get_current_campaign_name") else "N/A"
        explotacion_name = self.combo_explotacion.get_current_explotacion_name() if hasattr(self.combo_explotacion, "get_current_explotacion_name") else "N/A"

        if idcamp is None:
            QMessageBox.warning(self, "aGrae Toolbox", "Selecciona una campaña válida para el remuestreo.")
            return
        if idexpl is None:
            QMessageBox.warning(self, "aGrae Toolbox", "Selecciona una explotación válida para el remuestreo.")
            return

        # 2) Capa de segmentos
        layer = self.combo_segmentos_remuestreo.currentLayer()
        if layer is None:
            QMessageBox.warning(self, "aGrae Toolbox", "Selecciona la capa de Segmentos de Remuestreo (poligonal).")
            return

        # 3) Validación de campos requeridos
        field_names = {f.name() for f in layer.fields()}
        required = {"idlote", "idsegmento"}
        missing = sorted(required - field_names)
        if missing:
            QMessageBox.warning(
                self,
                "aGrae Toolbox",
                "La capa seleccionada no contiene los campos requeridos:\n - " + "\n - ".join(missing) +
                "\n\nElige otra capa o ajusta el modelo para incluir estos campos."
            )
            return

        # 4) Extraer listas únicas usando attribute() para evitar KeyError
        idlotes = set()
        idsegmentos = set()
        for feat in layer.getFeatures():  # cambia a getSelectedFeatures() si prefieres solo seleccionados
            v_lote = feat.attribute("idlote")
            v_seg  = feat.attribute("idsegmento")
            if v_lote is not None:
                try:
                    idlotes.add(int(v_lote))
                except Exception:
                    pass
            if v_seg is not None:
                try:
                    idsegmentos.add(int(v_seg))
                except Exception:
                    pass

        idlotes_lista = sorted(idlotes)
        idsegmentos_lista = sorted(idsegmentos)

        if not idlotes_lista or not idsegmentos_lista:
            QMessageBox.information(self, "aGrae Toolbox", "No se encontraron valores válidos de 'idlote' y/o 'idsegmento' en la capa.")
            return

        # 5) Confirmación
        msg = (
            "Vas a generar puntos de Remuestreo:\n"
            f" - Campaña anterior: {campania_name}\n"
            f" - Explotación: {explotacion_name}\n"
            f" - # Lotes: {len(idlotes_lista)}\n"
            f" - # Segmentos: {len(idsegmentos_lista)}\n\n"
            "¿Continuar?"
        )
        if QMessageBox.question(self, "aGrae Toolbox", msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
            return

        # 6) Llamada al backend
        resp = asyncio.run(
            self.tools.crearPuntosRemuestreo(
                idcampania_anterior=int(idcamp),
                idexplotacion=int(idexpl),
                idlotes_lista=idlotes_lista,
                idsegmentos_lista=idsegmentos_lista,
            )
        )

        if not resp:
            self.tools.messages("Puntos de Remuestreo", "Sin respuesta del servidor.", 1, alert=True)
            return

        if resp.get("ok") or resp.get("status_code") == 200:
            self.tools.messages(
                "Puntos de Remuestreo",
                f"Se generaron los puntos de remuestreo correctamente.\n{resp.get('message','')}",
                3, alert=True
            )
        else:
            self.tools.messages(
                "Puntos de Remuestreo",
                f"Error ({resp.get('status_code')}): {resp.get('message','')}",
                1, alert=True
            )
