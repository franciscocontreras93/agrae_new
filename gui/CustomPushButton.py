from qgis.PyQt.QtWidgets import QPushButton,QWidget
from qgis.PyQt.QtCore import QSize
from PyQt5.QtGui import QIcon

class CustomPushButton(QPushButton):
    def __init__(self,parent= None, text= None, icon=None,action=None):
        super(CustomPushButton,self).__init__(parent)
        self.setIconSize(QSize(20, 20))
        self.setIcon(icon)
        self.clicked.connect(action)


        pass