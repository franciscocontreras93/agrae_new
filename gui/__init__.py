import os
from PyQt5.QtGui import QIcon, QPixmap
from qgis.PyQt.QtCore import pyqtSignal, QSize, QDate
from qgis.PyQt.QtWidgets import QLineEdit

class agraeGUI():

    

    def __init__(self):
        self._DIALOG_SIZE = QSize(450,300)

        self.icons = {
         'main' : QIcon(os.path.join(os.path.dirname(__file__), r'icons\icon.svg')),
         'info' : QIcon(os.path.join(os.path.dirname(__file__), r'icons\info.png')),
         'matraz' : QIcon(os.path.join(os.path.dirname(__file__), r'icons\matraz.png')),
         'npk' : QIcon(os.path.join(os.path.dirname(__file__), r'icons\npk.png')),
         'lotes' : QIcon(os.path.join(os.path.dirname(__file__), r'icons\search-lotes.svg')),
         'add' : QIcon(os.path.join(os.path.dirname(__file__), r'icons\plus-solid.svg')),
         'minus' : QIcon(os.path.join(os.path.dirname(__file__), r'icons\minus-solid.svg')),
         'trash' : QIcon(os.path.join(os.path.dirname(__file__), r'icons\trash-solid.svg')),
         'edit' : QIcon(os.path.join(os.path.dirname(__file__), r'icons\pen-solid.svg')),
         'pen-to-square' : QIcon(os.path.join(os.path.dirname(__file__), r'icons\pen-to-square-solid.svg')),
         'save' : QIcon(os.path.join(os.path.dirname(__file__), r'icons\save-solid.svg')),
         'clone' : QIcon(os.path.join(os.path.dirname(__file__), r'icons\clone-solid.svg')),
         'reload' : QIcon(os.path.join(os.path.dirname(__file__), r'icons\reload.svg')),
         'weather' : QIcon(os.path.join(os.path.dirname(__file__), r'icons\weather.svg')),
         'csv' : QIcon(os.path.join(os.path.dirname(__file__), r'icons\file-excel-solid.svg')),
         'import' : QIcon(os.path.join(os.path.dirname(__file__), r'icons\file-import-solid.svg')),
         'tools' : QIcon(os.path.join(os.path.dirname(__file__), r'icons\tools.svg')),
         'upload' : QIcon(os.path.join(os.path.dirname(__file__), r'icons\upload-db.svg')),
         'add-layer' : QIcon(os.path.join(os.path.dirname(__file__), r'icons\layer-add-o.svg')),
         'chart-bar' : QIcon(os.path.join(os.path.dirname(__file__), r'icons\chart-bar-solid.svg')),
         'image' : QIcon(os.path.join(os.path.dirname(__file__), r'icons\image-solid.svg')),
         'list-check' : QIcon(os.path.join(os.path.dirname(__file__), r'icons\list-check-solid.svg')),
         'farmer' : QIcon(os.path.join(os.path.dirname(__file__), r'icons\farmer-solid.svg')),
         'user' : QIcon(os.path.join(os.path.dirname(__file__), r'icons\user-solid.svg')),
         'users' : QIcon(os.path.join(os.path.dirname(__file__), r'icons\users-solid.svg')),
         'handshake' : QIcon(os.path.join(os.path.dirname(__file__), r'icons\handshake-solid.svg')),
         'search' : QIcon(os.path.join(os.path.dirname(__file__), r'icons\search.svg')),
         'explotacion' : QIcon(os.path.join(os.path.dirname(__file__), r'icons\money-bill-wheat-solid.svg')),
         'cultivo' : QIcon(os.path.join(os.path.dirname(__file__), r'icons\cultivo-solid.svg')),
         'segmentos' : QIcon(os.path.join(os.path.dirname(__file__), r'icons\s-solid.svg')),
         'ambientes' : QIcon(os.path.join(os.path.dirname(__file__), r'icons\a-solid.svg')),
         'map' : QIcon(os.path.join(os.path.dirname(__file__), r'icons\map-solid.svg')),
         'circle_info' : QIcon(os.path.join(os.path.dirname(__file__), r'icons\circle-info-solid.svg')),
         'printer' : QIcon(os.path.join(os.path.dirname(__file__), r'icons\print-solid.svg')),
         'selection' : QIcon(os.path.join(os.path.dirname(__file__), r'icons\arrow.svg')),
         'tractor' : QIcon(os.path.join(os.path.dirname(__file__), r'icons\tractor-solid.svg')),
         'pois' : QIcon(os.path.join(os.path.dirname(__file__), r'icons\pois.svg')),
         'settings' : QIcon(os.path.join(os.path.dirname(__file__), r'icons\gear-solid.svg')),
         'rindes' : QIcon(os.path.join(os.path.dirname(__file__), r'icons\rindes.svg')),
         'satelite' : QIcon(os.path.join(os.path.dirname(__file__), r'icons\satellite-solid.svg')),
         

        }
        

        self.images_base = {

            'leyenda': QPixmap(os.path.join(os.path.dirname(__file__), r'base\lgnd1.svg')),
            'p1': QPixmap(os.path.join(os.path.dirname(__file__), r'base\p1.svg')),
            'co2': QPixmap(os.path.join(os.path.dirname(__file__), r'base\co2.svg')),

        }
        pass
      
    def getIcon(self,name) -> QIcon:
        """name =
        'main' 
        'info' 
        'matraz' 
        'npk' 
        'lotes' 
        'add' 
        'trash' 
        'edit' 
        'save' 
        'clone' 
        'reload' 
        'weather' 
        'csv' : 
        'import' 
        'tools' 
        'upload' 
        'add-layer'
        'chart-bar'
         
        """
        if name: return self.icons[name]
    
    def getImage(self,name) -> QPixmap: 
        """name =
        'leyenda' - 'p1'  - 'co2' """

        if name: return self.images_base[name]

    def formatUpper(self,widget:QLineEdit,v:str):
        widget.setText(v.upper())