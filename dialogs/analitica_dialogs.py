# -*- coding: utf-8 -*-
import pandas as pd

from qgis.PyQt import QtWidgets, QtCore
from qgis.core import *
from ..gui import agraeGUI
from ..tools import aGraeTools


class PandasModel(QtCore.QAbstractTableModel):
    """Modelo simple para mostrar un DataFrame en QTableView (headers = df.columns)."""
    def __init__(self, df: pd.DataFrame = None, parent=None):
        super().__init__(parent)
        self._df = df.copy() if df is not None else pd.DataFrame()

    def setDataFrame(self, df: pd.DataFrame):
        self.beginResetModel()
        self._df = df.copy()
        self.endResetModel()

    def dataframe(self) -> pd.DataFrame:
        return self._df.copy()

    def rowCount(self, parent=QtCore.QModelIndex()):
        return 0 if parent.isValid() else len(self._df)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return 0 if parent.isValid() else len(self._df.columns)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid() or role not in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            return None
        val = self._df.iat[index.row(), index.column()]
        if pd.isna(val):
            return ""
        return f"{val:.6g}" if isinstance(val, float) else str(val)

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role != QtCore.Qt.DisplayRole:
            return None
        if orientation == QtCore.Qt.Horizontal:
            try:
                return str(self._df.columns[section])
            except Exception:
                return ""
        return str(section + 1)  # numeración de filas


class agraeAnaliticaDialog(QtWidgets.QDialog):
    def __init__(self, data: pd.DataFrame, file_path: str = None, parent=None):
        super().__init__(parent)
        self.df = data if data is not None else pd.DataFrame()
        self.file_path = file_path
        self.tools = aGraeTools()

        self.setWindowTitle('aGrae Tools | Importar o actualizar analíticas')
        self.setModal(False)
        self.setMinimumSize(900, 600)

        # --- QTableView ---
        self._tableView = QtWidgets.QTableView(self)
        self._tableView.setSortingEnabled(True)
        self._tableView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self._tableView.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self._tableView.horizontalHeader().setStretchLastSection(True)

        # --- ToolButton a la derecha ---
        self.toolButton = QtWidgets.QToolButton(self)
        self.toolButton.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.toolButton.setPopupMode(QtWidgets.QToolButton.InstantPopup)

        # --- Layout principal: tabla (col 0), botón (col 1) ---
        grid = QtWidgets.QGridLayout(self)
        grid.addWidget(self._tableView, 0, 0)  # tabla a la izquierda
        grid.addWidget(self.toolButton, 0, 1, alignment=QtCore.Qt.AlignTop)  # botón a la derecha, arriba
        grid.setColumnStretch(0, 1)   # que la tabla se expanda
        grid.setColumnStretch(1, 0)   # columna del botón fija

        # --- Modelo ---
        self._model = PandasModel(self.df, self)
        self._tableView.setModel(self._model)

        # --- Acciones y flujo ---
        self.UIComponents()
        self.loadData()

    def UIComponents(self):
        self.GuardarDatosAnalisis = QtWidgets.QAction(
            agraeGUI().getIcon('upload'),
            'Importar o actualizar analíticas',
            self
        )
        self.GuardarDatosAnalisis.triggered.connect(self.guardarAnalitica)

        # Puedes seguir usando tu helper; con una sola acción funciona bien.
        self.tools.settingsToolsButtons(
            self.toolButton,
            [self.GuardarDatosAnalisis],
            icon=agraeGUI().getIcon('tools'),
            setMainIcon=True
        )

    def loadData(self):
        self._model.setDataFrame(self.df)
        self._tableView.resizeColumnsToContents()
        self._tableView.horizontalHeader().setStretchLastSection(True)

    def guardarAnalitica(self):
        total = len(self.df.index)
        if total == 0:
            self.tools.messages(
                'aGrae GIS',
                'No hay analíticas para importar.',
                Qgis.Warning
            )
            return

        reply = QtWidgets.QMessageBox.question(
            self,
            'aGrae GIS | Importar analíticas',
            f'¿Quieres importar o actualizar {total} analíticas?',
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        if reply != QtWidgets.QMessageBox.Yes:
            return

        self.GuardarDatosAnalisis.setEnabled(False)
        self.toolButton.setEnabled(False)
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        QtWidgets.QApplication.processEvents()

        try:
            imported = (
                self.tools.importarAnaliticaCsv(self.file_path)
                if self.file_path
                else self.tools.importarAnalitica(self.df)
            )
            self.tools.messages(
                'aGrae GIS',
                f'{imported} analíticas cargadas correctamente.',
                Qgis.Success,
                True
            )
            self.accept()
        except Exception as error:
            QgsMessageLog.logMessage(
                f'Error al importar analíticas: {error}',
                'aGrae Lab',
                Qgis.Critical
            )
            self.tools.messages(
                'aGrae GIS',
                f'Error al importar las analíticas: {error}',
                Qgis.Critical,
                True
            )
        finally:
            while QtWidgets.QApplication.overrideCursor() is not None:
                QtWidgets.QApplication.restoreOverrideCursor()
            self.GuardarDatosAnalisis.setEnabled(True)
            self.toolButton.setEnabled(True)
