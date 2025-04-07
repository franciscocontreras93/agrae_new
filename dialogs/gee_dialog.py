import os
import csv
# import ee

import time

import datetime


# from datetime import date
from psycopg2 import InterfaceError, errors, extras

from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QProgressBar
    )
from qgis.PyQt.QtCore import pyqtSignal, QSettings, QVariant, Qt, QSize,QThreadPool,QDate

from qgis.core import *
from qgis.gui import * 
from qgis.utils import iface


from ..gui import agraeGUI
from ..tools import aGraeTools
from ..tools.worker import Worker

from ..gui.CustomLineEdit import CustomLineEdit
from ..gui.CustomLineSearch import CustomLineSearch
from ..gui.CustomTable import CustomTable
from ..gui.CustomPushButton import CustomPushButton

import threading

class aGraeGEEDialog(QDialog):
    
    def __init__(self):
        super().__init__()
        # self.core = aGraeGEE()
        # self.core.test()
        self.UIComponents()
        # self.idexplotacion = idexplotacion
        self.resize(400,200)

        self.setWindowTitle('aGrae Google-Earth-Engine')
        # ee.Authenticate(auth_mode='localhost')

        # self.idexplotacion = idexplotacion
        # self.layer = self.getLayer(layer)

        self.tools = aGraeTools()
        self.threadpool = QThreadPool()

    def getLayer(self,layer:QgsVectorLayer):
        # if len(list(layer.getSelectedFeatures())) > 0:

        #     features = list(layer.getSelectedFeatures())
        # else:
        features = list(layer.getFeatures())
            
        new_layer  = QgsVectorLayer('MULTIPOLYGON?crs=EPSG:4326','new_layer','memory')
        new_layer.dataProvider().addFeatures(features)
        return new_layer

    
    def UIComponents(self):
        self.layout = QVBoxLayout()

        self.tabWidget = QTabWidget()
        self.tabWidget.setStyleSheet("QTabWidget::pane { padding: 10px; }")

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        ambientesWidget = QWidget()
        ambienteLayout = QVBoxLayout()

        layerGroupLayout = QVBoxLayout()
        self.layerGroup = QGroupBox()
        self.layerGroup.setTitle('Selecciona la Capa que contiene el Lote.')
        self.layer = QgsMapLayerComboBox()
        layerGroupLayout.addWidget(self.layer)
        self.layerGroup.setLayout(layerGroupLayout)

        #TAB AMBIENTES

        sceneAmbientesGroupLayout = QGridLayout()
        self.sceneAmbientesParametersGroup = QGroupBox()
        self.sceneAmbientesParametersGroup.setTitle('Configurar Parametros de Escena')

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


        self.btn_generate_ambientes = QPushButton('Generar Ambientes')
        self.btn_generate_ambientes.clicked.connect(self.generateAmbientes)

        sceneAmbientesGroupLayout.addWidget(label_year,0,0)
        sceneAmbientesGroupLayout.addWidget(self.year,1,0)
        sceneAmbientesGroupLayout.addWidget(label_period,0,1)
        sceneAmbientesGroupLayout.addWidget(self.period,1,1)
        sceneAmbientesGroupLayout.addWidget(label_cloud,0,2)
        sceneAmbientesGroupLayout.addWidget(self.cloud,1,2)
        sceneAmbientesGroupLayout.addWidget(self.btn_generate_ambientes,2,0,1,3)
        self.sceneAmbientesParametersGroup.setLayout(sceneAmbientesGroupLayout)

        # TAB COBERTERAS

        sceneCoberteraGroupLayout = QGridLayout()
        self.sceneCoberteraParametersGroup = QGroupBox()
        self.sceneCoberteraParametersGroup.setTitle('Configurar Parametros de Escena')


        self.hasta = QDateEdit()
        self.hasta.setCalendarPopup(True)
        self.hasta.setDisplayFormat('dd/MM/yyyy')
        self.hasta.setDate(QDate.currentDate())
        self.hasta.setMaximumDate(QDate.currentDate())
        

        self.desde = QDateEdit()
        self.desde.setCalendarPopup(True)
        self.desde.setDisplayFormat('dd/MM/yyyy')
        self.desde.setDate(self.hasta.date().addMonths(-1))
        self.desde.setMaximumDate(QDate.currentDate())

        self.nubes_cobertera = QSpinBox()
        self.nubes_cobertera.setMinimum(0)
        self.nubes_cobertera.setMaximum(40)
        self.nubes_cobertera.setValue(5)

        self.btn_generate_coberteras = QPushButton('Generar Coberteras')
        self.btn_generate_coberteras.clicked.connect(self.generateCoberteras)

        sceneCoberteraGroupLayout.addWidget(QLabel('Desde'),0,0)
        sceneCoberteraGroupLayout.addWidget(self.desde,1,0)
        sceneCoberteraGroupLayout.addWidget(QLabel('Hasta'),0,1)
        sceneCoberteraGroupLayout.addWidget(self.hasta,1,1)
        sceneCoberteraGroupLayout.addWidget(QLabel('Nubosidad'),0,2)
        sceneCoberteraGroupLayout.addWidget(self.nubes_cobertera,1,2)
        sceneCoberteraGroupLayout.addWidget(self.btn_generate_coberteras,2,0,1,3)
        
        self.sceneCoberteraParametersGroup.setLayout(sceneCoberteraGroupLayout)





        self.tabWidget.addTab(self.sceneAmbientesParametersGroup,'1) Generar Mapas de Ambientes')
        self.tabWidget.addTab(self.sceneCoberteraParametersGroup,'2) Generar Mapas de Coberteras')

        advanceGroupLayout = QGridLayout()
        self.advanceParametersGroup = QgsCollapsibleGroupBox()
        self.advanceParametersGroup.setCollapsed(True)
        self.advanceParametersGroup.setTitle('Configurar Parametros de Kernel')
        
        label_buffer = QLabel('Radio del Buffer')
        self.buffer = QSpinBox()
        self.buffer.setMinimum(0)
        self.buffer.setMaximum(20)
        self.buffer.setValue(10)

        label_radius = QLabel('Radio del Kernel')
        self.kernel_radius = QSpinBox()
        self.kernel_radius.setMinimum(5)
        self.kernel_radius.setMaximum(40)
        self.kernel_radius.setValue(5)

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

        
        advanceGroupLayout.addWidget(label_buffer,0,0)
        advanceGroupLayout.addWidget(self.buffer,1,0)
        advanceGroupLayout.addWidget(label_radius,0,1)
        advanceGroupLayout.addWidget(self.kernel_radius,1,1)
        advanceGroupLayout.addWidget(label_units,0,2)
        advanceGroupLayout.addWidget(self.kernel_units,1,2)
        advanceGroupLayout.addWidget(label_magnitude,0,3)
        advanceGroupLayout.addWidget(self.kernel_magnitude,1,3)




        self.advanceParametersGroup.setLayout(advanceGroupLayout)
        
        





        self.layout.addWidget(self.layerGroup)
        self.layout.addWidget(self.tabWidget)
        self.layout.addWidget(self.advanceParametersGroup)
        self.layout.addWidget(self.progress_bar)


        self.setLayout(self.layout)


    def execute(self):
        from ..tools.geeCore import aGraeNDVIMulti,aGraeNDRE
        
        layer = self.getLayer(self.layer.currentLayer())

        year = self.year.value()
        period = self.period.value()
        clouds = self.cloud.value()

        radius = self.kernel_radius.value()
        units = self.kernel_units.currentData()
        magnitude = self.kernel_magnitude.value()

        core = aGraeNDVIMulti(
            layer=layer,
            year = year,
            period = period,
            max_clouds= clouds,
            buffer_radius=self.buffer.value(),
            kernel_radius= radius,
            kernel_units= units,
            kernel_magnitude=magnitude
            )
        
        core.run()

    def generateAmbientes(self):
    
        self.tools.messages('aGrae GEE','Generando Mapas de Ambientes, este proceso puede tardar varios minutos.\nPorfavor espere un momento.',alert=True)
        # print('worker')
        worker = Worker(lambda: self.execute())
        # worker.signals.finished.connect(lambda: self.tools.UserMessages('Archivos generados correctamente',level=Qgis.Success))
        worker.signals.finished.connect(lambda: iface.messageBar().pushMessage("aGrae GIS", 'Archivos generados correctamente', level=Qgis.Success))
        self.threadpool.start(worker)

    def generateCoberteras(self):
        pass
        


    

        


