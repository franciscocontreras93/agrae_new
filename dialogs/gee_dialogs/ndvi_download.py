from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QLabel, QDateEdit, QPushButton, QDialogButtonBox, QHBoxLayout, QGroupBox, QRadioButton
from qgis.PyQt.QtCore import QDate, Qt

class GEEModuleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Seleccionar Rango de Fechas")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        # Create analysis type selectors
        self.analysis_group = QGroupBox("Tipo de Análisis:")
        analysis_layout = QHBoxLayout()

        self.ndvi_radio = QRadioButton("NDVI")
        self.savi_radio = QRadioButton("SAVI")
        self.natural_color_radio = QRadioButton("Color Natural")

        # Set NDVI as default
        self.ndvi_radio.setChecked(True)

        analysis_layout.addWidget(self.ndvi_radio)
        analysis_layout.addWidget(self.savi_radio)
        analysis_layout.addWidget(self.natural_color_radio)
        self.analysis_group.setLayout(analysis_layout)

        # Date Layout
        date_layout = QHBoxLayout()

        # Date From Layout
        date_from_layout = QVBoxLayout()
        # Date To Layout
        date_to_layout = QVBoxLayout()

        # Create the labels
        self.label_desde = QLabel("Desde:")
        self.label_hasta = QLabel("Hasta:")

        # Create the QDateEdit widgets
        self.date_edit_desde = QDateEdit()
        self.date_edit_hasta = QDateEdit()

        # Set the current date for "Desde" and the maximum date for both
        current_date = QDate.currentDate()
        one_year_ago = current_date.addYears(-1)
        self.date_edit_desde.setDate(one_year_ago)
        self.date_edit_desde.setMaximumDate(current_date)
        # self.date_edit_desde.setMinimumDate(one_year_ago)
        self.date_edit_hasta.setDate(current_date)
        self.date_edit_hasta.setMaximumDate(current_date)

        # Make the calendar popup
        self.date_edit_desde.setCalendarPopup(True)
        self.date_edit_hasta.setCalendarPopup(True)

        date_from_layout.addWidget(self.label_desde)
        date_from_layout.addWidget(self.date_edit_desde)

        date_to_layout.addWidget(self.label_hasta)
        date_to_layout.addWidget(self.date_edit_hasta)

        date_layout.addLayout(date_from_layout)
        date_layout.addLayout(date_to_layout)

        # Create the buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        # Create the layout
        layout = QVBoxLayout()        
        layout.addWidget(self.analysis_group)
        layout.addWidget(self.date_edit_desde)
        layout.addWidget(self.label_hasta)
        layout.addWidget(self.date_edit_hasta)
        layout.addWidget(self.button_box)

        self.setLayout(layout)