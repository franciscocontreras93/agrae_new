import os
import csv
import traceback

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
from qgis.PyQt.QtCore import pyqtSignal, QSettings, QVariant, Qt, QSize,QThreadPool,QDate,QObject,QRunnable

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



class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int) # Signal with current and total
    current_lote = pyqtSignal(str)

class GenerateAmbientesWorker(QRunnable):
    
    def __init__(self, features,bands:list,since:str,until:str):
        from ..tools.geeCore import aGraeGEECore
        super().__init__()
        self.core = aGraeGEECore()
        self.bands = bands
        self.since = since
        self.until = until
        self.features = features
        self.total_features = len(self.features)
        self.signals = WorkerSignals()

        

    def run(self):
        current = 0
        try:
            for i, feature in enumerate(self.features):
                current += 1
                progress_percentage = int((i + 1) / self.total_features * 100) #Calculate percentage
                self.signals.current_lote.emit('{} {}/{} '.format(feature['lote'], current,self.total_features))
                self.core.runGEECore(feature,bands=self.bands,since=self.since,until=self.until,buffer=10)
                self.signals.progress.emit(progress_percentage) # Emit percentage
                # time.sleep(0.5)
        except Exception as e:
            self.signals.error.emit((type(e), e, traceback.format_exc()))
        finally:
            self.signals.finished.emit()

    

class aGraeGEEDialog(QDialog):
    
    def __init__(self):
        super().__init__()
        self.UIComponents()
        self.resize(400,200)

        self.setWindowTitle('aGrae | Google-Earth-Engine API')
        self.tools = aGraeTools()
        self.threadpool = QThreadPool()

        self.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint) #Added Qt.WindowMinimizeButtonHint
        self.setModal(False) #Crucial change: Set modal to False

    def getLayer(self, layer: QgsVectorLayer):
        if self.check_layer.isChecked():
            features = list(layer.getSelectedFeatures())
        else:
            features = list(layer.getFeatures())

        new_layer = QgsVectorLayer('MULTIPOLYGON?crs=EPSG:4326', 'new_layer', 'memory')
        provider = new_layer.dataProvider()
        provider.addAttributes(layer.fields())  # Add attributes
        new_layer.updateFields()

        new_features = []
        for feature in features:
            new_feature = QgsFeature()
            new_feature.setGeometry(feature.geometry())
            new_feature.setAttributes(feature.attributes())  
            new_features.append(new_feature)

        provider.addFeatures(new_features)  
        new_layer.updateExtents()  

        return new_layer

    
    def UIComponents(self):
        self.layout = QVBoxLayout()

        self.tabWidget = QTabWidget()
        self.tabWidget.setStyleSheet("QTabWidget::pane { padding: 10px; }")

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setRange(0, 100)
        self.progress_label = QLabel()



        ambientesWidget = QWidget()
        ambienteLayout = QVBoxLayout()

        layerGroupLayout = QVBoxLayout()
        self.layerGroup = QGroupBox()
        self.layerGroup.setTitle('Selecciona la Capa que contiene el Lote.')
        self.layer = QgsMapLayerComboBox()
        self.check_layer = QCheckBox('Solo los Lotes Seleccionados.')
        self.check_layer.setChecked(True)
        layerGroupLayout.addWidget(self.layer)
        layerGroupLayout.addWidget(self.check_layer)
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
        self.advanceParametersGroup.setTitle('Configurar Parametros de Avanzados')
        self.advanceParametersGroup.collapsedStateChanged.connect(self.showWarning)
        
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
        self.layout.addWidget(self.progress_label)


        self.setLayout(self.layout)


    def execute(self,feature):
        
        
        # layer = self.getLayer(self.layer.currentLayer())

        # year = self.year.value()
        # period = self.period.value()
        # clouds = self.cloud.value()

        # radius = self.kernel_radius.value()
        # units = self.kernel_units.currentData()
        # magnitude = self.kernel_magnitude.value()

        self.core.run(feature)

        # core = aGraeNDVIMulti(
        #     layer=layer,
        #     feature=feature,
        #     crs=layer.crs(),
        #     year = year,
        #     period = period,
        #     max_clouds= clouds,
        #     buffer_radius=self.buffer.value(),
        #     kernel_radius= radius,
        #     kernel_units= units,
        #     kernel_magnitude=magnitude
        #     )
        
        # core.run()

    def generateAmbientes(self):
        # self.tools.messages('aGrae GEE', 'Generando Mapas de Ambientes, este proceso puede tardar varios minutos.\nPorfavor espere un momento.', alert=True)

        self.features = list(self.getLayer(self.layer.currentLayer()).getFeatures())
        self.progress_bar.setValue(0)

        since = QDate().currentDate().toString('yyyy-MM-dd')
        until = QDate().currentDate().addYears(-5).toString('yyyy-MM-dd')

        # print(since,until)

        worker = GenerateAmbientesWorker(self.features,bands=['B8','B4'],since=since,until=until)
        worker.signals.finished.connect(self.worker_finished)
        worker.signals.error.connect(self.worker_error)
        worker.signals.progress.connect(self.update_progress) # Connect progress signal
        worker.signals.current_lote.connect(self.update_label)
        self.threadpool.start(worker)



        # for feature in self.features:
        #     worker = ProcessLoteWorker(self.core, feature, self.total_features)
        #     worker.signals.finished.connect(self.worker_finished)
        #     worker.signals.error.connect(self.worker_error)
        #     worker.signals.progress.connect(self.update_progress) # Connect progress signal
        #     self.threadpool.start(worker)
            # print(feature.fields())

    def generateCoberteras(self):
        pass

    def worker_finished(self):
        self.progress_label.setText(f'Mapas de Ambientes Generados Correctamente')

    def worker_error(self, error):
        self.tools.messages('aGrae GEE', f'Error al procesar lote: {error}', 2, alert=True)

    def update_progress(self, current):
        self.progress_bar.setValue(current) # Update with the emitted value

    def update_label(self, text:str):
        self.progress_label.setText(f'Procesando Lote: {text.upper()}')


    def showWarning(self, collapsed):
        if not collapsed:  # Only show warning when expanding
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Warning)
            msgBox.setWindowTitle("Advertencia")
            msgBox.setText("Los parámetros están ajustados de forma predeterminada.")
            msgBox.setInformativeText(
                "Cualquier cambio puede alterar la calidad de los resultados. ¿Desea continuar?"
            )
            msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            msgBox.setDefaultButton(QMessageBox.Ok)
            ret = msgBox.exec_()

            if ret == QMessageBox.Cancel:
                self.advanceParametersGroup.setCollapsed(True) # Collapse if cancelled
        


    

        


class TotalFeatures(QObject):
    def __init__(self, total):
        super().__init__()
        self.total = total
        self.value = 0

    def increment(self):
        self.value += 1
