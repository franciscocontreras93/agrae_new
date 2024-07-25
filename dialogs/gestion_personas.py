import os
import csv
import string

import time


# from datetime import date
from psycopg2 import InterfaceError, errors, extras
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtCore import pyqtSignal, QSettings, QVariant, Qt, QSize, QDate
from qgis.core import *
from qgis.utils import iface
from qgis.PyQt.QtXml import QDomDocument
from qgis.PyQt import uic

from ..gui import agraeGUI
from ..db import agraeDataBaseDriver
from ..sql import aGraeSQLTools
from ..tools import aGraeTools

agraePersonasDialog_ , _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'ui/personas_dialog.ui'))

class GestionPersonasDialog(QDialog,agraePersonasDialog_): 
    closingPlugin = pyqtSignal()
    idPersonaSignal = pyqtSignal(list)
    def __init__(self, parent=None) -> None:
        super(GestionPersonasDialog,self).__init__(parent)
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'ui/personas_dialog.ui'), self)
        # self.setupUi(self)
        self.setWindowTitle('Gestionar Personas')
        self.conn = agraeDataBaseDriver().connection()
        self.agraeSql = aGraeSQLTools()
        self.tools = aGraeTools()
        self.idPersona = None

        self.completer = self.tools.dataCompleter('select nombre, apellidos, direccion from agrae.persona')

        self.currentDate = QDate().currentDate()

        self.UIComponents()
        self.getData()

        # self.setFixedSize(QSize(400,250))


    def UIComponents(self):
        self.tabWidget.setCurrentIndex(0)
        self.tabWidget.setTabIcon(0, agraeGUI().getIcon('search'))
        self.tabWidget.setTabIcon(1, agraeGUI().getIcon('pen-to-square'))

        self.tableWidget.setColumnHidden(0, True)
        self.tableWidget.doubleClicked.connect(self.getPersonData)


        self.ln_search.setCompleter(self.completer)
        self.ln_search.returnPressed.connect(self.getData)
        self.ln_search.textChanged.connect(self.getData)
        self.ln_search.setClearButtonEnabled(True)
        line_buscar_action = self.ln_search.addAction(
            agraeGUI().getIcon('search'), self.ln_search.TrailingPosition)
        line_buscar_action.triggered.connect(self.getData)


        self.btn_save.clicked.connect(self.saveDataPersona)
        self.btn_save.setIconSize(QSize(20, 20))
        self.btn_save.setIcon(agraeGUI().getIcon('save'))

        self.btn_delete.clicked.connect(self.deletePersona)
        self.btn_delete.setIconSize(QSize(20, 20))
        self.btn_delete.setIcon(agraeGUI().getIcon('trash'))
        
        pass
    
    def getData(self):
        param = self.ln_search.text()
        if param == '':
            sql = ''' select idpersona, dni, nombre || ' ' || apellidos from agrae.persona p   '''
            try:
                self.tools.populateTable(sql, self.tableWidget)
            except IndexError as ie:
                pass
            except Exception as ex:
                print(ex)
        else:
            sql = ''' select idpersona, dni, nombre || ' ' || apellidos  from agrae.persona p where p.dni = '{}' or p.nombre ilike '%{}%' or apellidos ilike '%{}%' or p.direccion ilike '%{}%' '''.format(param, param, param,param)
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

    def getPersonData(self): 
        with self.conn.cursor() as cursor: 
            try: 
                row = self.tableWidget.currentRow() 
                self.idPersona = self.tableWidget.item(row,0).text()
                sql = '''SELECT dni, nombre, apellidos, telefono, email,direccion
                FROM agrae.persona where idpersona = {} ; '''.format(self.idPersona)
                cursor.execute(sql)
                data = cursor.fetchone()
                self.ln_dni.setText(data[0])
                self.ln_name.setText(data[1])
                self.ln_last_name.setText(data[2])
                self.ln_phone.setText(data[3])
                self.ln_email.setText(data[4])
                self.ln_dir.setPlainText(data[5])


            except Exception as ex:
                print(ex)
                self.conn.rollback()
                pass
            finally:
                self.tabWidget.setCurrentIndex(1)
                pass
    
    
    def saveDataPersona(self):
         with self.conn.cursor() as cursor: 
            try: 
                DNI = self.ln_dni.text()
                NOMBRE = self.ln_name.text()
                APELLIDO = self.ln_last_name.text()
                DIRECCION = self.ln_dir.toPlainText()
                TELEFONO = self.ln_phone.text()
                EMAIL = self.ln_email.text()
                
                if self.idPersona == None:
                    sql = '''with data as (select '{}' as dni, '{}' as nombre, '{}' as apellidos, '{}' as direccion, '{}' as telefono, '{}' as email)
                    INSERT INTO agrae.persona (dni,nombre,apellidos,direccion,telefono,email)
                    select dni,nombre,apellidos,direccion,telefono,email from data
                    ON CONFLICT(dni) 
                    DO UPDATE SET
                    nombre = (select nombre from data),
                    apellidos = (select apellidos from data),
                    direccion = (select direccion from data),
                    telefono = (select telefono from data),
                    email = (select email from data)
                    where agrae.persona.dni = (select dni from data) ;'''.format(DNI.upper(),NOMBRE.upper(),APELLIDO.upper(),DIRECCION,TELEFONO,EMAIL)
                
                else:

                    sql = '''with data as (select '{}' as dni, '{}' as nombre, '{}' as apellidos, '{}' as direccion, '{}' as telefono, '{}' as email)
                    UPDATE agrae.persona SET
                    dni = (select dni from data),
                    nombre = (select nombre from data),
                    apellidos = (select apellidos from data),
                    direccion = (select direccion from data),
                    telefono = (select telefono from data),
                    email = (select email from data)
                    where idpersona = {} ;'''.format(DNI.upper(),NOMBRE.upper(),APELLIDO.upper(),DIRECCION,TELEFONO,EMAIL,self.idPersona)


                
                cursor.execute(sql)
                self.conn.commit()
                QMessageBox.about(self, "", "Datos Guardados Correctamente")
                # print(sql)
                self.getData()
                self.tabWidget.setCurrentIndex(0)
                # self.clearData()

                self.tools.clearWidget([
                    self.ln_dni,
                    self.ln_name,
                    self.ln_last_name,
                    self.ln_phone,
                    self.ln_email,
                    self.ln_dir
                ])
                
                

            except Exception as ex: 
                QgsMessageLog.logMessage("{}".format(ex), 'aGrae GIS', level=1)
                QMessageBox.about(self, "aGrae GIS:", "Ocurrio un Error, revisar el panel de registros.".format())
                self.conn.rollback()

    def deletePersona(self):
        row = self.tableWidget.currentRow()
        with self.conn.cursor() as cursor: 
            try:
                id = self.tableWidget.item(row,0).text()
                nombre = self.tableWidget.item(row,2).text()
                # print(id)
                sql = '''DELETE FROM agrae.persona
                WHERE idpersona={};
                '''.format(id)
                cursor.execute(sql)
                self.conn.commit() 
                QgsMessageLog.logMessage("Persona {} eliminada correctamente".format(nombre), 'aGrae GIS', level=3)
                QMessageBox.about(self, "aGrae GIS:", "La Persona {} se elimino correctamente".format(nombre))
                
            except  errors.lookup('23503'):
                QgsMessageLog.logMessage("La persona {} esta referida en otras tablas".format(nombre), 'aGrae GIS', level=1)
                QMessageBox.about(self, "aGrae GIS:", "No se puede borrar a la persona {}.".format(nombre))
                self.conn.rollback()
            except Exception as ex:
                QgsMessageLog.logMessage("{}".format(ex), 'aGrae GIS', level=1)
                QMessageBox.about(self, "aGrae GIS:", "Ocurrio un Error, revisar el panel de registros.".format())
                self.conn.rollback()
            finally:
                self.getData()
                pass
        pass

    
    def getPersonaAgricultor(self):
         row = self.tableWidget.currentRow()
         id = self.tableWidget.item(row,0).text()
         name = self.tableWidget.item(row,2).text()
         self.idPersonaSignal.emit([int(id),name])
         self.close()

        

    def closeEvent(self,event):
        self.closingPlugin.emit()
        event.accept()