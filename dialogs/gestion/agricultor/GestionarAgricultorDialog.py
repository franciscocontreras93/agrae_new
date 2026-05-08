# -*- coding: utf-8 -*-

from qgis.PyQt.QtCore import pyqtSignal, QSize
from qgis.PyQt.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QPushButton,
    QMessageBox,
)

from ....gui import agraeGUI
from ....gui.components.searchTableWidget import AgricultorSearchTable

from ..asesores import GestionarAsesoresDialog

from .agricultor_form_dialog import AgricultorFormDialog

from ....core.api import APIRequest


class GestionAgricultorDialog(QDialog):
    closingPlugin = pyqtSignal()
    idAgricultorSignal = pyqtSignal(object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Gestionar Agricultores")
        self.resize(980, 560)

        self._setup_ui()
        self._connect_signals()
        self.search_table.reload()

        self.api = APIRequest()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)

        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)
        main_layout.addLayout(content_layout)

        self.search_table = AgricultorSearchTable(self)
        content_layout.addWidget(self.search_table, 1)

        right_panel = QWidget(self)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(6)

        right_layout.addStretch()

        self.btn_asesor = QPushButton()
        self.btn_asesor.setFixedSize(42, 42)
        self.btn_asesor.setIcon(agraeGUI().getIcon("user"))
        self.btn_asesor.setIconSize(QSize(22, 22))
        self.btn_asesor.setToolTip("Asignar Asesor al Agricultor Seleccionado")
        right_layout.addWidget(self.btn_asesor)

        self.btn_edit = QPushButton()
        self.btn_edit.setFixedSize(42, 42)
        self.btn_edit.setIcon(agraeGUI().getIcon("edit"))
        self.btn_edit.setIconSize(QSize(22, 22))
        self.btn_edit.setToolTip("Editar agricultor seleccionado")
        right_layout.addWidget(self.btn_edit)
        

        self.btn_add = QPushButton()
        self.btn_add.setFixedSize(42, 42)
        self.btn_add.setIcon(agraeGUI().getIcon("add"))
        self.btn_add.setIconSize(QSize(22, 22))
        self.btn_add.setToolTip("Añadir nuevo agricultor")
        right_layout.addWidget(self.btn_add)

        self.btn_reload = QPushButton()
        self.btn_reload.setFixedSize(42, 42)
        self.btn_reload.setIcon(agraeGUI().getIcon("reload"))
        self.btn_reload.setIconSize(QSize(22, 22))
        self.btn_reload.setToolTip("Recargar lista de agricultores")
        right_layout.addWidget(self.btn_reload)

        self.btn_delete = QPushButton()
        self.btn_delete.setFixedSize(42, 42)
        self.btn_delete.setIcon(agraeGUI().getIcon("trash"))
        self.btn_delete.setIconSize(QSize(22, 22))
        self.btn_delete.setToolTip("Eliminar agricultor seleccionado")
        self.btn_delete.setEnabled(False)
        right_layout.addWidget(self.btn_delete)

        right_layout.addStretch()

        content_layout.addWidget(right_panel, 0)

    def _connect_signals(self):
        self.search_table.rowDoubleClicked.connect(self._on_row_double_clicked)
        self.search_table.table.selectionModel().selectionChanged.connect(self._on_selection_changed)
        self.btn_delete.clicked.connect(self._delete_selected)
        self.btn_reload.clicked.connect(self.search_table.reload)
        self.btn_add.clicked.connect(self._add_new_agricultor)
        self.btn_asesor.clicked.connect(self._dialog_asesor)

    def _on_row_double_clicked(self, value, item):
        self.idAgricultorSignal.emit(item)

    def _on_selection_changed(self, *args):
        item = self.search_table.selected_item()
        self.btn_delete.setEnabled(bool(item))

    def _add_new_agricultor(self):
        dialog = AgricultorFormDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.search_table.reload()

    def _dialog_asesor(self):
        item = self.search_table.selected_item()
        if not item:
            QMessageBox.information(self, "aGrae", "Selecciona un agricultor.")
            return

        agricultor = item
        dialog = GestionarAsesoresDialog(self)
        dialog.AsesorSignal.connect(lambda asesor: self._asignar_asesor(agricultor, asesor))
        dialog.exec_()

    def _asignar_asesor(self, agricultor, asesor):
        data = {
            "idagricultor": int(agricultor.get("idagricultor")),
            "idasesor": int(asesor.get("idasesor")),
        }


        try:
            confirm = QMessageBox.question(
                self,
                "Confirmar asignación",
                f"¿Asignar asesor {asesor.get('nombre', 'desconocido')} al agricultor {agricultor.get('persona', {}).get('nombre_completo', 'desconocido')}?"
            )
            if confirm != QMessageBox.Yes:
                return
            
            r = self.api.patch("gis/agricultores/update/asignar-asesor", data)

            if r.get("http_status") != 200:
                raise Exception(
                    f"HTTP {r.get('http_status')} - {r.get('data')}"
                )

            QMessageBox.information(
                self,
                "aGrae",
                "Asesor {} asignado al agricultor: {} correctamente.".format(
                    asesor.get("nombre", "desconocido"),
                    agricultor.get("persona", {}).get("nombre_completo", "desconocido")
                )
            )

            self.search_table.reload()

        except Exception as e:
            QMessageBox.warning(
                self,
                "aGrae",
                f"No se pudo asignar el asesor al agricultor.\nError: {str(e)}"
            )


    def _delete_selected(self):
        item = self.search_table.selected_item()
        if not item:
            QMessageBox.information(self, "aGrae", "Selecciona un agricultor.")
            return

        idagricultor = item.get("idagricultor")
        nombre = ((item.get("persona") or {}).get("nombre_completo", "")).strip()
        explotacion = ((item.get("explotacion") or {}).get("nombre", "")).strip()

        resp = QMessageBox.question(
            self,
            "Eliminar agricultor",
            f"¿Quieres eliminar a {nombre or 'este agricultor'} de la explotación {explotacion or 'desconocida'}?"
        )
        if resp != QMessageBox.Yes:
            return
        try:
            r = self.api.delete(f"gis/agricultores/{idagricultor}")

            if r.get("http_status") != 204:
                raise Exception(f"HTTP {r.get('http_status')}")
            
            QMessageBox.information(
                self,
                "aGrae",
                f"Agricultor {nombre or idagricultor} de la explotación {explotacion or 'desconocida'} eliminado."
            )

            self.search_table.reload()
        except Exception as e:
            QMessageBox.warning(
                self,
                "aGrae",
                f"No se pudo eliminar el agricultor {nombre or idagricultor} de la explotación {explotacion or 'desconocida'}.\nError: {str(e)}"
            )
        # QMessageBox.information(
        #     self,
        #     "aGrae",
        #     f"Aquí luego conectamos el DELETE del agricultor {idagricultor}."
        # )

    def selected_item(self):
        return self.search_table.selected_item()

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()