import os

# from datetime import date
from psycopg2 import errors,  Binary


from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtCore import pyqtSignal, QSize, QDate
from qgis.core import *
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
        self.layers_segmento.layerChanged.connect(self.updateSegmentosField)
        self.layers_ambiente.layerChanged.connect(self.updateAmbientesField)
        self.field_segmento.setFilters(QgsFieldProxyModel.Numeric)
        self.field_ambiente.setFilters(QgsFieldProxyModel.Numeric)
        self.field_ndvi.setFilters(QgsFieldProxyModel.Numeric)

        self.btn_create_segmentos.clicked.connect(self.loadSegmentos)
        self.btn_create_ambientes.clicked.connect(self.loadAmbientes)

        pass

    def updateSegmentosField(self,layer):
        self.field_segmento.setLayer(layer)


    def updateAmbientesField(self,layer):
        for w in [self.field_ambiente, self.field_ndvi]:
            w.setLayer(layer)
        pass

    def loadSegmentos(self):
        self.tools.crearSegmento(
            layer = self.layers_segmento.currentLayer(),
            field_segmento = self.field_segmento.currentField())
        pass
    def loadAmbientes(self):
        self.tools.crearAmbiente(layer = self.layers_ambiente.currentLayer(),
                                 field_ambiente = self.field_ambiente.currentField(),
                                 field_ndvi = self.field_ndvi.currentField())
        pass



