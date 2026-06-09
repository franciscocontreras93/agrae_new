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

# from ...gestion_personas import  GestionPersonasDialog

from ..personas import GestionarPersonasDialog
from ..explotacion import GestionarExplotacionDialog
from ..asesores import GestionarAsesoresDialog
from ..distribuidor import GestionarDistribuidoresDialog



class AgricultorFormDialog(QDialog):

    def __init__(self, parent=None, item=None):
        super().__init__(parent)

        self.api = APIRequest()
        self.item = item

        self.idpersona = None
        self.idexplotacion = None
        self.iddistribuidor = None

        self.setWindowTitle("Nuevo agricultor" if item is None else "Editar agricultor")
        self.resize(520, 180)

        self._setup_ui()
        self._connect_signals()

        if self.item:
            self._load_item()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        form = QFormLayout()
        main_layout.addLayout(form)

        self.ln_persona = QLineEdit()
        self.ln_persona.setReadOnly(True)
        self.ln_persona.setPlaceholderText("Seleccionar persona...")
        self.ln_persona.addAction(agraeGUI().getIcon("user"), QLineEdit.TrailingPosition)

        self.ln_explotacion = QLineEdit()
        self.ln_explotacion.setReadOnly(True)
        self.ln_explotacion.setPlaceholderText("Seleccionar explotación...")
        self.ln_explotacion.addAction(agraeGUI().getIcon("explotacion"), QLineEdit.TrailingPosition)

        self.ln_distribuidor = QLineEdit()
        self.ln_distribuidor.setReadOnly(True)
        self.ln_distribuidor.setPlaceholderText("Seleccionar distribuidor...")
        self.ln_distribuidor.addAction(agraeGUI().getIcon("handshake"), QLineEdit.TrailingPosition)

        self.ln_asesor = QLineEdit()
        self.ln_asesor.setReadOnly(True)
        self.ln_asesor.setPlaceholderText("Seleccionar asesor...")
        self.ln_asesor.addAction(agraeGUI().getIcon("user"), QLineEdit.TrailingPosition)

        form.addRow("Persona:", self.ln_persona)
        form.addRow("Explotación:", self.ln_explotacion)
        form.addRow("Distribuidor:", self.ln_distribuidor)
        form.addRow("Asesor:", self.ln_asesor)
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

        # Más adelante aquí abrimos los selectores modernos:
        self.ln_persona.mousePressEvent = self._open_persona_selector
        self.ln_explotacion.mousePressEvent = self._open_explotacion_selector
        self.ln_distribuidor.mousePressEvent = self._open_distribuidor_selector
        self.ln_asesor.mousePressEvent = self._open_asesor_selector
    def _load_item(self):
        persona = (self.item.get("persona") or {})
        explotacion = (self.item.get("explotacion") or {})
        distribuidor = (self.item.get("distribuidor") or {})
        asesor = (self.item.get("asesor") or {})
        self.idpersona = persona.get("idpersona")
        self.idexplotacion = explotacion.get("idexplotacion")
        self.iddistribuidor = distribuidor.get("iddistribuidor")
        self.idasesor = asesor.get("idasesor")

        self.ln_persona.setText(persona.get("nombre_completo", ""))
        self.ln_explotacion.setText(explotacion.get("nombre", ""))
        self.ln_distribuidor.setText(distribuidor.get("nombre", ""))

        self._validate()

    def _open_persona_selector(self, event):
        # TODO: conectar diálogo/componente nuevo de personas
        QLineEdit.mousePressEvent(self.ln_persona, event)

        dlg = GestionarPersonasDialog(self)
        dlg.PersonaSignal.connect(self.set_persona)
        dlg.exec_()

        # QMessageBox.information(self, "aGrae", "Aquí conectamos selector de persona.")

    def _open_explotacion_selector(self, event):
        QLineEdit.mousePressEvent(self.ln_explotacion, event)
        dlg = GestionarExplotacionDialog(self)
        dlg.ExplotacionSignal.connect(self.set_explotacion)
        dlg.exec_()


    def _open_distribuidor_selector(self, event):
        QLineEdit.mousePressEvent(self.ln_distribuidor, event)
        dlg = GestionarDistribuidoresDialog(self)
        dlg.DistribuidorSignal.connect(self.set_distribuidor)
        dlg.exec_()

        # # TODO: conectar diálogo/componente nuevo de distribuidor
        # QMessageBox.information(self, "aGrae", "Aquí conectamos selector de distribuidor.")

    def _open_asesor_selector(self, event):
        QLineEdit.mousePressEvent(self.ln_asesor, event)
        dlg = GestionarAsesoresDialog(self)
        dlg.AsesorSignal.connect(self.set_asesor)
        dlg.exec_()


    def set_persona(self, item: dict):
        if not item:
            return

        self.idpersona = item.get("idpersona")
        self.ln_persona.setText(item.get("nombre_completo", ""))
        self._validate()

    def set_explotacion(self, item: dict):
        if not item:
            return

        self.idexplotacion = item.get("idexplotacion")
        self.ln_explotacion.setText(item.get("nombre", ""))
        self._validate()

    def set_distribuidor(self, item: dict):
        if not item:
            return

        self.iddistribuidor = item.get("iddistribuidor")
        self.ln_distribuidor.setText(item.get("nombre", ""))
        self._validate()

    def set_asesor(self, item: dict):
        if not item:
            return

        self.idasesor = item.get("idasesor")
        self.ln_asesor.setText(item.get("nombre", ""))
        self._validate()

    def _validate(self):
        ok = bool(self.idpersona and self.idexplotacion and self.iddistribuidor)
        
        self.btn_save.setEnabled(ok)

    def _save(self):
        payload = {
            "idpersona": self.idpersona,
            "idexplotacion": self.idexplotacion,
            "iddistribuidor": self.iddistribuidor or 25,  # Distribuidor "aGrae" por defecto
            "idasesor": self.idasesor
        }

        try:
            if self.item is None:
                r = self.api.post("gis/agricultores/", payload)
                # print(r)
                # http_status = r.get("http_status")
                # if http_status not in (200, 201):
                #     raise Exception(f"HTTP {http_status}")
            # else:
            #     idagricultor = self.item.get("idagricultor")
            #     r = self.api.put(f"gis/agricultores/{idagricultor}/", payload)
            #     http_status = r.get("http_status")
            #     if http_status not in (200, 204):
            #         raise Exception(f"HTTP {http_status}")
                
            # print(r)

                QMessageBox.information(self, "aGrae", "Agricultor creado correctamente.")

            self.accept()

        except Exception as e:
            QMessageBox.warning(
                self,
                "aGrae",
                f"No se pudo guardar el agricultor.\nError: {e}"
            )