import os
import csv

import time


# from datetime import date
from psycopg2 import InterfaceError, errors, extras


from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtWidgets import (
    QAction,
    QDialog,
    QGridLayout,
    QVBoxLayout,
    QGroupBox,
    QLabel,
    QToolButton,
    QComboBox,
    QMessageBox,
    QFileDialog ,
    QMenu
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
from ..tools.analisis_tools import aGraeResamplearMuestras

from ..gui.CustomLineEdit import CustomLineEdit
from ..gui.CustomLineSearch import CustomLineSearch
from ..gui.CustomTable import CustomTable
from ..gui.CustomTableView import (CustomTableView,CustomTableModel)
from ..gui.CustomPushButton import CustomPushButton

from .analitica_dialogs import agraeAnaliticaDialog


class GestionLaboratorioDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.tools = aGraeTools()
        self.UIComponents()
        # self.getCampaniasData()
        # self.getExplotacionData()
        
    
    def UIComponents(self):
        self.setWindowTitle('aGrae Tools | Gestion de Muestras y Analiticas')
        self.resize(1200,600)
        self.combo_campania = QComboBox()
        self.combo_explotacion = QComboBox()
        self.combo_explotacion.setEditable(True)
        self.combo_explotacion.setInsertPolicy(QComboBox.NoInsert)
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
        self.toolButton.setMenu(QMenu())
        self.toolButton.setPopupMode(QToolButton.MenuButtonPopup)
        self.toolButton.setIconSize(QSize(15,15))
        self.toolMenu = self.toolButton.menu()
        self.toolMenu.addSeparator().setText('Gestion de Muestras')


        self.ExportarDataCSV = QAction(agraeGUI().getIcon('csv'),'Exportar informacion de Explotacion a CSV',self)
        self.ExportarDataCSV.triggered.connect(self.exportarDataCSV)
        self.CargarCapaMuestras = QAction(agraeGUI().getIcon('pois'),'Cargar Capa de Muestras',self)
        self.CargarCapaMuestras.triggered.connect(self.loadLayerMuestreo)
        self.GenerarArchivoLaboratorio = QAction(agraeGUI().getIcon('csv'),'Generar Archivo de Laboratorio',self)
        self.GenerarArchivoLaboratorio.triggered.connect(self.crearFormatoAnalitica)
        self.ImportarArchivoAnalisis = QAction(agraeGUI().getIcon('import'),'Cargar Archivo de Laboratorio',self)
        self.ImportarArchivoAnalisis.triggered.connect(self.cargarAnalitica)
        self.DerivarDatosAnalisis = QAction(agraeGUI().getIcon('csv'),'Derivar datos de Analitica',self)
        self.DerivarDatosAnalisis.triggered.connect(self.DerivarAnalitica)
        self.GenerarReporteAnalitica = QAction(agraeGUI().getIcon('chart-bar-2'),'Generar reporte de Laboratorio (Campaña)',self)
        self.GenerarReporteAnalitica.triggered.connect(self.generarReporteAnalitica)

        # self.tools.settingsToolsButtons(self.toolButton,[self.ExportarDataCSV,self.CargarCapaMuestras,self.GenerarArchivoLaboratorio,self.ImportarArchivoAnalisis,self.DerivarDatosAnalisis,self.GenerarReporteAnalitica],agraeGUI().getIcon('tools'),setMainIcon=True)
        # self.toolButton.menu().addAction(actions[i])

        self.toolMenu.addAction(self.GenerarArchivoLaboratorio)
        self.toolMenu.addAction(self.ImportarArchivoAnalisis)
        self.toolMenu.addAction(self.DerivarDatosAnalisis)

        self.toolMenu.addSeparator().setText('Gestion de Laboratorio')

        self.toolMenu.addAction(self.CargarCapaMuestras)
        self.toolMenu.addAction(self.ExportarDataCSV)
        self.toolMenu.addAction(self.GenerarReporteAnalitica)
  
        self.toolButton.setIcon(agraeGUI().getIcon('tools'))
        

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

        self.toolMenu.setStyleSheet('''
        QMenu {
            padding:5px;               }
''')

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
                self.tools.messages('aGrae Tools','Archivo exportado Correctamente',3)

    def loadLayerMuestreo(self):
        query = aGraeSQLTools().getSql('muestreo_data_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'select row_number() over () as id, * from muestras')
        muestras = self.tools.getDataBaseLayer(query,'{}-{}'.format(self.combo_campania.currentText(),self.combo_explotacion.currentText()),'muestreo_status',geometry='MultiPoint')
        QgsProject.instance().addMapLayer(muestras)
        iface.mapCanvas().setExtent(muestras.extent())

    def crearFormatoAnalitica(self):
        # METODO PARA CREAR LOS FORMATOS DE REPORTES ANALITICOS EN ARCHIVOS .CSV
        exp = self.combo_explotacion.currentText().replace(' ','_')
        exp = exp.split('-')[1]
        camp  = self.combo_campania.currentText()[2:].replace(' ','_')
        name = '{}_{}'.format(camp,exp)
        reply = QMessageBox.question(self,'aGrae Toolbox','Quieres generar el archivo de Analitica para la explotacion:\n{}?'.format(name),QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.tools.crearFormatoAnalitica(self.combo_campania.currentData(),self.combo_explotacion.currentData(),name)
    
    def cargarAnalitica(self):
        data = self.tools.cargarReporteAnalitica()
        if not data.empty:
            dlg = agraeAnaliticaDialog(data)
            dlg.exec()

    
    def DerivarAnalitica(self):
        file = self.tools.cargarReporteAnalitica(dataframe=False)
        if file:
            try:
                print(file)
                modulo = aGraeResamplearMuestras(file)
                modulo.processing()
                self.tools.messages('aGrae GIS','Archivo procesado Correctamente',3,True)
            except Exception as ex:
                self.tools.messages('aGrae GIS',ex,2)
    
    def generarReporteAnalitica(self):
        outputh_path = str(QFileDialog.getExistingDirectory(self, "Selecciona el Directorio."))
        output_query = '''copy ({}) to stdout  with csv header delimiter ';' ; '''.format(aGraeSQLTools().getSql('reporte_muestras_general.sql').format(self.combo_campania.currentData()))
        with open(os.path.join(outputh_path,'REPORTE_GENERAL_{}.csv'.format(self.combo_campania.currentText())),'w') as file:
            with self.tools.conn.cursor() as cur:
                cur.copy_expert(output_query,file)
                self.tools.messages('aGrae Tools','Archivo exportado Correctamente',3)
