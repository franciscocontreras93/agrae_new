# -*- coding: utf-8 -*-
"""
agricultorSelectDialog.py

Diálogo simple de selección:
- buscador
- tabla
- doble click => emite idagricultor y cierra
"""

from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout
from qgis.PyQt.QtCore import pyqtSignal

from ...core.models.agricultorModel import AgricultoresTableModel
from ...gui.components import SearchTableWidget


from ...tools import aGraeTools

import asyncio



def map_agricultores(raw):
    """
    raw = respuesta JSON del endpoint (lista de dicts)
    devuelve = lista de dicts que entiende AgricultoresTableModel
    """
    items = []

    for r in (raw or []):
        persona = r.get("persona") or {}
        explot = r.get("explotacion") or {}

        items.append({
            "idagricultor": r.get("idagricultor"),
            "persona": {
                "nombre_completo": persona.get("nombre_completo", "")
            },
            "explotacion": {
                "nombre": explot.get("nombre", ""),
                "direccion": explot.get("direccion", ""),
            }
        })

    return items


class AgricultorSelectDialog(QDialog):
    agricultorSignal = pyqtSignal(int, dict)

    def __init__(self, idexplotacion: int, idlotes:list ,parent=None):
        super().__init__(parent)

        self.setWindowTitle("Seleccionar agricultor")
        self.resize(900, 500)

        self.selected_value = None
        self.selected_item = None
        self.idlotes = idlotes

        self.tools = aGraeTools()


        self.table = SearchTableWidget(
            model=AgricultoresTableModel(),
            endpoint='/gis/agricultores/exp/{}'.format(idexplotacion),
            map_func=map_agricultores,
            placeholder="Buscar agricultor...",
            emit_field="idagricultor",
            local_filter=True
        )

        self.table.rowDoubleClicked.connect(self._on_selected)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.addWidget(self.table)

        # carga inicial
        self.table.reload()

    def _on_selected(self, value, item):
        self.selected_value = value
        self.selected_item = item

        payload = {
            "idagricultor": self.selected_value,
            "idlotes": self.idlotes
        }

        # print(self.selected_value, self.selected_item)
        print('payload _dialog:', payload)
        asyncio.run(self.tools.asignarLotesAgricultor(payload))  
        # self.accept()