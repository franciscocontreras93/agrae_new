# -*- coding: utf-8 -*-
"""
searchProxyModel.py

Proxy genérico para filtrar por texto en todas las columnas del modelo.
"""

from qgis.PyQt.QtCore import QSortFilterProxyModel, Qt, QModelIndex


class MultiColumnFilterProxy(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._needle = ""

    def set_needle(self, text: str):
        self._needle = (text or "").strip().lower()
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex):
        if not self._needle:
            return True

        model = self.sourceModel()
        if model is None:
            return True

        cols = model.columnCount()
        for c in range(cols):
            idx = model.index(source_row, c, source_parent)
            val = model.data(idx, Qt.DisplayRole)
            if val and self._needle in str(val).lower():
                return True

        return False
