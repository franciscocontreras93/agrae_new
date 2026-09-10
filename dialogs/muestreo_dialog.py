from math import exp
from qgis.PyQt.QtWidgets import * 
from qgis.PyQt.QtCore import * 
from qgis.PyQt.QtGui import * 

from qgis.PyQt.QtCore import pyqtSignal, QSize, QDate
from qgis.core import *
from qgis.gui import * 
from qgis.PyQt import uic

from ..gui import agraeGUI
from ..gui.components import CampaniasComboBox, ExplotacionesComboBox
from ..db import agraeDataBaseDriver
from ..sql import aGraeSQLTools
from ..tools import aGraeTools

from ..core.workers.network import _AsyncRunner

import asyncio


class MuestreoDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.agraeSql = aGraeSQLTools()
        self.tools = aGraeTools()
        self._muestreo_runner = None
        self.setWindowTitle('aGrae | Generar Puntos de Muestreo')
        self.setMinimumSize(640, 420)
        self.resize(720, 460)
        self.setSizeGripEnabled(True)

        self.UIComponents()

    def UIComponents(self): 
        # ====== MAIN LAYOUT + TABS ======
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        self.tab_widget = QTabWidget(self)

        # -- Pestañas
        self.tab_muestreo = QWidget(self.tab_widget)
        self.tab_remuestreo = QWidget(self.tab_widget)

        # ====== TAB: MUESTREO ======
        tab_muestreo_v = QVBoxLayout(self.tab_muestreo)
        tab_muestreo_v.setContentsMargins(12, 12, 12, 12)
        tab_muestreo_v.setSpacing(12)

        group_muestreo = QGroupBox('Generar Puntos de Muestreo en Lotes', self.tab_muestreo)
        group_muestreo_g = QGridLayout(group_muestreo)
        group_muestreo_g.setContentsMargins(14, 16, 14, 14)
        group_muestreo_g.setHorizontalSpacing(16)
        group_muestreo_g.setVerticalSpacing(12)
        group_muestreo_g.setColumnStretch(0, 0)
        group_muestreo_g.setColumnStretch(1, 1)

        # Controles principales
        self.combo_layer_lotes = QgsMapLayerComboBox(self.tab_muestreo)
        self.check_seleccionados = QCheckBox('Lotes seleccionados', self.tab_muestreo)
        self.check_seleccionados.setChecked(True)
        self.check_seguimiento = QCheckBox('Muestra de Seguimiento', self.tab_muestreo)
        self.check_seguimiento.setChecked(False)

        # Sub-group: segmentos
        group_segmentos = QGroupBox('Generar Muestras en Segmentos', group_muestreo)
        group_segmentos_h = QHBoxLayout(group_segmentos)
        group_segmentos_h.setContentsMargins(10, 8, 10, 8)
        group_segmentos_h.setSpacing(12)

        self.check_segmento_1 = QCheckBox('Segmento 1', group_segmentos)
        self.check_segmento_1.setChecked(True)
        self.check_segmento_2 = QCheckBox('Segmento 2', group_segmentos)
        self.check_segmento_2.setChecked(True)
        self.check_segmento_3 = QCheckBox('Segmento 3', group_segmentos)
        self.check_segmento_3.setChecked(True)

        group_segmentos_h.addWidget(self.check_segmento_1)
        group_segmentos_h.addWidget(self.check_segmento_2)
        group_segmentos_h.addWidget(self.check_segmento_3)
        group_segmentos_h.addStretch(1)


        # Una muestra solo puede tener una prioridad.
        self.combo_prioridad = QComboBox(group_muestreo)
        self.combo_prioridad.addItem('Normal', 1)
        self.combo_prioridad.addItem('Alta', 2)
        self.combo_prioridad.addItem('Urgente', 3)
        self.combo_prioridad.setToolTip('Prioridad que se asignará a los puntos generados')
        self.combo_prioridad.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.input_comentario = QPlainTextEdit(group_muestreo)
        self.input_comentario.setPlaceholderText('Añade una observación opcional')
        self.input_comentario.setMaximumHeight(72)
        self.input_comentario.setTabChangesFocus(True)

        # Botón MUestreo
        self.btn_create_muestreo = QPushButton('Generar muestreo', group_muestreo)
        self.btn_create_muestreo.setMinimumWidth(160)
        self.progress_muestreo = QProgressBar(group_muestreo)
        self.progress_muestreo.setRange(0, 0)
        self.progress_muestreo.setTextVisible(False)
        self.progress_muestreo.setMaximumWidth(160)
        self.progress_muestreo.setVisible(False)
        # Importante: conectar al slot correcto (no a self.create)
        self.btn_create_muestreo.clicked.connect(self.createMuestreoPoints)

        # Colocar en la grilla del group principal
        row = 0
        group_muestreo_g.addWidget(QLabel('Capa de lotes'), row, 0, 1, 1)
        group_muestreo_g.addWidget(self.combo_layer_lotes, row, 1, 1, 1)
        row += 1
        opciones_muestreo = QWidget(group_muestreo)
        opciones_muestreo_h = QHBoxLayout(opciones_muestreo)
        opciones_muestreo_h.setContentsMargins(0, 0, 0, 0)
        opciones_muestreo_h.setSpacing(24)
        opciones_muestreo_h.addWidget(self.check_seleccionados)
        opciones_muestreo_h.addWidget(self.check_seguimiento)
        opciones_muestreo_h.addStretch(1)
        group_muestreo_g.addWidget(QLabel('Opciones'), row, 0)
        group_muestreo_g.addWidget(opciones_muestreo, row, 1)
        row += 1
        group_muestreo_g.addWidget(group_segmentos, row, 0, 1, 2)
        row += 1
        group_muestreo_g.addWidget(QLabel('Prioridad'), row, 0)
        group_muestreo_g.addWidget(self.combo_prioridad, row, 1)
        row += 1
        etiqueta_comentario = QLabel('Comentario')
        etiqueta_comentario.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        group_muestreo_g.addWidget(etiqueta_comentario, row, 0)
        group_muestreo_g.addWidget(self.input_comentario, row, 1)
        row += 1
        acciones_muestreo = QHBoxLayout()
        acciones_muestreo.addWidget(self.progress_muestreo)
        acciones_muestreo.addStretch(1)
        acciones_muestreo.addWidget(self.btn_create_muestreo)
        group_muestreo_g.addLayout(acciones_muestreo, row, 0, 1, 2)

        tab_muestreo_v.addWidget(group_muestreo)
        tab_muestreo_v.addStretch(1)

        # ====== TAB: REMUESTREO ======
        tab_remuestreo_v = QVBoxLayout(self.tab_remuestreo)
        tab_remuestreo_v.setContentsMargins(12, 12, 12, 12)
        tab_remuestreo_v.setSpacing(12)

        group_remuestreo = QGroupBox('Generar Puntos de Remuestreo', self.tab_remuestreo)
        group_remuestreo_g = QGridLayout(group_remuestreo)
        group_remuestreo_g.setContentsMargins(14, 16, 14, 14)
        group_remuestreo_g.setHorizontalSpacing(16)
        group_remuestreo_g.setVerticalSpacing(12)
        group_remuestreo_g.setColumnStretch(0, 0)
        group_remuestreo_g.setColumnStretch(1, 1)

        # Controles Remuestreo
        self.combo_campania = CampaniasComboBox(parent=group_remuestreo,exclude_latest=True)
        self.combo_campania.setPlaceholderText('Selecciona una campaña')

        self.combo_explotacion = ExplotacionesComboBox(parent=group_remuestreo)
        self.combo_explotacion.setPlaceholderText('Selecciona una explotación')
        self.combo_explotacion.bind_to_campaigns(self.combo_campania)

        self.combo_segmentos_remuestreo = QgsMapLayerComboBox(group_remuestreo)
        self.combo_segmentos_remuestreo.setPlaceholderText('Selecciona la capa de Segmentos de Remuestreo')
        self.combo_segmentos_remuestreo.setFilters(QgsMapLayerProxyModel.PolygonLayer)

        # Botón Remuestreo
        self.btn_create_remuestreo = QPushButton('Generar remuestreo', group_remuestreo)
        self.btn_create_remuestreo.setMinimumWidth(160)
        self.btn_create_remuestreo.clicked.connect(self.createRemuestreoPoints)

        # Distribución Remuestreo con contador local
        row_r = 0
        group_remuestreo_g.addWidget(QLabel('Campaña de origen'), row_r, 0)
        group_remuestreo_g.addWidget(self.combo_campania, row_r, 1); row_r += 1

        group_remuestreo_g.addWidget(QLabel('Explotación'), row_r, 0)
        group_remuestreo_g.addWidget(self.combo_explotacion, row_r, 1); row_r += 1

        group_remuestreo_g.addWidget(QLabel('Capa de segmentos'), row_r, 0)
        group_remuestreo_g.addWidget(self.combo_segmentos_remuestreo, row_r, 1); row_r += 1

        acciones_remuestreo = QHBoxLayout()
        acciones_remuestreo.addStretch(1)
        acciones_remuestreo.addWidget(self.btn_create_remuestreo)
        group_remuestreo_g.addLayout(acciones_remuestreo, row_r, 0, 1, 2)

        tab_remuestreo_v.addWidget(group_remuestreo)
        tab_remuestreo_v.addStretch(1)

        # Validación reactiva de la capa de remuestreo (UX: deshabilita botón si falta schema)
        if hasattr(self.combo_segmentos_remuestreo, "layerChanged"):
            self.combo_segmentos_remuestreo.layerChanged.connect(self._validate_remuestreo_layer)
        # Validación inicial
        self._validate_remuestreo_layer(self.combo_segmentos_remuestreo.currentLayer())

        # ====== ENSAMBLAR TABS ======
        self.tab_widget.addTab(self.tab_muestreo, 'Muestreo')
        self.tab_widget.addTab(self.tab_remuestreo, 'Remuestreo')
        main_layout.addWidget(self.tab_widget)

    # ------------------ helpers UX ------------------
    def _validate_remuestreo_layer(self, layer: QgsMapLayer | None):
        """
        Habilita/Deshabilita el botón de remuestreo según que la capa tenga
        los campos 'idlote' e 'idsegmento'. Coloca un tooltip explicativo.
        """
        ok = False
        if layer is not None and isinstance(layer, QgsVectorLayer):
            names = {f.name() for f in layer.fields()}
            ok = ("idlote" in names) and ("idsegmento" in names)
        self.btn_create_remuestreo.setEnabled(ok)
        tip = "" if ok else "La capa debe tener los campos 'idlote' e 'idsegmento'."
        self.btn_create_remuestreo.setToolTip(tip)

    # ================== LÓGICA ==================
    def createMuestreoPoints(self):
        """Valida la entrada y lanza la creación sin bloquear la interfaz."""
        if self._muestreo_runner is not None:
            return

        layer = self.combo_layer_lotes.currentLayer()
        if layer is None or not isinstance(layer, QgsVectorLayer):
            QMessageBox.warning(self, 'aGrae Toolbox', 'Selecciona una capa de lotes válida.')
            return

        if 'iddata' not in {field.name() for field in layer.fields()}:
            QMessageBox.warning(
                self,
                'aGrae Toolbox',
                "La capa seleccionada no contiene el campo requerido 'iddata'."
            )
            return

        segmentos_muestreo = [
            numero
            for numero, check in (
                (1, self.check_segmento_1),
                (2, self.check_segmento_2),
                (3, self.check_segmento_3),
            )
            if check.isChecked()
        ]
        if not segmentos_muestreo:
            QMessageBox.warning(self, 'aGrae Toolbox', 'Selecciona al menos un segmento.')
            return

        alcance = 'todos los lotes de la capa'
        if self.check_seleccionados.isChecked():
            features = list(layer.getSelectedFeatures())
            if not features:
                ask = QMessageBox.question(
                    self,
                    'aGrae Toolbox',
                    'No hay lotes seleccionados.\n\n¿Quieres procesar TODOS los lotes de la capa?',
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if ask == QMessageBox.Yes:
                    features = list(layer.getFeatures())
                else:
                    QMessageBox.information(self, 'aGrae Toolbox', 'Debes seleccionar uno o más lotes y volver a intentarlo.')
                    return
            else:
                alcance = 'los lotes seleccionados'
        else:
            features = list(layer.getFeatures())

        ids = []
        ids_vistos = set()
        for feature in features:
            try:
                iddata = int(feature.attribute('iddata'))
            except (TypeError, ValueError):
                QMessageBox.warning(
                    self,
                    'aGrae Toolbox',
                    "Se ha encontrado un valor 'iddata' vacío o no numérico. Revisa la capa antes de continuar."
                )
                return
            if iddata not in ids_vistos:
                ids.append(iddata)
                ids_vistos.add(iddata)

        tipo = 3 if self.check_seguimiento.isChecked() else 1
        prioridad = int(self.combo_prioridad.currentData())
        comentario = self.input_comentario.toPlainText().strip()

        if not ids:
            QMessageBox.information(self, 'aGrae Toolbox', 'No hay lotes para procesar.')
            return

        segmentos_derivar = [
            numero for numero in (1, 2, 3) if numero not in segmentos_muestreo
        ] or [0]
        tipo_texto = 'Seguimiento' if tipo == 3 else 'Normal'
        comentario_texto = 'Sí' if comentario else 'No'

        reply = QMessageBox.question(
            self,
            'aGrae Toolbox',
            'Vas a generar puntos de muestreo con esta configuración:\n\n'
            f' · Alcance: {alcance}\n'
            f' · Lotes: {len(ids)}\n'
            f' · Segmentos: {", ".join(map(str, segmentos_muestreo))}\n'
            f' · Tipo: {tipo_texto}\n'
            f' · Prioridad: {self.combo_prioridad.currentText()}\n'
            f' · Comentario: {comentario_texto}\n\n'
            '¿Continuar?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        runner = _AsyncRunner(
            self.tools.crearPuntosMuestreo(
                ids,
                segmentos_muestreo,
                segmentos_derivar,
                tipo,
                prioridad=prioridad,
                comentario=comentario,
            )
        )
        runner.signals.done.connect(self._on_muestreo_done)
        runner.signals.error.connect(self._on_muestreo_error)
        self._muestreo_runner = runner
        self._set_muestreo_busy(True)
        QThreadPool.globalInstance().start(runner)

    def _set_muestreo_busy(self, busy):
        """Bloquea los controles de muestreo mientras existe una petición activa."""
        for control in (
            self.combo_layer_lotes,
            self.check_seleccionados,
            self.check_seguimiento,
            self.check_segmento_1,
            self.check_segmento_2,
            self.check_segmento_3,
            self.combo_prioridad,
            self.input_comentario,
        ):
            control.setEnabled(not busy)
        self.btn_create_muestreo.setEnabled(not busy)
        self.btn_create_muestreo.setText('Generando…' if busy else 'Generar muestreo')
        self.progress_muestreo.setVisible(busy)

    def _on_muestreo_done(self, data):
        """Procesa en el hilo de interfaz la respuesta normalizada del backend."""
        self._set_muestreo_busy(False)
        self._muestreo_runner = None

        if not isinstance(data, dict):
            self.tools.messages('Puntos de Muestreo', 'Respuesta no válida del servidor.', 1, alert=True)
            return

        status = data.get('status_code')
        message = data.get('message', '')
        if data.get('ok') is True:
            self.input_comentario.clear()
            self.tools.messages(
                'Puntos de Muestreo',
                f'Se han generado los puntos de muestreo correctamente.\n{message}',
                3,
                alert=True
            )
        elif status == 409:
            self.tools.messages(
                'Puntos de Muestreo',
                f'No se han podido generar los puntos de muestreo.\n{message}',
                1,
                alert=True
            )
        elif status in (400, 422):
            self.tools.messages(
                'Puntos de Muestreo',
                f'El servidor ha rechazado los datos enviados.\n{message}',
                1,
                alert=True
            )
        elif status in (401, 403):
            self.tools.messages(
                'Puntos de Muestreo',
                f'No tienes autorización para realizar esta operación.\n{message}',
                1,
                alert=True
            )
        else:
            self.tools.messages(
                'Puntos de Muestreo',
                f'Error de comunicación con el servidor ({status}).\n{message}',
                2,
                alert=True
            )

    def _on_muestreo_error(self, message):
        """Restaura la interfaz cuando el ejecutor falla fuera de la petición HTTP."""
        self._set_muestreo_busy(False)
        self._muestreo_runner = None
        self.tools.messages(
            'Puntos de Muestreo',
            f'No se ha podido ejecutar la operación.\n{message}',
            1,
            alert=True
        )

    def createRemuestreoPoints(self):
        """
        Genera puntos de RE-muestreo con validación de esquema de capa.
        Evita KeyError si la capa no contiene 'idlote' o 'idsegmento'.
        """
        # 1) Campaña y Explotación
        idcamp = self.combo_campania.get_current_campaign_id() if hasattr(self.combo_campania, "get_current_campaign_id") else self.combo_campania.currentData()
        idexpl = self.combo_explotacion.get_current_explotacion_id() if hasattr(self.combo_explotacion, "get_current_explotacion_id") else self.combo_explotacion.currentData()

        campania_name = self.combo_campania.get_current_campaign_name() if hasattr(self.combo_campania, "get_current_campaign_name") else "N/A"
        explotacion_name = self.combo_explotacion.get_current_explotacion_name() if hasattr(self.combo_explotacion, "get_current_explotacion_name") else "N/A"

        if idcamp is None:
            QMessageBox.warning(self, "aGrae Toolbox", "Selecciona una campaña válida para el remuestreo.")
            return
        if idexpl is None:
            QMessageBox.warning(self, "aGrae Toolbox", "Selecciona una explotación válida para el remuestreo.")
            return

        # 2) Capa de segmentos
        layer = self.combo_segmentos_remuestreo.currentLayer()
        if layer is None:
            QMessageBox.warning(self, "aGrae Toolbox", "Selecciona la capa de Segmentos de Remuestreo (poligonal).")
            return

        # 3) Validación de campos requeridos
        field_names = {f.name() for f in layer.fields()}
        required = {"idlote", "idsegmento"}
        missing = sorted(required - field_names)
        if missing:
            QMessageBox.warning(
                self,
                "aGrae Toolbox",
                "La capa seleccionada no contiene los campos requeridos:\n - " + "\n - ".join(missing) +
                "\n\nElige otra capa o ajusta el modelo para incluir estos campos."
            )
            return

        # 4) Extraer listas únicas usando attribute() para evitar KeyError
        idlotes = set()
        idsegmentos = set()
        for feat in layer.getFeatures():  # cambia a getSelectedFeatures() si prefieres solo seleccionados
            v_lote = feat.attribute("idlote")
            v_seg  = feat.attribute("idsegmento")
            if v_lote is not None:
                try:
                    idlotes.add(int(v_lote))
                except Exception:
                    pass
            if v_seg is not None:
                try:
                    idsegmentos.add(int(v_seg))
                except Exception:
                    pass

        idlotes_lista = sorted(idlotes)
        idsegmentos_lista = sorted(idsegmentos)

        if not idlotes_lista or not idsegmentos_lista:
            QMessageBox.information(self, "aGrae Toolbox", "No se encontraron valores válidos de 'idlote' y/o 'idsegmento' en la capa.")
            return

        # 5) Confirmación
        msg = (
            "Vas a generar puntos de Remuestreo:\n"
            f" - Campaña anterior: {campania_name}\n"
            f" - Explotación: {explotacion_name}\n"
            f" - # Lotes: {len(idlotes_lista)}\n"
            f" - # Segmentos: {len(idsegmentos_lista)}\n\n"
            "¿Continuar?"
        )
        if QMessageBox.question(self, "aGrae Toolbox", msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
            return

        # 6) Llamada al backend
        resp = asyncio.run(
            self.tools.crearPuntosRemuestreo(
                idcampania_anterior=int(idcamp),
                idexplotacion=int(idexpl),
                idlotes_lista=idlotes_lista,
                idsegmentos_lista=idsegmentos_lista,
            )
        )

        if not resp:
            self.tools.messages("Puntos de Remuestreo", "Sin respuesta del servidor.", 1, alert=True)
            return

        if resp.get("ok") or resp.get("status_code") == 200:
            self.tools.messages(
                "Puntos de Remuestreo",
                f"Se generaron los puntos de remuestreo correctamente.\n{resp.get('message','')}",
                3, alert=True
            )
        else:
            self.tools.messages(
                "Puntos de Remuestreo",
                f"Error ({resp.get('status_code')}): {resp.get('message','')}",
                1, alert=True
            )
