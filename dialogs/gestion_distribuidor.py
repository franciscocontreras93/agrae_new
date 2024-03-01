import os
# from datetime import date
from psycopg2 import errors, Binary
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtCore import pyqtSignal, QSize, QDate
from qgis.core import *
from qgis.PyQt import uic

from ..gui import agraeGUI
from ..db import agraeDataBaseDriver
from ..sql import aGraeSQLTools
from ..tools import aGraeTools

agraeDistribuidorDialog_ , _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'ui/distribuidor_dialog.ui'))

class GestionDistribuidorDialog(QDialog,agraeDistribuidorDialog_): 
    closingPlugin = pyqtSignal()
    idDistribuidorSignal = pyqtSignal(list)
    def __init__(self, parent=None) -> None:
        super(GestionDistribuidorDialog,self).__init__(parent)
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'ui/distribuidor_dialog.ui'), self)
        # self.setupUi(self)
        self.setWindowTitle('Gestionar Distribuidores')
        self.conn = agraeDataBaseDriver().connection()
        self.agraeSql = aGraeSQLTools()
        self.tools = aGraeTools()
        self.idDistribuidor = None
        self.iconDist = ''
       

        self.completer = self.tools.dataCompleter('select cif,nombre,personacontacto from agrae.distribuidor')

        self.currentDate = QDate().currentDate()

        self.UIComponents()
        self.getData()

        # self.setFixedSize(QSize(400,250))


    def UIComponents(self):
        self.date_start.setDate(self.currentDate)
        self.tabWidget.setCurrentIndex(0)
        self.tabWidget.setTabIcon(0, agraeGUI().getIcon('search'))
        self.tabWidget.setTabIcon(1, agraeGUI().getIcon('pen-to-square'))

        self.tableWidget.setColumnHidden(0, True)
        self.tableWidget.doubleClicked.connect(self.getDistribuidorData)


        self.ln_search.setCompleter(self.completer)
        self.ln_search.returnPressed.connect(self.getData)
        self.ln_search.textChanged.connect(self.getData)
        self.ln_search.setClearButtonEnabled(True)
        line_buscar_action = self.ln_search.addAction(
            agraeGUI().getIcon('search'), self.ln_search.TrailingPosition)
        line_buscar_action.triggered.connect(self.getData)


        self.btn_save.clicked.connect(self.saveDataDistribuidor)
        self.btn_save.setIconSize(QSize(20, 20))
        self.btn_save.setIcon(agraeGUI().getIcon('save'))

        self.btn_delete.clicked.connect(self.deleteDistribuidor)
        self.btn_delete.setIconSize(QSize(20, 20))
        self.btn_delete.setIcon(agraeGUI().getIcon('trash'))


        line_open_dialog = self.ln_image.addAction(agraeGUI().getIcon('image'),self.ln_image.TrailingPosition)
        line_open_dialog.triggered.connect(self.openImageDialog)
        
        pass
    
    def getData(self):
        param = self.ln_search.text()
        if param == '':
            sql =  sql = ''' select d.iddistribuidor, d.cif,d.nombre,d.personacontacto,d.telefono,d.email,d.direccionfiscal,d.direccionenvio,d.fechainicio from agrae.distribuidor d   '''
            try:
                self.tools.populateTable(sql, self.tableWidget)
            except IndexError as ie:
                self.conn.rollback()
                pass
            except Exception as ex:
                self.conn.rollback()
                print(ex)
        else:
            sql = ''' select d.iddistribuidor, d.cif,d.nombre,d.personacontacto,d.telefono,d.email,d.direccionfiscal,d.direccionenvio,d.fechainicio 
            from agrae.distribuidor d 
            where d.cif ilike  '%{}%' 
            or d.nombre ilike '%{}%' 
            or d.personacontacto ilike '%{}%' 
            or d.direccionfiscal ilike '%{}%' '''.format(param, param, param,param)
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

    def getDistribuidorData(self): 
        with self.conn.cursor() as cursor: 
            try: 
                row = self.tableWidget.currentRow() 
                self.idDistribuidor = self.tableWidget.item(row,0).text()
                sql = '''SELECT cif,nombre,personacontacto,telefono,email,fechainicio,direccionfiscal,direccionenvio,imagen,icono
                FROM agrae.distribuidor where iddistribuidor = {} ; '''.format(self.idDistribuidor)
                cursor.execute(sql)
                data = cursor.fetchone()                
                self.ln_cif.setText(data[0])
                self.ln_name.setText(data[1])
                self.ln_contact.setText(data[2])
                self.ln_phone.setText(data[3])
                self.ln_email.setText(data[4])
                self.date_start.setDate(QDate(data[5]))
                self.ln_dir_fiscal.setPlainText(data[6])
                self.ln_dir_envio.setPlainText(data[7])
                self.iconDist = Binary(bytes(data[8]))
                self.ln_image.setText(data[9])


            except Exception as ex:
                print(ex)
                self.conn.rollback()
                pass
            finally:
                self.tabWidget.setCurrentIndex(1)
                pass
    
    def openImageDialog(self): 
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(
            self, "aGrae GIS", "", "Todos los archivos (*);;PNG(*.png);;JPG(*.jpg)", options=options)
        if fileName:
            path = fileName.split('/')
            file = path[-1]
            self.ln_image.setText(file)
            self.iconDist = fileName
        else:
            return False 
        
    def saveDataDistribuidor(self):

        if not isinstance(self.iconDist,Binary):
            bin = self.tools.processImageToBytea(self.iconDist)
        else:
            bin = self.iconDist



        with self.conn.cursor() as cursor: 
            try: 
                CIF = self.ln_cif.text()
                NOMBRE = self.ln_name.text()
                CONTACTO = self.ln_contact.text()
                ICONO = self.ln_image.text()
                DIRECCIONFISCAL = self.ln_dir_fiscal.toPlainText()
                DIRECCIOENVIO = self.ln_dir_envio.toPlainText()
                TELEFONO = self.ln_phone.text()
                EMAIL = self.ln_email.text()
                FECHAINICIO = self.date_start.date().toString("yyyy/MM/dd")
                               
               
                if self.iconDist != '':
                    sql = '''with data as (select '{}' as cif, '{}' as nombre, '{}' as personacontacto, '{}' as telefono,'{}' as email,'{}'::date as fechainicio,'{}' as direccionfiscal, '{}' as direccionenvio, {} as imagen,'{}' as icono)
                    INSERT INTO agrae.distribuidor (cif,nombre,personacontacto,telefono,email,fechainicio,direccionfiscal,direccionenvio,imagen,icono)
                    select * from data
                    ON CONFLICT(cif) 
                    DO UPDATE SET
                    nombre = (select nombre from data),
                    personacontacto = (select personacontacto from data),
                    telefono = (select telefono from data),
                    email = (select email from data),
                    fechainicio = (select fechainicio from data),
                    direccionfiscal = (select direccionfiscal from data),
                    direccionenvio = (select direccionenvio from data),
                    imagen = (select imagen from data)
                    where agrae.distribuidor.cif = (select cif from data) ;'''.format(CIF.upper(),NOMBRE.upper(),CONTACTO.upper(),TELEFONO,EMAIL,FECHAINICIO,DIRECCIONFISCAL,DIRECCIOENVIO,bin,ICONO)
                    cursor.execute(sql)
                    self.conn.commit()
                    QMessageBox.about(self, "", "Datos Guardados Correctamente")
                    # print(sql)
                    self.getData()
                    self.tabWidget.setCurrentIndex(0)
                    self.tools.clearWidget(
                        [
                        self.ln_cif,
                        self.ln_name,
                        self.ln_contact,
                        self.ln_image,
                        self.ln_dir_fiscal,
                        self.ln_dir_envio,
                        self.ln_phone,
                        self.ln_email,
                        ]
                    )
                    self.date_start.setDate(self.currentDate)
                else: 
                    QMessageBox.about(self, "aGrae GIS:", "Debe cargar un logo para el cliente.".format())
                
                

            except Exception as ex: 
                QgsMessageLog.logMessage("{}".format(ex), 'aGrae GIS', level=1)
                QMessageBox.about(self, "aGrae GIS:", "Ocurrio un Error, revisar el panel de registros.".format())
                self.conn.rollback()

    def deleteDistribuidor(self):
        row = self.tableWidget.currentRow()
        with self.conn.cursor() as cursor: 
            try:
                id = self.tableWidget.item(row,0).text()
                nombre = self.tableWidget.item(row,2).text()
                # print(id)
                sql = '''DELETE FROM agrae.distribuidor
                WHERE iddistribuidor ={};
                '''.format(id)
                cursor.execute(sql)
                self.conn.commit() 
                QgsMessageLog.logMessage("Distribuidor {} eliminada correctamente".format(nombre), 'aGrae GIS', level=3)
                QMessageBox.about(self, "aGrae GIS:", "El Distribuidor {} se elimino correctamente".format(nombre))
                
            except  errors.lookup('23503'):
                QgsMessageLog.logMessage("El Distribuidor {} esta referido en otras tablas".format(nombre), 'aGrae GIS', level=1)
                QMessageBox.about(self, "aGrae GIS:", "No se puede borrar al Distribuidor {}.".format(nombre))
                self.conn.rollback()
            except Exception as ex:
                QgsMessageLog.logMessage("{}".format(ex), 'aGrae GIS', level=1)
                QMessageBox.about(self, "aGrae GIS:", "Ocurrio un Error, revisar el panel de registros.".format())
                self.conn.rollback()
            finally:
                self.getData()
                pass
        pass

    
    def getDistribuidorAgricultor(self):
         row = self.tableWidget.currentRow()
         id = self.tableWidget.item(row,0).text()
         name = self.tableWidget.item(row,2).text()
         self.idDistribuidorSignal.emit([int(id),name])
         self.close()


        

    def closeEvent(self,event):
        self.closingPlugin.emit()
        event.accept()