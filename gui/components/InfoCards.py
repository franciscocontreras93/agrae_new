# agrae/gui/components/InfoCards.py
# -*- coding: utf-8 -*-
"""
InfoCards - Versión mínima y robusta (1 tarjeta: Num. Lotes)
- Lanza request SOLO cuando ExplotacionesComboBox cambia/termina de cargar.
- Incluye idcampania en los parámetros (no dispara por campaña).
- QThread efímero con retención en self._threads para evitar GC prematuro.
- Conecta success/error/finished_signal -> siempre se cierra el hilo.
- Debounce 150 ms para evitar tormenta de señales.
"""

from typing import Any, Dict, Optional

from .CustomComboBox import CampaniasComboBox, ExplotacionesComboBox
from qgis.PyQt.QtCore import Qt, QThread, QTimer, pyqtSignal
from qgis.PyQt.QtGui import QFont, QCursor
from qgis.PyQt.QtWidgets import QWidget, QFrame, QLabel, QVBoxLayout
from qgis.core import QgsMessageLog, Qgis

from ...tools import aGraeTools
from ...tools.api_worker import GenericApiWorker


# ---------------- util: label de "Cargando..." con puntos ----------------

class _LoadingDotsLabel(QLabel):
    def __init__(self, base_text: str = "Cargando", parent=None):
        super().__init__(parent)
        self._base = base_text
        self._n = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self.setAlignment(Qt.AlignCenter)
        self.setText(self._base)

    def start(self, interval_ms: int = 380):
        self._n = 0
        self._timer.start(interval_ms)
        self._tick()

    def stop(self):
        self._timer.stop()
        self.setText(self._base)

    def _tick(self):
        self._n = (self._n + 1) % 4
        self.setText(self._base + "." * self._n)


# ---------------- vista simple de tarjeta ----------------

class _StatCard(QFrame):
    def __init__(self, title_fallback: str, parent=None):
        super().__init__(parent)
        self.setObjectName("aGraeStatCard")
        self.setFrameShape(QFrame.StyledPanel)

        self.lbl_title = QLabel(title_fallback, self)
        ft = QFont(); ft.setPointSize(9); ft.setBold(True)
        self.lbl_title.setFont(ft)

        self.lbl_value = QLabel("—", self)
        fv = QFont(); fv.setPointSize(18); fv.setBold(True)
        self.lbl_value.setFont(fv)

        self.lbl_sub = QLabel("", self)
        fs = QFont(); fs.setPointSize(8); self.lbl_sub.setFont(fs)
        self.lbl_sub.setVisible(False)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(4)
        lay.addWidget(self.lbl_title)
        lay.addWidget(self.lbl_value)
        lay.addWidget(self.lbl_sub)

        self.setStyleSheet("""
        QFrame#aGraeStatCard {
            border: 1px solid rgba(130,130,130,0.35);
            border-radius: 8px;
            background: palette(base);
        }
        QLabel { color: palette(text); }
        """)

    def set_loading(self, loading: bool):
        self.setCursor(QCursor(Qt.BusyCursor) if loading else QCursor(Qt.ArrowCursor))

    def apply_payload(self, d: Dict[str, Any], *, title_fallback: str, fixed_decimals: Optional[int]):
        title = d.get("title") or title_fallback or ""
        value = d.get("value", None)
        unit = d.get("unit")
        fmt = d.get("format") or {}
        decimals = fmt.get("decimals", fixed_decimals)
        subtitle = d.get("subtitle")
        tooltip = d.get("tooltip")
        style = d.get("style") or {}

        self.lbl_title.setText(title)
        self.lbl_value.setText(self._format_value(value, unit, decimals))
        self.lbl_sub.setVisible(bool(subtitle))
        self.lbl_sub.setText(subtitle or "")
        for w in (self, self.lbl_title, self.lbl_value, self.lbl_sub):
            w.setToolTip(tooltip or "")

        self._apply_style(style)

    def _format_value(self, value: Any, unit: Optional[str], decimals: Optional[int]) -> str:
        if value is None or value == "":
            return "—"
        if isinstance(value, (int, float)):
            txt = f"{value:.{decimals}f}" if isinstance(value, float) and isinstance(decimals, int) else str(value)
        else:
            txt = str(value)
        return f"{txt} {unit}" if unit else txt

    def _apply_style(self, style: Dict[str, Any]):
        qss = style.get("qss")
        if qss:
            self.setStyleSheet(self.styleSheet() + "\n" + qss)
            return
        fg = style.get("value_fg") or style.get("fg")
        bg = style.get("bg")
        border = style.get("border")
        if fg:
            self.lbl_value.setStyleSheet(f"color:{fg};")
        if bg or border:
            base = self.styleSheet()
            self.setStyleSheet(
                base + (
                    f"\nQFrame#aGraeStatCard{{"
                    f"background:{bg if bg else 'palette(base)'};"
                    f"border:1px solid {border if border else 'rgba(130,130,130,0.35)'};"
                    f"border-radius:8px;}}"
                )
            )


# ---------------- tarjeta lógica: SOLO Num. Lotes ----------------

class InfoCardNumLotes(QWidget):
    """
    Tarjeta KPI "Num. Lotes".
    - Endpoint: /api/kpi/num_lotes (idcampania, idexplotacion).
    - TRIGGER ÚNICO: explotación (items_loaded, current_value_changed + respaldo currentIndexChanged).
    - Incluye idcampania en params, pero no dispara por campaña.

    Señales esperadas en ExplotacionesComboBox:
        items_loaded (custom), current_value_changed (custom), currentIndexChanged (Qt)
    """
    data_loaded = pyqtSignal(object)  # payload final mostrado
    error = pyqtSignal(str)

    def __init__(self, parent=None, *, endpoint: str = "/api/kpi/num_lotes", title: str = "Lotes",
                 decimals: Optional[int] = None, timeout_total: int = 60, debounce_ms: int = 150):
        super().__init__(parent)
        self._backend = aGraeTools().backend_endpoint.rstrip("/")
        self.endpoint = endpoint if endpoint.startswith("/") else f"/{endpoint}"
        self.title = title
        self.fixed_decimals = decimals
        self.timeout_total = timeout_total

        # Concurrencia y ciclo
        self._busy = False
        self._threads = set()          # Retiene QThreads vivos
        self._debounce = QTimer(self)  # Agrupa señales
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(debounce_ms)
        self._debounce.timeout.connect(self._do_refresh)

        # Combos
        self._combo_campania = None
        self._combo_explotacion = None

        # UI
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(4)

        self.card = _StatCard(title_fallback=self.title, parent=self)
        root.addWidget(self.card)

        self.loading_label = _LoadingDotsLabel("Cargando", self)
        self.loading_label.setVisible(False)
        root.addWidget(self.loading_label)

        self.error_label = QLabel("", self)
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setStyleSheet("color: #d9534f;")
        self.error_label.setVisible(False)
        root.addWidget(self.error_label)

        # Estado inicial
        self.card.apply_payload({"title": self.title, "value": None, "style": {}},
                                title_fallback=self.title, fixed_decimals=self.fixed_decimals)

    # -------- binding --------

    def bind_to_explotacion(self, combo_campania: CampaniasComboBox, combo_explotacion:ExplotacionesComboBox):
        self._combo_campania = combo_campania
        self._combo_explotacion = combo_explotacion

        # Conectar SOLO señales de explotación
        for sig_name in ("items_loaded", "current_value_changed"):
            try:
                getattr(combo_explotacion, sig_name).connect(self._schedule_refresh)
            except Exception:
                pass
        try:
            combo_explotacion.currentIndexChanged.connect(self._schedule_refresh)
        except Exception:
            pass

        # Si ya hay selección, planifica un refresh inicial
        try:
            if combo_explotacion.currentData() is not None:
                QTimer.singleShot(0, self._schedule_refresh)
        except Exception:
            pass

    def _schedule_refresh(self, *_):
        # Rearmar el debounce; si llegan varias señales, se hace una sola llamada
        self._debounce.start()

    # -------- requests --------

    def _do_refresh(self):
        if self._busy:
            QgsMessageLog.logMessage("[InfoCardNumLotes] request ya en curso", "aGrae", Qgis.Info)
            return

        # Params: leer campaña y explotación actuales
        params: Dict[str, Any] = {}
        try:
            if self._combo_campania:
                cid = self._combo_campania.currentData()
                if cid is not None:
                    params["idcampania"] = cid
        except Exception:
            pass
        try:
            if self._combo_explotacion:
                eid = self._combo_explotacion.currentData()
                if eid is not None:
                    params["idexplotacion"] = eid
        except Exception:
            pass

        if "idexplotacion" not in params:
            # nada que consultar
            return

        api_config = {
            "url": f"{self._backend}{self.endpoint}",
            "params": params,
            "headers": {},
            "timeout": self.timeout_total
        }

        # Estado UI
        self._set_error(None)
        self._set_loading(True)
        self._busy = True

        # Crear hilo + worker y RETENER referencias
        thread = QThread(self)
        worker = GenericApiWorker(api_config, request_context="kpi:num_lotes")
        worker.moveToThread(thread)

        self._threads.add(thread)

        def _release_thread():
            # Limpieza y liberar referencia del set
            self._set_loading(False)
            self._busy = False
            if thread in self._threads:
                self._threads.remove(thread)

        def _on_success(resp, ctx):
            try:
                payload = self._adapt_payload(resp)
                self.card.apply_payload(payload, title_fallback=self.title, fixed_decimals=self.fixed_decimals)
                self.data_loaded.emit(payload)
            finally:
                thread.quit()

        def _on_error(msg, ctx):
            try:
                self._set_error(msg)
            finally:
                thread.quit()

        # Conectar TODAS las rutas de salida
        worker.success.connect(_on_success)
        worker.error.connect(_on_error)
        try:
            worker.finished_signal.connect(thread.quit)
        except Exception:
            pass

        # Cierre definitivo
        thread.finished.connect(_release_thread)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

        thread.started.connect(worker.run)
        thread.start()

    # -------- adaptador & estado --------

    def _adapt_payload(self, data: Any) -> Dict[str, Any]:
        # Lista de dicts -> primer elemento
        if isinstance(data, list):
            data = data[0] if data and isinstance(data[0], dict) else {}

        # KPIResponse ya válido
        if isinstance(data, dict) and ("value" in data or "title" in data or "style" in data):
            # si no trae title, pon el nuestro por si acaso
            data.setdefault("title", self.title)
            return data

        # Legacy {"num_lotes": N}
        if isinstance(data, dict) and "num_lotes" in data:
            return {
                "title": self.title,
                "value": data.get("num_lotes", 0),
                "format": {},
                "style": {}
            }

        return {"title": self.title, "value": None, "style": {}}

    def _set_loading(self, is_loading: bool):
        self.card.set_loading(is_loading)
        self.loading_label.setVisible(is_loading)
        if is_loading:
            self.loading_label.start()
            self.setCursor(QCursor(Qt.BusyCursor))
        else:
            self.loading_label.stop()
            self.unsetCursor()

    def _set_error(self, msg: Optional[str]):
        has_err = bool(msg)
        self.error_label.setVisible(has_err)
        if has_err:
            self.error_label.setText(f"Error: {msg}")
            self.card.lbl_value.setStyleSheet("color:#d9534f;")
        else:
            self.error_label.setText("")
            self.card.lbl_value.setStyleSheet("")
