import os
import pandas as pd
import numpy as np

from qgis.PyQt import QtWidgets, uic
# from qgis.PyQt.QtXml import QDomDocument
from qgis.core import *
from ..gui import agraeGUI
from ..tools import aGraeTools

analiticaDialog, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'ui/analitica_dialog.ui'))

class agraeAnaliticaDialog(QtWidgets.QDialog,analiticaDialog):
    def __init__(self,data:pd.DataFrame,parent=None):
        super(agraeAnaliticaDialog,self).__init__(parent)
        self.setupUi(self)
        self.df = data
        self.tools = aGraeTools()
        self.UIComponents()
        self.loadData()

    def UIComponents(self):
        self.ImportarArchivoAnalisis = QtWidgets.QAction(agraeGUI().getIcon('upload'),'Guardar datos de Analitica',self)
        self.ImportarArchivoAnalisis.triggered.connect(self.guardarAnalitica)
        self.tools.settingsToolsButtons(self.toolButton,[self.ImportarArchivoAnalisis,self.ImportarArchivoAnalisis],icon=agraeGUI().getIcon('tools'),setMainIcon=True)

        pass

    def loadData(self):
        columns = [c for c in self.df.columns]
        # print(columns)
        data = [[row['COD'],row['ceap'],row['N'],row['P'],row['K'],row['PH'],row['CE'],row['CARBON'],row['CALIZA'],row['CA'],row['MG'],row['NA'],row['ORGANI']] for index,row in self.df.iterrows()]
        a = len(data)
        b = len(data[0])
        i = 1
        j = 1
    
        self.tableWidget.setRowCount(a)
        self.tableWidget.setColumnCount(b)
        for j in range(a):
            for i in range(b):
                item = QtWidgets.QTableWidgetItem(str(data[j][i]))
                self.tableWidget.setItem(j, i, item)
        pass

    def guardarAnalitica(self):
        self.tools.guardarReporteAnalitica(self.df)

