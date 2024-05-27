import os



# from datetime import date
import psycopg2
from PyQt5.QtWidgets import *
from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal, QSettings

from ..gui import agraeGUI
from ..tools import aGraeTools



dialog, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'ui/config_dialog.ui'))

class agraeConfigDialog(QtWidgets.QDialog,dialog):
    closingPlugin = pyqtSignal()
    pathSignal = pyqtSignal(str)

    def __init__(self, parent = None):
        super(agraeConfigDialog,self).__init__(parent)
        self.tools = aGraeTools()
        self.settings = QSettings('agrae','dbConnection')

        self.setupUi(self)
        self.UIComponents()

        self.paths_params = {
            'paneles_path': None,
            'ufs_path': None,
            'reporte_path': None,
            'analisis_path': None,
            'amb_path': None,
        }

        self.db_params = {
            'dbhost' : None,
            'dbname' : None,
            'dbport' : None,
            'dbuser' : None,
            'dbpass' : None
        }

        self.paths_lines = {
            'paneles_path': self.panel_path,
            'ufs_path': self.uf_path,
            'reporte_path': self.reporte_path,
            'analisis_path': self.analisis_path,
            'amb_path': self.amb_path,
        }

        self.db_lines = {
            'dbhost' : self.dbhost,
            'dbname' : self.dbname,
            'dbport' : self.dbport,
            'dbuser' : self.dbuser,
            'dbpass' : self.dbpassword
        }

        self.readParams(self.paths_params,self.paths_lines)
        self.readParams(self.db_params,self.db_lines)

        


    def UIComponents(self):
        self.setWindowTitle('Ajustes aGrae GIS')
        self.setWindowIcon(agraeGUI().getIcon('settings'))
        self.dbpassword.setPasswordVisibility(False)
        self.save_conn_params.setEnabled(False)
        
        self.btn_1.clicked.connect(lambda: self.getDirectory('paneles_path','Seleccionar Directorio de Paneles'))
        self.btn_2.clicked.connect(lambda: self.getDirectory('ufs_path','Seleccionar Directorio de UFS'))
        self.btn_3.clicked.connect(lambda: self.getDirectory('reporte_path','Seleccionar Directorio de Reportes'))
        self.btn_4.clicked.connect(lambda: self.getDirectory('analisis_path','Seleccionar Directorio de Analisis'))
        self.btn_5.clicked.connect(lambda: self.getDirectory('amb_path','Seleccionar Directorio de Ambientes'))
        

        self.btn_save_paths.clicked.connect(lambda: self.save(self.paths_params,self.paths_lines))
        self.save_conn_params.clicked.connect(lambda: self.save(self.db_params,self.db_lines))
        self.test_btn.clicked.connect(self.testConnection)

    
    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def getDirectory(self,value:str,title:str='Seleccione un Directorio'):
        dirname = QFileDialog().getExistingDirectory(self,title)
        self.paths_lines[value].setText('{}'.format(dirname))
        self.paths_params[value] = dirname
    

    def save(self,params,lines):
        #validate
        for k in params:
            if not params[k] == lines[k].text() : 
                params[k] = lines[k].text()

        for k in params:
            self.settings.setValue(k,params[k])

        self.tools.messages('aGrae GIS','Conexion establecida correctamente.',3,alert=True)



    def readParams(self,settingsValues:dict,settingsLines:dict):
        for k in settingsValues:
            value = self.settings.value(k)
            settingsValues[k] = value
            settingsLines[k].setText(value)

    def testConnection(self):
        try:
            psycopg2.connect(
                database=self.db_lines['dbname'].text(), 
                user = self.db_lines['dbuser'].text(), 
                password = self.db_lines['dbpass'].text(), 
                host = self.db_lines['dbhost'].text(), 
                port = self.db_lines['dbport'].text())
            self.tools.messages('aGrae GIS','Conexion establecida.',3,alert=True)
            self.save_conn_params.setEnabled(True)

        except psycopg2.OperationalError:
            self.tools.messages('aGrae GIS','No es posible conectarse a la base de datos.\nVerifica los parametros de conexion.',1,alert=True)
