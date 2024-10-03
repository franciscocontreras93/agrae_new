import os



# from datetime import date
import psycopg2
# from PyQt5.QtCore import QRegExp, QDate, QDateTime, QThreadPool
from PyQt5.QtGui import QRegExpValidator, QIcon, QPixmap
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *
from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal, QSettings, QVariant,QSize

from ..gui import agraeGUI
from ..tools import aGraeTools
from ..sql import aGraeSQLTools



dialog, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'ui/asignar_cultivos_dialog.ui'))


class AsignarCultivosDialog(QtWidgets.QDialog,dialog):
    idCultivoSignal = pyqtSignal(int)

    def __init__(self,iddata:list, parent=None):
        """_summary_

        Args:
            iddata (list): Lista de iddata de los lotes seleccionados
            parent (_type_, optional): _description_. Defaults to None.
        """        
        super(AsignarCultivosDialog,self).__init__(parent)
        self.setupUi(self)

        self.tools = aGraeTools()
        
        self.iddata = iddata


        self.UIComponents()

    def  UIComponents(self):
        self.setWindowTitle('aGrae Tools | Asignar Cultivos a los Lotes Seleccionados')
        self.combo_cultivo.setEditable(True)
        self.combo_cultivo.setInsertPolicy(QtWidgets.QComboBox.NoInsert)
        self.combo_cultivo.completer().setCompletionMode(QtWidgets.QCompleter.PopupCompletion)
        self.getCultivosData()
        self.getRegimenData()

        self.pushButton.clicked.connect(self.asignarCultivos)


        pass

    def getCultivosData(self):
        with self.tools.conn.cursor() as cursor:
            try:
                cursor.execute('SELECT DISTINCT UPPER(nombre), idcultivo  FROM agrae.cultivo ORDER BY UPPER(nombre)')
                data_exp = cursor.fetchall() 
                self.tools.conn.commit()
                for e in data_exp: 
                    self.combo_cultivo.addItem(e[0],e[1])
            except Exception as ex:
                self.tools.conn.rollback()
                print(ex)

    def getRegimenData(self):
        with self.tools.conn.cursor() as cursor:
            try:
                cursor.execute('SELECT DISTINCT UPPER(nombre), id  FROM analytic.regimen ORDER BY id')
                data_reg = cursor.fetchall()
                self.tools.conn.commit()
                for e in data_reg:
                    self.combo_regimen.addItem(e[0],e[1])
            except Exception as ex:
                self.tools.conn.rollback()
                print(ex)

    
    def asignarCultivos(self):
        idcultivo = self.combo_cultivo.currentData()
        idregimen = self.combo_regimen.currentData() 
        prod_esperada = self.ln_prod.value()
        lotes = self.iddata
        if self.combo_cultivo.currentData() != None and self.combo_regimen.currentData() != None:
            reply = QtWidgets.QMessageBox.question(self,'aGrae Toolbox','Quieres Asignar el cultivo {} a los ({}) lotes Seleccionados?'.format(self.combo_cultivo.currentText(),len(self.iddata)),QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
            if reply == QtWidgets.QMessageBox.Yes:
                self.tools.asignarMultiplesCultivos(idcultivo,idregimen,prod_esperada,lotes)




    