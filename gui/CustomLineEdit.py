from qgis.PyQt.QtWidgets import QLineEdit

class CustomLineEdit(QLineEdit):

    def __init__(self,placeholder:str=None):
        super().__init__()
        self.textChanged.connect(self.upper)
        if placeholder:
            self.setPlaceholderText(placeholder)

    def upper(self,v):
        v = v.upper()
        self.setText(v)
