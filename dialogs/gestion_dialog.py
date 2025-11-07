from qgis.PyQt.QtWidgets import (QMainWindow, QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, QToolTip, QFileDialog, QAction, # type: ignore
                                 QLabel, QComboBox, QPushButton, QSizePolicy, QSpacerItem, QWidget, QFrame, QMessageBox, QCompleter,
                                 QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget, QSplitter) 
from qgis.PyQt.QtCore import Qt, pyqtSignal, QThread  # type: ignore
from qgis.core import QgsMessageLog, Qgis # type: ignore

from ..tools import aGraeTools
from ..sql import aGraeSQLTools
from ..gui import  agraeGUI

class agraeGestionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowStaysOnTopHint)
        self.setWindowTitle("aGrae | Progreso de Campaña y Gestión")
        # self.setWindowIcon(agraeGUI().getIcon('agrae'))
        self.setMinimumSize(800, 600)

        self.tools = aGraeTools()
        self.sql_tools = aGraeSQLTools()

        self.UIcomponents()

        

    def UIcomponents(self):

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)


       
       
       
        pass