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

import psycopg2

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

        # Main layout for the dialog
        main_dialog_layout = QVBoxLayout(self)

        # Create TabWidget
        self.tab_widget = QTabWidget()
        main_dialog_layout.addWidget(self.tab_widget)

        # --- Tab 1: Muestras Pendientes (Nueva) ---
        self.tab_muestras_pendientes = QWidget()
        layout_muestras_pendientes = QVBoxLayout(self.tab_muestras_pendientes)
        
        # Placeholder para la futura tabla de muestras pendientes
        self.label_placeholder_pendientes = QLabel("Aquí se mostrarán las explotaciones con muestras pendientes.")
        self.label_placeholder_pendientes.setAlignment(Qt.AlignCenter)
        layout_muestras_pendientes.addWidget(self.label_placeholder_pendientes)
        
        self.tab_widget.addTab(self.tab_muestras_pendientes, "Muestras Pendientes")

        # --- Tab 2: Gestión General de Muestras (Interfaz Actual) ---
        self.tab_gestion_general = QWidget()
        layout_gestion_general = QVBoxLayout(self.tab_gestion_general)

        self.combo_campania = QComboBox()
        self.combo_explotacion = QComboBox()
        self.combo_explotacion.setEditable(True)
        self.combo_explotacion.setInsertPolicy(QComboBox.NoInsert)
        self.getCampaniasData()
        
        data_muestreo = agraeDataBaseDriver().read(aGraeSQLTools().getSql('muestreo_data_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'select iddata,campania,explotacion,lote,codigo,prioridad,tipo_muestra,status_lab, status,observaciones from muestras'))
        self.table = CustomTable(
            columns=['iddata','Campaña','Explotacion','Lote','Codigo','Prioridad','Tipo Muestra','Estado Analitica','Estado de Muestreo','Observaciones'],
            data = data_muestreo
        )
        self.combo_campania.currentIndexChanged.connect(self.updateTable)
        self.combo_explotacion.currentIndexChanged.connect(self.updateTable)
        
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
        self.DerivarMuestrasPendientes = QAction(agraeGUI().getIcon('pois'),'Derivar Parcelas cercanas',self)
        self.DerivarMuestrasPendientes.triggered.connect(self.derivar_muestras_cercanas)

        self.toolMenu.addAction(self.GenerarArchivoLaboratorio)
        self.toolMenu.addAction(self.ImportarArchivoAnalisis)
        self.toolMenu.addAction(self.DerivarDatosAnalisis)
        self.toolMenu.addAction(self.DerivarMuestrasPendientes)

        self.toolMenu.addSeparator().setText('Gestion de Laboratorio')

        self.toolMenu.addAction(self.CargarCapaMuestras)
        self.toolMenu.addAction(self.ExportarDataCSV)
        self.toolMenu.addAction(self.GenerarReporteAnalitica)
  
        self.toolButton.setIcon(agraeGUI().getIcon('tools'))
        
        # Layout para los combos y el toolbutton en la pestaña de gestión general
        group_combos = QGroupBox()
        layout_group_combos = QGridLayout()
        layout_group_combos.addWidget(QLabel('Seleccionar Campaña'),0,0)
        layout_group_combos.addWidget(QLabel('Seleccionar Explotacion'),0,1)
        layout_group_combos.addWidget(self.combo_campania,1,0)
        layout_group_combos.addWidget(self.combo_explotacion,1,1)
        layout_group_combos.addWidget(self.toolButton,1,2)
        group_combos.setLayout(layout_group_combos)

        layout_gestion_general.addWidget(group_combos)
        layout_gestion_general.addWidget(self.table)
        self.tab_gestion_general.setLayout(layout_gestion_general)
        self.tab_widget.addTab(self.tab_gestion_general, "Gestión General")

        self.tab_widget.setCurrentIndex(0) # Asegura que la nueva pestaña sea la primera

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
        data_muestreo = agraeDataBaseDriver().read(aGraeSQLTools().getSql('muestreo_data_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'select iddata,campania,explotacion,lote,codigo,prioridad,tipo_muestra,status_lab, status,observaciones from muestras'))
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
                # print(file)
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

    def derivar_muestras_cercanas(self):
        numero_de_muestras = 2
        query = '''with muestras as (select * from field.muestras where idcampania = {} and idexplotacion = {}),
        muestreadas as (select * from muestras where muestreado = true),
        derivadas as (select * from muestras where tipo = 2),
        procesadas as (select a.*,m.geom from muestras m join analytic.analitica a on a.cod = m.codigo ),
        pendientes as (select * from derivadas d  where d.codigo not in (select cod from procesadas)  and codigo ilike '%_D1%'),
        segmentos as (select p.codigo,s.ceap from agrae.segmentos s join pendientes p on st_intersects(s.geometria, p.geom)),
        cercanas as (select p.codigo ,c.cod,s.ceap, st_makeLine(st_centroid(p.geom),st_centroid(c.geom)) matriz_distancia, c.dist,p.geom from pendientes p
        cross join lateral (select pr.codigo as cod,round(st_transform(pr.geom,3857) <-> st_transform(p.geom,3857)) as dist, pr.geom  from muestreadas pr order by dist limit {}) as c
        join segmentos  s using(codigo)),
        data_unida as (select c.codigo,c.ceap,avg(ph) ph,avg(ce) ce,avg(carbon) carbon,avg(caliza) caliza,avg(ca) ca,avg(mg) mg,avg(k) k,avg(na) na,avg(n) n,avg(p) p,avg(organi) organi,
        avg(cox) cox,avg(al) al,avg(b) b,avg(fe) fe,avg(mn) mn,avg(cu) cu,avg(zn) zn,avg(s) s,avg(mo) mo,avg(ni) ni,avg(co) co,avg(ti) ti,avg("as") "as",avg(pb) pb,avg(cr) cr,avg(metodo) metodo
        from cercanas c 
        join analytic.analitica a on c.cod = a.cod
        group by c.codigo,c.ceap)
        insert into analytic.analitica (cod,ceap,ph,ce,carbon,caliza,ca,mg,k,na,n,p,organi,cox,al,b,fe,mn,cu,zn,s,mo,ni,co,ti,"as",pb,cr,metodo)
        select * from data_unida '''.format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),numero_de_muestras)

        with self.tools.conn.cursor(cursor_factory= psycopg2.extras.RealDictCursor) as cursor:
            try:
                cursor.execute(query)
                self.tools.conn.commit()
                print('Se actulizo')
            except Exception as ex:
                self.tools.conn.rollback()
                print(ex)