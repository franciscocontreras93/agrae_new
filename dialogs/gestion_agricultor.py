import os

# from datetime import date
from psycopg2 import errors,  Binary


from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtCore import pyqtSignal, QSize, QDate
from qgis.core import *
from qgis.PyQt import uic

from ..gui import agraeGUI
from ..db import agraeDataBaseDriver
from ..sql import aGraeSQLTools
from ..tools import aGraeTools

from .gestion_personas import GestionPersonasDialog
from .explotacion_dialogs import GestionExplotacionDialog
from .gestion_distribuidor import GestionDistribuidorDialog


agraeDistribuidorDialog_ , _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'ui/agricultor_dialog.ui'))

class GestionAgricultorDialog(QDialog,agraeDistribuidorDialog_): 
    closingPlugin = pyqtSignal()
    def __init__(self, parent=None) -> None:
        super(GestionAgricultorDialog,self).__init__(parent)
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'ui/agricultor_dialog.ui'), self)
        # self.setupUi(self)
        self.setWindowTitle('Gestionar Agricultores')
        self.conn = agraeDataBaseDriver().connection()
        self.agraeSql = aGraeSQLTools()
        self.tools = aGraeTools()
        self.idPersona = None
        self.idExplotacion = None
        self.idDistribuidor = None
        self.idAgricultor = 0
        self.nombreAgricultor = None
       

        self.completer = self.tools.dataCompleter('''select p.nombre || ' ' || p.apellidos, e.nombre, d.nombre from agrae.agricultor a 
            left join agrae.explotacion e on a.idexplotacion = e.idexplotacion 
            left join agrae.persona p on p.idpersona = a.idpersona
            left join agrae.distribuidor d on d.iddistribuidor = a.iddistribuidor''')

        self.currentDate = QDate().currentDate()

        self.UIComponents()
        self.getData()

        # self.setFixedSize(QSize(400,250))


    def UIComponents(self):
        self.date_cultivo.setDate(QDate().currentDate())

        self.tabWidget.setCurrentIndex(0)
        self.tabWidget.setTabIcon(0, agraeGUI().getIcon('search'))
        self.tabWidget.setTabIcon(1, agraeGUI().getIcon('pen-to-square'))
        self.tabWidget.setTabIcon(2, agraeGUI().getIcon('cultivo'))
        self.tabWidget.setTabEnabled(2,False)


        self.tableWidget.setColumnHidden(0, True)
        self.tableWidget.doubleClicked.connect(self.getAgricultorData)


        self.tableWidget_2.setColumnHidden(0,True)
        self.tableWidget_2.setColumnHidden(1,True)
        self.tableWidget_2.setColumnHidden(2,True)
        self.tableWidget_2.doubleClicked.connect(self.getCultivoAgricultorData)

        self.ln_search.setCompleter(self.completer)
        self.ln_search.returnPressed.connect(self.getData)
        self.ln_search.textChanged.connect(self.getData)
        self.ln_search.setClearButtonEnabled(True)
        ln_search_action = self.ln_search.addAction(
            agraeGUI().getIcon('search'), self.ln_search.TrailingPosition)
        ln_search_action.triggered.connect(self.getData)

        self.btn_save.setEnabled(False)


        self.btn_save.clicked.connect(self.saveDataAgricultor)
        self.btn_save.setIconSize(QSize(20, 20))
        self.btn_save.setIcon(agraeGUI().getIcon('save'))

        self.btn_delete.clicked.connect(self.deleteAgricultor)
        self.btn_delete.setIconSize(QSize(20, 20))
        self.btn_delete.setIcon(agraeGUI().getIcon('trash'))
        
        self.btn_save_agri_cult.clicked.connect(self.saveCultivoAgricultor)
        self.btn_save_agri_cult.setIconSize(QSize(20, 20))
        self.btn_save_agri_cult.setIcon(agraeGUI().getIcon('save'))

        self.btn_delete_agri_cult.clicked.connect(self.deleteCultivoAgricultor)
        self.btn_delete_agri_cult.setIconSize(QSize(20, 20))
        self.btn_delete_agri_cult.setIcon(agraeGUI().getIcon('trash'))


        ln_persona_action = self.ln_persona.addAction(
            agraeGUI().getIcon('user'), self.ln_persona.TrailingPosition)
        ln_persona_action.triggered.connect(self.personaDialog)

        ln_explotacion_action = self.ln_explotacion.addAction(
            agraeGUI().getIcon('explotacion'), self.ln_explotacion.TrailingPosition)
        ln_explotacion_action.triggered.connect(self.explotacionDialog)

        ln_distribuidor_action = self.ln_distribuidor.addAction(
            agraeGUI().getIcon('handshake'), self.ln_distribuidor.TrailingPosition)
        ln_distribuidor_action.triggered.connect(self.distribuidorDialog)


        


    
        pass
    
    def getData(self):
        param = self.ln_search.text()
        if param == '':
            sql =  sql = ''' select a.idagricultor, p.dni, p.nombre || ' ' || p.apellidos nombre, e.nombre explotacion, d.nombre as distribuidor from agrae.agricultor a 
            left join agrae.explotacion e on a.idexplotacion = e.idexplotacion 
            left join agrae.persona p on p.idpersona = a.idpersona
            left join agrae.distribuidor d on d.iddistribuidor = a.iddistribuidor
            order by a.idagricultor desc   '''
            try:
                self.tools.populateTable(sql, self.tableWidget)
            except IndexError as ie:
                self.conn.rollback()
                pass
            except Exception as ex:
                self.conn.rollback()
                print(ex)
        else:
            sql = ''' select a.idagricultor, p.dni, p.nombre || ' ' || p.apellidos nombre, e.nombre explotacion, d.nombre as distribuidor from agrae.agricultor a 
            left join agrae.explotacion e on a.idexplotacion = e.idexplotacion 
            left join agrae.persona p on p.idpersona = a.idpersona
            left join agrae.distribuidor d on d.iddistribuidor = a.iddistribuidor 
            where a.nombre ilike '%{}%'  or e.nombre ilike '%{}%' or d.nombre ilike '%{}%'
            order by a.idagricultor desc '''.format(param, param, param,param)
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

    def getAgricultorData(self): 
        with self.conn.cursor() as cursor: 
            try: 
                row = self.tableWidget.currentRow() 
                self.idAgricultor = self.tableWidget.item(row,0).text()
                sql = '''select a.idagricultor, p.idpersona, e.idexplotacion,d.iddistribuidor, p.nombre || ' ' || p.apellidos nombre, e.nombre explotacion, d.nombre as distribuidor from agrae.agricultor a 
                left join agrae.explotacion e on a.idexplotacion = e.idexplotacion 
                left join agrae.persona p on p.idpersona = a.idpersona
                left join agrae.distribuidor d on d.iddistribuidor = a.iddistribuidor
                where a.idagricultor = {} ; '''.format(self.idAgricultor)
                cursor.execute(sql)
                data = cursor.fetchone()    
                self.idAgricultor = data[0]
                self.idPersona = data[1]
                self.idExplotacion = data[2]
                self.idDistribuidor = data[3]
                self.nombreAgricultor = data[4]
                # self.ln_persona.setText(data[4])            
                # self.ln_explotacion.setText(data[5])           
                # self.ln_distribuidor.setText(data[6])    
                self.lbl_agricultor.setText('Cultivos asociados al agricultor:  {}'.format(data[4]))    

                sql = '''select distinct  upper(c.nombre),d.idcultivo  from campaign.data d
                join agrae.cultivo c on c.idcultivo = d.idcultivo
                where d.idexplotacion  = {}'''.format(self.idExplotacion)
                self.tools.getCultivosData(sql,self.combo_cultivo)   
                self.getDataCultivos(self.idAgricultor)


            except Exception as ex:
                print(ex)
                self.conn.rollback()
                pass
            finally:
                self.tabWidget.setCurrentIndex(2)
                self.tabWidget.setTabEnabled(2,True)
                pass

    def getDataCultivos(self,idagricultor):
        sql = ''' select ca.idcultivoagricultor , a.idagricultor, cu.idcultivo, cu.nombre as cultivo , ca.unidadesnpktradicionales fert_tradicional, ca.costefertilizante::integer from agrae.agricultor a 
        join agrae.cultivoagricultor ca on ca.idagricultor = a.idagricultor 
        join agrae.cultivo cu on cu.idcultivo = ca.idcultivo
        where a.idagricultor  = {}
        order by a.idagricultor desc  '''.format(idagricultor)
        self.tools.populateTable(sql,self.tableWidget_2)


    def personaDialog(self):
       
        dlg = GestionPersonasDialog()
        dlg.tableWidget.doubleClicked.disconnect()
        dlg.tableWidget.doubleClicked.connect(dlg.getPersonaAgricultor)
        dlg.idPersonaSignal.connect(self.popDataPersona)
        dlg.exec()
        
    def popData(self,data,variable,widget):
        variable = data[0]
        widget.setText(data[1])

    def popDataPersona(self,data):
        self.idPersona = data[0]
        self.ln_persona.setText(data[1])
        self.validateData()

    def explotacionDialog(self):
        dlg = GestionExplotacionDialog()
        dlg.tableWidget.doubleClicked.disconnect()
        dlg.tableWidget.doubleClicked.connect(dlg.getExplotacionAgricultor)
        dlg.idExplotacionSignal.connect(self.popDataExplotacion)
        dlg.exec()
        
    def popDataExplotacion(self,data):
        self.idExplotacion = data[0]
        self.ln_explotacion.setText(data[1])
        self.validateData()
        # print(data)

    def distribuidorDialog(self):
        dlg = GestionDistribuidorDialog()
        dlg.tableWidget.doubleClicked.disconnect()
        dlg.tableWidget.doubleClicked.connect(dlg.getDistribuidorAgricultor)
        dlg.idDistribuidorSignal.connect(self.popDataDistribuidor)
        dlg.exec()
        
    def popDataDistribuidor(self,data):
        self.idDistribuidor = data[0]
        self.ln_distribuidor.setText(data[1])
        self.validateData()
        # print(data)

    def validateData(self):
        if self.idPersona and self.idExplotacion and self.idDistribuidor:
            self.btn_save.setEnabled(True)


    def saveDataAgricultor(self):
        with self.conn.cursor() as cursor: 
            try:                               
               
                if self.idPersona and self.idExplotacion and self.idDistribuidor:
                    sql = '''with data as (select {} as idpersona, {} as idexplotacion, {} as iddistribuidor)
                    INSERT INTO agrae.agricultor (idpersona,idexplotacion,iddistribuidor)
                    select * from data
                    ON CONFLICT(idpersona,idexplotacion,iddistribuidor) 
                    DO UPDATE SET
                    idpersona = (select idpersona from data),
                    idexplotacion = (select idexplotacion from data),
                    iddistribuidor = (select iddistribuidor from data)
                    where agrae.agricultor.idagricultor = {} ;'''.format(self.idPersona,self.idExplotacion,self.idDistribuidor,self.idAgricultor)
                    cursor.execute(sql)
                    self.conn.commit()
                    QMessageBox.about(self, "", "Datos Guardados Correctamente")
                    # print(sql)
                    self.getData()
                    self.tabWidget.setCurrentIndex(0)
                    
                    
                else: 
                    QMessageBox.about(self, "aGrae GIS:", "Debe completar el formulario.".format())
                
                

            except Exception as ex: 
                QgsMessageLog.logMessage("{}".format(ex), 'aGrae GIS', level=1)
                QMessageBox.about(self, "aGrae GIS:", "Ocurrio un Error, revisar el panel de registros.".format())
                self.conn.rollback()

            finally:
                self.idPersona = None
                self.idExplotacion = None 
                self.idDistribuidor = None 
                self.idAgricultor = 0
                self.tools.clearWidget(
                        [
                        self.ln_persona,
                        self.ln_explotacion,
                        self.ln_distribuidor
                        ]
                    )
                self.btn_save.setEnabled(False)


    def deleteAgricultor(self):
        row = self.tableWidget.currentRow()
        with self.conn.cursor() as cursor: 
            try:
                id = self.tableWidget.item(row,0).text()
                nombre = self.tableWidget.item(row,2).text()
                # print(id)
                sql = '''DELETE FROM agrae.agricultor
                WHERE idagricultor ={};
                '''.format(id)
                question = 'Quieres eliminar al agricultor {}?'.format(nombre)
                self.tools.deleteAction(question,sql) 

                self.getData()
                QgsMessageLog.logMessage("Agricultor {} eliminado correctamente".format(nombre), 'aGrae GIS', level=3)
                QMessageBox.about(self, "aGrae GIS:", "El Agricultor {} se elimino correctamente".format(nombre))
                
            except  errors.lookup('23503'):
                QgsMessageLog.logMessage("El Agricultor {} esta referido en otras tablas".format(nombre), 'aGrae GIS', level=1)
                QMessageBox.about(self, "aGrae GIS:", "No se puede borrar al Agricultor {}.".format(nombre))
                self.conn.rollback()
            except Exception as ex:
                QgsMessageLog.logMessage("{}".format(ex), 'aGrae GIS', level=1)
                QMessageBox.about(self, "aGrae GIS:", "Ocurrio un Error, revisar el panel de registros.".format())
                self.conn.rollback()
            finally:
                self.getData()
                pass
        pass
    

    def getCultivoAgricultorData(self):
        row = self.tableWidget_2.currentRow() 
        self.idCultivoAgricultor = self.tableWidget_2.item(row,0).text()
        self.idAgricultor =  self.tableWidget_2.item(row,1).text()
        self.combo_cultivo.setCurrentIndex(self.combo_cultivo.findData(self.tableWidget_2.item(row,2).text()))
        self.ln_und_tradicionales.setText(self.tableWidget_2.item(row,4).text())
        precio = int(float(self.tableWidget_2.item(row,5).text()))
        self.ln_price.setValue(precio)

    def saveCultivoAgricultor(self):
        agricultor = self.idAgricultor
        cultivo = self.combo_cultivo.currentData()
        unidades = self.ln_und_tradicionales.text()
        costo = self.ln_price.value()
        fecha = self.date_cultivo.date().toString('yyyy-MM-dd')

        sql = '''with data as (select {} as idagricultor, {} as idcultivo, '{}' as unidadesnpktradicionales, {} as costefertilizante, '{}'::date as fechacultivo)
        INSERT INTO agrae.cultivoagricultor (idagricultor,idcultivo,unidadesnpktradicionales,costefertilizante,fechacultivo)
        select * from data
        ON CONFLICT(idagricultor,idcultivo) 
        DO UPDATE SET
        idagricultor = (select idagricultor from data),
        idcultivo = (select idcultivo from data),
        unidadesnpktradicionales = (select unidadesnpktradicionales from data),
        costefertilizante = (select costefertilizante from data),
        fechacultivo = (select fechacultivo from data)
        where agrae.cultivoagricultor.idagricultor = (select idagricultor from data)  and agrae.cultivoagricultor.idcultivo = (select idcultivo from data);'''.format(agricultor,cultivo,unidades,costo,fecha)
        try:
            with self.conn.cursor() as cursor: 
                cursor.execute(sql)
                self.conn.commit()
                self.tools.clearWidget([
                    self.ln_und_tradicionales
                ])
                self.combo_cultivo.setCurrentIndex(0)
                self.ln_price.setValue(0)

                self.getDataCultivos(self.idAgricultor)

                QMessageBox.about(self, "", "Datos Guardados Correctamente")

        except Exception as ex:
            QgsMessageLog.logMessage("{}".format(ex), 'aGrae GIS', level=1)
            QMessageBox.about(self, "aGrae GIS:", "Ocurrio un Error, revisar el panel de registros.".format())
            self.conn.rollback()
       
    def deleteCultivoAgricultor(self):
        row = self.tableWidget_2.currentRow() 
        self.idCultivoAgricultor = self.tableWidget_2.item(row,0).text()
        cultivo = self.tableWidget_2.item(row,3).text()

        sql = '''DELETE FROM agrae.cultivoagricultor
                WHERE idcultivoagricultor ={};
                '''.format(self.idCultivoAgricultor)
        try:
            question = 'Quieres eliminar el cultivo {} asociado al agricultor {}?'.format(cultivo,self.nombreAgricultor)
            self.tools.deleteAction(question,sql) 
            self.getDataCultivos(self.idAgricultor)

        except Exception as ex:
            QgsMessageLog.logMessage("{}".format(ex), 'aGrae GIS', level=1)
            QMessageBox.about(self, "aGrae GIS:", "Ocurrio un Error, revisar el panel de registros.".format())
            self.conn.rollback()





    


        

    def closeEvent(self,event):
        self.closingPlugin.emit()
        event.accept()