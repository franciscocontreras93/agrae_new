import os
import csv

import time


# from datetime import date
from psycopg2 import InterfaceError, errors, extras

from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtWidgets import (
    QAction,
    QDialog,
    QLayout,
    QGridLayout,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QGroupBox,
    QLabel,
    QToolButton,
    QPlainTextEdit,
    QComboBox,
    QMessageBox,
    QTabWidget,
    QTableView,
    QWidget,
    QCompleter,
    QFileDialog ,
    QMainWindow
    )
from qgis.PyQt.QtCore import pyqtSignal, QSettings, QVariant, Qt, QSize, QRegExp
from qgis.core import *
from qgis.gui import * 
from qgis.utils import iface
from qgis.PyQt.QtXml import QDomDocument
from qgis.PyQt import uic

from ..gui import agraeGUI
from ..db import agraeDataBaseDriver
from ..sql import aGraeSQLTools
from ..tools import aGraeTools

from ..gui.CustomLineEdit import CustomLineEdit
from ..gui.CustomLineSearch import CustomLineSearch
from ..gui.CustomTable import CustomTable
from ..gui.CustomTableView import (CustomTableView,CustomTableModel)
from ..gui.CustomPushButton import CustomPushButton


class GestionarMuestrasDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.tools = aGraeTools()
        self.UIComponents()
        # self.getCampaniasData()
        # self.getExplotacionData()
        
    
    def UIComponents(self):
        self.setWindowTitle('aGrae Tools | Gestion de Muestras y Analiticas')
        self.resize(400,300)
        self.combo_campania = QComboBox()
        self.combo_explotacion = QComboBox()
        self.combo_explotacionsetEditable(True)
        self.combo_explotacionsetInsertPolicy(QComboBox.NoInsert)
        self.getCampaniasData()
        data_muestreo = agraeDataBaseDriver().read(aGraeSQLTools().getSql('muestreo_data_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'select iddata,campania,explotacion,lote,codigo,prioridad,status_mues,status_lab from muestras'))
        self.table = CustomTable(
            columns=['iddata','Campaña','Explotacion','Lote','Codigo','Prioridad','Estado Muestreo','Estado Analitica'],
            data = data_muestreo
        )
        self.combo_campania.currentIndexChanged.connect(self.updateTable)
        self.combo_explotacion.currentIndexChanged.connect(self.updateTable)

        # for c in [self.combo_explotacion]:
        #     c.setEditable(True)
        #     c.setInsertPolicy(QComboBox.NoInsert)
            # change completion mode of the default completer from InlineCompletion to PopupCompletion
            # c.completer().setCompletionMode(QCompleter.PopupCompletion)
        
        self.toolButton = QToolButton()
        self.ExportarDataCSV = QAction(agraeGUI().getIcon('csv'),'Exportar informacion a CSV',self)
        self.ExportarDataCSV.triggered.connect(self.exportarDataCSV)
        self.CargarCapaMuestras = QAction(agraeGUI().getIcon('pois'),'Cargar Capa de Muestras',self)
        self.CargarCapaMuestras.triggered.connect(self.loadLayerMuestreo)
        self.tools.settingsToolsButtons(self.toolButton,[self.ExportarDataCSV,self.CargarCapaMuestras],agraeGUI().getIcon('tools'),setMainIcon=True)

        main_layout = QVBoxLayout()
        group_combos = QGroupBox()
        layout_group_combos = QGridLayout()
        layout_group_combos.addWidget(QLabel('Seleccionar Campaña'),0,0)
        layout_group_combos.addWidget(QLabel('Seleccionar Explotacion'),0,1)
        layout_group_combos.addWidget(self.combo_campania,1,0)
        layout_group_combos.addWidget(self.combo_explotacion,1,1)
        layout_group_combos.addWidget(self.toolButton,1,2)
        group_combos.setLayout(layout_group_combos)

        main_layout.addWidget(group_combos)
        main_layout.addWidget(self.table)


        self.setLayout(main_layout)

    def getCampaniasData(self):
        self.combo_campania.clear()
        with self.tools.conn.cursor() as cursor:
            # try:
                cursor.execute('''SELECT DISTINCT concat(upper(prefix),'-',UPPER(nombre)) as nombre , id  FROM campaign.campanias ORDER BY id desc''')
                data_camp = cursor.fetchall()
                for e in data_camp:
                    self.combo_campania.addItem(e[0],e[1])
                self.getExplotacionData(self.combo_campania.currentData())
    
    def getExplotacionData(self,idcampania):
        self.combo_explotacion.clear()
        sql = '''select distinct e.nombre , d.idexplotacion from campaign.data d
        join campaign.campanias c on c.id = d.idcampania 
        join agrae.explotacion e on e.idexplotacion = d.idexplotacion 
        where c.id = {}
        order by e.nombre'''.format(idcampania)
        # print(idcampania)
        if idcampania != None:
            with self.tools.conn.cursor() as cursor:
                try:
                    cursor.execute(sql)
                    data = cursor.fetchall()

                    if len(data) >= 1 and self.combo_campania.currentData() != None:
                        for e in data:
                            self.combo_explotacion.addItem('{}-{}'.format(e[1],e[0]),e[1])
                    
                    exp_completer = self.tools.dataCompleter(data_combo=['{}-{}'.format(e[1],e[0]) for e in data])
                    self.combo_explotacion.setCompleter(exp_completer)
                except Exception as ex:
                    print(ex,'Error getExpData')

    def updateTable(self):
        data_muestreo = agraeDataBaseDriver().read(aGraeSQLTools().getSql('muestreo_data_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'select iddata,campania,explotacion,lote,codigo,prioridad,status_mues,status_lab from muestras'))
        self.table.populate(data_muestreo)

    def exportarDataCSV(self):
        outputh_path = str(QFileDialog.getExistingDirectory(self, "Selecciona el Directorio."))
        output_query = '''copy ({}) to stdout  with csv header delimiter ';' ; '''.format(aGraeSQLTools().getSql('muestreo_data_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'select iddata,campania,explotacion,lote,codigo,prioridad,status_mues,status_lab from muestras'))
        with open(os.path.join(outputh_path,'REPORTE_MUESTREO_{}.csv'.format(self.combo_explotacion.currentText())),'w') as file:
            with self.tools.conn.cursor() as cur:
                cur.copy_expert(output_query,file)

    def loadLayerMuestreo(self):
        query = aGraeSQLTools().getSql('muestreo_data_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'select row_number() over () as id, * from muestras')
        muestras = self.tools.getDataBaseLayer(query,'{}-{}'.format(self.combo_campania.currentText(),self.combo_explotacion.currentText()),'muestreo_status',geometry='MultiPoint')
        QgsProject.instance().addMapLayer(muestras)
        iface.mapCanvas().setExtent(muestras.extent())
