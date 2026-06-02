from qgis.PyQt.QtCore import Qt, QAbstractTableModel, QModelIndex


def safe_get(d: dict, path: str, default=""):
    cur = d or {}
    for k in path.split("."):
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur.get(k)
    return default if cur is None else cur


def map_facturas(raw):
    items = []

    for r in (raw or []):
        items.append({
            # "idfactura": int(r.get("idfactura") or 0),
            "uid": r.get("uid", ""),
            "codigo": r.get("codigo", ""),
            "estado": r.get("estado", ""),
            "idempresa": r.get("idempresa", ""),
            "fecha_emision": r.get("fecha_emision", ""),
            "fecha_vencimiento": r.get("fecha_vencimiento", ""),
            "base_total": r.get("base_total", ""),
            "iva_total": r.get("iva_total", ""),
            "total": r.get("total", ""),
            "pagado_total": r.get("pagado_total", ""),
            "saldo_pendiente": r.get("saldo_pendiente", ""),
            "saldo_a_favor": r.get("saldo_a_favor", ""),
            "idexplotacion" : r.get("explotacion", "").get("idexplotacion", ""),
            "explotacion": r.get("explotacion", {}).get("nombre", ""),
            "idagricultor": r.get("agricultor", {}).get("idagricultor", ""),
            "agricultor": r.get("agricultor", {}).get("nombre_completo", ""),
            "dni": r.get("agricultor", {}).get("dni", ""),

        })

    # print(items)

    return items

def map_pagos(raw):
    items = []

    for r in (raw or []):
        items.append({
            "idpago": int(r.get("idpago") or 0),
            "importe": int(r.get("importe") or 0),
            "metodo_pago": r.get("metodo_pago", ""),
            "fecha_pago": r.get("fecha_pago", ""),
            "referencia": r.get("referencia", ""),
            "observaciones": r.get("observaciones", ""),
            "created_at": r.get("created_at", ""),
        })

    return items


class FacturasTableModel(QAbstractTableModel):

    COLS = [
        # ("ID Factura", "idfactura"),
        ("UID", "uid"),
        # ("ID Empresa", "idempresa"),
        # ("ID Explotación", "idexplotacion"),
        # ("ID Agricultor", "idagricultor"),

        ("Explotación", "explotacion"),
        ("Agricultor", "agricultor"),


        ("Factura Código", "codigo"),
        ("Fecha de Emisión", "fecha_emision"),
        ("Fecha de Vencimiento", "fecha_vencimiento"),
        ("Estado", "estado"),
        # ("Base Total", "base_total"),
        # ("IVA Total", "iva_total"),
        ("Total", "total"),
        ("Saldo Pendiente", "saldo_pendiente"),


        # ("ID Agricultor (Pagador)", "idagricultor_payer"),
        # ("Modo", "modo"),
        # ("ID Serie", "idserie"),
        # ("Número", "numero"),
        # ("Código", "codigo"),
        # ("Fecha de Emisión", "fecha_emision"),
        # ("Fecha de Vencimiento", "fecha_vencimiento"),
        # ("Estado", "estado"),
        # ("Razón Social del Cliente", "cliente_razon_social"),
        # ("NIF del Cliente", "cliente_nif"),
        # ("Dirección del Cliente", "cliente_direccion"),
        # ("Provincia del Cliente", "cliente_provincia"),
        # ("Municipio del Cliente", "cliente_municipio"),
        # ("Código Postal del Cliente", "cliente_codigo_postal"),
        # ("País del Cliente", "cliente_pais"),
        # ("Email del Cliente", "cliente_email"),
        # ("Teléfono del Cliente", "cliente_telefono"),
        # ("Aplicar Área Mínima", "aplicar_area_minima"),
        # ("Área Mínima (ha)", "area_minima_ha"),
        # ("Base Total", "base_total"),
        # ("IVA Total", "iva_total"),
        # ("Total", "total"),
        # ("Creado en", "created_at"),
        # ("Actualizado en", "updated_at"),
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
    

class PagosTableModel(QAbstractTableModel):
    COLS = [
        ("ID Pago", "idpago"),
        ("ID Factura", "idfactura"),
        ("FECHA", "fecha_pago"),
        ("IMPORTE", "importe"),
        ("METODO DE PAGO", "metodo_pago"),
        ("REFERENCIA", "referencia"),
        ("OBSERVACIONES", "observaciones"),
        ("CREADO", "created_at"),
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