from qgis.PyQt.QtCore import QSortFilterProxyModel, Qt, QModelIndex


class MultiColumnFilterProxy(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._needle = ""
        self._column_filters = {}  # {column_index: text}

    def set_needle(self, text: str):
        self._needle = (text or "").strip().lower()
        self.invalidateFilter()

    def set_column_filter(self, column: int, text: str):
        text = (text or "").strip().lower()
        if text:
            self._column_filters[column] = text
        elif column in self._column_filters:
            del self._column_filters[column]

        self.invalidateFilter()

    def clear_column_filters(self):
        self._column_filters.clear()
        self.invalidateFilter()

    def clear_all_filters(self):
        self._needle = ""
        self._column_filters.clear()
        self.invalidateFilter()

    def _match_global(self, model, source_row: int, source_parent: QModelIndex) -> bool:
        if not self._needle:
            return True

        cols = model.columnCount()
        for c in range(cols):
            idx = model.index(source_row, c, source_parent)
            val = model.data(idx, Qt.DisplayRole)
            if val and self._needle in str(val).lower():
                return True

        return False

    def _match_columns(self, model, source_row: int, source_parent: QModelIndex) -> bool:
        if not self._column_filters:
            return True

        for col, needle in self._column_filters.items():
            idx = model.index(source_row, col, source_parent)
            val = model.data(idx, Qt.DisplayRole)
            val = "" if val is None else str(val).lower()

            if needle not in val:
                return False

        return True

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex):
        model = self.sourceModel()
        if model is None:
            return True

        return self._match_global(model, source_row, source_parent) and self._match_columns(model, source_row, source_parent)
    

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Vertical:
            return section + 1
        return super().headerData(section, orientation, role)