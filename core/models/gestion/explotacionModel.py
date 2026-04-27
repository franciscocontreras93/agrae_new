from qgis.PyQt.QtCore import Qt, QAbstractTableModel, QModelIndex


def safe_get(d: dict, path: str, default=""):
    cur = d or {}
    for k in path.split("."):
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur.get(k)
    return default if cur is None else cur


def map_explotacion(raw):
    items = []

    for r in (raw or []):
        items.append({
            "idexplotacion": int(r.get("idexplotacion") or 0),
            "nombre": r.get("nombre", ""),
            "direccion": r.get("direccion", ""),
            "agricultores": r.get("agricultores", 0),
        })

    return items


class ExplotacionesTableModel(QAbstractTableModel):

    COLS = [
        ("ID Explotación", "idexplotacion"),
        ("Nombre", "nombre"),
        ("Dirección", "direccion"),
        ("Agricultores", "agricultores"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = []

    def set_items(self, items: list[dict]):
        self.beginResetModel()
        self._items = items or []
        self.endResetModel()

    def items(self) -> list[dict]:
        return self._items

    def item_at(self, row: int) -> dict | None:
        if 0 <= row < len(self._items):
            return self._items[row]
        return None

    def rowCount(self, parent=QModelIndex()):
        return len(self._items)

    def columnCount(self, parent=QModelIndex()):
        return len(self.COLS)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal:
            return self.COLS[section][0]

        return section + 1

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()

        if row < 0 or row >= len(self._items):
            return None

        item = self._items[row]
        _, path = self.COLS[col]

        if role == Qt.DisplayRole:
            val = safe_get(item, path, "")
            return "" if val is None else str(val)

        if role == Qt.UserRole:
            return item

        return None