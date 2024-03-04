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

        self.UIComponents()

    def UIComponents(self):
        pass


