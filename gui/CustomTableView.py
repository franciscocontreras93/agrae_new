from qgis.PyQt.QtWidgets import QTableView,QAbstractItemView,QHeaderView,QStyledItemDelegate
from qgis.PyQt.QtCore import Qt
from qgis.PyQt import QtCore,QtGui

class CustomTableView(QTableView):
    def __init__(self):
        super(CustomTableView,self).__init__()
        # self.setColumnHidden(0,True)
        # self.currentChanged(lambda : self.setColumnHidden(0,True))
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

   
    

class CustomTableModel(QtCore.QAbstractTableModel):
    def __init__(self, data, headerLabels:list):
        super(CustomTableModel, self).__init__()
        self._data = data
        self.headerLabels =  headerLabels
        # delegate = ReadOnlyDelegate(self)
        # self.setItemDelegate(delegate)



    def data(self, index, role):
        if role == Qt.DisplayRole:
            # See below for the nested-list data structure.
            # .row() indexes into the outer list,
            # .column() indexes into the sub-list
            return self._data[index.row()][index.column()]

    def rowCount(self, index):
        # The length of the outer list.
        try:
            return len(self._data)
        except:
            return 0

    def columnCount(self, index):
        # The following takes the first sub-list, and returns
        # the length (only works if all rows are an equal length)
        # return len(self._data[0])
        try:
            return len(self._data[0])
        except:
            return 0
    
    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headerLabels[section]
        # if orientation == Qt.Vertical and role == Qt.DisplayRole:
        #     return f"{section + 1}"

    def flags(self, index):
        if not index.isValid() and index != self.columnCount() :
            return Qt.ItemIsEnabled

        return super().flags(index) | Qt.ItemIsEditable
    
    # def setData(self, index, value, role):
    #     if role == Qt.EditRole:
    #         # Set the value into the frame.
    #         self._data[index.row()][index.column()] = value
    #         return True

        # return False


class ReadOnlyDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        # last column
        if index.column() == (index.model().columnCount() - 1):
            return super().createEditor(parent, option, index)