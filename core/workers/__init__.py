from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtCore import *

from ...tools import aGraeTools



class   WorkerGenerarPuntosMuestreo(QThread):
    ImageUpdate = pyqtSignal(QImage)
    QrCodeString = pyqtSignal(str)

    def __init__(self,ids,segmentos):
        super().__init__()
        self.tools = aGraeTools()
        self.ids = ids
        self.segmentos = segmentos
        pass
    def run(self): 
        self.ThreadActive = True
       
        while self.ThreadActive:
            self.tools.crearPuntosMuestreo(self.ids,self.segmentos)
            self.tools.MuestreoEndSignal.connect(self.stop)
            # self.stop()
            

    def stop(self,state):
        self.ThreadActive = state
        self.quit() 



