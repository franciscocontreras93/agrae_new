import os

# from datetime import date
from psycopg2 import errors,  Binary


from qgis.PyQt.QtWidgets import *
# from qgis.PyQt import QtWidgets
from qgis.PyQt.QtCore import pyqtSignal, QSize, QDate
from qgis.core import *
from qgis.gui import * 
from qgis.PyQt import uic

from ..gui import agraeGUI
from ..db import agraeDataBaseDriver
from ..sql import aGraeSQLTools
from ..tools import aGraeTools

agraeDatosBaseDialog , _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'ui/datos_base_dialog.ui'))
class GestionDatosBaseDialog(QDialog,agraeDatosBaseDialog): 
    closingPlugin = pyqtSignal()
    def __init__(self, parent=None) -> None:
        super(GestionDatosBaseDialog,self).__init__(parent)
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'ui/datos_base_dialog.ui'), self)
        self.setWindowTitle('Gestionar Capas Base')

        self.tools = aGraeTools()

        self.UIComponents()
        self.updateSegmentosField(self.layers_segmento.currentLayer())
        self.updateAmbientesField(self.layers_ambiente.currentLayer())
        # print(self.layers_segmento.currentLayer())

    def UIComponents(self):
        self.layers_ce.layerChanged.connect(self.updateCEFields)
        self.layers_segmento.layerChanged.connect(self.updateSegmentosField)
        self.layers_ambiente.layerChanged.connect(self.updateAmbientesField)
        # self.field_segmento.setFilters(QgsFieldProxyModel.Numeric)
        # self.field_ambiente.setFilters(QgsFieldProxyModel.Numeric)
        # self.field_ndvi.setFilters(QgsFieldProxyModel.Numeric)

        self.btn_create_ce.clicked.connect(self.loadCE)
        self.btn_create_segmentos.clicked.connect(self.loadSegmentos)
        self.btn_create_ambientes.clicked.connect(self.loadAmbientes)

        pass
    
    def updateCEFields(self,layer):
        for w in [self.field_ce36, self.field_ce90]:
            w.setLayer(layer)
        pass

    def updateSegmentosField(self,layer):
        self.field_segmento.setLayer(layer)
        self.field_ceap.setLayer(layer)


    def updateAmbientesField(self,layer):
        for w in [self.field_ambiente, self.field_ndvi]:
            w.setLayer(layer)
        pass

    

    def loadSegmentos(self):
        self.tools.crearSegmento(
            layer = self.layers_segmento.currentLayer(),
            field_segmento = self.field_segmento.currentField(),
            field_ceap=self.field_ceap.currentField())
        pass
    def loadAmbientes(self):
        self.tools.crearAmbiente(layer = self.layers_ambiente.currentLayer(),
                                 field_ambiente = self.field_ambiente.currentField(),
                                 field_ndvi = self.field_ndvi.currentField())
        pass

    def loadCE(self):
         self.tools.crearCE(layer = self.layers_ce.currentLayer(),
                                 field_ce36= self.field_ce36.currentField(),
                                 field_ce90 = self.field_ce36.currentField())


class CrearLotesDialog(QDialog):
    closingPlugin = pyqtSignal()
    # idExplotacionSignal = pyqtSignal(list)
    def __init__(self, idcampania:int=None,idexplotacion:int=None):
        super().__init__()
        self.setWindowTitle('aGrae | Cargar Lotes desde Capa')
        self.agraeSql = aGraeSQLTools()
        self.tools = aGraeTools()

        self.conn = agraeDataBaseDriver().connection()

        self.UIComponents()

        self.idcampania = idcampania
        self.idexplotacion = idexplotacion

        self.resize(300,200)
        self.setModal(False)

    def UIComponents(self):
        self.layout = QGridLayout()
        
        self.groupBoxLayout = QVBoxLayout()
        self.groupBox = QGroupBox()
        self.groupBox.setTitle('Cargar Lotes al Sistema aGre')
        
        self.label_1 = QLabel('Selecciona la Capa con los Lotes')
        self.combo_layer = QgsMapLayerComboBox()
        self.combo_layer.layerChanged.connect(self.updateCombo)

        self.select_seleccionados = QCheckBox('Lotes seleccionados')
        
        self.label_2 = QLabel('Seleccionar Campo Nombre del Lote')
        self.label_2.setMaximumSize(QSize(250,15))
        
        self.combo_nombre = QgsFieldComboBox()
        self.combo_nombre.setFilters(QgsFieldProxyModel.String)
        self.combo_nombre.setLayer(self.combo_layer.currentLayer())

        self.select_explotacion = QCheckBox('Añadir lotes a la Explotacion Actual')

        self.btn_cargar = QPushButton('Cargar Lotes')
        self.btn_cargar.clicked.connect(self.loadLotes)
        
        
        self.groupBoxLayout.addWidget(self.label_1)
        self.groupBoxLayout.addWidget(self.combo_layer)
        self.groupBoxLayout.addWidget(self.select_seleccionados)
        self.groupBoxLayout.addWidget(self.label_2)
        self.groupBoxLayout.addWidget(self.combo_nombre)
        self.groupBoxLayout.addWidget(self.select_explotacion)
        self.groupBoxLayout.addWidget(self.btn_cargar)



        self.groupBox.setLayout(self.groupBoxLayout)
        self.layout.addWidget(self.groupBox)
        self.setLayout(self.layout)

        pass
    def updateCombo(self,layer):
        self.combo_nombre.setLayer(layer)

    def loadLotes(self):
        layer = self.combo_layer.currentLayer()
        sourceCrs = layer.crs()
        crsBase = QgsCoordinateReferenceSystem(4326)
        tr = QgsCoordinateTransform(sourceCrs, crsBase, QgsProject.instance())
        if self.select_seleccionados.isChecked():
            features = [f for f in layer.getSelectedFeatures()]
        else: 
            features = [f for f in layer.getFeatures()]
        
        if self.select_explotacion.isChecked():
            sql = self.agraeSql.getSql('new_lote_assign_copy.sql')
        else:
            sql = self.agraeSql.getSql('create_lote.sql')
        
        with self.conn.cursor() as cursor:
            for f in features: 
                nombre = str(f[self.combo_nombre.currentField()])
                for e in ['/','-']:
                    nombre.replace(e,'_')
                    
                geom = f.geometry()
                if sourceCrs != crsBase:
                    geom.transform(tr)
                if self.select_explotacion.isChecked():
                    query = sql.format(nombre,geom.asWkt(),self.idcampania,self.idexplotacion)
                else:
                    query = sql.format(nombre,geom.asWkt())
                
                # print(query)

                try:
                    cursor.execute(query)
                    response = cursor.fetchone()

                    # print(response)
                    if len(response) > 0:
                        QgsMessageLog.logMessage('Lote: {} cargado correctamente as la Base de Datos'.format(response[0]), 'aGrae Logs', 3)
                        self.tools.messages('aGrae Toolbox','Lote: {} cargado correctamente as la Base de Datos'.format(response[0]),3)
                        self.conn.commit()
                    else: 
                        self.tools.messages('Lote: {} ya existe en la Base de Datos'.format(nombre),1)
                        QgsMessageLog.logMessage('Lote: {} ya existe en la Base de Datos'.format(nombre), 'aGrae Logs', 1)
                        self.conn.rollback()

                    # print(query)

                except Exception as ex:
                    print(ex)
                    self.conn.rollback()
            # print(query) 
        
    
    

