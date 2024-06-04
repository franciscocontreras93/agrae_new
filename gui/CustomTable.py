from qgis.PyQt.QtWidgets import QTableWidget,QTableWidgetItem,QAbstractItemView


class CustomTable(QTableWidget):
    def __init__(self,parent=None,columns:list=[],data=None):
        super(CustomTable,self).__init__(parent)
        self.horizontalHeader().setStretchLastSection(True)
        self.setSortingEnabled(True)
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels(columns)
        self.setColumnHidden(0, True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)

        if data:
            self.populate(data)


    def populate(self,data):
        
        try:
            print(data)
            # self.setRowCount(0)
            # if len(data) > 0:
            #     # print(data)
            #     a = len(data)
            #     b = len(data[0])
            #     i = 1
            #     j = 1
            #     self.setRowCount(a)
            #     self.setColumnCount(b)
            #     for j in range(a):
            #         for i in range(b):
            #             if str(data[j][i]) != 'None':
            #                 item = QTableWidgetItem(str(data[j][i]))
            #             else:
            #                 item  = QTableWidgetItem(str('N/D'))  
            #             self.setItem(j, i, item)
            #             # self.resizeRowToContext()
        except IndexError as ie:
            pass
        

    