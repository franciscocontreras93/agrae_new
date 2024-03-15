from PIL import Image
import os
from qgis.PyQt import uic
from qgis.PyQt.QtXml import QDomDocument

from qgis.core import *
from qgis.utils import iface

from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSignal, QSettings, QDateTime, QThreadPool
from PyQt5.QtGui import QFont

from ..tools import aGraeTools
from ..tools.composerTools import aGraeComposerTools

agraeComposerDialog, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'ui/composer_dialog.ui'))
class agraeComposer(QDialog,agraeComposerDialog):
    closingPlugin = pyqtSignal()
    def __init__(self,layers,idcampania,idexplotacion,parent=None) -> None:
        super(agraeComposer,self).__init__(parent)
        self.setupUi(self)
        self.layers = layers
        self.composerTools = aGraeComposerTools(self.layers,idcampania,idexplotacion)
        self.setWindowTitle('Generar Reporte de Preescripcion')
        

        # self.threadpool = QThreadPool()
        # self.atlas = None
        # self.settings = QSettings('agrae','dbConnection')
        # self.panels_path = self.settings.value('paneles_path')
        # self.reportes_path = self.settings.value('reporte_path')
        # self.tools = aGraeTools()
        # self.conn = self.tools.conn()
        # # self.tools = AgraeToolset()
        # self.excludedProviders = ['DB2', 'EE', 'OAPIF', 'WFS', 'arcgisfeatureserver', 'arcgismapserver', 'ept', 'gdal', 'grass', 'grassraster', 'hana', 'mdal', 'mesh_memory', 'mssql','oracle', 'postgresraster',  'virtualraster', 'wcs', 'wms']
        # self.clasificationMethods = [
        #     'Cuantil',
        #     'Escala Logaritmica',
        #     'Desviacion Standard',
        #     'Intervalo Igual',
        #     'Pretty Breaks',
        #     'Jenks']
        self.plugin_dir = os.path.dirname(__file__)
        # self.root = QgsProject.instance().layerTreeRoot()
        # self.groups = [ g for g in self.root.children() if isinstance(g, QgsLayerTreeGroup) ] 

        # # self.comboBox.addItems(lambda name: for x.name() in self.groups)

        

        # self.render = None
       

        
        self.UIComponents()
        # print(self.excludedLayers)
    def closeEvent(self,event):
        self.closingPlugin.emit()

        event.accept()
    def populateCombos(self):
    
        self.combo_basemap.clear()
        self.combo_basemap.addItems([k for k in self.composerTools.basemaps])

    def UIComponents(self):
        self.populateCombos()
        self.pushButton.clicked.connect(self.generateComposer)
        # self.pushButton.clicked.connect(lambda: self.layoutGenerator(preview=True))
        # self.pushButton_2.clicked.connect(self.ComposerPrintWorker)
    
    
    def generateComposer(self):
        self.composerTools.generateComposer(self.combo_basemap.currentText())
        self.close()
        
        pass
    






    
