import os
import csv

import time


# from datetime import date
from psycopg2 import InterfaceError, errors, extras

from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtWidgets import (
    QDialog,
    QLayout,
    QGridLayout,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QGroupBox,
    QLabel,
    QPlainTextEdit,
    QComboBox,
    QMessageBox,
    QTabWidget,
    QTableView,
    QWidget
 
    
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



class MonitorRendimientosDialog(QDialog):
    def __init__(self,idcampania:int,idexplotacion:int):
        super().__init__()
        self.idexplotacion = idexplotacion
        self.idcampania = idcampania
        self.conn = agraeDataBaseDriver().connection()
        # print(self.idcampania,self.idexplotacion)

        self.UIComponents()

    def UIComponents(self):
        self.setWindowTitle('Monitor de Rendimiento')
        self.resize(400,300)
        main_layout = QVBoxLayout()

        widgetInformacion = QWidget()
        layout_informacion = QGridLayout()

        widgetCarga = QWidget()
        layout_carga_rindes = QGridLayout()
        # layout_carga_rindes.setRowStretch(0 | 1 | 2 , 200)

        widgetAjusteRindes = QWidget()
        layout_ajuste_rindes = QVBoxLayout()



        layout_group_2 = QGridLayout()
        group_1 = QGroupBox()
        # group_1.addTab('Cargar Datos')
        group_2 = QGroupBox()

        # ELEMENTS 
        # informacion widgets
        lbl_info_1 = QLabel('Campaña')
        lbl_info_2 = QLabel('Explotacion')
        lbl_info_camp = QLabel('')
        lbl_info_exp = QLabel('')
        lbl_info_3 = QLabel('Num. Lotes')
        lbl_info_count = QLabel('')
        self.lbl_info_info = QLabel('INFORMACION IMPORTANTE')
        self.lbl_info_info.setFixedHeight(20)
        self.lbl_info_info.setStyleSheet("QLabel { background-color : red; color : white; font-weight : bold }")
        

        for lbl in [lbl_info_1,lbl_info_2,lbl_info_camp,lbl_info_exp,lbl_info_3,lbl_info_count,self.lbl_info_info] : lbl.setAlignment(Qt.AlignCenter)


        # carga widgets
        lbl_carga_1 = QLabel('Seleccionar capa de Rindes:')
        lbl_carga_2 = QLabel('Campo Volumen')
        lbl_carga_3 = QLabel('Campo Humedad')
        lbl_carga_4 = QLabel('Fecha de Muestreo')


        self.layer_rinde_combo = QgsMapLayerComboBox()
        self.layer_rinde_combo.setFilters(QgsMapLayerProxyModel.PointLayer)
        self.layer_rinde_combo.layerChanged.connect(self.updateFieldsCombos)
        self.layer_rinde_date = QgsDateEdit()
        self.layer_rinde_date.setCalendarPopup(True)

        self.volumen_field_combo = QgsFieldComboBox()
        self.volumen_field_combo.setLayer(self.layer_rinde_combo.currentLayer())

        self.humedad_field_combo = QgsFieldComboBox()
        self.humedad_field_combo.setLayer(self.layer_rinde_combo.currentLayer())

        loadRindesData = QPushButton('Cargar Datos de Rindes')
        loadRindesData.clicked.connect(self.cargarDatosRindes)
        
        # ajuste widgets 
        widgetAjusteLotes = QWidget()
        widgetAjusteCultivos = QWidget()
        layout_widgetAjusteLotes = QGridLayout()
        layout_widgetAjusteCultivos = QGridLayout()
        ajuste_tab = QTabWidget()
        ajuste_data_lotes = agraeDataBaseDriver().read(aGraeSQLTools().getSql('rindes_data_lotes.sql').format(self.idcampania,self.idexplotacion))
        self.tableAjusteLotes = CustomTable(widgetAjusteLotes,['data','Lote','Cultivo','Prod. Final'],ajuste_data_lotes,editable=True,editable_column='Prod. Final',regex="^[1-9][0-9]+(?:_[a-zA-Z])?$")
        saveAjusteLotes = QPushButton('Guardar Rendimientos por Lote')
        saveAjusteLotes.clicked.connect(self.saveProductionByLote)


        ajuste_data_cultivos = agraeDataBaseDriver().read(aGraeSQLTools().getSql('rindes_data_cultivos.sql').format(self.idcampania,self.idexplotacion))
        self.tableAjusteCultivos = CustomTable(widgetAjusteLotes,['idcultivo','Cultivo','Prod. Final'],ajuste_data_cultivos,editable=True,editable_column='Prod. Final',regex="^[1-9][0-9]*$")
        saveAjusteCultivo = QPushButton('Guardar Rendimientos por Cultivo')
        saveAjusteCultivo.clicked.connect(self.saveProductionByCultivo)

        ########### TAB WIDGET ####################
        
        tab_1 = QTabWidget()
        tab_1.addTab(widgetInformacion,'Informacion Rindes')
        tab_1.addTab(widgetCarga,'Carga de Datos')
        tab_1.addTab(widgetAjusteRindes,'Ajuste de Valores de Rendimiento')

        #SETTING ELEMENTS IN LAYOUTS
        # layout info
        layout_informacion.addWidget(lbl_info_1,0,0)
        layout_informacion.addWidget(lbl_info_2,0,1)
        layout_informacion.addWidget(lbl_info_3,0,2)
        layout_informacion.addWidget(lbl_info_camp,1,0)
        layout_informacion.addWidget(lbl_info_exp,1,1)
        layout_informacion.addWidget(lbl_info_count,1,2)
        layout_informacion.addWidget(self.lbl_info_info,2,0,2,0)

        widgetInformacion.setLayout(layout_informacion)
       
        
       
        

        # layout carga
        layout_carga_rindes.addWidget(lbl_carga_1,0,0)
        layout_carga_rindes.addWidget(self.layer_rinde_combo,0,1)
        layout_carga_rindes.addWidget(lbl_carga_2,1,0)
        layout_carga_rindes.addWidget(lbl_carga_3,1,1)
        layout_carga_rindes.addWidget(lbl_carga_4,1,2)

        layout_carga_rindes.addWidget(self.volumen_field_combo,2,0)
        layout_carga_rindes.addWidget(self.humedad_field_combo,2,1)
        layout_carga_rindes.addWidget(self.layer_rinde_date,2,2)
        layout_carga_rindes.addWidget(loadRindesData,3,0,2,0)

        widgetCarga.setLayout(layout_carga_rindes)

        


        

        # LAYOUT AJUSTE
       


        layout_widgetAjusteLotes.addWidget(self.tableAjusteLotes,0,0)
        layout_widgetAjusteLotes.addWidget(saveAjusteLotes,1,0)

        layout_widgetAjusteCultivos.addWidget(self.tableAjusteCultivos,0,0)
        layout_widgetAjusteCultivos.addWidget(saveAjusteCultivo,1,0)

        widgetAjusteLotes.setLayout(layout_widgetAjusteLotes)
        widgetAjusteCultivos.setLayout(layout_widgetAjusteCultivos)


        ajuste_tab.addTab(widgetAjusteLotes,'Ajustar por Lotes (1-2)')
        ajuste_tab.addTab(widgetAjusteCultivos,'Ajustar por Cultivos (3)')
        
        
        
        
        
        layout_ajuste_rindes.addWidget(ajuste_tab)





        widgetAjusteRindes.setLayout(layout_ajuste_rindes)

        # group_1.setLayout(layout_carga_rindes)
        # group_2.setLayout(layout_group_2)

        # layout.addWidget(group_1)
        # layout.addWidget(group_2)
        main_layout.addWidget(tab_1)
        self.setLayout(main_layout)
        pass

    def validateData(self):
        with self.conn.cursor() as cursor: 
            cursor.execute()
        pass
    
    def updateFieldsCombos(self,layer):
        # print(layer)
        self.humedad_field_combo.setLayer(layer)
        self.volumen_field_combo.setLayer(layer)
    
    def loadInfo(self):
        pass

    def saveProductionByLote(self):
        data = dict()
        rows = self.tableAjusteLotes.rowCount()
        for r in range(rows):
            iddata = self.tableAjusteLotes.item(r,0).text()
            value = self.tableAjusteLotes.item(r,3).text()
            if '_' in value:
                prod = value.split('_')[0]
                group = value.split('_')[1]
                data[iddata] = {'produccion': int(prod) , 'grupo': group}
            else:
                group = 'N/D'
                data[iddata] = {'produccion': int(value) , 'grupo': group}
            # print(iddata,value)

        
        
        groupped , not_groupped = self.groupped(data)
        if len(groupped) > 0:
            for k in groupped:
                sql_groupped = aGraeSQLTools().getSql('rindes_save_prod_groupped.sql').format(' ,'.join(groupped[k]['ids']),groupped[k]['produccion'])
    
        if len(not_groupped) > 0:
            sql_not_groupped = aGraeSQLTools().getSql('rindes_save_prod_not_groupped.sql')
            query = ''
            for k in not_groupped:
                query = query + '({},{}),\n'.format(not_groupped[k],k)
            sql_not_groupped = sql_not_groupped.format(query[:-2])

        with self.conn.cursor() as cursor:
            try:
                try:
                    cursor.execute(sql_groupped)
                except: pass
                try: 
                    cursor.execute(sql_not_groupped)
                except:
                    pass
                self.conn.commit()
                aGraeTools().messages('Monitor de Rendimientos','Se han guardado los datos de Produccion',3)
                self.close()
            except Exception as ex:
                aGraeTools().messages('Monitor de Rendimientos',ex,2,alert=True)
                self.conn.rollback()
                pass

            

    def saveProductionByCultivo(self):

        rows = self.tableAjusteCultivos.rowCount()
        with self.conn.cursor() as cursor:
            try:
                for r in range(rows):
                    idcultivo = self.tableAjusteCultivos.item(r,0).text()
                    value = self.tableAjusteCultivos.item(r,2).text()
                    sql_cultivos = aGraeSQLTools().getSql('rindes_save_prod_cultivo.sql').format(self.idcampania,self.idexplotacion,idcultivo,value)
                    cursor.execute(sql_cultivos)
                self.conn.commit()
                # print(sql_cultivos)
                aGraeTools().messages('Monitor de Rendimientos','Se han guardado los datos de Produccion',3)
            except Exception as ex:
                # print(ex)
                self.conn.rollback()
                aGraeTools().messages('Monitor de Rendimientos',ex,2,alert=True)

    def groupped(self,data):
        groupped = {}
        not_groupped = {}


        for key, value in data.items():
            if value['grupo'] != 'N/D':
                if value['grupo'] not in groupped:
                    ids = [key]
                    groupped[value['grupo']] = {
                        'ids' : ids,
                        'produccion' : value['produccion']
                    }
                else:
                    groupped[value['grupo']]['ids'].append(key)
            else: 
                not_groupped[key] = value['produccion']
            
        
        return groupped,not_groupped
    
    def cargarDatosRindes(self):
        # layer = self.layer_rinde_combo.currentLayer()
        # field_volumen=self.volumen_field_combo.currentField(),
        # field_humedad=self.humedad_field_combo.currentField(),
        # fecha = self.layer_rinde_date.date().toString('yyyy/MM/dd')
        # print(fecha)

        aGraeTools().cargarRindes(
                layer=self.layer_rinde_combo.currentLayer(),
                field_volumen=self.volumen_field_combo.currentField(),
                field_humedad=self.humedad_field_combo.currentField(),
                fecha= self.layer_rinde_date.date().toString('yyyy/MM/dd'),
                idcampania=self.idcampania,
                idexplotacion=self.idexplotacion
                )

