import os
import csv
# import ee

import time

import datetime


# from datetime import date
from psycopg2 import InterfaceError, errors, extras

from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtWidgets import (
    QDialog,
    QSpinBox,
    QGridLayout,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QGroupBox,
    QLabel,
    QPlainTextEdit,
    QComboBox,
    QMessageBox,
    QTabWidget,
    QWidget
 
    
    )
from qgis.PyQt.QtCore import pyqtSignal, QSettings, QVariant, Qt, QSize
from qgis.core import *
from qgis.gui import * 
from qgis.utils import iface
from qgis.PyQt.QtXml import QDomDocument
from qgis.PyQt import uic

from ..gui import agraeGUI
from ..tools import aGraeTools


from ..gui.CustomLineEdit import CustomLineEdit
from ..gui.CustomLineSearch import CustomLineSearch
from ..gui.CustomTable import CustomTable
from ..gui.CustomPushButton import CustomPushButton






class aGraeGEEDialog(QDialog):
    
    def __init__(self):
        super().__init__()
        # self.core = aGraeGEE()
        # self.core.test()
        self.UIComponents()

        self.resize(400,400)

        self.setWindowTitle('aGrae Google-Earth-Engine')
        # ee.Authenticate(auth_mode='localhost')

    def UIComponents(self):
        self.layout = QVBoxLayout()

        layerGroupLayout = QVBoxLayout()
        self.layerGroup = QGroupBox()
        self.layerGroup.setTitle('Selecciona la Capa que contiene el Lote.')
        self.layer = QgsMapLayerComboBox()
        layerGroupLayout.addWidget(self.layer)
        self.layerGroup.setLayout(layerGroupLayout)

        sceneGroupLayout = QGridLayout()
        self.sceneParametersGroup = QGroupBox()
        self.sceneParametersGroup.setTitle('Configurar Parametros de Escena')

        label_year = QLabel('Año')
        self.year = QSpinBox()
        self.year.setMinimum(1900)
        self.year.setMaximum(datetime.datetime.today().year)
        self.year.setValue(datetime.datetime.today().year)

        label_period = QLabel('Periodo')
        self.period = QSpinBox()
        self.period.setMinimum(1)
        self.period.setMaximum(20)
        self.period.setValue(5)

        label_cloud = QLabel('Nubosidad')
        self.cloud = QSpinBox()
        self.cloud.setMinimum(0)
        self.cloud.setMaximum(40)
        self.cloud.setValue(5)


        
        
        sceneGroupLayout.addWidget(label_year,0,0)
        sceneGroupLayout.addWidget(self.year,1,0)
        
        sceneGroupLayout.addWidget(label_period,0,1)
        sceneGroupLayout.addWidget(self.period,1,1)

        sceneGroupLayout.addWidget(label_cloud,0,2)
        sceneGroupLayout.addWidget(self.cloud,1,2)

        self.sceneParametersGroup.setLayout(sceneGroupLayout)

        advanceGroupLayout = QGridLayout()
        self.advanceParametersGroup = QGroupBox()
        self.advanceParametersGroup.setTitle('Configurar Parametros de Kernel')

        label_radius = QLabel('Radio del Kernel')
        self.kernel_radius = QSpinBox()
        self.kernel_radius.setMinimum(5)
        self.kernel_radius.setMaximum(40)
        self.kernel_radius.setValue(20)

        label_units = QLabel('Unidades del Kernel')
        self.kernel_units = QComboBox()
        self.kernel_units.addItem('Pixel',1)
        self.kernel_units.addItem('Metros',2)

        self.kernel_units.setCurrentIndex(0)


        label_magnitude = QLabel('Magnitud del Kernel')
        self.kernel_magnitude = QSpinBox()
        self.kernel_magnitude.setMinimum(1)
        self.kernel_magnitude.setMaximum(5)
        self.kernel_magnitude.setValue(1)

        
        advanceGroupLayout.addWidget(label_radius,0,0)
        advanceGroupLayout.addWidget(self.kernel_radius,1,0)
        advanceGroupLayout.addWidget(label_units,0,1)
        advanceGroupLayout.addWidget(self.kernel_units,1,1)
        advanceGroupLayout.addWidget(label_magnitude,0,2)
        advanceGroupLayout.addWidget(self.kernel_magnitude,1,2)




        self.advanceParametersGroup.setLayout(advanceGroupLayout)
        self.btn_run = QPushButton('Ejecutar')
        self.btn_run.clicked.connect(self.execute)
        





        self.layout.addWidget(self.layerGroup)
        self.layout.addWidget(self.sceneParametersGroup)
        self.layout.addWidget(self.advanceParametersGroup)
        self.layout.addWidget(self.btn_run)


        self.setLayout(self.layout)


    def execute(self):
        from ..tools.geeCore import aGraeNDVI
        
        layer = self.layer.currentLayer()
        year = self.year.value()
        period = self.period.value()
        clouds = self.cloud.value()

        radius = self.kernel_radius.value()
        units = self.kernel_units.currentData()
        magnitude = self.kernel_magnitude.value()

        core = aGraeNDVI(
            layer=layer,
            year = year,
            period = period,
            min_cloud= clouds,
            kernel_radius= radius,
            kernel_units= units,
            kernel_magnitude=magnitude
            )
        
        core.run()

        


