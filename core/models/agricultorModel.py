# -*- coding: utf-8 -*-
"""
agricultorModel.py

Modelo Qt (QAbstractTableModel) para mostrar Agricultores en QTableView.

Columnas:
- idagricultor
- persona (nombre completo)
- explotación (nombre)
- dirección (explotación)

Uso:
    from .agricultorModel import AgricultoresTableModel
    model = AgricultoresTableModel()
    model.set_items(items_normalizados)
"""

from qgis.PyQt.QtCore import Qt, QAbstractTableModel, QModelIndex


def safe_get(d: dict, path: str, default=""):
    """
    Obtiene un valor desde un dict anidado usando path con puntos.
    Ej: safe_get(item, "persona.nombre_completo")
    """
    cur = d or {}
    for k in path.split("."):
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur.get(k)
    return default if cur is None else cur


class AgricultoresTableModel(QAbstractTableModel):
    """
    Tabla para QTableView.
    Guarda items como lista de dicts ya normalizados (o raw si respetan paths).
    """

    COLS = [
        ("ID Agricultor", "idagricultor"),
        ("Nombre", "persona.nombre_completo"),
        ("Explotación", "explotacion.nombre"),
        ("Dirección", "explotacion.direccion"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = []

    # -----------------------------
    # API pública
    # -----------------------------
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

    # -----------------------------
    # Overrides Qt
    # -----------------------------
    def rowCount(self, parent=QModelIndex()):
        return len(self._items)

    def columnCount(self, parent=QModelIndex()):
        return len(self.COLS)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal:
            return self.COLS[section][0]

        # encabezado vertical (número de fila)
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

        # Devuelve el dict completo para selección/acciones
        if role == Qt.UserRole:
            return item

        return None
