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

def map_agricultores(raw):
    """
    raw = respuesta JSON del endpoint (lista de dicts)
    devuelve = lista de dicts que entiende AgricultoresTableModel
    """
    items = []

    for r in (raw or []):
        persona = r.get("persona") or {}
        explotacion = r.get("explotacion") or {}
        distribuidor = r.get("distribuidor") or {}
        asesor = r.get("asesor") or {}
        asesor_persona = asesor.get("persona") or {}

        items.append({
            "idagricultor": r.get("idagricultor"),

            "persona": {
                "idpersona": persona.get("idpersona"),
                "dni": persona.get("dni", ""),
                "nombre": persona.get("nombre", ""),
                "apellidos": persona.get("apellidos", ""),
                "direccion": persona.get("direccion", ""),
                "telefono": persona.get("telefono", ""),
                "email": persona.get("email", ""),
                "nombre_completo": persona.get("nombre_completo", ""),
            },

            "explotacion": {
                "idexplotacion": explotacion.get("idexplotacion"),
                "nombre": explotacion.get("nombre", ""),
                "direccion": explotacion.get("direccion", ""),
            },

            "distribuidor": {
                "iddistribuidor": distribuidor.get("iddistribuidor"),
                "nombre": distribuidor.get("nombre", ""),
            },

            "asesor": {
                "idasesor": asesor.get("idasesor"),
                "nombre_completo": asesor.get("nombre_completo", ""),
                # "apellidos": asesor.get("apellidos", ""),
                "movil": asesor.get("movil", ""),
                "correo": asesor.get("correo", ""),
            }
        })

    return items


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
        ("Asesor", "asesor.nombre_completo"),
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
