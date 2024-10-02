from qgis.PyQt.QtWidgets import * 
from qgis.PyQt.QtCore import * 
from qgis.PyQt.QtGui import * 

from qgis.PyQt.QtCore import pyqtSignal, QSize, QDate
from qgis.core import *
from qgis.gui import * 
from qgis.PyQt import uic

from ..gui import agraeGUI
from ..db import agraeDataBaseDriver
from ..sql import aGraeSQLTools
from ..tools import aGraeTools

from ..core.workers import WorkerGenerarPuntosMuestreo



class MuestreoDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.agraeSql = aGraeSQLTools()
        self.tools = aGraeTools()
        self.setWindowTitle('aGrae | Generar Puntos de Muestreo')

        self.UIComponents()
        pass

    def UIComponents(self): 
        main_layout = QVBoxLayout()
        group_layout = QVBoxLayout()
        groupBox = QGroupBox()
        groupBox.setTitle('Generar Puntos de Muestreo en Lotes')

        
        self.combo_layer = QgsMapLayerComboBox()
        self.check_seleccionados = QCheckBox('Lotes seleccionados')
        self.check_seleccionados.setChecked(True)

        
        
        group_segmentos = QGroupBox()
        group_segmentos.setTitle('Generar Muestras en Segmentos')
        group_segmentos_layout = QHBoxLayout()

        self.check_segmento_1 = QCheckBox('Segmento 1')
        self.check_segmento_1.setChecked(True)
        self.check_segmento_2 = QCheckBox('Segmento 2')
        self.check_segmento_2.setChecked(True)
        self.check_segmento_3 = QCheckBox('Segmento 3')
        self.check_segmento_3.setChecked(True)

        group_segmentos_layout.addWidget(self.check_segmento_1)
        group_segmentos_layout.addWidget(self.check_segmento_2)
        group_segmentos_layout.addWidget(self.check_segmento_3)

        group_segmentos.setLayout(group_segmentos_layout)
        # groupBox.setLayout(group_layout)

        self.btn_create = QPushButton('Generar')
        self.btn_create.clicked.connect(self.createMuestreoPoints)

        group_layout.addWidget(QLabel('Selecciona la Capa con los Lotes'))
        group_layout.addWidget(self.combo_layer)
        group_layout.addWidget(self.check_seleccionados)
        group_layout.addWidget(group_segmentos)
        group_layout.addWidget(self.btn_create)
        
        groupBox.setLayout(group_layout)
        main_layout.addWidget(groupBox)
        self.setLayout(main_layout)
        return


    def createMuestreoPoints(self):
        layer = self.combo_layer.currentLayer()
        segmentos = [1,2,3]
        selected = []
        
        if self.check_segmento_1.isChecked():
             selected.append(1)
        if self.check_segmento_2.isChecked():
             selected.append(2)
        if self.check_segmento_3.isChecked():
             selected.append(3)

        if self.check_seleccionados.isChecked():
            ids  = [f['iddata'] for f in  list(layer.getSelectedFeatures())]
        else:
            ids = [f['iddata'] for f in  list(layer.getFeatures())]

        # print(selected,segmentos,segmentos_remuestreo)
        
        for x in selected:
            segmentos.remove(x)
        if len(selected) == 3:
            segmentos = [0]
        
        
        # # print(ids)
        segmento_derivar = segmentos
        segmento_remuestreo = selected
        # segmentos_derivar = ','.join([str(x) for x in segmentos])
        # segmentos_remuestreo = ','.join([str(x) for x in selected])
        # print(segmentos_remuestreo,'---',segmentos_derivar)
        
        
        reply = QMessageBox.question(self,'aGrae Toolbox','Quieres generar los puntos de muestreo para:\n{} Lotes?'.format(len(ids)),QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:

            self.tools.crearPuntosMuestreo(ids,segmento_remuestreo,segmento_derivar)
            #! TRABAJAR EN MULTITHREADING NO ESTA FUNCIONANDO CORRECTAMENTE
            #! self.worker = WorkerGenerarPuntosMuestreo(ids,segmentos)
            #! self.worker.start()





