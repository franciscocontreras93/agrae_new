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

from ..gui.components import CampaniasComboBox, ExplotacionesComboBox

agraeDatosBaseDialog , _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'ui/datos_base_dialog.ui'))
class GestionDatosBaseDialog(QDialog,agraeDatosBaseDialog): 
    closingPlugin = pyqtSignal()
    def __init__(self, parent=None) -> None:
        super(GestionDatosBaseDialog,self).__init__(parent)
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'ui/datos_base_dialog.ui'), self)
        self.setWindowTitle('Gestionar Capas Base')

        self.tools = aGraeTools()

        self.UIComponents()
        # self.updateSegmentosField(self.layers_segmento.currentLayer())
        # self.updateAmbientesField(self.layers_ambiente.currentLayer())


    def UIComponents(self):
        

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
            field_segmento = 'SEGM',
            field_ceap='ceap')
        pass
    def loadAmbientes(self):
        self.tools.crearAmbiente(layer = self.layers_ambiente.currentLayer(),
                                 field_ambiente = 'ambiente',
                                 field_ndvi = 'NDVImax')
        pass

    def loadCE(self):
         self.tools.crearCE(layer = self.layers_ce.currentLayer(),
                                 field_ce36= 'ce36',
                                 field_ce90 = 'ce90')


class CrearLotesDialog(QDialog):
    closingPlugin = pyqtSignal()
    # idExplotacionSignal = pyqtSignal(list)
    def __init__(self):
        super().__init__()
        self.setWindowTitle('aGrae | Cargar Lotes desde Capa')
        self.agraeSql = aGraeSQLTools()
        self.tools = aGraeTools()

        self.conn = agraeDataBaseDriver().connection()

        self.UIComponents()

       

        self.resize(500,200)
        self.setModal(False)

    def UIComponents(self):
        
        #TODO : mejorar el layout
        #TODO: eliminar todas las referencias a self.select_explotacion y su logica asociada
        
        self.layout = QGridLayout()
        
        self.groupBoxLayout = QGridLayout()
        self.groupBox = QGroupBox()
        self.groupBox.setTitle('Cargar Lotes al Sistema aGre')
        
        self.label_1 = QLabel('Selecciona la Capa con los Lotes')
        self.combo_layer = QgsMapLayerComboBox()
        self.combo_layer.layerChanged.connect(self.updateCombo)

        self.select_seleccionados = QCheckBox('Lotes seleccionados')
        self.select_seleccionados.setChecked(True)
        
        self.label_2 = QLabel('Seleccionar Campo Nombre del Lote')
        self.label_2.setMaximumSize(QSize(250,15))
        
        self.combo_nombre = QgsFieldComboBox()
        self.combo_nombre.setFilters(QgsFieldProxyModel.String)
        self.combo_nombre.setLayer(self.combo_layer.currentLayer())

        # self.select_explotacion = QCheckBox('Añadir lotes a la Explotacion')
        # self.select_explotacion.stateChanged.connect(self.enableCombos)

    


        self.combo_campania = CampaniasComboBox()
        # self.combo_campania._auto_enable_on_load = False

        self.combo_explotacion = ExplotacionesComboBox()
        # self.combo_explotacion._auto_enable_on_load = True
        self.combo_explotacion.DEFAULT_FIRST_ITEM_TEXT = 'Seleccionar Explotacion...'
        self.combo_explotacion.allow_first_item_text = True
    

        self.btn_cargar = QPushButton('Cargar Lotes')
        self.btn_cargar.clicked.connect(self.loadLotes)
        
        
        
        self.groupBoxLayout.addWidget(QLabel('Selecciona la Capa con los Lotes'),0,0,1,0)
        self.groupBoxLayout.addWidget(self.combo_layer,1,0,1,0)
        self.groupBoxLayout.addWidget(QLabel('Seleccionar Campo Nombre del Lote'),2,0,1,0)
        self.groupBoxLayout.addWidget(self.combo_nombre,3,0,1,0)
        self.groupBoxLayout.addWidget(self.select_seleccionados,4,0,1,0)
        # self.groupBoxLayout.addWidget(self.select_explotacion,5,0,1,0)
        self.groupBoxLayout.addWidget(QLabel('Seleccionar Campaña'),6,0,1,0)
        self.groupBoxLayout.addWidget(QLabel('Seleccionar Explotacion'),6,1,1,0)
        self.groupBoxLayout.addWidget(self.combo_campania,7,0)
        self.groupBoxLayout.addWidget(self.combo_explotacion,7,1)
        self.groupBoxLayout.addWidget(self.btn_cargar,8,0,1,0)



        self.groupBox.setLayout(self.groupBoxLayout)
        self.layout.addWidget(self.groupBox)
        self.setLayout(self.layout)

        pass

    def updateCombo(self,layer):
        self.combo_nombre.setLayer(layer)


    def loadLotes(self):
        # print('hey!')

        nombre = self.combo_explotacion.get_current_explotacion_name()
        if self.combo_explotacion.get_current_explotacion_id() is None:
            return self.tools.messages('Error','Debes seleccionar una Explotacion para asignar los lotes.',1,alert=True)
        
        reply = QMessageBox.question(None,'aGrae Toolbox','¿Estás seguro de cargar los lotes seleccionados a la explotacion {}?'.format(nombre.upper()), QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            
            layer = self.combo_layer.currentLayer()
            sourceCrs = layer.crs()
            crsBase = QgsCoordinateReferenceSystem(4326)
            tr = QgsCoordinateTransform(sourceCrs, crsBase, QgsProject.instance())
        
            selected_only = self.select_seleccionados.isChecked()
            features = list(layer.getSelectedFeatures() if selected_only else layer.getFeatures())

            if selected_only and not features:
                self.tools.messages('Advertencia', 'No hay lotes seleccionados.', 1, alert=True)
                return
            
            sql = self.agraeSql.getSql('new_lote_assign_copy.sql')
        
            # se quita la posibilidad de cargar un lote sin asignarlo a una explotacion. 
            # if self.select_explotacion.isChecked():
            #     sql = self.agraeSql.getSql('new_lote_assign_copy.sql')
            # # else:
            #     sql = self.agraeSql.getSql('create_lote.sql')
            
            with self.conn.cursor() as cursor:
                for f in features: 
                    nombre = str(f[self.combo_nombre.currentField()])
                    for e in ['/','-']:
                        nombre.replace(e,'_')
                        
                    geom = f.geometry()
                    if sourceCrs != crsBase:
                        geom.transform(tr)

                    query = sql.format(nombre,geom.asWkt(),self.combo_campania.get_current_campaign_id(),self.combo_explotacion.get_current_explotacion_id())

                    # if self.select_explotacion.isChecked():
                    #     query = sql.format(nombre,geom.asWkt(),self.combo_campania.get_current_campaign_id(),self.combo_explotacion.get_current_explotacion_id())
                    # else:
                    #     query = sql.format(nombre,geom.asWkt())
                    
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
