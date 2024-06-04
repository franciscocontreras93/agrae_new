
import string



# from datetime import date
from psycopg2 import extras
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtCore import pyqtSignal, QSize, QDate
from qgis.core import *
from qgis.utils import iface



from ..db import agraeDataBaseDriver
from ..sql import aGraeSQLTools
from ..tools import aGraeTools
from ..gui import agraeGUI
from ..gui.CustomLineEdit import CustomLineEdit


class CreateCampaniaDialog(QDialog):
    closingPlugin = pyqtSignal()
    campCreated = pyqtSignal()
    # loteCreated = pyqtSignal(int)
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Gestion de Campañas')
        self.conn = agraeDataBaseDriver().connection()
        self.agraeSql = aGraeSQLTools()
        self.tools = aGraeTools()

        self.currentDate = QDate().currentDate()

        self.UIComponents()

        self.setFixedSize(agraeGUI()._DIALOG_SIZE)

        self.date_test = 'NULL'

    def UIComponents(self):
        
        self.layout = QGridLayout()
        self.groupBoxLayout = QGridLayout()
        self.groupBox = QGroupBox()
        self.groupBox.setTitle('Crear Nueva Campaña')
        self.label_1 = QLabel('Nombre de la nueva Campaña')
        self.label_1.setMaximumSize(QSize(200,15))
        self.line_nombre = CustomLineEdit()
        

        self.label_4 = QLabel('Prefijo de Campaña')
        self.prefixCombo = QComboBox()
        self.prefixCombo.addItem('Seleccionar...')
        self.prefixCombo.addItems(list(string.ascii_uppercase))

        self.label_2 = QLabel('Fecha Desde')
        self.label_2.setMaximumSize(QSize(200,15))
        self.date_desde = QDateEdit()
        self.date_desde.setCalendarPopup(True)
        self.date_desde.setDate(self.currentDate)

        self.label_3 = QLabel('Fecha Hasta')
        self.label_3.setMaximumSize(QSize(200,15))
        self.date_hasta = QDateEdit()
        self.date_hasta.setCalendarPopup(True)
        self.date_hasta.setDate(self.currentDate)
        self.date_hasta.editingFinished.connect(self.checkDate)

        self.date_desde.dateChanged.connect(self.setMinimumDate)

        self.btn_create = QPushButton('Crear Campaña')
        self.btn_create.clicked.connect(self.create)

        self.groupBoxLayout.addWidget(self.label_1,0,0,1,0)
        self.groupBoxLayout.addWidget(self.line_nombre,1,0,1,0)
        self.groupBoxLayout.addWidget(self.label_4,2,0,1,0)
        self.groupBoxLayout.addWidget(self.prefixCombo,3,0,1,0)
        self.groupBoxLayout.addWidget(self.line_nombre,4,0,1,0)
        self.groupBoxLayout.addWidget(self.label_2,5,0)
        self.groupBoxLayout.addWidget(self.label_3,5,1)
        self.groupBoxLayout.addWidget(self.date_desde,6,0)
        self.groupBoxLayout.addWidget(self.date_hasta,6,1)
        self.groupBoxLayout.addWidget(self.btn_create,7,0,1,0)

        self.groupBox.setLayout(self.groupBoxLayout)
        self.layout.addWidget(self.groupBox)
        self.setLayout(self.layout)

        pass
    def setMinimumDate(self,date):
        self.date_hasta.setMinimumDate(date)

    def checkDate(self):
        if not self.date_hasta.hasFocus():
            self.date_test = 'NULL'
        else:
            self.date_test = self.date_hasta.date().toString('yyyy-MM-dd')
            # print('True')
    def create(self):
        # # print('Creando Explotacion')
        nombre = self.line_nombre.text().upper()
        prefix = self.prefixCombo.currentText()
        # print(prefix)
        desde = self.date_desde.date().toString('yyyy-MM-dd')
        hasta = self.date_hasta.date().toString('yyyy-MM-dd')
        sql = '''insert into campaign.campanias (nombre,fecha_desde,fecha_hasta,prefix) values('{}','{}','{}','{}')'''.format(nombre,desde,hasta,prefix)
        # sql = '''insert into campaign.campanias (nombre,fecha_desde) values('{}','{}','{}')'''.format(nombre,desde)
        with self.conn.cursor() as cursor:
            try:

                cursor.execute(sql)
                self.conn.commit()
                self.tools.messages('aGrae Toolbox','Campaña {} creada correctamente'.format(nombre),3)
                self.campCreated.emit()
                self.close()
                
            except Exception as ex:
                iface.messageBar().pushMessage('aGrae Toolbox','Ocurrio un error. Revisa el Panel de Mensajes del Registro'.format(nombre),2,duration=5)
                QgsMessageLog.logMessage('aGrae Toolbox', ex)
                self.conn.rollback()

    def test(self):
        prefix = self.prefixCombo.currentText()
        print(prefix)



    

class UpdateCampaniaDialog(QDialog):
    campUpdated = pyqtSignal()
    def __init__(self,idcampania):
        super().__init__()
        self.setWindowTitle('Gestion de Campañas')
        self.conn = agraeDataBaseDriver().connection()
        self.agraeSql = aGraeSQLTools()
        self.tools = aGraeTools()
        self.idCampania = idcampania
        self.currentDate = QDate().currentDate()
        self.UIComponents()
        

        self.setFixedSize(agraeGUI()._DIALOG_SIZE)

        

        pass
    
    
    def UIComponents(self):
        
        self.layout = QGridLayout()
        self.groupBoxLayout = QGridLayout()
        self.groupBox = QGroupBox()
        self.groupBox.setTitle('Actualizar Campaña')
        self.label_1 = QLabel('Nombre de la Campaña')
        self.label_1.setMaximumSize(QSize(200,15))
        self.line_nombre = CustomLineEdit()
        # self.line_nombre.textChanged.connect(lambda v: agraeGUI().formatUpper(self.line_nombre,v))

        self.label_4 = QLabel('Prefijo de Campaña')
        self.prefixCombo = QComboBox()
        self.prefixCombo.addItem('Seleccionar...')
        self.prefixCombo.addItems(list(string.ascii_uppercase))


        self.label_2 = QLabel('Fecha Desde')
        self.label_2.setMaximumSize(QSize(200,15))
        self.date_desde = QDateEdit()
        self.date_desde.setCalendarPopup(True)
        self.date_desde.setDate(self.currentDate)

        self.label_3 = QLabel('Fecha Hasta')
        self.label_3.setMaximumSize(QSize(200,15))
        self.date_hasta = QDateEdit()
        self.date_hasta.setCalendarPopup(True)
        self.date_hasta.setDate(self.currentDate)

        self.date_desde.dateChanged.connect(self.setMinimumDate)

        self.btn_create = QPushButton('Actualizar Campaña')
        self.btn_create.clicked.connect(self.update)

        self.groupBoxLayout.addWidget(self.label_1,0,0,1,0)
        self.groupBoxLayout.addWidget(self.line_nombre,1,0,1,0)
        self.groupBoxLayout.addWidget(self.label_4,2,0,1,0)
        self.groupBoxLayout.addWidget(self.prefixCombo,3,0,1,0)
        self.groupBoxLayout.addWidget(self.label_2,4,0)
        self.groupBoxLayout.addWidget(self.label_3,4,1)
        self.groupBoxLayout.addWidget(self.date_desde,5,0)
        self.groupBoxLayout.addWidget(self.date_hasta,5,1)
        self.groupBoxLayout.addWidget(self.btn_create,6,0,1,0)

        self.groupBox.setLayout(self.groupBoxLayout)
        self.layout.addWidget(self.groupBox)
        self.setLayout(self.layout)

        self.getCampaniaData()

        pass
    def setMinimumDate(self,date):
        self.date_hasta.setMinimumDate(date)


    def getCampaniaData(self):
        sql = '''select nombre, fecha_desde,fecha_hasta, prefix from campaign.campanias where id = {}'''.format(self.idCampania)
        # print(sql)
        with self.conn.cursor() as cursor:
            try:
                cursor.execute(sql)
                data = cursor.fetchone() 
                print(data)
                self.line_nombre.setText(data[0])
                self.date_desde.setDate(data[1])
                self.date_hasta.setDate(data[2])
                self.prefixCombo.setCurrentText(data[3])
            except Exception as ex:
              print(ex)
              self.conn.rollback()

    def update(self):
        nombre = str(self.line_nombre.text()).upper()
        desde = self.date_desde.date().toString('yyyy-MM-dd')
        hasta = self.date_hasta.date().toString('yyyy-MM-dd')
        prefix = str(self.prefixCombo.currentText())
        sql = '''UPDATE campaign.campanias
        SET nombre='{}', fecha_desde='{}', fecha_hasta='{}', prefix = '{}'
        WHERE id={}
        '''.format(nombre,desde,hasta,prefix,self.idCampania)

        with self.conn.cursor() as cursor:
            try:
                cursor.execute(sql)
                self.conn.commit()
                self.tools.messages('aGrae Toolbox','Campaña {} actualizada correctamente'.format(nombre),3)
                self.campUpdated.emit()
                self.close()
            except Exception as ex:
                iface.messageBar().pushMessage('aGrae Toolbox','Ocurrio un error. Revisa el Panel de Mensajes del Registro'.format(nombre),2,duration=5)
                QgsMessageLog.logMessage('aGrae Toolbox', ex, 2)
                self.conn.rollback()



class CloneCampaniaDialog(QDialog):
    campCloned = pyqtSignal()
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Gestion de Campañas')
        self.conn = agraeDataBaseDriver().connection()
        self.agraeSql = aGraeSQLTools()
        self.tools = aGraeTools()
        # self.idCampania = idcampania
        self.currentDate = QDate().currentDate()
        self.UIComponents()
        

        self.setFixedSize(agraeGUI()._DIALOG_SIZE)
        self.getCampaniasData()
        

        pass
    
    
    def UIComponents(self):
        
        self.layout = QGridLayout()
        self.groupBoxLayout = QGridLayout()
        self.groupBox = QGroupBox()
        self.groupBox.setTitle('Clonar Campaña')

        self.label_0 = QLabel('Copiar datos desde la campaña')
        self.label_0.setMaximumSize(QSize(200,15))
        self.combo_campanias = QComboBox()


        self.label_1 = QLabel('Ingrese el Nombre de la campaña')
        self.label_1.setMaximumSize(QSize(200,15))
        self.line_nombre = CustomLineEdit()
        # self.line_nombre.textChanged.connect(lambda v: agraeGUI().formatUpper(self.line_nombre,v))
        
        self.label_2 = QLabel('Fecha Desde')
        self.label_2.setMaximumSize(QSize(200,15))
        self.date_desde = QDateEdit()
        self.date_desde.setCalendarPopup(True)
        self.date_desde.setDate(self.currentDate)

        self.label_3 = QLabel('Fecha Hasta')
        self.label_3.setMaximumSize(QSize(200,15))
        self.date_hasta = QDateEdit()
        self.date_hasta.setCalendarPopup(True)
        self.date_hasta.setDate(self.currentDate.addMonths(5))
        self.date_hasta.setMinimumDate(self.currentDate)
        
        self.label_4 = QLabel('Prefijo de Campaña')
        self.prefixCombo = QComboBox()
        self.prefixCombo.addItem('Seleccionar...')
        self.prefixCombo.addItems(list(string.ascii_uppercase))

        self.date_desde.dateChanged.connect(self.setMinimumDate)

        self.btn_create = QPushButton('Crear Campaña')
        self.btn_create.clicked.connect(self.create)


        self.groupBoxLayout.addWidget(self.label_0,0,0,1,0)
        self.groupBoxLayout.addWidget(self.combo_campanias,1,0,1,0)
        self.groupBoxLayout.addWidget(self.label_1,2,0,1,0)
        self.groupBoxLayout.addWidget(self.line_nombre,3,0,1,0)
        self.groupBoxLayout.addWidget(self.label_4,4,0,1,0)
        self.groupBoxLayout.addWidget(self.prefixCombo,5,0,1,0)
        
        self.groupBoxLayout.addWidget(self.label_2,6,0)
        self.groupBoxLayout.addWidget(self.label_3,6,1)
        self.groupBoxLayout.addWidget(self.date_desde,7,0)
        self.groupBoxLayout.addWidget(self.date_hasta,7,1)
        self.groupBoxLayout.addWidget(self.btn_create,8,0,1,0)

        self.groupBox.setLayout(self.groupBoxLayout)
        self.layout.addWidget(self.groupBox)
        self.setLayout(self.layout)

        # self.getCampaniaData()

        pass
    def setMinimumDate(self,date):
        self.date_hasta.setMinimumDate(date)


    def getCampaniasData(self):
        sql = '''select distinct c.nombre, c.id from campaign.campanias c
        join campaign.data d on c.id = d.idcampania '''
        with self.conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
            try:
                cursor.execute(sql)
                data = cursor.fetchall()
                for e in data:
                    print(e)
                    self.combo_campanias.addItem(e['nombre'],e['id'])

            except Exception as ex:
                iface.messageBar().pushMessage('aGrae Toolbox','Ocurrio un error. Revisa el Panel de Mensajes del Registro',2,duration=5)
                QgsMessageLog.logMessage('aGrae Toolbox', ex, 2)
                self.conn.rollback()
        
        pass

    def create(self):
        idCampania = self.combo_campanias.currentData()
        nombre = str(self.line_nombre.text()).upper()
        desde = self.date_desde.date().toString('yyyy-MM-dd')
        hasta = self.date_hasta.date().toString('yyyy-MM-dd')
        prefix = str(self.prefixCombo.currentText())
        sql = '''with 
        select_data as (select idexplotacion,idlote from campaign.data where idcampania = {}),
        new_campaign as (insert into campaign.campanias (nombre,fecha_desde,fecha_hasta,prefix) values('{}', '{}', '{}', '{}') returning id)
        insert into campaign.data (idcampania,idexplotacion,idlote) 
        select (select id from new_campaign), * from select_data'''.format(idCampania,nombre,desde,hasta,prefix)

        with self.conn.cursor() as cursor:
            reply = QMessageBox.question(self,'aGrae Toolbox','Quieres copiar los datos asociados a la campaña {}?'.format(self.combo_campanias.currentText()), QMessageBox.Yes, QMessageBox.No)
        
            if reply == QMessageBox.Yes:
                try:
                    cursor.execute(sql)
                    self.conn.commit()
                    self.tools.messages('aGrae Toolbox','Campaña {} creada correctamente'.format(nombre),3)
                    self.campCloned.emit()
                    self.close()
                except Exception as ex:
                    iface.messageBar().pushMessage('aGrae Toolbox','Ocurrio un error. Revisa el Panel de Mensajes del Registro',2,duration=5)
                    QgsMessageLog.logMessage('aGrae Toolbox', ex, 2)
                    self.conn.rollback()
        pass
