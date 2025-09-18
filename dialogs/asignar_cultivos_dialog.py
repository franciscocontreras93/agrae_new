# asignar_cultivos_dialog.py (versión sin .ui)

from typing import List, Optional, Dict, Any, Tuple
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal, Qt, QDate
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QGroupBox, QGridLayout, QLabel,
    QSpinBox, QHBoxLayout, QPushButton, QMessageBox, QDateEdit, QCheckBox
)

# Componentes custom que ya usas en tu proyecto
from ..gui.components.CustomComboBox import CultivosComboBox, RegimenComboBox
from ..tools import aGraeTools


class AsignarCultivosDialog(QDialog):
    """
    Diálogo para asignar cultivo/régimen/producción esperada/fechas siembra y cosecha a múltiples lotes.
    - Usa CultivosComboBox y RegimenComboBox.
    - Mantiene la acción existente con aGraeTools.asignarMultiplesCultivos(...) para no romper flujos.
    - Expone get_backend_payloads() por si quieres migrar a tu endpoint PATCH.
    """
    idCultivoSignal = pyqtSignal(int)

    def __init__(self, iddata: List[int], dates:Tuple[QDate, QDate], parent: Optional[QtWidgets.QWidget] = None):
        """
        Args:
            iddata: lista de iddata de los lotes seleccionados
        """
        super().__init__(parent)
        self.setWindowTitle("aGrae Tools | Asignar Cultivos a los Lotes Seleccionados")
        self.setMinimumWidth(460)
        self.setWindowModality(Qt.ApplicationModal)

        self.tools = aGraeTools()
        self.iddata = iddata or []
        self.dates = dates

        self._build_ui()
        self._wire_events()

    # ---------------- UI ----------------

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        group_box = QGroupBox("Parámetros de asignación")
        group_layout = QGridLayout()

        # Combos custom
        self.combo_cultivo = CultivosComboBox(auto_enable_on_load=True)
        self.combo_regimen = RegimenComboBox(auto_enable_on_load=True)

        # Producción esperada
        self.ln_prod = QSpinBox()
        self.ln_prod.setDisplayIntegerBase(10)
        self.ln_prod.setMaximum(1000000)
        self.ln_prod.setSuffix(" Kg/ha")
        self.ln_prod.setSingleStep(500)
        self.ln_prod.setToolTip("Producción esperada en Kg/ha")
        self.ln_prod.setValue(0)

        self.fecha_siembra = QDateEdit()
        self.fecha_siembra.setCalendarPopup(True)
        self.fecha_siembra.setDisplayFormat("dd/MM/yyyy")
        self.fecha_siembra.setDate(QDate.currentDate())
        self.fecha_siembra.setToolTip("Fecha de siembra (opcional)")
        self.fecha_siembra.setEnabled(False)  # Deshabilitada por defecto
        self.fecha_siembra.setMinimumDate(self.dates[0])
        self.fecha_siembra.setMaximumDate(self.dates[1])

        self.fecha_cosecha = QDateEdit()
        self.fecha_cosecha.setCalendarPopup(True)
        self.fecha_cosecha.setDisplayFormat("dd/MM/yyyy")
        self.fecha_cosecha.setDate(QDate.currentDate())
        self.fecha_cosecha.setToolTip("Fecha de cosecha (opcional)")
        self.fecha_cosecha.setEnabled(False)  # Deshabilitada por defecto
        self.fecha_cosecha.setMinimumDate(self.dates[0])
        self.fecha_cosecha.setMaximumDate(self.dates[1])

        self.check_siembra = QtWidgets.QCheckBox("Fecha Siembra")
        self.check_siembra.setToolTip("Habilitar para asignar fecha de siembra")
        self.check_siembra.toggled.connect(self.fecha_siembra.setEnabled)



        self.check_cosecha = QtWidgets.QCheckBox("Fecha Cosecha")
        self.check_cosecha.setToolTip("Habilitar para asignar fecha de cosecha")
        self.check_cosecha.toggled.connect(self.fecha_cosecha.setEnabled)


        

        # Formulario
        group_layout.addWidget(QLabel("Cultivo"), 0, 0)
        group_layout.addWidget(self.combo_cultivo, 0, 1)
        group_layout.addWidget(QLabel("Régimen"), 1, 0)
        group_layout.addWidget(self.combo_regimen, 1, 1)
        group_layout.addWidget(QLabel("Producción esperada"), 2, 0)
        group_layout.addWidget(self.ln_prod, 2, 1)
        group_layout.addWidget(self.check_siembra, 3, 0)
        group_layout.addWidget(self.fecha_siembra, 3, 1)
        group_layout.addWidget(self.check_cosecha, 4, 0)
        group_layout.addWidget(self.fecha_cosecha, 4, 1)

        group_box.setLayout(group_layout)
        main_layout.addWidget(group_box)

        # Botonera
        btns = QHBoxLayout()
        btns.addStretch(1)
        self.btn_asignar = QPushButton("Asignar")
        self.btn_asignar.setDefault(True)
        self.btn_cancelar = QPushButton("Cancelar")
        btns.addWidget(self.btn_asignar)
        btns.addWidget(self.btn_cancelar)
        main_layout.addLayout(btns)

        # Accesos rápidos
        self.btn_asignar.setShortcut("Ctrl+Return")
        self.btn_cancelar.setShortcut("Esc")

    def _wire_events(self):
        self.btn_asignar.clicked.connect(self._on_asignar)
        self.btn_cancelar.clicked.connect(self.reject)

        # Señal útil si en otra parte quieres reaccionar a un cambio de cultivo
        self.combo_cultivo.currentIndexChanged.connect(self._emit_selected_cultivo_id)

    def _emit_selected_cultivo_id(self):
        try:
            get_id = getattr(self.combo_cultivo, "get_current_id", None)
            cid = get_id() if callable(get_id) else self.combo_cultivo.currentData()
            if cid is not None:
                self.idCultivoSignal.emit(int(cid))
        except Exception:
            pass

    # ------------- Lógica principal -------------

    def _on_asignar(self):
        """
        Flujo actual: usa aGraeTools.asignarMultiplesCultivos(...) para no romper tu lógica.
        Si prefieres backend, más abajo tienes get_backend_payloads() para pegarle al PATCH.
        """
        idcultivo = self.combo_cultivo.get_current_id()
        idregimen = self.combo_regimen.get_current_id()
        prod_esperada = float(self.ln_prod.value())

        if idcultivo is None or idregimen is None:
            QMessageBox.warning(self, "aGrae Toolbox", "Selecciona un Cultivo y un Régimen.")
            return

        if not self.iddata:
            QMessageBox.information(self, "aGrae Toolbox", "No hay lotes seleccionados.")
            return

        reply = QMessageBox.question(
            self,
            "Confirmar asignación",
            f'¿Asignar el cultivo "{self.combo_cultivo.currentText()}" '
            f'al régimen "{self.combo_regimen.currentText()}" '
            f'a los {len(self.iddata)} lotes seleccionados?',
            QMessageBox.Yes, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        try:
            # === Lógica actual (local) ===
            # self.tools.asignarMultiplesCultivos(idcultivo, idregimen, prod_esperada, self.iddata)

            # Si migras al backend, comenta la línea anterior y usa tu cliente HTTP aquí.
            # Por ejemplo, iterando self.get_backend_payloads(...) con PATCH /{iddata}
            # print(self.get_backend_payloads()) 

            payload = self.get_backend_payloads()

            self.tools.updateMultiLoteInfo(payload)
            

            QMessageBox.information(self, "aGrae Toolbox", "Asignación completada.")
            self.accept()

        except Exception as ex:
            QMessageBox.critical(self, "aGrae Toolbox", f"Error al asignar cultivos:\n{ex}")


    # ------------- Soporte migración a backend -------------

    def get_backend_payloads(self) -> List[Dict[str, Any]]:
        """
        Genera una lista de {iddata, payload} lista para PATCH /{iddata}
        (si decides dejar de usar aGraeTools y migrar a FastAPI).

        Returns:
            
              {"iddata": 123, "payload": {"data_campania": {...}}},
              ...
            
        """
        idcultivo = self.combo_cultivo.get_current_id()
        idregimen = self.combo_regimen.get_current_id()
        prod_esperada = float(self.ln_prod.value())

        payload = {
            "iddata" : self.iddata,
            "idcultivo": idcultivo,
            "idregimen": idregimen,
            "prod_esperada": prod_esperada,
            "fechasiembra": None,
            "fechacosecha": None
        }
        # Si más adelante agregas fechas opcionales aquí, solo añade las claves si existen (o usa None para borrar).

        if self.check_siembra.isChecked():
            payload["fechasiembra"] = self.fecha_siembra.date().toString("yyyy-MM-dd")

        if self.check_cosecha.isChecked():
            payload["fechacosecha"] = self.fecha_cosecha.date().toString("yyyy-MM-dd")


        return payload

    # ------------- Helpers de construcción -------------

    @classmethod
    def from_selection(cls, selected_iddata: List[int], parent=None) -> "AsignarCultivosDialog":
        """
        Conveniencia: crea el diálogo desde una selección existente de iddata.
        """
        return cls(selected_iddata, parent)
