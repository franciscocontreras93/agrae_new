# agrae/dialogs/copy_analitica_dialog.py
from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout

class CopyAnaliticaWizardDialog(QDialog):
    """
    Diálogo simple tipo asistente: etapa PADRE -> etapa HIJOS.
    No controla selección, sólo muestra estado e instrucciones.
    """
    cancelled = pyqtSignal()
    reset_requested = pyqtSignal()
    execute_requested = pyqtSignal()
    confirm_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Copiar analítica por división de lotes")
        self.setMinimumWidth(420)

        self.lbl_step = QLabel("")
        self.lbl_info = QLabel("")
        self.lbl_info.setWordWrap(True)

        self.btn_reset = QPushButton("Reset")
        self.btn_confirm = QPushButton("Confirmar Padre")
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_execute = QPushButton("Ejecutar endpoint")
        self.btn_execute.setEnabled(False)

        row = QHBoxLayout()
        row.addWidget(self.btn_reset)
        row.addWidget(self.btn_confirm)
        row.addStretch(1)
        row.addWidget(self.btn_execute)
        row.addWidget(self.btn_cancel)

        lay = QVBoxLayout()
        lay.addWidget(self.lbl_step)
        lay.addWidget(self.lbl_info)
        lay.addLayout(row)
        self.setLayout(lay)

        self.btn_cancel.clicked.connect(self.cancelled.emit)
        self.btn_reset.clicked.connect(self.reset_requested.emit)
        self.btn_confirm.clicked.connect(self.confirm_requested.emit)
        self.btn_execute.clicked.connect(self.execute_requested.emit)

        self.set_step_padre()

    def set_step_padre(self):
        self.btn_confirm.setText("Confirmar Padre")
        self.lbl_step.setText("Paso 1/2 — Seleccionar lote padre (donante)")
        self.lbl_info.setText(
            "• Click izquierdo sobre el lote padre para seleccionarlo.\n"
            "• Click derecho para confirmar el padre.\n"
            "El padre se resaltará con un color distinto."
        )
        self.btn_execute.setEnabled(False)

    def set_step_hijos(self):
        self.lbl_step.setText("Paso 2/2 — Seleccionar lote(s) hijo (receptores)")
        self.lbl_info.setText(
            "• Click izquierdo para agregar/quitar hijos.\n"
            "• Click derecho para confirmar hijos y/o ejecutar el endpoint.\n"
            "Los hijos se resaltarán con otro color."
        )
        # se habilita cuando haya padre + al menos 1 hijo (lo decide el tool)
        self.btn_execute.setEnabled(False)

    def set_execute_enabled(self, enabled: bool):
        self.btn_execute.setEnabled(bool(enabled))

    def update_counts(self, padre_ok: bool, n_hijos: int):
        # opcional: podés enriquecer el texto con contadores si querés
        pass
