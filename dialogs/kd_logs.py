import os

# from datetime import date
from psycopg2 import errors,  Binary


from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtCore import pyqtSignal, QSize, QDate
from qgis.core import *
from qgis.PyQt import uic

from ..gui import agraeGUI
from ..gui.CustomTable import CustomTable
from ..db import agraeDataBaseDriver
from ..sql import aGraeSQLTools
from ..tools import aGraeTools

from .gestion_personas import GestionPersonasDialog
from .explotacion_dialogs import GestionExplotacionDialog
from .gestion_distribuidor import GestionDistribuidorDialog



class GestionAgricultorDialog(QDialog): 
    closingPlugin = pyqtSignal()
    def __init__(self, parent=None) -> None:
        super().__init__()
        # self.setupUi(self)
        self.setWindowTitle('Logs | KD Usuarios')
        self.conn = agraeDataBaseDriver().connection()
        self.agraeSql = aGraeSQLTools()
        self.tools = aGraeTools()
        
        self.UIComponents()
        self.getData()

        # self.setFixedSize(QSize(400,250))

    def UIComponents(self):
        query = '''with logs as (select * from logs.kd_login kl)
        select l.id,l.userid,l.userip,ex.nombre,l.date from logs l join agrae.explotacion ex on l.userid = ex.idexplotacion
        {}'''
        data = agraeDataBaseDriver().read(query)
        self.tableWidget = CustomTable(self,['id','user','ip','explotacion','fecha'],data)

        main_layout = QVBoxLayout()
        # group_combos = QGroupBox()
        # layout_group_combos = QGridLayout()
        # layout_group_combos.addWidget(QLabel('Seleccionar Campaña'),0,0)
        # layout_group_combos.addWidget(QLabel('Seleccionar Explotacion'),0,1)
        # layout_group_combos.addWidget(self.combo_campania,1,0)
        # layout_group_combos.addWidget(self.combo_explotacion,1,1)
        # layout_group_combos.addWidget(self.toolButton,1,2)
        # group_combos.setLayout(layout_group_combos)

        # main_layout.addWidget(group_combos)
        main_layout.addWidget(self.tableWidget)


        self.setLayout(main_layout)
        return 

