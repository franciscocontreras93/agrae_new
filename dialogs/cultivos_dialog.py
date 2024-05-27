import os



# from datetime import date
import psycopg2
# from PyQt5.QtCore import QRegExp, QDate, QDateTime, QThreadPool
from PyQt5.QtGui import QRegExpValidator, QIcon, QPixmap
from PyQt5.QtWidgets import *
from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal, QSettings, QVariant,QSize

from ..gui import agraeGUI
from ..tools import aGraeTools
from ..sql import aGraeSQLTools



dialog, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'ui/cultivo_dialog.ui'))


class GestionarCultivosDialog(QtWidgets.QDialog,dialog):
    def __init__(self, parent=None):
        super(GestionarCultivosDialog,self).__init__(parent)
        self.tools = aGraeTools()
        self.completer = self.tools.dataCompleter('select nombre from agrae.cultivo order by nombre')
        self.idCultivo = None
        self.UIWidgets = list()
        self.setupUi(self)
        self.UIComponents()
        self.getData()
        
    
    def UIComponents(self):
        
        self.setWindowTitle('Gestion de Cultivos')
        self.setWindowIcon(agraeGUI().getIcon('cultivo'))
        self.tabWidget.setCurrentIndex(0)
        self.tabWidget_2.setCurrentIndex(0)
        self.tabWidget.setTabIcon(0, agraeGUI().getIcon('search'))
        self.tabWidget.setTabIcon(1, agraeGUI().getIcon('pen-to-square'))

        self.ln_search.setCompleter(self.completer)
        self.ln_search.returnPressed.connect(self.getData)
        self.ln_search.textChanged.connect(self.getData)
        self.ln_search.setClearButtonEnabled(True)
        line_buscar_action = self.ln_search.addAction(
            agraeGUI().getIcon('search'), self.ln_search.TrailingPosition)
        line_buscar_action.triggered.connect(self.getData)

        self.ln_name.textChanged.connect(self.formatName)

        self.tableWidget.setColumnHidden(0, True)
        self.tableWidget.doubleClicked.connect(self.getCultivoData)

        self.btn_save.clicked.connect(self.saveCultivo)
        self.btn_save.setIconSize(QSize(20, 20))
        self.btn_save.setIcon(agraeGUI().getIcon('save'))

        self.btn_delete.clicked.connect(self.deleteCultivo)
        self.btn_delete.setIconSize(QSize(20, 20))
        self.btn_delete.setIcon(agraeGUI().getIcon('trash'))
        
        # UPDATE SPINS DECIMALS
        # COSECHA
        self.n_cos.valueChanged.connect(lambda v: self.updateDecimals(self.n_cos,v))
        self.p_cos.valueChanged.connect(lambda v: self.updateDecimals(self.p_cos,v))
        self.k_cos.valueChanged.connect(lambda v: self.updateDecimals(self.k_cos,v))
        self.c_cos.valueChanged.connect(lambda v: self.updateDecimals(self.c_cos,v))
        self.s_cos.valueChanged.connect(lambda v: self.updateDecimals(self.s_cos,v))
        self.ca_cos.valueChanged.connect(lambda v: self.updateDecimals(self.ca_cos,v))
        self.mg_cos.valueChanged.connect(lambda v: self.updateDecimals(self.mg_cos,v))
        self.b_cos.valueChanged.connect(lambda v: self.updateDecimals(self.b_cos,v))
        # RESIDUO
        self.n_res.valueChanged.connect(lambda v: self.updateDecimals(self.n_res,v))
        self.p_res.valueChanged.connect(lambda v: self.updateDecimals(self.p_res,v))
        self.k_res.valueChanged.connect(lambda v: self.updateDecimals(self.k_res,v))
        self.c_res.valueChanged.connect(lambda v: self.updateDecimals(self.c_res,v))
        self.s_res.valueChanged.connect(lambda v: self.updateDecimals(self.s_res,v))
        self.ca_res.valueChanged.connect(lambda v: self.updateDecimals(self.ca_res,v))
        self.mg_res.valueChanged.connect(lambda v: self.updateDecimals(self.mg_res,v))
        self.b_res.valueChanged.connect(lambda v: self.updateDecimals(self.b_res,v))

        self.UIWidgets = [
            self.ln_name,
            self.ic,
            self.ms_cos,
            self.ms_res,
            self.humedad,
            self.precio,
            self.n_cos,
            self.p_cos,
            self.k_cos,
            self.c_cos,
            self.s_cos,
            self.ca_cos,
            self.mg_cos,
            self.b_cos,
            self.n_res,
            self.p_res,
            self.k_res,
            self.c_res,
            self.s_res,
            self.ca_res,
            self.mg_res,
            self.b_res,
        ] 


    def updateDecimals(self,widget:QDoubleSpinBox,value:float):
        pos = widget.decimals()
        l = len(str(value).split('.')[1])
        if l == pos:
            widget.setDecimals(l+1)
        
    def getData(self):
        param = self.ln_search.text()
        query_empty = ''' select idcultivo, nombre from agrae.cultivo  order by nombre '''
        query_param = ''' select idcultivo, nombre from agrae.cultivo  where nombre ilike '%{}%' order by nombre '''.format(param)
        self.tools.searchGetData(self.ln_search,self.tableWidget,param,query_empty,query_param)
    
    def getCultivoData(self):
        row = self.tableWidget.currentRow()
        self.idCultivo = int(self.tableWidget.item(row,0).text())
        if self.idCultivo:
            with self.tools.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                try:
                    query = aGraeSQLTools().getSql('query_cultivos_data.sql').format(self.idCultivo)
                    cursor.execute(query)
                    data = cursor.fetchone()
                    for v in data:
                        data[v] = self.validate(data[v])
                    self.fillData(data)          
                except Exception as ex:
                    self.tools.messages('aGrae GIS','Ocurrio un Error: {}'.format(ex),2)

    def validate(self,value):
        if value != None:
            return value
        else:
            return 0
        
    def fillData(self,data:dict):
        self.ln_name.setText(data['nombre'])
        self.ic.setValue(data['ic'])
        self.ms_cos.setValue(data['ms_cos'])
        self.ms_res.setValue(data['ms_res'])
        self.humedad.setValue(int(data['humedad']))
        self.precio.setValue(data['precio'])

        self.n_cos.setValue(data['n_cos'])
        self.p_cos.setValue(data['p_cos'])
        self.k_cos.setValue(data['k_cos'])
        self.c_cos.setValue(data['c_cos'])
        self.s_cos.setValue(data['s_cos'])
        self.ca_cos.setValue(data['ca_cos'])
        self.mg_cos.setValue(data['mg_cos'])
        self.b_cos.setValue(data['b_cos'])

        self.n_res.setValue(data['n_res'])
        self.p_res.setValue(data['p_res'])
        self.k_res.setValue(data['k_res'])
        self.c_res.setValue(data['c_res'])
        self.s_res.setValue(data['s_res'])
        self.ca_res.setValue(data['ca_res'])
        self.mg_res.setValue(data['mg_res'])
        self.b_res.setValue(data['b_res'])

        self.tabWidget.setCurrentIndex(1)

    def saveCultivo(self):
        data = {
            'nombre' : str(self.ln_name.text()),
            'ic' : str(self.ic.value()),
            'ms_cos' : str(self.ms_cos.value()),
            'ms_res' : str(self.ms_res.value()),
            'humedad' : str(self.humedad.value()),
            'precio' : str(self.precio.value()),
            'n_cos' : str(self.n_cos.value()),
            'p_cos' : str(self.p_cos.value()),
            'k_cos' : str(self.k_cos.value()),
            'c_cos' : str(self.c_cos.value()),
            's_cos' : str(self.s_cos.value()),
            'ca_cos' : str(self.ca_cos.value()),
            'mg_cos' : str(self.mg_cos.value()),
            'b_cos' : str(self.b_cos.value()),
            'n_res' : str(self.n_res.value()),
            'p_res' : str(self.p_res.value()),
            'k_res' : str(self.k_res.value()),
            'c_res' : str(self.c_res.value()),
            's_res' : str(self.s_res.value()),
            'ca_res' : str(self.ca_res.value()),
            'mg_res' : str(self.mg_res.value()),
            'b_res' : str(self.b_res.value()),
        }

        query = aGraeSQLTools().getSql('query_cultivos_create.sql').format(**data)

        with self.tools.conn.cursor() as cursor:
            try:
                cursor.execute(query)
                self.tools.conn.commit()
                self.tools.messages('aGrae GIS','Se Guardo el Cultivo {}'.format(data['nombre']),3,alert=True)
            except Exception as ex:
                self.tools.conn.rollback()
                self.tools.messages('aGrae GIS','Ocurrio un Error:\n{}'.format(ex),2)
            
            finally:
                self.tabWidget.setCurrentIndex(0)
                self.getData()
                self.reset()
                self.idCultivo = None


    def deleteCultivo(self):
        row = self.tableWidget.currentRow()
        self.idCultivo = int(self.tableWidget.item(row,0).text())

        try:
            id = self.tableWidget.item(row,0).text()
            nombre = self.tableWidget.item(row,1).text()
                # print(id)
            sql = '''DELETE FROM agrae.cultivo
            WHERE idcultivo ={};
                '''.format(id)
            question = 'Quieres eliminar el Cultivo seleccionado {}?'.format(nombre)
            self.tools.deleteAction(question,sql)
            self.tools.messages('aGrae GIS','Se Elimino el Cultivo {}'.format(nombre),3,alert=True)
        except Exception as ex:
            self.tools.messages('aGrae GIS','Ocurrio un Error:\n{}'.format(ex),2)
        finally:
            self.getData()
            pass

    def formatName(self,v:str):
        self.ln_name.setText(v.upper())

    def reset(self):
        for e in self.UIWidgets:
            if isinstance(e, QDoubleSpinBox):
                e.setValue(0)
            elif isinstance( e, QLineEdit):
                e.clear()
