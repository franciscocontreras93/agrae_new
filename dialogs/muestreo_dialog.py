from qgis.PyQt.QtWidgets import * 
from qgis.PyQt.QtCore import * 
from qgis.PyQt.QtGui import * 

from qgis.PyQt.QtCore import pyqtSignal, QSize, QDate
from qgis.core import *
from qgis.gui import * 
from qgis.PyQt import uic

from ..gui import agraeGUI
from ..gui.components import CampaniasComboBox
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
        # Pestaña -> layout vertical
        tab_muestreo_v = QVBoxLayout(self.tab_muestreo)
        tab_muestreo_v.setContentsMargins(8, 8, 8, 8)
        tab_muestreo_v.setSpacing(10)

        # Group principal
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

        # Botón
        self.btn_create = QPushButton('Generar', self.tab_muestreo)
        self.btn_create.clicked.connect(self.createMuestreoPoints)

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
        group_muestreo_g.addWidget(self.btn_create, row, 0, 1, 2)

        # Añadir el group a la pestaña
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

        # Controles iniciales para remuestreo (base para que sigas)
        self.combo_campania = CampaniasComboBox(parent=group_remuestreo)
        self.combo_campania.setPlaceholderText('Selecciona una campaña')

        group_remuestreo_g.addWidget(QLabel('Selecciona la Campaña'), 0, 0)
        group_remuestreo_g.addWidget(self.combo_campania, 0, 1)

        # (deja preparado el espacio para más controles)
        # p.ej.: self.combo_lotes_remuestreo = QgsMapLayerComboBox(group_remuestreo)
        # group_remuestreo_g.addWidget(QLabel('Lotes'), 1, 0)
        # group_remuestreo_g.addWidget(self.combo_lotes_remuestreo, 1, 1)

        tab_remuestreo_v.addWidget(group_remuestreo)
        tab_remuestreo_v.addStretch(1)

        # ====== ENSAMBLAR TABS ======
        self.tab_widget.addTab(self.tab_muestreo, 'Muestreo')
        self.tab_widget.addTab(self.tab_remuestreo, 'Remuestreo')
        main_layout.addWidget(self.tab_widget)

    # ================== LÓGICA ==================
    def createMuestreoPoints(self):
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

        if self.check_seleccionados.isChecked():
            ids = [f['iddata'] for f in list(layer.getSelectedFeatures())]
        else:
            ids = [f['iddata'] for f in list(layer.getFeatures())]

        # Calcular segmentos a derivar
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
                if data.get('status_code') == 200:
                    self.tools.messages(
                        'Puntos de Muestreo',
                        f'Se han generado los puntos de muestreo correctamente.\n{data.get("message")}',
                        3,
                        alert=True
                    )
                elif data.get('status_code') == 409:
                    self.tools.messages(
                        'Puntos de Muestreo',
                        f'No se han podido generar los puntos de muestreo.\n{data.get("message")}',
                        1,
                        alert=True
                    )
