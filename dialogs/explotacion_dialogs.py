
import os
import csv

import time


# from datetime import date
from psycopg2 import InterfaceError, errors, extras

from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtWidgets import (
    QDialog,
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
    QWidget
 
    
    )
from qgis.PyQt.QtCore import pyqtSignal, QSettings, QVariant, Qt, QSize
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
from ..gui.CustomPushButton import CustomPushButton

class CreateExplotacionDialog(QDialog):
    closingPlugin = pyqtSignal()
    expCreated = pyqtSignal(str)
    loteCreated = pyqtSignal(int)
    def __init__(self,idCampania:int):
        super().__init__()
        self.setWindowTitle('Gestion de Explotaciones')
        self.conn = agraeDataBaseDriver().connection()
        self.agraeSql = aGraeSQLTools()
        self.tools = aGraeTools()

        self.idCampania = idCampania
        self.idExplotacion = None


        self.UIComponents()

        self.setFixedSize(QSize(350,300))

    def messages(self,title:str,text:str,level):
        iface.messageBar().pushMessage(title,text,level)
        QgsMessageLog.logMessage(text, title, level)

    def UIComponents(self):
        
        self.layout = QGridLayout()
        self.groupBoxLayout = QGridLayout()
        self.groupBox = QGroupBox()
        self.groupBox.setTitle('Crear Nueva Explotacion')
        self.label_1 = QLabel('Nombre de la nueva Explotacion')
        self.label_1.setMaximumSize(QSize(200,15))
        self.line_nombre = CustomLineEdit()
        # self.line_nombre.textChanged.connect(lambda v: agraeGUI().formatUpper(self.line_nombre,v))

        self.label_2 = QLabel('Direccion de la Explotacion')
        self.text_direccion = QPlainTextEdit()


        self.check_layer = QCheckBox('Crear capa de lotes automaticamente (vacia)')
        self.check_layer.setChecked(True)
        self.btn_create = QPushButton('Crear Explotacion')
        self.btn_create.clicked.connect(self.create)



        self.groupBoxLayout.addWidget(self.label_1,0,0)
        self.groupBoxLayout.addWidget(self.line_nombre,1,0)
        self.groupBoxLayout.addWidget(self.label_2,2,0)
        self.groupBoxLayout.addWidget(self.text_direccion,3,0)

        self.groupBoxLayout.addWidget(self.check_layer,5,0)
        self.groupBoxLayout.addWidget(self.btn_create,6,0)

        self.groupBox.setLayout(self.groupBoxLayout)
        self.layout.addWidget(self.groupBox)
        self.setLayout(self.layout)

        pass
    
    def create(self):
        # print('Creando Explotacion')
        nombre = self.line_nombre.text().upper()
        direccion = self.text_direccion.toPlainText()
        # print(nombre,direccion)
        with self.conn.cursor() as cursor:
            try:
              
                sql = '''insert into agrae.explotacion(nombre,direccion) values('{}','{}') returning idexplotacion'''.format(nombre,direccion)
                cursor.execute(sql)
                self.idExplotacion = cursor.fetchone()[0]

                self.conn.commit()
                self.tools.messages('aGrae Toolbox','Explotacion {} creada exitosamente'.format(nombre),0)
                self.expCreated.emit(nombre)

                if self.check_layer.isChecked():
                    layer = QgsVectorLayer('Polygon?crs=epsg:4036&index=yes','Lotes explotacion: {}'.format(nombre),'memory')
                    layer.afterCommitChanges.connect(lambda: self.saveLotesLayer(layer,self.idExplotacion))
                    provider = layer.dataProvider()

                    provider.addAttributes([
                        QgsField('lote',QVariant.String)
                    ])
                    layer.updateFields()
                    layer.startEditing()
                    iface.actionAddFeature().trigger()

                    QgsProject.instance().addMapLayer(layer)
                    # print('Creando Capa de Nuevos Lotes')
                self.close()
                pass
            except Exception as ex:
                self.conn.rollback()
                self.tools.messages('aGrae Toolbox','Ocurrio un error {}'.format(ex),2)
    
    def saveLotesLayer(self,layer:QgsVectorLayer,idExplotacion:int):
        layer.afterCommitChanges.disconnect()
        features = [f for f in layer.getFeatures()]
        try:
            for f in features:
                geom = f.geometry().asWkt()
                nombre = f['lote']

                sql = '''with new_lote as (insert into agrae.lotes(nombre,geom) values('{}', st_multi(st_geomfromtext('{}',4326))) returning idlote)
                insert into campaign.data(idcampania,idexplotacion,idlote) values({},{},(select idlote from new_lote))'''.format(nombre,geom,self.idCampania,idExplotacion)
                # print(sql)
                with self.conn.cursor() as cursor:
                    cursor.execute(sql)

                    self.conn.commit()

                    # print('lote {} creado y asociado con la campania'.format(nombre))
            self.loteCreated.emit(self.idExplotacion)
            self.tools.messages('aGrae Toolbox','Lotes creados exitosamente',3)

                
        except Exception as ex:
            self.conn.rollback()
            self.tools.messages('aGrae Toolbox','Ocurrio un error {}'.format(ex),2)

        
class UpdateExplotacionDialog(QDialog):
    closingPlugin = pyqtSignal()
    expUpdated = pyqtSignal()
    def __init__(self,idExp:int,name:str):
        super().__init__()
        self.nombreExplotacion = name
        self.idExp = idExp
        self.setWindowTitle('Gestion de Explotaciones')
        self.conn = agraeDataBaseDriver().connection()
        self.agraeSql = aGraeSQLTools()
        self.tools = aGraeTools()
        self.UIComponents()
        self.setFixedSize(QSize(350,300))

        self.getDireccion()
        
        

    def UIComponents(self):
        self.layout = QGridLayout()
        
        self.groupBoxLayout = QGridLayout()
        self.groupBox = QGroupBox()
        self.groupBox.setTitle('Actualizar Explotacion')

        self.label_1 = QLabel('Nombre de la Explotacion')
        self.label_1.setMaximumSize(QSize(200,15))
        self.line_nombre = CustomLineEdit()
        self.line_nombre.setText(self.nombreExplotacion)
        # self.line_nombre.textChanged.connect(lambda v: agraeGUI().formatUpper(self.line_nombre,v))

        self.label_2 = QLabel('Direccion de la Explotacion')
        self.text_direccion = QPlainTextEdit()



        self.btn_upadte = QPushButton('Actualizar Explotacion')
        self.btn_upadte.clicked.connect(self.update)
        

        self.groupBoxLayout.addWidget(self.label_1,0,0)
        self.groupBoxLayout.addWidget(self.line_nombre,1,0)
        self.groupBoxLayout.addWidget(self.label_2,2,0)
        self.groupBoxLayout.addWidget(self.text_direccion,3,0)

        self.groupBoxLayout.addWidget(self.btn_upadte,5,0)


        self.groupBox.setLayout(self.groupBoxLayout)
        self.layout.addWidget(self.groupBox)
        self.setLayout(self.layout)

        pass
    def getDireccion(self):
        sql = '''select direccion from agrae.explotacion where idexplotacion = {}'''.format(self.idExp)
        with self.conn.cursor() as cursor:
            cursor.execute(sql)
            data = cursor.fetchone()

            self.text_direccion.setPlainText(data[0])
    def update(self):
        sql = '''update agrae.explotacion set nombre = '{}', direccion = '{}' where idexplotacion = {} '''.format(self.line_nombre.text().upper(),self.text_direccion.toPlainText(),self.idExp)
        with self.conn.cursor() as cursor:
            try:
              cursor.execute(sql)

              self.conn.commit()
              self.tools.messages('aGrae Toolbox','Explotacion actualizada.',3)
              self.expUpdated.emit()
            except Exception as ex:
                iface.messageBar().pushMessage('aGrae Toolbox','Ocurrio un error. Revisa el Panel de Mensajes del Registro',2,duration=5)
                QgsMessageLog.logMessage('aGrae Toolbox', ex, 2)
                self.conn.rollback()
      
        
    

        # print(layer)


class CopyExplotacionDialog(QDialog):
    expCopied = pyqtSignal()
    def __init__(self,idExp, idCampania, nombre):
        super().__init__()

        self.setWindowTitle('Gestion de Explotaciones')
        self.conn = agraeDataBaseDriver().connection()
        self.idExp = idExp
        self.idCampania = idCampania
        self.nombre = nombre
        self.agraeSql = aGraeSQLTools()
        self.tools = aGraeTools()
        self.UIComponents()

        self.setFixedSize(QSize(350,200))
        self.getCampaniasData()


    def UIComponents(self):
        self.layout = QGridLayout()
        
        self.groupBoxLayout = QGridLayout()
        self.groupBox = QGroupBox()
        self.groupBox.setTitle('Copiar Explotacion')

        self.label_1 = QLabel('Seleccionar Campaña Destino')
        self.label_1.setMaximumSize(QSize(250,15))
        
        self.combo_campanias = QComboBox()

        self.btn_upadte = QPushButton('Copiar Explotacion')
        self.btn_upadte.clicked.connect(self.copyExplotacion)
        

        self.groupBoxLayout.addWidget(self.label_1,0,0)
        self.groupBoxLayout.addWidget(self.combo_campanias,1,0)
        self.groupBoxLayout.addWidget(self.btn_upadte,2,0)


        self.groupBox.setLayout(self.groupBoxLayout)
        self.layout.addWidget(self.groupBox)
        self.setLayout(self.layout)

        pass


    def getCampaniasData(self):
        sql = '''select distinct c.nombre, c.id from campaign.campanias c where id != {}
        '''.format(self.idCampania)

        with self.conn.cursor() as cursor:
            try:
                cursor.execute(sql)
                data = cursor.fetchall()

                for e in data:
                    self.combo_campanias.addItem(e[0],e[1])
                
                self.conn.commit()

            except Exception as ex:
                iface.messageBar().pushMessage('aGrae Toolbox','Ocurrio un error. Revisa el Panel de Mensajes del Registro',2,duration=5)
                QgsMessageLog.logMessage('aGrae Toolbox', str(ex))
                self.conn.rollback()

    
    def copyExplotacion(self):
        
        sql = ''' with exp_data as (select idexplotacion, idlote,idcultivo , idregimen from campaign.data where idcampania = {} and idexplotacion = {})
        insert into campaign.data (idcampania,idexplotacion,idlote,idcultivo,idregimen)
        select {}, * from exp_data'''.format(self.idCampania,self.idExp,self.combo_campanias.currentData())
        
        reply = QMessageBox.question(self,'aGrae Toolbox','Quieres copiar los datos asociados a la explotacion {} a la campaña {}?'.format(self.nombre,self.combo_campanias.currentText()), QMessageBox.Yes, QMessageBox.No)
        
        if reply == QMessageBox.Yes:

            with self.conn.cursor() as cursor: 
                try:
                    cursor.execute(sql)
                    self.conn.commit()
                    self.tools.messages('aGrae Toolbox','Explotacion actualizada.',3)
                    self.expCopied.emit()

                except Exception as ex:
                    iface.messageBar().pushMessage('aGrae Toolbox','Ocurrio un error. Revisa el Panel de Mensajes del Registro',2,duration=5)
                    QgsMessageLog.logMessage('aGrae Toolbox', ex)
                    self.conn.rollback()

class AsignarLotesExplotacion(QDialog):
    closingPlugin = pyqtSignal()
    # idExplotacionSignal = pyqtSignal(list)
    def __init__(self, layer: QgsVectorLayer):
        super().__init__()
        self.layer = layer
        self.setWindowTitle('Asignar Lotes')

        self.UIComponents()

    def UIComponents(self):
        self.layout = QGridLayout()
        
        self.groupBoxLayout = QGridLayout()
        self.groupBox = QGroupBox()
        self.groupBox.setTitle('Asignar Lotes a Explotacion')

        self.label_1 = QLabel('Seleccionar Campo Nombre del Lote')
        self.label_1.setMaximumSize(QSize(250,15))
        
        self.combo_nombre = QgsFieldComboBox()
        self.combo_nombre.setLayer(self.layer)

        self.btn_asignar = QPushButton('Copiar Explotacion')
        # self.btn_upadte.clicked.connect(self.copyExplotacion)
        

        self.groupBoxLayout.addWidget(self.label_1,0,0)
        self.groupBoxLayout.addWidget(self.combo_nombre,1,0)
        self.groupBoxLayout.addWidget(self.btn_asignar,2,0)


        self.groupBox.setLayout(self.groupBoxLayout)
        self.layout.addWidget(self.groupBox)
        self.setLayout(self.layout)

        pass





class GestionExplotacionDialog(QDialog): 
    closingPlugin = pyqtSignal()
    idExplotacionSignal = pyqtSignal(list)

    def __init__(self, parent=None) -> None:
        super(GestionExplotacionDialog,self).__init__(parent)
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'ui/explotacion_dialog.ui'), self)
        # self.setupUi(self)
        self.setWindowTitle('Gestionar Explotaciones')
        self.conn = agraeDataBaseDriver().connection()
        self.agraeSql = aGraeSQLTools()
        self.tools = aGraeTools()
        self.idExplotacion = 0
       

        self.completer = self.tools.dataCompleter('select nombre,direccion from agrae.explotacion')


        self.UIComponents()
        self.getData()

        # self.setFixedSize(QSize(400,250))


    def UIComponents(self):
        self.tabWidget.setCurrentIndex(0)
        self.tabWidget.setTabIcon(0, agraeGUI().getIcon('search'))
        self.tabWidget.setTabIcon(1, agraeGUI().getIcon('pen-to-square'))

        self.tableWidget.setColumnHidden(0, True)
        self.tableWidget.doubleClicked.connect(self.getExplotacionData)

        
        self.ln_search.setCompleter(self.completer)
        self.ln_search.returnPressed.connect(self.getData)
        self.ln_search.textChanged.connect(self.getData)
        self.ln_search.setClearButtonEnabled(True)
        line_buscar_action = self.ln_search.addAction(
            agraeGUI().getIcon('search'), self.ln_search.TrailingPosition)
        line_buscar_action.triggered.connect(self.getData)


        self.btn_save.clicked.connect(self.saveDataExplotacion)
        self.btn_save.setIconSize(QSize(20, 20))
        self.btn_save.setIcon(agraeGUI().getIcon('save'))

        self.btn_delete.clicked.connect(self.deleteExplotacion)
        self.btn_delete.setIconSize(QSize(20, 20))
        self.btn_delete.setIcon(agraeGUI().getIcon('trash'))



        
        pass
    
    def getData(self):
        param = self.ln_search.text()
        if param == '':
            sql =  sql = ''' select e.idexplotacion, e.nombre, e.direccion, count(a.idagricultor) agricultores from agrae.explotacion e
            left join agrae.agricultor a on a.idexplotacion = e.idexplotacion
            group by e.idexplotacion, e.nombre, e.direccion
            order by e.idexplotacion desc   '''
            try:
                self.tools.populateTable(sql, self.tableWidget)
            except IndexError as ie:
                self.conn.rollback()
                pass
            except Exception as ex:
                self.conn.rollback()
                print(ex)
        else:
            sql = ''' select e.idexplotacion,e.nombre,e.direccion , count(a.idagricultor) agricultores from agrae.explotacion e 
            left join agrae.agricultor a on a.idexplotacion = e.idexplotacion 
            where e.nombre ilike '%{}%' or e.direccion ilike '%{}%' 
            group by e.idexplotacion,e.nombre,e.direccion 
            order by e.idexplotacion desc '''.format(param, param, param,param)
            try:
                # print(sql)
                self.tools.populateTable(sql, self.tableWidget)
            except IndexError as ie:
                print(ie)
                self.conn.rollback()
                pass
            except Exception as ex:
                print(ex)
                self.conn.rollback()

    def getExplotacionData(self): 
        with self.conn.cursor() as cursor: 
            try: 
                row = self.tableWidget.currentRow() 
                self.idExplotacion = self.tableWidget.item(row,0).text()
                sql = '''SELECT nombre,direccion
                FROM agrae.explotacion where idexplotacion = {} ; '''.format(self.idExplotacion)
                cursor.execute(sql)
                data = cursor.fetchone()                
                self.ln_name.setText(data[0])
                self.ln_dir.setPlainText(data[1])
                
                


            except Exception as ex:
                print(ex)
                self.conn.rollback()
                pass
            finally:
                self.tabWidget.setCurrentIndex(1)
                pass
    
        
    def saveDataExplotacion(self):
        nombre = self.ln_name.text()
        direccion = self.ln_dir.toPlainText()
        
        if nombre != '' and direccion != '':
            try:
                sql = '''with data as (select '{}' as nombre, '{}' as direccion)
                    INSERT INTO agrae.explotacion (nombre,direccion)
                    select * from data
                    ON CONFLICT(nombre,direccion) 
                    DO UPDATE SET
                    nombre = (select nombre from data),
                    direccion = (select direccion from data)
                    where agrae.explotacion.idexplotacion = {} ;'''.format(nombre,direccion,self.idExplotacion)
                # print(sql)
                with self.conn.cursor() as cursor:
                    cursor.execute(sql)
                    self.conn.commit()
                    QgsMessageLog.logMessage("Explotacion {} creada correctamente".format(nombre), 'aGrae GIS', level=3)
                    QMessageBox.about(self, "aGrae GIS:", "Explotacion {} creada correctamente".format(nombre))
                    self.tools.clearWidget([
                        self.ln_name, 
                        self.ln_dir
                    ])
                    self.getData()
                
            except Exception as ex:
                QgsMessageLog.logMessage("{}".format(ex), 'aGrae GIS', level=1)
                QMessageBox.about(self, "aGrae GIS:", "Ocurrio un Error, revisar el panel de registros.".format())
                self.conn.rollback()

    def deleteExplotacion(self):
        row = self.tableWidget.currentRow()
        with self.conn.cursor() as cursor: 
            try:
                id = self.tableWidget.item(row,0).text()
                nombre = self.tableWidget.item(row,2).text()
                # print(id)
                sql = '''DELETE FROM agrae.explotacion
                WHERE idexplotacion ={};
                '''.format(id)
                question = 'Quieres eliminar la Explotacion {}?, esta acción eliminará\nsolo los datos asociados a la campaña seleccionada.'.format(nombre)
                self.tools.deleteAction(question,sql)

                
            except  errors.lookup('23503'):
                QgsMessageLog.logMessage("Explotacion {} esta referido en otras tablas".format(nombre), 'aGrae GIS', level=1)
                QMessageBox.about(self, "aGrae GIS:", "No se puede borrar la Explotacion {}.".format(nombre))
                self.conn.rollback()
            except Exception as ex:
                QgsMessageLog.logMessage("{}".format(ex), 'aGrae GIS', level=1)
                QMessageBox.about(self, "aGrae GIS:", "Ocurrio un Error, revisar el panel de registros.".format())
                self.conn.rollback()
            finally:
                self.getData()
                pass
        pass

    
    def getExplotacionAgricultor(self):
         row = self.tableWidget.currentRow()
         id = self.tableWidget.item(row,0).text()
         name = self.tableWidget.item(row,1).text()
         self.idExplotacionSignal.emit([int(id),name])
         self.close()

    def getExplotacionCampania(self):
        row = self.tableWidget.currentRow()
        id = self.tableWidget.item(row,0).text()
        self.idExplotacionSignal.emit([int(id)])
        self.close()

        

    def closeEvent(self,event):
        self.closingPlugin.emit()
        event.accept()
        




class GestionarExplotacionesDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.tools = aGraeTools()
        self.conn = agraeDataBaseDriver().connection()
        self.completer = self.tools.dataCompleter('select nombre,direccion from agrae.explotacion')
        self.idExplotacion = None
        self.UIComponents()
        self.getData()

    
    def UIComponents(self):
        self.setMinimumSize(QSize(600,350))
        self.setWindowTitle('Gestion de Explotaciones')
        self.setWindowIcon(agraeGUI().getIcon('explotacion'))
        self.tabWidget = QTabWidget()
        

        widgetConsulta = QWidget()
        layoutConsulta = QGridLayout()
        columnsLabels = ['id','Nombre','Direccion','Agricultores']
        self.tableWidget = CustomTable(widgetConsulta,['id','Nombre','Agricultores','Direccion'])
        self.tableWidget.doubleClicked.connect(self.getExplotacionData)

        self.ln_search = CustomLineSearch(self.completer,self.getData,placeholder='Ingresa el Nombre o Direccion de la explotacion a buscar')
        self.btn_delete = CustomPushButton(widgetConsulta,icon=agraeGUI().getIcon('trash'),action=self.delete)

        

        layoutConsulta.addWidget(self.ln_search,0,0,1,1)
        layoutConsulta.addWidget(self.tableWidget,1,0)
        layoutConsulta.addWidget(self.btn_delete,1,2)
        widgetConsulta.setLayout(layoutConsulta)
        self.tabWidget.addTab(widgetConsulta,agraeGUI().getIcon('search'),'Consultar')

        widgetEdicion = QWidget()
        layoutEdicion = QHBoxLayout()
        layoutGroup = QGridLayout()
        groupEdicion = QGroupBox('Formulario de Registro')
        self.ln_name = CustomLineEdit()
        self.ln_dir = QPlainTextEdit()
        self.btn_create = CustomPushButton(widgetEdicion,icon=agraeGUI().getIcon('save'),action=self.create)

        layoutGroup.addWidget(QLabel('Nombre Explotacion:'),0,0)
        layoutGroup.addWidget(self.ln_name,1,0)
        layoutGroup.addWidget(QLabel('Direccion Explotacion:'),2,0)
        layoutGroup.addWidget(self.ln_dir,3,0)


        layoutEdicion.addWidget(groupEdicion)
        layoutEdicion.addWidget(self.btn_create)
        groupEdicion.setLayout(layoutGroup)
        widgetEdicion.setLayout(layoutEdicion)

        self.tabWidget.addTab(widgetEdicion,agraeGUI().getIcon('edit'),'Crear o Modificar')

        self.tabWidget.currentChanged.connect(self.clean)
        

        # self.tab.addTab(QWidget(),'Crear o Modificar')

        grid_layout = QGridLayout()
        central_layout = QVBoxLayout()

        central_layout.addWidget(self.tabWidget)
        self.setLayout(central_layout)



    def getData(self):
        param = str(self.ln_search.text()).rstrip()
        if param == '':
            sql =  sql = ''' select e.idexplotacion, e.nombre,count(a.idagricultor) agricultores, e.direccion from agrae.explotacion e
            left join agrae.agricultor a on a.idexplotacion = e.idexplotacion
            group by e.idexplotacion, e.nombre, e.direccion
            order by e.idexplotacion desc   '''
            try:
                self.tools.populateTable(sql, self.tableWidget)
            except IndexError as ie:
                self.conn.rollback()
                pass
            except Exception as ex:
                self.conn.rollback()
                print(ex)
        else:
            sql = ''' select e.idexplotacion,e.nombre, count(a.idagricultor) agricultores, e.direccion from agrae.explotacion e 
            left join agrae.agricultor a on a.idexplotacion = e.idexplotacion 
            where e.nombre ilike '%{}%' or e.direccion ilike '%{}%' 
            group by e.idexplotacion,e.nombre,e.direccion 
            order by e.idexplotacion desc '''.format(param, param)
            try:
                # print(sql)
                self.tools.populateTable(sql, self.tableWidget)
            except IndexError as ie:
                print(ie)
                self.conn.rollback()
                pass
            except Exception as ex:
                print(ex)
                self.conn.rollback()
        
    def create(self):
        nombre = self.ln_name.text()
        direccion = self.ln_dir.toPlainText()
        
        
        try:
            if nombre != '' and direccion != '' and  self.idExplotacion == None:
                # sql = '''with data as (select '{}' as nombre, '{}' as direccion)
                #     INSERT INTO agrae.explotacion (nombre,direccion)
                #     select * from data
                #     ON CONFLICT(nombre,direccion) 
                #     DO UPDATE SET
                #     nombre = (select nombre from data),
                #     direccion = (select direccion from data)
                #     where agrae.explotacion.idexplotacion = {} ;'''.format(nombre,direccion,self.idExplotacion)
                sql = '''with data as (select '{}' as nombre, '{}' as direccion)
                    INSERT INTO agrae.explotacion (nombre,direccion)
                    select * from data
                    '''.format(nombre,direccion,self.idExplotacion)
                # print(sql)
            if nombre != '' and direccion != '' and self.idExplotacion != None:
                sql = '''
                with data as (select '{}' as nombre, '{}' as direccion)
                update agrae.explotacion set
                nombre = (select nombre from data),
                direccion = (select direccion from data)
                where agrae.explotacion.idexplotacion = {};
                '''.format(nombre,direccion,self.idExplotacion)
                
            with self.conn.cursor() as cursor:
                cursor.execute(sql)
                self.conn.commit()
                QgsMessageLog.logMessage("Explotacion {} creada correctamente".format(nombre), 'aGrae GIS', level=3)
                QMessageBox.about(self, "aGrae GIS:", "Explotacion {} creada correctamente".format(nombre))
                self.tools.clearWidget([
                    self.ln_name, 
                    self.ln_dir
                ])
                self.getData()
            
        except Exception as ex:
            # print(ex)
            QgsMessageLog.logMessage("{}".format(ex), 'aGrae GIS', level=1)
            QMessageBox.about(self, "aGrae GIS:", "Ocurrio un Error, revisar el panel de registros.".format())
            self.conn.rollback()

        finally:
            self.tabWidget.setCurrentIndex(0)


        

        

    def delete(self):
        row = self.tableWidget.currentRow()

        try:
            id = self.tableWidget.item(row,0).text()
            nombre = self.tableWidget.item(row,1).text()
            sql = '''DELETE FROM agrae.explotacion
            WHERE idexplotacion ={};
            '''.format(id)
            question = 'Quieres eliminar la Explotacion {}?, esta acción eliminará\nsolo los datos asociados a la campaña seleccionada.'.format(nombre)
            self.tools.deleteAction(question,sql)

        except  errors.lookup('23503'):
            QgsMessageLog.logMessage("Explotacion {} esta referido en otras tablas".format(nombre), 'aGrae GIS', level=1)
            QMessageBox.about(self, "aGrae GIS:", "No se puede borrar la Explotacion {}.".format(nombre))
            self.conn.rollback()
        except Exception as ex:
            QgsMessageLog.logMessage("{}".format(ex), 'aGrae GIS', level=1)
            QMessageBox.about(self, "aGrae GIS:", "Ocurrio un Error, revisar el panel de registros.".format())
            self.conn.rollback()
        finally:
            self.getData()

    def getExplotacionData(self): 
        with self.conn.cursor() as cursor: 
            try: 
                row = self.tableWidget.currentRow() 
                self.idExplotacion = self.tableWidget.item(row,0).text()
                sql = '''SELECT nombre,direccion
                FROM agrae.explotacion where idexplotacion = {} ; '''.format(self.idExplotacion)
                cursor.execute(sql)
                data = cursor.fetchone()                
                self.ln_name.setText(data[0])
                self.ln_dir.setPlainText(data[1])
                
                


            except Exception as ex:
                print(ex)
                self.conn.rollback()
                pass
            finally:
                self.tabWidget.setCurrentIndex(1)
                pass

    def clean(self):
        if self.tabWidget.currentIndex() == 0:
            self.ln_name.clear()
            self.ln_dir.clear()
      