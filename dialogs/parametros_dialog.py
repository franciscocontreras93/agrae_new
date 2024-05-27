import os



# from datetime import date
import psycopg2
# from PyQt5.QtCore import QRegExp, QDate, QDateTime, QThreadPool
from PyQt5.QtGui import QRegExpValidator, QIcon, QPixmap,QColor
from PyQt5.QtWidgets import *
from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal, QSettings, QVariant,QSize

from ..gui import agraeGUI
from ..tools import aGraeTools
from ..sql import aGraeSQLTools



dialog, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'ui/parametros_dialog.ui'))


class GestionarParametrosDialog(QDialog,dialog):
    def __init__(self, parent = None):
        super(GestionarParametrosDialog,self).__init__(parent)

        self.tools = aGraeTools()

        self.dataSuelo = {
             1 : 'ARENOSO',
             2 : 'FRANCO',
             3 : 'ARCILLOSO'
        }

        self.dataMetodos = {
             1 : '1) OLSEN' ,
             2 : '2) MEHLICH-III'
        }
        
        self.dataRegimen = {
            1 : 'REGADIO',
            2 : 'SEMIREGADIO',
            3 : 'SECANO'
        }

        
        



        self.editStatus = False
        self.initialRowCount = 0
        self.removeIds = []
        self.removeRows = []
        self.levelCount = []


        self.setupUi(self)
        self.UIComponents()

        self.tables =  {
            0 : self.n_table,
            1 : self.p_table,
            2 : self.k_table,
            3 : self.ce_table,
            4 : self.textura_table,
            5 : self.ph_table,
            6 : self.carbonatos_table,
            7 : self.caliza_table,
            8 : self.cic_table,
            9 : self.ca_table,
            10 : self.mg_table,
            11: self.na_table
        }
        

    def UIComponents(self):
        

        self.setWindowTitle('Gestión de parámetros analíticos')
        self.setWindowIcon(agraeGUI().getIcon('matraz'))
        

        self.tables = self.findChildren(QTableWidget)
        for table in self.tables:
            table.horizontalHeader().setStretchLastSection(True)
            # table.setColumnHidden(0,True)

        

        
        self.populateCombos(self.dataSuelo,[w for w in self.findChildren(QComboBox) if '_suelo' in w.objectName()])
        self.populateCombos(self.dataMetodos,[w for w in self.findChildren(QComboBox) if '_metodo' in w.objectName()])
        self.populateCombos(self.dataRegimen,[w for w in self.findChildren(QComboBox) if '_regimen' in w.objectName()])

        self.setButtonActions(self.add_action,agraeGUI().getIcon('add'),lambda :self.addRowAction(self.tabWidget.currentIndex()))
        self.setButtonActions(self.remove_action,agraeGUI().getIcon('minus'),lambda :self.removeRowAction(self.tabWidget.currentIndex()))
        self.setButtonActions(self.edit_action,agraeGUI().getIcon('edit'),lambda :self.removeRowAction(self.tabWidget.currentIndex()))

        # self.add_action.setIcon(agraeGUI().getIcon('add'))
        # self.add_action.setIconSize(icon_size)




        for w in [w for w in self.findChildren(QComboBox)]:
            w.currentIndexChanged.connect(lambda : self.tabChanged(self.tabWidget.currentIndex()))
        
        self.tabWidget.currentChanged.connect(self.tabChanged)
        self.tabWidget.setCurrentIndex(0)

    def populateCombos(self,data:dict,widgets:list):
        for w in widgets:
            for i in range(len(data)):
                e = i + 1
                w.addItem(data[e],e)

    def setButtonActions(self,widget:QPushButton,icon:QIcon,action,tooltip:str='',enabled:bool=True,*args):
        icon_size = QSize(20, 20)
        widget.setIcon(icon)
        widget.setIconSize(icon_size)
        widget.setToolTip(tooltip)
        widget.setEnabled(enabled)

        widget.clicked.connect(lambda: action(*args))

    def editionMode(self,index):
        table = self.tables[index]
        if self.editStatus == False:
            table.setEditTriggers(QAbstractItemView.AllEditTriggers)
            # delegateCalcio = self.readOnlyColumn(self.tableWidget_7)
            # self.tableWidget_7.setItemDelegateForColumn(2, delegateCalcio)
            self.editStatus = True
            self.initialRowCount = table.rowCount()
            # b1.setEnabled(True)
            # b2.setEnabled(True)
            # b3.setEnabled(True)
        
        else:
            table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.editStatus = False
            self.initialRowCount = 0
            # b1.setEnabled(False)
            # b2.setEnabled(False)
            # b3.setEnabled(False)

    def addRowAction(self,index:int,c=None,v=None):
        # print('TEST ADD')
        table = self.tables[index]
        delegate = ColorDelegateGreen(table)
        table.insertRow(table.rowCount())
        rowCount = table.rowCount()
       
        table.setItem(rowCount-1,0, QTableWidgetItem(str(int(table.item(rowCount-2,0).text())+1)))
        # print(table.item(rowCount-2,0).text())
        self.initialRowCount = table.rowCount()
        self.levelCount = int(table.item(rowCount-2,0).text())+1
        if c != None and v != None:
            if table.item(rowCount-2, v) != None:
                table.setItem(rowCount-1,c, QTableWidgetItem(str(table.item(rowCount-2,v).text())))
            else: 
                pass
        rowCount = table.rowCount()-1
        table.setItemDelegateForRow(rowCount, delegate)


    def removeRowAction(self,index:int):
        queries = {
            0 : 'select * from analytic.nitrogeno order by id',
            1 : 'select id,tipo,limite_inferior , limite_superior , incremento from analytic.fosforo where metodo = {} and regimen = {} and suelo = {}  order by nivel  '.format(self.p_metodo.currentData(),self.p_regimen.currentData(),self.p_suelo.currentData()),
            2 : 'select id,tipo,limite_inferior , limite_superior , incremento from analytic.potasio where  regimen = {} and suelo = {}  order by nivel '.format(self.k_regimen.currentData(),self.k_suelo.currentData()),
            3 : 'select idce,tipo,limite_i , limite_s , influencia from analytic.conductividad_electrica ce order by idce ',
            4 : 'select * from analytic.textura t  ',
            5 : 'select * from analytic.ph order by id ',
            6 : 'select * from analytic.carbonatos order by id',
            7 : 'select * from analytic.caliza_activa order by id',
            8 : 'select * from analytic.cic order by id',
            9 : 'select id,tipo, limite_inferior , limite_superior , incremento  from analytic.calcio where suelo = {} order by id'.format(self.ca_suelo.currentData()),
            10 : 'select id,tipo, limite_inferior , limite_superior , incremento  from analytic.magnesio where suelo = {} order by id'.format(self.mg_suelo.currentData()),
            11 : 'DELETE FROM analytic.sodio WHERE id= '.format(self.na_suelo.currentData()),
        }
        table = self.tables[index]
        delegate = ColorDelegateRed(table)
        if table.rowCount() > 0:
            idx = table.selectionModel().selectedRows()
            if len(idx) == 1: 
                for r in sorted(idx):
                    id = int(table.item(r.row(),0).text())
                    row = r.row()
                    table.setItemDelegateForRow(row, delegate)
                    if id not in self.removeIds: 
                        self.removeIds.append(int(id))
                        self.removeRows.append(int(r.row()))
                    # table.removeRow(r.row())
                #     print(int(table.item(r.row(), 0).text()))

                print(self.removeIds)
                    

            else: 
                print('Debe seleccionar una fila')

        pass



    
    def tabChanged(self,i):
        queries = {
            0 : 'select * from analytic.nitrogeno order by id',
            1 : 'select id,tipo,limite_inferior , limite_superior , incremento from analytic.fosforo where metodo = {} and regimen = {} and suelo = {}  order by nivel  '.format(self.p_metodo.currentData(),self.p_regimen.currentData(),self.p_suelo.currentData()),
            2 : 'select id,tipo,limite_inferior , limite_superior , incremento from analytic.potasio where  regimen = {} and suelo = {}  order by nivel '.format(self.k_regimen.currentData(),self.k_suelo.currentData()),
            3 : 'select idce,tipo,limite_i , limite_s , influencia from analytic.conductividad_electrica ce order by idce ',
            4 : 'select * from analytic.textura t  ',
            5 : 'select * from analytic.ph order by id ',
            6 : 'select * from analytic.carbonatos order by id',
            7 : 'select * from analytic.caliza_activa order by id',
            8 : 'select * from analytic.cic order by id',
            9 : 'select id,tipo, limite_inferior , limite_superior , incremento  from analytic.calcio where suelo = {} order by id'.format(self.ca_suelo.currentData()),
            10 : 'select id,tipo, limite_inferior , limite_superior , incremento  from analytic.magnesio where suelo = {} order by id'.format(self.mg_suelo.currentData()),
            11 : 'select id,tipo, limite_inferior , limite_superior , incremento  from analytic.sodio where suelo = {} order by id'.format(self.na_suelo.currentData()),
        }

        widgets = {
            0 : self.n_table,
            1 : self.p_table,
            2 : self.k_table,
            3 : self.ce_table,
            4 : self.textura_table,
            5 : self.ph_table,
            6 : self.carbonatos_table,
            7 : self.caliza_table,
            8 : self.cic_table,
            9 : self.ca_table,
            10 : self.mg_table,
            11: self.na_table
        }

        # print(queries[i])
        if i == 1:
            if self.p_metodo.currentData() == 2:
                # print(self.p_metodo.currentData())
                queries[i]  =  '''select id,nivel,tipo,limite_inferior , limite_superior , incremento from analytic.fosforo where metodo = {} and regimen = {}  order by nivel;'''.format(self.p_metodo.currentData(),self.p_regimen.currentData())
                # print(queries[i])

        # print(queries)


        self.loadData(widgets[i],queries[i])
        self.removeIds = []
        self.removeRows = []
    

    def loadData(self,widget:QTableWidget,sql:str):
        self.editStatus = False
        try:
            self.tools.populateTable(sql, widget)
        except Exception as ex:
            print(ex)


            

        





class ColorDelegateRed(QStyledItemDelegate):

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.backgroundBrush = QColor("red")
class ColorDelegateGreen(QStyledItemDelegate):

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        
        option.backgroundBrush = QColor(170,240,170) 
class ReadOnlyDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        return
    

