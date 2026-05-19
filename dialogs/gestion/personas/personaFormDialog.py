# -*- coding: utf-8 -*-

import re

from qgis.PyQt.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QLabel,
)

from ....gui import agraeGUI
from ....core.api import APIRequest


class PersonaFormDialog(QDialog):
    def __init__(self, parent=None, item=None):
        super().__init__(parent)

        self.api = APIRequest()
        self.item = item

        self.idpersona = None
        self.required_labels = {}

        self.setWindowTitle("Nueva persona" if item is None else "Editar persona")
        self.resize(680, 260)

        self._setup_ui()
        self._connect_signals()

        if self.item:
            self._load_item()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        form = QFormLayout()
        main_layout.addLayout(form)

        # ------------------------------------------------------------------
        # CAMPOS
        # ------------------------------------------------------------------

        self.dni = QLineEdit()
        self.dni.setPlaceholderText("DNI / NIF...")

        self.ln_nombre = QLineEdit()
        self.ln_nombre.setPlaceholderText("Nombre...")
        self.ln_nombre.textChanged.connect(self._text_upper)

        self.ln_apellidos = QLineEdit()
        self.ln_apellidos.setPlaceholderText("Apellidos...")
        self.ln_apellidos.textChanged.connect(self._text_upper)

        self.ln_direccion = QLineEdit()
        self.ln_direccion.setPlaceholderText("Dirección...")

        self.ln_prinvincia = QLineEdit()
        self.ln_prinvincia.setPlaceholderText("Provincia...")
        self.ln_prinvincia.textChanged.connect(self._text_upper)

        self.ln_municipio = QLineEdit()
        self.ln_municipio.setPlaceholderText("Municipio...")
        self.ln_municipio.textChanged.connect(self._text_upper)

        self.ln_postal_code = QLineEdit()
        self.ln_postal_code.setPlaceholderText("Código postal...")
        self.ln_postal_code.setMaxLength(5)
        self.ln_postal_code.textChanged.connect(self._validate_postal_code)

        self.ln_telefono = QLineEdit()
        self.ln_telefono.setPlaceholderText("Teléfono...")
        self.ln_telefono.textChanged.connect(self._validate_phone)

        self.ln_email = QLineEdit()
        self.ln_email.setPlaceholderText("Email...")
        self.ln_email.textChanged.connect(self._validate_email)

        # ------------------------------------------------------------------
        # FILAS ORGANIZADAS
        # ------------------------------------------------------------------

        row_identificacion = QHBoxLayout()
        row_identificacion.addWidget(self.dni)

        row_nombre = QHBoxLayout()
        row_nombre.addWidget(self.ln_nombre)
        row_nombre.addWidget(self.ln_apellidos)

        row_direccion = QHBoxLayout()
        row_direccion.addWidget(self.ln_direccion)

        row_ubicacion = QHBoxLayout()
        row_ubicacion.addWidget(self.ln_postal_code)
        row_ubicacion.addWidget(self.ln_municipio)
        row_ubicacion.addWidget(self.ln_prinvincia)

        row_contacto = QHBoxLayout()
        row_contacto.addWidget(self.ln_telefono)
        row_contacto.addWidget(self.ln_email)

        self.lbl_dni = QLabel("DNI / NIF:")
        self.lbl_nombre = QLabel("Nombre / Apellidos:")
        self.lbl_direccion = QLabel("Dirección:")
        self.lbl_ubicacion = QLabel("CP / Municipio / Provincia:")
        self.lbl_contacto = QLabel("Teléfono / Email:")

        form.addRow(self.lbl_dni, row_identificacion)
        form.addRow(self.lbl_nombre, row_nombre)
        form.addRow(self.lbl_direccion, row_direccion)
        form.addRow(self.lbl_ubicacion, row_ubicacion)
        form.addRow(self.lbl_contacto, row_contacto)

        self.required_labels = {
            self.ln_nombre: self.lbl_nombre,
            self.ln_direccion: self.lbl_direccion,
        }

        # ------------------------------------------------------------------
        # BOTONES
        # ------------------------------------------------------------------

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

        self.dni.textChanged.connect(self._validate)
        self.ln_nombre.textChanged.connect(self._validate)
        self.ln_apellidos.textChanged.connect(self._validate)
        self.ln_direccion.textChanged.connect(self._validate)
        self.ln_telefono.textChanged.connect(self._validate)
        self.ln_email.textChanged.connect(self._validate)
        self.ln_prinvincia.textChanged.connect(self._validate)
        self.ln_municipio.textChanged.connect(self._validate)
        self.ln_postal_code.textChanged.connect(self._validate)

    def _load_item(self):
        self.idpersona = self.item.get("idpersona")

        self.dni.setText(self.item.get("dni", "") or "")
        self.ln_nombre.setText(self.item.get("nombre", "") or "")
        self.ln_apellidos.setText(self.item.get("apellidos", "") or "")
        self.ln_direccion.setText(self.item.get("direccion", "") or "")
        self.ln_telefono.setText(self.item.get("telefono", "") or "")
        self.ln_email.setText(self.item.get("email", "") or "")
        self.ln_prinvincia.setText(self.item.get("provincia", "") or "")
        self.ln_municipio.setText(self.item.get("municipio", "") or "")
        self.ln_postal_code.setText(self.item.get("codigo_postal", "") or "")

        self._validate()

    def _validate(self):
        nombre = self.ln_nombre.text().strip()
        direccion = self.ln_direccion.text().strip()
        email = self.ln_email.text().strip()
        codigo_postal = self.ln_postal_code.text().strip()

        email_ok = True if email == "" else self._is_valid_email(email)
        postal_ok = True if codigo_postal == "" else self._is_valid_spanish_postal_code(codigo_postal)

        self._set_input_valid(self.ln_email, email_ok)
        self._set_input_valid(self.ln_postal_code, postal_ok)

        self._set_required_label(self.ln_nombre, bool(nombre))
        self._set_required_label(self.ln_direccion, bool(direccion))

        valid = bool(nombre and direccion and email_ok and postal_ok)
        self.btn_save.setEnabled(valid)

    def _save(self):
        if not self.btn_save.isEnabled():
            QMessageBox.warning(
                self,
                "aGrae",
                "Revise los campos antes de guardar.\n\n"
                "Campos obligatorios:\n"
                "- Nombre\n"
                "- Dirección\n\n"
                "Además, si informa email o código postal, deben tener un formato válido."
            )
            return

        payload = {
            "dni": self.dni.text().strip() or None,
            "nombre": self.ln_nombre.text().strip() or None,
            "apellidos": self.ln_apellidos.text().strip() or None,
            "direccion": self.ln_direccion.text().strip() or None,
            "telefono": self.ln_telefono.text().strip() or None,
            "email": self.ln_email.text().strip() or None,
            "provincia": self.ln_prinvincia.text().strip() or None,
            "municipio": self.ln_municipio.text().strip() or None,
            "codigo_postal": self.ln_postal_code.text().strip() or None,
        }

        try:
            if self.item is None:
                r = self.api.post("gis/personas/", payload)

                data = r.get("data") or r
                self.idpersona = data.get("idpersona")

                QMessageBox.information(
                    self,
                    "aGrae",
                    f"Persona {self.ln_nombre.text().strip()} creada correctamente.\n"
                    f"ID persona: {self.idpersona}"
                )

            else:
                payload["idpersona"] = self.idpersona

                self.api.put("gis/personas", payload)

                QMessageBox.information(
                    self,
                    "aGrae",
                    f"Persona {self.ln_nombre.text().strip()} actualizada correctamente.\n"
                    f"ID persona: {self.idpersona}"
                )

            self.accept()

        except Exception as e:
            QMessageBox.warning(
                self,
                "aGrae",
                f"No se pudo guardar la persona.\nError: {e}"
            )

    def _text_upper(self, text: str):
        widget = self.sender()

        if not isinstance(widget, QLineEdit):
            return

        upper = text.upper()

        if text != upper:
            cursor_pos = widget.cursorPosition()
            widget.blockSignals(True)
            widget.setText(upper)
            widget.setCursorPosition(cursor_pos)
            widget.blockSignals(False)

        self._validate()

    def _validate_phone(self, text: str):
        clean = "".join(filter(str.isdigit, text))

        if text != clean:
            cursor_pos = self.ln_telefono.cursorPosition()
            self.ln_telefono.blockSignals(True)
            self.ln_telefono.setText(clean)
            self.ln_telefono.setCursorPosition(max(0, cursor_pos - 1))
            self.ln_telefono.blockSignals(False)

        self._validate()

    def _validate_email(self, text: str):
        email = text.strip()
        valid = True if email == "" else self._is_valid_email(email)

        self._set_input_valid(self.ln_email, valid)
        self._validate()

    def _validate_postal_code(self, text: str):
        clean = "".join(filter(str.isdigit, text))[:5]

        if text != clean:
            self.ln_postal_code.blockSignals(True)
            self.ln_postal_code.setText(clean)
            self.ln_postal_code.blockSignals(False)

        codigo_postal = self.ln_postal_code.text().strip()
        valid = True if codigo_postal == "" else self._is_valid_spanish_postal_code(codigo_postal)

        self._set_input_valid(self.ln_postal_code, valid)
        self._validate()

    def _is_valid_email(self, email: str) -> bool:
        regex = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
        return re.match(regex, email) is not None

    def _is_valid_spanish_postal_code(self, codigo_postal: str) -> bool:
        if not re.match(r"^\d{5}$", codigo_postal):
            return False

        provincia = int(codigo_postal[:2])
        return 1 <= provincia <= 52

    def _set_input_valid(self, widget: QLineEdit, valid: bool):
        if valid:
            widget.setStyleSheet("")
        else:
            widget.setStyleSheet("border: 1px solid #d9534f;")

    def _set_required_label(self, widget: QLineEdit, valid: bool):
        label = self.required_labels.get(widget)

        if label is None:
            return

        if valid:
            label.setStyleSheet("")
        else:
            label.setStyleSheet("color: #d9534f; font-weight: bold;")