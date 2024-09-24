from qgis.PyQt.QtWidgets import QgsFieldComboBox



class CustomFieldComboBox(QgsFieldComboBox):
    def __init__(self,layer):
        super().__init__()
        self.layer = layer

        self.setLayer(self.layer)
        pass

    