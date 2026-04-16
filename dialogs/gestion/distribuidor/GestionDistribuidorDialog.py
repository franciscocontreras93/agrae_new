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
from ....gui.components.searchTableWidget import DistribuidorSearchTable
from ....core.api import APIRequest


class GestionarDistribuidoresDialog(QDialog):
    closingPlugin = pyqtSignal()
    DistribuidorSignal = pyqtSignal(object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Gestionar Distribuidores")
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

        self.search_table = DistribuidorSearchTable(self)
        content_layout.addWidget(self.search_table, 1)

        right_panel = QWidget(self)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(6)

        right_layout.addStretch()

        self.btn_add = QPushButton()
        self.btn_add.setFixedSize(42, 42)
        self.btn_add.setIcon(agraeGUI().getIcon("add"))
        self.btn_add.setIconSize(QSize(22, 22))
        self.btn_add.setToolTip("Añadir nuevo distribuidor")
        right_layout.addWidget(self.btn_add)

        self.btn_reload = QPushButton()
        self.btn_reload.setFixedSize(42, 42)
        self.btn_reload.setIcon(agraeGUI().getIcon("reload"))
        self.btn_reload.setIconSize(QSize(22, 22))
        self.btn_reload.setToolTip("Recargar lista de distribuidores")
        right_layout.addWidget(self.btn_reload)

        self.btn_delete = QPushButton()
        self.btn_delete.setFixedSize(42, 42)
        self.btn_delete.setIcon(agraeGUI().getIcon("trash"))
        self.btn_delete.setIconSize(QSize(22, 22))
        self.btn_delete.setToolTip("Eliminar distribuidor seleccionado")
        self.btn_delete.setEnabled(False)
        right_layout.addWidget(self.btn_delete)

        right_layout.addStretch()

        content_layout.addWidget(right_panel, 0)

    def _connect_signals(self):
        self.search_table.rowDoubleClicked.connect(self._on_row_double_clicked)
        self.search_table.table.selectionModel().selectionChanged.connect(self._on_selection_changed)
        self.btn_delete.clicked.connect(self._delete_selected)
        self.btn_reload.clicked.connect(self.search_table.reload)
        self.btn_add.clicked.connect(self._add_new_distribuidor)

    def _on_row_double_clicked(self, value, item):
        self.DistribuidorSignal.emit(item)
        self.accept()

    def _on_selection_changed(self, *args):
        item = self.search_table.selected_item()
        self.btn_delete.setEnabled(bool(item))

    def _add_new_distribuidor(self):
        pass

    def _delete_selected(self):
        item = self.search_table.selected_item()
        if not item:
            QMessageBox.information(self, "aGrae", "Selecciona un distribuidor.")
            return

        iddistribuidor = item.get("iddistribuidor")
        nombre = (item.get("nombre_completo", "")).strip()

        resp = QMessageBox.question(
            self,
            "Eliminar distribuidor",
            f"¿Quieres eliminar a {nombre or 'este distribuidor'}?"
        )
        if resp != QMessageBox.Yes:
            return

        try:
            r = self.api.delete(f"gis/distribuidores/{iddistribuidor}/")

            if r.get("http_status") != 204:
                raise Exception(f"HTTP {r.get('http_status')}")

            QMessageBox.information(
                self,
                "aGrae",
                f"Distribuidor {nombre or iddistribuidor} eliminado."
            )

            self.search_table.reload()

        except Exception as e:
            QMessageBox.warning(
                self,
                "aGrae",
                f"No se pudo eliminar el distribuidor {nombre or iddistribuidor}.\nError: {str(e)}"
            )

    def selected_item(self):
        return self.search_table.selected_item()

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()