from qgis.PyQt.QtWidgets import QLineEdit, QCompleter
from . import agraeGUI

class CustomLineSearch(QLineEdit):
    def __init__(self,
                 completer:QCompleter,
                 action,
                 placeholder:str=None
                 ):
        super().__init__()
        self.setCompleter(completer)
        self.returnPressed.connect(action)
        self.textChanged.connect(action)
        self.setClearButtonEnabled(True)
        line_search_action = self.addAction(
            agraeGUI().getIcon('search'), self.TrailingPosition)
        line_search_action.triggered.connect(action)

        if placeholder:
            self.setPlaceholderText(placeholder)

    