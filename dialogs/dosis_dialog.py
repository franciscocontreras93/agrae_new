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

 