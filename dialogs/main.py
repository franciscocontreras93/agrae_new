import os
import csv
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time


# from datetime import date
from psycopg2 import InterfaceError, errors, extras
from PyQt5.QtCore import QRegExp, QDate, QDateTime, QThreadPool
from PyQt5.QtGui import QRegExpValidator, QIcon, QPixmap
from PyQt5.QtWidgets import *
from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal, QSettings, QVariant
from qgis.core import *
from qgis.utils import iface
from qgis.PyQt.QtXml import QDomDocument
# from .agrae_dialogs import expFindDialog, agraeSegmentoDialog, agraeParametrosDialog, cultivoFindDialog, agricultorDialog

# from .utils import AgraeUtils, AgraeToolset,  AgraeAnalitic, TableModel, PanelRender, AgraeZipper
# from .agrae_worker import Worker
# from .resources import *

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from PyQt5 import QtCore, QtWidgets
import sys
import matplotlib
import threading

agraeMainDialogUI, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'ui/agrae_main.ui'))

class agraeMainWidget(QtWidgets.QMainWindow, agraeMainDialogUI):
    closingPlugin = pyqtSignal()
    dataSignal = pyqtSignal(tuple)
    def __init__(self, parent=None):
        """Constructor."""      
        super(agraeMainWidget, self).__init__(parent)
        self.setupUi(self)

    




