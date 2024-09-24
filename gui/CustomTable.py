from qgis.PyQt.QtWidgets import QTableWidget,QTableWidgetItem,QAbstractItemView,QStyledItemDelegate,QItemDelegate,QHeaderView,QLineEdit,QSpinBox
from qgis.PyQt.QtCore import QRegExp
from qgis.PyQt.QtGui import QRegExpValidator

class CustomTable(QTableWidget):
    def __init__(self,parent=None,columns:list=[],data=None,editable:bool=False,editable_column=None,regex:str=''):
        super(CustomTable,self).__init__(parent)
        self.horizontalHeader().setStretchLastSection(True)
        self.setSortingEnabled(True)
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels(columns)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setColumnHidden(0, True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        # self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # delegate = ReadOnlyDelegate(self)
        # self.setItemDelegate(delegate)

        if data:
            self.populate(data)

        if editable:
            self.setEditTriggers(QAbstractItemView.AllEditTriggers)
            readDelegate = ReadOnlyDelegate(self)
            ranges = [e for e in range(len(columns))]
            excluded = ranges.pop(columns.index(editable_column))
            for c in ranges:
                self.setItemDelegateForColumn(c,readDelegate)
            regexDelegate = RegexDelegate(regex=regex)
            self.setItemDelegateForColumn(excluded,regexDelegate)
            



    def populate(self,data):
        
        try:
            # print(data)
            self.setRowCount(0)
            if len(data) > 0:
                # print(data)
                a = len(data)
                b = len(data[0])
                i = 1
                j = 1
                self.setRowCount(a)
                self.setColumnCount(b)
                for j in range(a):
                    for i in range(b):
                        if str(data[j][i]) != 'None':
                            item = QTableWidgetItem(str(data[j][i]))
                        else:
                            item  = QTableWidgetItem(str('N/D'))  
                        self.setItem(j, i, item)
                        # self.resizeRowToContext()
        except IndexError as ie:
            pass
        

class ReadOnlyDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        # last column
        # if index.column() == (index.model().columnCount() - 1):
        #     return super().createEditor(parent, option, index)
        return
    
class RegexDelegate(QItemDelegate):
    def __init__(self,regex):
        super().__init__()
        self.regex = regex

    def createEditor(self, parent, option, index):     # self, parent, option, index    
       
        line = QLineEdit(parent)                       #  parent
        
        # try it:
        validador = QRegExp(self.regex)
        ok = QRegExpValidator(validador, parent)
        line.setValidator(ok)
        
        # or try it:                                      # <<<-----<
        #line.setInputMask("0.0;")                        # <<<-----<
        
        return line 