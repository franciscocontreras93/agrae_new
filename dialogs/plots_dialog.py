# -*- coding: utf-8 -*-
"""
/***************************************************************************
agraeDockWidget
                                 A QGIS plugin
 Conjunto de herramientas
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2021-12-03
        git sha              : $Format:%H$
        copyright            : (C) 2021 by  aGrae Solutions, S.L.
        email                : info@agrae.es
 ***************************************************************************/
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
import csv
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time


from PyQt5.QtCore import QRegExp, QDate, QDateTime, QThreadPool
from PyQt5.QtGui import QRegExpValidator, QIcon, QPixmap
from PyQt5.QtWidgets import *

from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal, QSettings, QVariant
from qgis.core import *


# from .utils import AgraeUtils, AgraeToolset,  AgraeAnalitic, TableModel, PanelRender, AgraeZipper
from ..db import agraeDataBaseDriver
from ..sql import aGraeSQLTools
from ..tools import aGraeTools
from ..gui import agraeGUI
from ..tools.plotTools import TableModel, PanelRender
# from .agrae_worker import Worker

from ..resources import *

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from PyQt5 import QtCore, QtWidgets
import sys
import matplotlib
import threading

agraePlotsDialog_, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'ui/analitica_dialog_2.ui'))

class agraePlotsDialog(QtWidgets.QDialog, agraePlotsDialog_):
    matplotlib.use('Qt5Agg')
    closingPlugin = pyqtSignal()

    # def __init__(self,dataSuelo, dataExtraccion, lote,parcela, prod, cultivo, idlotecampania, ic,biomasa,residuo, ccosecha,cresiduo, parent=None):
    def __init__(self,iddata: int, lote : str, cultivo : str, produccion_esperada : str, dataSuelo: list, dataExtraccion:list, ic:float,biomasa:float,residuo:float, ccosecha:float,cresiduo:float, parent=None):
        super(agraePlotsDialog, self).__init__(parent)
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'ui/analitica_dialog_2.ui'), self)
        self.conn = agraeDataBaseDriver().connection()
        self.tools = aGraeTools()
        self.lote = lote.upper()
        self.cultivo = cultivo.upper()
        self.produccion = produccion_esperada.upper()

        self.dataSuelo = dataSuelo
        self.dataExtraccion = dataExtraccion
        self.iddata = iddata
        self.lote = lote 
        self.prod = produccion_esperada
        self.cultivo = cultivo
        self.ic = float(ic)
        self.biomasa = float(biomasa)
        self.residuo = float(residuo)
        self.ccosecha = float(ccosecha)
        self.cresiduo = float(cresiduo)
        
        self.enabled = False
        self.i = 0
        
        self.area = None
        self.prod_ponderado = None 
        self.n_ponderado = None
        self.p_ponderado = None
        self.k_ponderado = None
        self.formulas = []
        self.formula = None
        self.dataNecesidades = None
        self.dataValidator = False
        self.dataAuto = None
        self.dataHuellaCarbono = None


        self._pesos = []
        self._pesos_aplicados = []
        self._precios = []
        self._precio_ton = []


        self.UIcomponents()

        self.sc = MplCanvas(self)
        self.sc.setStyleSheet("background-color:transparent;")
        self.sc.plot(self.dataSuelo)

        self.verticalLayout.addWidget(self.sc)

        self.populateTable()
        self.necesidadesTotales()

    def UIcomponents(self): 
        # icons_path = self.icons_path
        self.tabWidget.setCurrentIndex(0)
        self.setWindowTitle('Analitica Lote: {}'.format(self.lote.upper()))
        self.setWindowIcon(agraeGUI().getIcon('chart-bar'))

        # self.tabeWidget.setTabEnabled(1,False)
        leyenda = agraeGUI().getImage('leyenda')
        p1_img = agraeGUI().getImage('p1')
        co2_img = agraeGUI().getImage('co2')
        # leyenda.scaledToWidth(281)
        self.setStyleSheet(aGraeTools().styleSheetPlotDialog())
        self.lgnd1.setPixmap(leyenda)
        self.lbl_co2.setPixmap(co2_img)
        self.p1.setPixmap(p1_img)
        # self.lbl_lote.setText('{} - {}'.format(self.lote.upper(),self.parcela.upper()))
        self.lbl_lote.setText('{}'.format(self.lote))
        self.lbl_cultivo.setText('{}'.format(self.cultivo))
        self.lbl_prod.setText('{} Kg/Ha'.format(self.produccion))
        self.tableView.setShowGrid(False)

        self.btn_panel.setIcon(agraeGUI().getIcon('image'))
        self.btn_panel.setIconSize(QtCore.QSize(20, 20))
        self.btn_panel.setToolTip('Exportar Paneles')
        self.btn_panel.clicked.connect(self.panel)
        # self.btn_panel.clicked.connect(self.huellaCarbono)
        
        self.btn_save_data.setIcon(agraeGUI().getIcon('save'))
        self.btn_save_data.setIconSize(QtCore.QSize(20, 20))
        self.btn_save_data.setToolTip('Guardar Datos')
        self.btn_save_data.clicked.connect(self.saveFertData)


        # self.btn_ajuste_auto.clicked.connect(self.execAutoFert)

        self.regexFormula = QRegExpValidator(QRegExp(r'(\d{2}\-\d{2}\-\d{2})'))
        self.line_formula_1.setValidator(self.regexFormula)
        # self.line_formula_1.setInputMask(("99-"*3)[:-1]) #! AGREGAR MASCARA AL INGRESAR LA FORMULA TODO: 
        self.line_formula_1.textChanged.connect(self.fert)
        self.line_formula_2.setValidator(self.regexFormula)
        self.line_formula_2.textChanged.connect(self.fert)
        self.line_formula_3.setValidator(self.regexFormula)
        self.line_formula_3.textChanged.connect(self.fert)
        self.line_formula_4.setValidator(self.regexFormula)
        self.line_formula_4.textChanged.connect(self.fert)

        
        
        #TODO 

        self.line_cantidad_1.textChanged.connect(lambda t, c=self.combo_ajuste_1: self.enableCombo(t,c))
        self.line_cantidad_2.textChanged.connect(lambda t, c=self.combo_ajuste_2: self.enableCombo(t,c))
        self.line_cantidad_3.textChanged.connect(lambda t, c=self.combo_ajuste_3: self.enableCombo(t,c))
        self.line_cantidad_4.textChanged.connect(lambda t, c=self.combo_ajuste_4: self.enableCombo(t,c))
        
        # #TODO END
        # # self.btn_ok_1.clicked.connect(lambda c=self.line_cantidad_5.text(): self.fertTradicional(c))
        # # self.line_cantidad_6.textChanged.connect(lambda c:self.fertTradicional(c,False))

        self.combo_ajuste_1.currentIndexChanged.connect(lambda i,t=self.table_aporte_1,p=self.line_precio_1,l=self.t_aporte_1, lp=self.t_precio_1, a=self.line_cantidad_1: self.fertilizar(i,t,p,l,lp,a,1))
        self.combo_ajuste_2.currentIndexChanged.connect(lambda i,t=self.table_aporte_2,p=self.line_precio_2,l=self.t_aporte_2, lp=self.t_precio_2, a=self.line_cantidad_2: self.fertilizar(i,t,p,l,lp,a,2))
        self.combo_ajuste_3.currentIndexChanged.connect(lambda i,t=self.table_aporte_3,p=self.line_precio_3,l=self.t_aporte_3, lp=self.t_precio_3, a=self.line_cantidad_3: self.fertilizar(i,t,p,l,lp,a,3))
        self.combo_ajuste_4.currentIndexChanged.connect(lambda i,t=self.table_aporte_4,p=self.line_precio_4,l=self.t_aporte_4, lp=self.t_precio_4, a=self.line_cantidad_4: self.fertilizar(i,t,p,l,lp,a,4))

        self.getDataFertilizacion()

    def populateTable(self): 
        cols = [0,1,2,3,4,5]
        datagen = ([f[col] for col in cols] for f in self.dataExtraccion)
        
        df = pd.DataFrame.from_records(data=datagen, columns=cols)        
        df_sorted = df.sort_values(by=0).round({'area_has':2})
        # print(df_sorted) #! debug
        model = TableModel(df_sorted)
        self.tableView.setModel(model)
        self.tableView.setColumnWidth(0,35)
        self.tableView.setColumnWidth(5,35)
        os.chdir(os.path.join('../',os.path.dirname(__file__)))
        os.chdir('../')
        # print(os.getcwd())
        self.tableView.grab().save(os.path.join(
            os.getcwd(), r'tools\img\tabla.png'))
        self.sc.saveImage(os.path.join(
        os.getcwd(), r'tools\img\chart.png'))

        

        uf = [e[0] for e in self.dataExtraccion]
        area = [float(e[5]) for e in self.dataExtraccion]
        npk = [str(e[4]) for e in self.dataExtraccion]
        lista = [e.split(' / ') for e in npk ]
        try: 
            n = [int(e[0]) for e in lista ]
            p = [int(e[1]) for e in lista ]
            k = [int(e[2]) for e in lista ]
            dataNecesidades = zip(uf,n,p,k)
            cols = [0,1,2,3]
            datagen = ([f[col] for col in cols] for f in dataNecesidades)
            df = pd.DataFrame.from_records(data=datagen, columns=cols)
            model = TableModel(df)
            self.table_necesidades.setModel(model)
            self.table_necesidades.setColumnWidth(0, 35)
            self.table_necesidades.setColumnWidth(1, 79)
            self.table_necesidades.setColumnWidth(2, 79)
            self.table_necesidades.setColumnWidth(3, 79)
        except: pass
    
    def necesidadesTotales(self) -> None: 
        data = self.dataExtraccion
        ce = [int(e[1]) for e in data]
        area = [float(e[5]) for e in data]
        npk = [str(e[4]) for e in data]
        lista = [e.split(' / ') for e in npk ]
        try: 
            n = [int(e[0]) for e in lista ]
            p = [int(e[1]) for e in lista ]
            k = [int(e[2]) for e in lista ]



            self.prod_ponderado = self.sumaPonderada(ce,area)
            self.n_ponderado = self.sumaPonderada(n, area)
            self.p_ponderado = self.sumaPonderada(p, area)
            self.k_ponderado = self.sumaPonderada(k, area)
            self.area = round(sum(area),2)

            
            self.prod_pond.setText('{} Kg Cosecha/Ha'.format(self.prod_ponderado))
            self.area_total.setText('{} Ha'.format(round(sum(area),2)))
            self.npk_pond.setText('{} / {} / {}'.format(self.n_ponderado,self.p_ponderado,self.k_ponderado))
            # self.npk_pond_2.setText('{} / {} / {}'.format(self.n_ponderado,self.p_ponderado,self.k_ponderado))
            # self.lbl_n.setText('{}'.format(self.n_ponderado))
            # self.lbl_p.setText('{}'.format(self.p_ponderado))
            # self.lbl_k.setText('{}'.format(self.k_ponderado))
        except Exception as ex:  QgsMessageLog.logMessage(f'{ex}', 'aGrae GIS', level=1)

    
    def sumaPonderada(self,v,a) -> int:
        """
        v = Value a = Area

        """
        try:
            zipedd = zip(v, a)
            # print('zipped',zipedd)
            p1 = [v * a for (v, a) in zipedd]
            p2 = round(sum(p1)/sum(a))
        except ZeroDivisionError:
            p2=0 

        # print('suma_ponderada',p2)
        return p2  

    def ajustesFertilizantes(self,n:list,x:float,p:list,y:float,k:list,z:float) -> zip:
        
        """
        n: List of uf values for N
        x: value for N dosification
        p: List of uf values for P
        y: Value dosification for P, 
        k: List of K values
        z: Value dosification for K 

        return data: Structured analized values, Totals


        """
        uf = ['UF1','UF2','UF3','UF4','UF5','UF6','UF7','UF8','UF9']

        n1 = [round(e/x) if x != 0 else 0 for e in n]
        zn = zip(uf, n1)
        tn = sum(n1)
        dataN = {k:v for k,v in zn}
        # print('N: ', dataN)

        p1 = [round(e/y) if y != 0 else 0 for e in p]
        zp = zip(uf,p1)
        dataP = {k:v for k,v in zp}
        tp = sum(p1)
        # print('P: ',dataP)  

        k1 = [round(e/z) if z != 0 else 0 for e in k]
        zk = zip(uf,k1)
        tk = sum(k1)
        dataK = {k:v for k,v in zk}
        # print('K :',dataK)

        pk1 = [round((e+i)/2) for e,i in zip(p1,k1)]
        zpk = zip(uf,pk1)
        tpk = sum(pk1)
        dataPK = {k:v for k,v in zpk}
        

        totales = [tn,tp,tk,tpk]

        # print('PK :',dataPK)

        data = zip(uf,n1,p1,k1,pk1)
        return data

    def fertilizar(self,index,table,precio,l_peso,l_precio,l_aplicados,i):
        """fertilizar _summary_

        _extended_summary_

        :param _type_ index: _description_
        :param _type_ table: _description_
        :param _type_ precio: _description_
        :param _type_ l_peso: _description_
        :param _type_ l_precio: _description_
        :param _type_ l_aplicados: _description_
        :param _type_ i: _description_
        """
        d = None
        try:
            if index != 0 and self.dataValidator == False:
                precio = precio.text()
                data = self.dataExtraccion
                # print(precio)
                # print(self.dataExtraccion)
                area = [float(e[5]) for e in data]
                npk = [str(e[4]) for e in data]
                lista = [e.split(' / ') for e in npk ]
                n = [int(e[0]) for e in lista ]
                p = [int(e[1]) for e in lista ]
                k = [int(e[2]) for e in lista ]
            elif self.dataValidator == True:
                precio = precio.text()
                data = self.dataNecesidades
                data = list(zip(*[data[col] for col in data]))
                # print(data)
                area = [float(e[5]) for e in self.dataExtraccion]
                uf = [e[0] for e in data]
                n = [int(e[1]) for e in data]
                p = [int(e[2]) for e in data]
                k = [int(e[3]) for e in data]



            f_n = int(self.formula[0])/100 # FACTOR NITROGENO EN DOSIS APLICADA
            f_p = int(self.formula[1])/100 # FACTOR FOSFORO EN DOSIS APLICADA
            f_k = int(self.formula[2])/100 # FACTOR POTASIO EN DOSIS APLICADA


            cols = [0,(index)]
            d = self.ajustesFertilizantes(n=n,x=f_n,p=p,y=f_p,k=k,z=f_k)
            # print(d)        
            datagen = ([f[col] for col in cols] for f in d)
            df = pd.DataFrame.from_records(data=datagen, columns=cols)
            # df.style.format({index: '{:.1f} Kg/Ha'})
            model = TableModel(df)
            table.setModel(model)
            table.setColumnWidth(0, 35)
            table.setColumnWidth(1, 35)
            os.chdir(os.path.join('../',os.path.dirname(__file__)))
            os.chdir('../')
            table.grab().save(os.path.join(os.getcwd(), r'tools\img\tf{}.png'.format(i)))


            d = self.ajustesFertilizantes(n=n, x=f_n, p=p, y=f_p, k=k, z=f_k)
            datagen = ([f[col] for col in cols] for f in d)
            l = list(datagen)
            a1 = [int(e[1]) for e in l]
            a2 = [int(round(x*y)) for x,y in zip(a1,area)]
            p_aporte = self.sumaPonderada(a1, area)
            # p_aporte = sum(a2)
            # p_aporte = p_aporte  #* sum(area)
            # print('p_aporte',p_aporte)
            self._pesos.append(round(p_aporte))
            self._pesos_aplicados.append(round(sum(a2)))


            pr_aporte = int(precio)*(int(p_aporte)/1000)
            self._precios.append(round(pr_aporte))
            l_peso.setText('{} Kg/Ha'.format(str(round(p_aporte))))
            l_precio.setText('{} €/Ha'.format(str(round(pr_aporte))))

            
            d = self.ajustesFertilizantes(n=n, x=f_n, p=p, y=f_p, k=k, z=f_k)
            genValue = (f[index]  for f in d)
            values = list(genValue)

            self.i = self.i + 1
            self.balanceNutrientes(values,f_n,f_p,f_k)
            self.formulas.append(self.formula)
            self._precio_ton.append(int(precio))

        except ValueError as ve: 
            QgsMessageLog.logMessage(f'{ve}', 'aGrae GIS', level=1)

            pass

    def balanceNutrientes(self,valores:list,dosis_n:float,dosis_p:float,dosis_k:float):


        if self.dataValidator == False:
            data = self.dataExtraccion
            uf = [e[0] for e in data]
            area = [float(e[5]) for e in data]
            npk = [str(e[4]) for e in data]
            lista = [e.split(' / ') for e in npk ]
            n = [int(e[0]) for e in lista ]
            p = [int(e[1]) for e in lista ]
            k = [int(e[2]) for e in lista ]        

            aporte_n = [round(v*dosis_n) for v in valores]
            aporte_p = [round(v*dosis_p) for v in valores]
            aporte_k = [round(v*dosis_k) for v in valores]
            # print(aporte_n)
            total_n = [int(i-a) for i,a in zip(n,aporte_n)]
            total_p = [int(i-a) for i,a in zip(p,aporte_p)]
            total_k = [int(i-a) for i,a in zip(k,aporte_k)]

            self.dataNecesidades = zip(uf, total_n, total_p, total_k)

            cols = [0, 1, 2, 3]
            datagen = ([f[col] for col in cols] for f in self.dataNecesidades)
            df = pd.DataFrame.from_records(data=datagen, columns=cols)
            model = TableModel(df)

            self.table_necesidades.setModel(model)
            self.table_necesidades.setColumnWidth(0, 35)
            self.table_necesidades.setColumnWidth(1, 79)
            self.table_necesidades.setColumnWidth(2, 79)
            self.table_necesidades.setColumnWidth(3, 79)
            # print('-----------dep 1 ------------')
            self.dataNecesidades = df
            self.dataValidator = True
            # print(self.dataNecesidades)
            # print('-----------dep 1 end ------------')



        else: 
            data = self.dataNecesidades
            data = list(zip(*[data[col] for col in data]))
            # print(data)
            
            uf = [e[0] for e in data]
            n = [int(e[1]) for e in data ]
            p = [int(e[2]) for e in data ]
            k = [int(e[3]) for e in data ]
            aporte_n = [round(v*dosis_n) for v in valores]
            aporte_p = [round(v*dosis_p) for v in valores]
            aporte_k = [round(v*dosis_k) for v in valores]
            
            total_n = [int(i-a) for i, a in zip(n, aporte_n)]
            total_p = [int(i-a) for i, a in zip(p, aporte_p)]
            total_k = [int(i-a) for i, a in zip(k, aporte_k)]
            self.dataNecesidades = zip(uf, total_n, total_p, total_k)

            # print(total_n,total_p,total_k)


        
            cols = [0, 1, 2, 3]
            datagen = ([f[col] for col in cols] for f in self.dataNecesidades)
            df = pd.DataFrame.from_records(data=datagen, columns=cols)
            model = TableModel(df)
            self.table_necesidades.setModel(model)
            self.table_necesidades.setColumnWidth(0, 35)
            self.table_necesidades.setColumnWidth(1, 79)
            self.table_necesidades.setColumnWidth(2, 79)
            self.table_necesidades.setColumnWidth(3, 79)
            # print('----------- dep 2------------------')
            self.dataNecesidades = df
            # print(self.dataNecesidades)
            # print('-----------dep 2 end ------------')
            self.dataValidator = True



        
        
    

       
        pass
       
    def enableCombo(self,text,combo):
        if len(text) >= 0:        
            combo.setEnabled(True)
        else:
            combo.setEnabled(False)
  
    def fert(self,text):
        if len(text) ==8:
            self.formula = text.split('-')
            # self.pushButton_2.setEnabled(True)

   
    def getDataFertilizacion(self): 
        sql = ''' 
        select 
        d.fertilizantefondoformula,
        d.fertilizantefondoprecio,
        d.fertilizantefondoajustado,
        d.fertilizantefondoaplicado,
        d.fertilizantecob1formula,
        d.fertilizantecob1precio,
        d.fertilizantecob1ajustado,
        d.fertilizantecob1aplicado,
        d.fertilizantecob2formula,
        d.fertilizantecob2precio,
        d.fertilizantecob2ajustado,
        d.fertilizantecob2aplicado,
        d.fertilizantecob3formula,
        d.fertilizantecob3precio,
        d.fertilizantecob3ajustado, 
        d.fertilizantecob3aplicado,
        d.fert_status from campaign.data d
        where d.iddata = {}
        '''.format(self.iddata)
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute(sql)
            data = cursor.fetchall()
        data = list(data[0])        
        data = [e if e != 0 and e != '' and e is not None else None for e in data]
        _validate = [data[e] for e in range(3) if data[e] != None]
        # print(_validate)
        # print(len(_validate))

        if len(_validate) >= 3:
            # print(data)
            # self.btn_ajuste_auto.setEnabled(True)
            # self.btn_save_data.setEnabled(False)
            self.dataAuto = data
            self.execAutoFert()
            # print(self.dataAuto)
        else: 
            self.btn_save_data.setEnabled(True)
        
    def autoFert(self):
        txt = '''<html><head/><body><p align="center">Se han calculado 1 combinaciones de <br/>fertilizantes para ajustar las<br/>necesidades del cultivo. De ellas se ha<br/>seleccionado la combinacion mas<br/>economica.<br/>Los fertilizantes que<br/>se han Analizado son:</p>'''
        data = self.dataAuto
        # print(data)
        if data[0] != None or data[1] != None or data[2] != None :
            f1 = str(data[0])
            txt = txt + '''<p align="center"><span style=" font-weight:600;">APORTE 1 {} </span>  </p>'''.format(f1)   
            self.line_formula_1.setText(data[0])
            self.line_precio_1.setText(str(int(round(data[1]))))
            self.combo_ajuste_1.setCurrentText(str(data[2]).upper())
            # self.line_cantidad_1.setText(str(float(data[3])))
            time.sleep(1)
            # print(data[0])
        if data[4] != None and data[5] != None and data[6] != None :
            f2 = str(data[4])
            txt = txt + '''<p align="center"><span style=" font-weight:600;">APORTE 2 {} </span></p>'''.format(f2)   
            self.line_formula_2.setText(data[4])
            self.line_precio_2.setText(str(int(round(data[5]))))
            self.combo_ajuste_2.setCurrentText(str(data[6]).upper())
            # self.line_cantidad_2.setText(str(float(data[7])))
            time.sleep(1)
            # print(data[2])
        if data[8] != None and data[9] != None and data[10] != None:
            f3 = str(data[8])
            txt = txt + '''<p align="center"><span style=" font-weight:600;">APORTE 3 {} </span></p>'''.format(f3)
            self.line_formula_3.setText(data[8])
            self.line_precio_3.setText(str(int(round(data[9]))))
            self.combo_ajuste_3.setCurrentText(str(data[10]).upper())
            # self.line_cantidad_3.setText(str(float(data[11])))
            time.sleep(1)
        if data[12] != None and data[13] != None and data[14] != None :
            f4 = str(data[12])
            txt = txt + '''<p align="center"><span style=" font-weight:600;">APORTE 4 {} </span></p>'''.format(f4)
            self.line_formula_4.setText(data[13])
            self.line_precio_4.setText(str(int(round(data[13]))))
            self.combo_ajuste_4.setCurrentText(str(data[14]).upper())
            # self.line_cantidad_4.setText(str(float(data[15])))
            time.sleep(1)
        self.combo_status.setCurrentText(str(data[16]))
        txt = txt + '''</body></html>'''
        # self.label_16.setText(txt)
        self.btn_save_data.setEnabled(True)
        self.huellaCarbono()
    def execAutoFert(self):
        x = threading.Thread(target=self.autoFert)
        try: 
            x.start()
        except: 
            pass
        
    def panel(self):
        #TODO CONCATENAR IDLOTECAMPANIA AL NOMBRE DEL ARCHIVO
        self.huellaCarbono()
        npk = [self.n_ponderado,self.p_ponderado, self.k_ponderado]
        render = PanelRender(self.lote, self.cultivo, self.prod_ponderado, self.area, npk,self.i,self._pesos,self._precios,self._pesos_aplicados,formulas=self.formulas,dataHuellaCarbono=self.dataHuellaCarbono,preciosTon=self._precio_ton,moneda='€')
        # print(self._pesos_aplicados, self._precios)

        render.savePanel()
        QMessageBox.about(self, "", "Paneles Generados Correctamente")
    
    def saveFertData(self):
        datos = {}
        sql_base = '''UPDATE campaign."data" \nSET\n'''
        query = ''
        ajustes = [self.combo_ajuste_1,self.combo_ajuste_2,self.combo_ajuste_3,self.combo_ajuste_4]
        formulas = [self.line_formula_1,self.line_formula_2,self.line_formula_3,self.line_formula_4]
        precios = [self.line_precio_1,self.line_precio_2,self.line_precio_3,self.line_precio_4]

        for e in range(len(ajustes)):
            if ajustes[e].currentIndex() != 0:
                datos[e] = {
                'formula': str(formulas[e].text()),
                'precio': int(round(float(precios[e].text()))),
                'ajuste': str(ajustes[e].currentText())
            }

        
        for d in datos:
            if d is 0:
                query = '''fertilizantefondoformula='{}', fertilizantefondoprecio={}, fertilizantefondoajustado='{}', '''.format(
                    datos[d]['formula'],
                    datos[d]['precio'],
                    datos[d]['ajuste'])
            elif d is 1:
                query = query + '''fertilizantecob1formula='{}', fertilizantecob1precio={}, fertilizantecob1ajustado='{}','''.format(
                    datos[d]['formula'],
                    datos[d]['precio'],
                    datos[d]['ajuste'])
            elif d is 2:
                query = query + '''fertilizantecob2formula='{}', fertilizantecob2precio={}, fertilizantecob2ajustado='{}','''.format(
                    datos[d]['formula'],
                    datos[d]['precio'],
                    datos[d]['ajuste'])
            elif d is 3:
                query = query + '''fertilizantecob3formula='{}', fertilizantecob3precio={}, fertilizantecob3ajustado='{}','''.format(
                    datos[d]['formula'],
                    datos[d]['precio'],
                    datos[d]['ajuste'])
            
        query = sql_base + query[:-1] + '\nWHERE iddata = {}'.format(self.iddata)
            

        with self.conn.cursor() as cursor: 
            try:
                    
                cursor.execute(query)
                self.conn.commit()
                QMessageBox.about(self, "", "Datos de Fertilizacion guardados correctamente")
                    
                # self.close()
                # self.huellaCarbono()
            except Exception as ex:
                print(ex)
                QgsMessageLog.logMessage(f'{ex}', 'aGrae GIS', level=1)

    def huellaCarbono(self):
        

        # print('huella de carbono')
        data = self.dataExtraccion
        with self.conn.cursor() as cursor: 
            try:
                sql = '''select ca.unidadesnpktradicionales  from campaign."data" d 
                join agrae.agricultor ag on ag.idexplotacion  = d.idexplotacion 
                join agrae.cultivoagricultor ca on ca.idagricultor = ag.idagricultor 
                where d.iddata  = {}'''.format(self.iddata)
                cursor.execute(sql)
                data = cursor.fetchall() 
                # print('PRECALCULO HC',data)
                npk = [str(e[0]) for e in data]
                lista = [e.split('-') for e in npk]
                n = int(lista[0][0])
                p = int(lista[0][1])
                k = int(lista[0][2])
                # print(n,p,k)
                #! CALCULO HUELLA CARBONO FERTILIZACION TRADICIONAL
                huella_carbono_fp = round((n * 4.9500) + (p * 0.7333) + (k * 0.5500))
                # print('**** FERTILIZACION TRADICIONAL:\nCAPTURA HUELLA DE CARBONO: {}  KgCO2eq/ha ****'.format(huella_carbono_fp))
            except ValueError as ve:
                QgsMessageLog.logMessage(f'{ve}', 'aGrae GIS', level=1)
                # QMessageBox.about(self, f"aGrae GIS:",f"No Existen datos de Fertilizacion Tradicional")
                # self.btn_panel.setEnabled(False)
            except Exception as ex: 
                QgsMessageLog.logMessage(f'Exception {ex}', 'aGrae GIS', level=1)





            
            
            #! CALCULO HUELLA CARBONO FERTILIZACION INTRAPARCELARIA
            sql =  aGraeSQLTools().getSql('necesidades_huella_carbono.sql')
            sql = sql.format(self.iddata)
            # print(sql)
            cursor.execute(sql)
            data = cursor.fetchall() 
            # print('DEBUG',data)
            area = [float(e[3]) for e in data]
            n = [int(e[0]) for e in data]
            p = [int(e[1]) for e in data]
            k = [int(e[2]) for e in data]
            # print(n,p,k)

            n_ponderado_ip = self.sumaPonderada(n, area)
            p_ponderado_ip = self.sumaPonderada(p, area)
            k_ponderado_ip  = self.sumaPonderada(k, area)
            # print(n_ponderado_ip, p_ponderado_ip, k_ponderado_ip)

            huella_carbono_fv = round((n_ponderado_ip * 4.9500) + (p_ponderado_ip * 0.7333) + (k_ponderado_ip * 0.5500))

            # print('**** FERTILIZACION VARIABLE:\nCAPTURA HUELLA DE CARBONO: {}  KgCO2eq/ha ****'.format(huella_carbono_fv))

            #! REDUCCION HUELLA DE CARBONO: 
            try: 
                _reduccion = -huella_carbono_fp+huella_carbono_fv
                _percent = round((+_reduccion/huella_carbono_fp)*100)
                # print('**** REDUCCION HUELLA DE CARBONO: {} KgCO2eq/ha o un {} % ****'.format(_reduccion,_percent))


                #! CAPTURA DE CARBONO EN CULTIVO

                x1 = int(round((-float(self.prod) * self.ccosecha )*(44/12)))
                x2 = int(round((-float(self.residuo) * self.cresiduo )*(44/12)))
                ccc =  x1+x2
                chc = -1*(-ccc+_reduccion)
                # print(self.prod, self.ccosecha )
                # print('**** HUELLA DE CARBONO: {} KgCO2eq/ha ****'.format(ccc)) 
                self.lbl_hc_cantidad.setText('{:,} KgCO2/ha'.format(chc))
                self.lbl_hc_percent.setText('Reducción: {}%'.format(_percent))

                self.dataHuellaCarbono = {
                'percent': _percent, #_percent
                'chc': chc, #chc,
                'biomasa': ccc, #ccc,
                'cosecha': x1, #x1,
                'residuo': x2, #x2,
                'fertilizacion': _reduccion  #_reduccion 
                } 

                # print(self.dataHuellaCarbono)
            except Exception as ex:
                QgsMessageLog.logMessage(f'{ex}', 'aGrae GIS', level=1)


    def closeEvent(self, event):
        self.closingPlugin.emit()
        self.sc.close()
        event.accept()


class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None):

        fig, (self.ax1, self.ax2, self.ax3) = plt.subplots(1, 3)
        fig.patch.set_facecolor('None')
        fig.patch.set_alpha(0)
        super(MplCanvas, self).__init__(fig)
        
    def close(self): 
        plt.cla()
    def saveImage(self,path):
        self.ax1.set_title('')  
        self.ax1.set_yticklabels('') 
        self.ax2.set_title('')  
        self.ax2.set_yticklabels('') 
        self.ax3.set_title('')  
        self.ax3.set_yticklabels('') 
        plt.savefig(path)

    def plot(self,data):
        # print(data)
        

        def valores(suelo):
            values = []
            colors = []
            for i in suelo:
                if i == 'Muy Alto':
                    colors.append('#995AE2')
                    values.append(5)
                elif i == 'Alto':
                    colors.append('#5AB8E2')
                    values.append(4)
                elif i == 'Medio':
                    colors.append('#5EE25A')
                    values.append(3)
                elif i == 'Normal':
                    colors.append('#5EE25A')
                    values.append(3)
                
                elif i == 'Bajo':
                    colors.append('#FFAB66')
                    values.append(2)
                elif i == 'Muy Bajo':
                    colors.append('#FF6666')
                    # colors.append('#FF3333')
                    values.append(1)
                else:
                    values.append(0)
            # print(values)
            return values, colors

        def borderless(ax):
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_visible(False)
            ax.spines['left'].set_visible(True)
        
        def barGenerator(ax,values,colors,y,y_pos,title,y_visible=True):
            ax.barh(y_pos, values, align='center', color=colors)
            ax.set_xticks([])
            ax.set_title('{}'.format(title))            
            ax.set_yticks(y_pos)
            ax.set_yticklabels(y, fontsize=8)
            ax.invert_yaxis()  # labels read top-to-bottom
            ax.patch.set_facecolor('None')
            ax.patch.set_alpha(0)
            ax.set_xlim(0, 5)
            borderless(ax)
            if y_visible == False:                
                ax.axes.get_yaxis().set_visible(False)

        def getValues(i):
            try:
                if i <= len(n_values):  
                    values = [n_values[i], p_values[i], k_values[i], carb_values[i]]
                    # print(values)
                else: 
                    values = [0,0,0,0]
                    # print(values)
            except IndexError as ie:
                values = [0,0,0,0]
                # print(values)
                return values

            
            return values   

    

        segmentos = [f[0] for f in data]
        nitrogeno = [f[1] for f in data]
        fosforo = [f[2] for f in data]
        potasio = [f[3] for f in data]
        carbonato = [f[4] for f in data]
        n_values = {segmentos[i]: nitrogeno[i] for i in range(len(segmentos))}
        p_values = {segmentos[i]: fosforo[i] for i in range(len(segmentos))}
        k_values = {segmentos[i]: potasio[i] for i in range(len(segmentos))}
        carb_values = {segmentos[i]: carbonato[i] for i in range(len(segmentos))}
        # print(n_values)

        suelo_1 = getValues(1)
        suelo_2 = getValues(2)
        suelo_3 = getValues(3)

        

        categorias = ('N', 'P', 'K', 'Carb')
        y_pos = np.arange(len(categorias))

        values_1, colors_1 = valores(suelo_1)
        values_2, colors_2 = valores(suelo_2)
        values_3, colors_3 = valores(suelo_3)

        barGenerator(self.ax1,values_3,colors_3,categorias,y_pos,'',False)
        barGenerator(self.ax2,values_2,colors_2,categorias,y_pos,'',False)
        barGenerator(self.ax3, values_1, colors_1,categorias, y_pos, '', False)
        # barGenerator(self.ax1,values_3,colors_3,categorias,y_pos,'Suelo 3',True)
        # barGenerator(self.ax2,values_2,colors_2,categorias,y_pos,'Suelo 2',False)
        # barGenerator(self.ax3, values_1, colors_1,categorias, y_pos, 'Suelo 1', False)