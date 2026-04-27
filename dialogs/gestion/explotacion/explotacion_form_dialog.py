# -*- coding: utf-8 -*-

from qgis.PyQt.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QMessageBox,
)

from ....gui import agraeGUI
from ....core.api import APIRequest


class ExplotacionFormDialog(QDialog):
    def __init__(self, parent=None, item=None):
        super().__init__(parent)

        self.api = APIRequest()
        self.item = item

        self.idexplotacion = None

        self.setWindowTitle("Nueva explotación" if item is None else "Editar explotación")
        self.resize(520, 160)

        self._setup_ui()
        self._connect_signals()

        if self.item:
            self._load_item()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        form = QFormLayout()
        main_layout.addLayout(form)

        self.ln_nombre = QLineEdit()
        self.ln_nombre.setPlaceholderText("Nombre de la explotación...")
        self.ln_nombre.textChanged.connect(self._on_nombre_changed)

        self.ln_direccion = QLineEdit()
        self.ln_direccion.setPlaceholderText("Dirección...")

        form.addRow("Nombre:", self.ln_nombre)
        form.addRow("Dirección:", self.ln_direccion)

        btns = QHBoxLayout()
        main_layout.addLayout(btns)

        btns.addStretch()

        self.btn_cancel = QPushButton("Cancelar")
        self.btn_save = QPushButton("Guardar")
        self.btn_save.setIcon(agraeGUI().getIcon("save"))
        self.btn_save.setEnabled(False)

        btns.addWidget(self.btn_cancel)
        btns.addWidget(self.btn_save)

    def _connect_signals(self):
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_save.clicked.connect(self._save)

        self.ln_nombre.textChanged.connect(self._validate)
        self.ln_direccion.textChanged.connect(self._validate)

    def _load_item(self):
        self.idexplotacion = self.item.get("idexplotacion")
        self.ln_nombre.setText(self.item.get("nombre", ""))
        self.ln_direccion.setText(self.item.get("direccion", ""))
        self._validate()

    def _validate(self):
        nombre = self.ln_nombre.text().strip()
        direccion = self.ln_direccion.text().strip()
        self.btn_save.setEnabled(bool(nombre and direccion))

    def _save(self):
        payload = {
            "nombre": self.ln_nombre.text().strip(),
            "direccion": self.ln_direccion.text().strip(),
        }

        try:
            if self.item is None:
                r = self.api.post("gis/explotaciones/", payload)
                
                # http_status = r.get("http_status")
                # if http_status not in (200, 201):
                #     raise Exception(f"HTTP {http_status}")

                data = r.get("data") or r
                self.idexplotacion = data.get("idexplotacion")

                QMessageBox.information(
                    self,
                    "aGrae",
                    f"Explotación {self.ln_nombre.text().strip()} creada correctamente.\nID explotación: {self.idexplotacion}"
                )
            #     )
            else:
                payload["idexplotacion"] = self.idexplotacion
                
                r = self.api.put(f"gis/explotaciones", payload)
                # http_status = r.get("http_status")

                # if http_status not in (200, 204):
                #     raise Exception(f"HTTP {http_status}")

                QMessageBox.information(
                    self,
                    "aGrae",
                    f"Explotación {self.ln_nombre.text().strip()} actualizada correctamente.\nID explotación: {self.idexplotacion}")

            self.accept()

        except Exception as e:
            QMessageBox.warning(
                self,
                "aGrae",
                f"No se pudo guardar la explotación.\nError: {e}"
            )
    
    def _on_nombre_changed(self, text: str):
        upper = text.upper()
        if text != upper:
            cursor_pos = self.ln_nombre.cursorPosition()
            self.ln_nombre.blockSignals(True)
            self.ln_nombre.setText(upper)
            self.ln_nombre.setCursorPosition(cursor_pos)
            self.ln_nombre.blockSignals(False)

        self._validate()