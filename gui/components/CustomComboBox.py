"""
CustomComboBox.py
--------------------

Combos reutilizables para QGIS (PyQt5) que cargan datos desde un backend en un
hilo separado (QThread), con:

  - Estados: Cargando / Error / (opcional) "Todos".
  - Ordenación de resultados.
  - Formateador de etiqueta (sólo al poblar items).
  - Señales: items_loaded y current_value_changed.
  - Opción editable + QCompleter (filtro 'contains').
  - Dependencias entre combos (Explotaciones filtradas por Campaña).
  - Métodos utilitarios para obtener el ID y el NOMBRE “puro” (sin formateo).
  - Transformación opcional de items en el base (items_transform).
  - En CampaniasComboBox: opción exclude_latest para excluir la campaña más reciente (id más alto).
  - En CampaniasComboBox: soporte para fechas (fecha_desde/fecha_hasta) con helpers.

Requisitos:
- aGraeTools().backend_endpoint → URL base del backend (sin slash final).
- GenericApiWorker(api_config, request_context) con señales:
    - success(object, object), error(str, object), finished_signal()

Autor: aGrae
"""

from qgis.PyQt.QtWidgets import ( 
    QComboBox, 
    QCompleter, 
    # NUEVO
    QStyledItemDelegate 
)
from qgis.PyQt.QtCore import (
    Qt,
    pyqtSignal, 
    QThread, 
    QStringListModel, 
    QTimer, 
    QDate, 
    # NUEVO
    QEvent
)


from qgis.PyQt.QtGui import (
    # NUEVO
    QStandardItemModel,
    QStandardItem,
    QFontMetrics,
    QPalette,
)

from qgis.core import QgsMessageLog, Qgis

from ...tools import aGraeTools
from ...tools.api_worker import GenericApiWorker

from collections.abc import Callable
from typing import Any, Optional, Tuple
import re


# =============================================================================
# Combo base genérico
# =============================================================================

class CustomComboBox(QComboBox):
   
    """
    ComboBox que carga ítems desde un endpoint REST en un hilo aparte.

    Parámetros del constructor:
    - endpoint: str
        Ruta del recurso (p. ej., "/api/campanias/").
    - parent: QWidget | None

    kwargs:
    - label_field: str = "nombre"
        Campo del dict para mostrar si no se usa label_formatter.
    - value_field: str = "id"
        Campo del dict que se guarda como userData.
    - allow_all: bool = False
        Si True, agrega "Todos" (userData=None) al inicio.
    - all_text: str | None = None
        Texto para el ítem "Todos".
    - editable: bool = False
        Si True, activa edición + QCompleter (MatchContains).
    - sort_key: str | None = None
        Clave para ordenar (por defecto value_field).
    - sort_reverse: bool = True
        Orden inverso.
    - param_provider: Callable[[], dict[str, Any]] | None = None
        Función que genera los parámetros de la request (p. ej., {"idcampania": 42}).
    - label_formatter: Callable[[dict[str, Any]], str] | None = None
        Formatea la etiqueta visible a partir del dict del backend (sólo al poblar).
    - items_transform: Callable[[list[dict[str, Any]]], list[dict[str, Any]]] | None = None
        Transformación de la lista de items justo antes de ordenar y poblar.
    - auto_enable_on_load: bool = True
        Si True, el combo se habilita automáticamente tras cargar datos.
    """

    items_loaded = pyqtSignal(object)
    current_value_changed = pyqtSignal(object)

    DEFAULT_LOADING_TEXT = "Cargando..."
    DEFAULT_ERROR_TEXT = "Error al cargar datos"
    DEFAULT_ALL_TEXT = "Todos"
    DEFAULT_FIRST_ITEM_TEXT = "Seleccione una opción..."

    def __init__(
        self,
        endpoint: str,
        parent=None,
        *,
        label_field: str = "nombre",
        value_field: str = "id",
        allow_all: bool = False,
        all_text: str | None = None,
        first_item_text: bool = False,
        editable: bool = False,
        sort_key: str | None = None,
        sort_reverse: bool = True,
        param_provider: Callable[[], dict[str, Any]] | None = None,
        label_formatter: Callable[[dict[str, Any]], str] | None = None,
        items_transform: Callable[[list[dict[str, Any]]], list[dict[str, Any]]] | None = None,
        auto_enable_on_load: bool = True
    ):
        super().__init__(parent)

        self._backend = aGraeTools().backend_url.rstrip("/")
        self.endpoint = endpoint if endpoint.startswith("/") else f"/{endpoint}"

        self.label_field = label_field
        self.value_field = value_field
        self.allow_all = allow_all
        self.allow_first_item_text = first_item_text
        self.all_text = all_text or self.DEFAULT_ALL_TEXT
        self.sort_key = sort_key
        self.sort_reverse = sort_reverse

        self.param_provider = param_provider
        self.label_formatter = label_formatter
        self.items_transform = items_transform
        self._auto_enable_on_load = bool(auto_enable_on_load)

        self.loading_text = self.DEFAULT_LOADING_TEXT
        self.error_text = self.DEFAULT_ERROR_TEXT

        self.api_thread: QThread | None = None
        self.api_worker: GenericApiWorker | None = None
        self._last_items: list[dict[str, Any]] = []
        self._labels_for_completer: list[str] = []

        self.setEditable(editable)
        if editable:
            self.setInsertPolicy(QComboBox.NoInsert)

        self._connect_signals()
        self.set_initial_state(self.loading_text, enabled=False)
        self.load_items()

    # ------------------------- Interfaz pública -------------------------
    def refresh(self) -> None:
        """Recarga los datos del endpoint con los parámetros actuales."""
        self.load_items()

    def get_current_id(self) -> Any:
        """Devuelve el userData del ítem actual (normalmente, el ID)."""
        return self.currentData()

    def get_current_label(self) -> str:
        """
        Devuelve la etiqueta visible tal cual se muestra.
        NOTA: No pasa por label_formatter; éste sólo se usa al poblar items.
        """
        return self.currentText()

    def get_current_item(self) -> dict[str, Any] | None:
        """
        Devuelve el dict original del ítem actual (buscando por userData/value_field).
        Si no lo encuentra o userData es None (p. ej. "Todos"), retorna None.
        """
        current_val = self.currentData()
        if current_val is None:
            return None
        for it in self._last_items:
            try:
                if it.get(self.value_field) == current_val:
                    return it
            except Exception:
                pass
        return None

    def get_current_id_and_name(self) -> tuple[Any, str | None]:
        """
        Helper: retorna (id, nombre) del ítem actual.
        Si no encuentra el dict, intenta usar la etiqueta visible.
        """
        it = self.get_current_item()
        cid = self.get_current_id()
        if isinstance(it, dict):
            return cid, it.get("nombre")
        label = self.get_current_label()
        if " - " in label:
            return cid, label.split(" - ", 1)[1]
        return cid, label or None

    def set_param_provider(self, provider: Callable[[], dict[str, Any]] | None) -> None:
        """Define/limpia la función que retorna los params de la petición."""
        self.param_provider = provider

    def set_label_formatter(self, formatter: Callable[[dict[str, Any]], str] | None) -> None:
        """Permite cambiar dinámicamente el formateador de etiquetas."""
        self.label_formatter = formatter

    def set_items_transform(self, transform: Callable[[list[dict[str, Any]]], list[dict[str, Any]]] | None, *, refresh: bool = False) -> None:
        """Establece una transformación de items previa al populate."""
        self.items_transform = transform
        if refresh:
            self.refresh()

    def set_auto_enable_on_load(self, flag: bool, *, enable_now_if_loaded: bool = False) -> None:
        """
        Controla si el combo se auto-habilita al cargar datos.
        - flag=True  -> comportamiento por defecto (se habilita al cargar)
        - flag=False -> respeta el estado externo (útil para modo edición)
        """
        self._auto_enable_on_load = bool(flag)
        if enable_now_if_loaded and flag and self.count() > 0:
            self.setEnabled(True)

    def select_by_id(self, value: Any) -> bool:
        """Selecciona la fila cuyo userData == value. Devuelve True si lo encontró."""
        for i in range(self.count()):
            if self.itemData(i) == value:
                self.setCurrentIndex(i)
                return True
        return False

    # --------------------------- Soporte interno ------------------------
    def set_initial_state(self, text: str, enabled: bool = False) -> None:
        """Deja el combo con un único ítem (texto de estado) y enabled=enabled."""
        self.blockSignals(True)
        self.clear()
        self.addItem(text, None)
        self.setEnabled(enabled)
        self.blockSignals(False)

    def _connect_signals(self) -> None:
        self.currentIndexChanged.connect(self._emit_current_value_changed)

    def _emit_current_value_changed(self, _idx: int) -> None:
        self.current_value_changed.emit(self.currentData())

    def _make_api_config(self) -> dict[str, Any]:
        """Crea el dict de config para GenericApiWorker."""
        params: dict[str, Any] = {}
        if callable(self.param_provider):
            try:
                params = self.param_provider() or {}
            except Exception as e:
                QgsMessageLog.logMessage(
                    f"[CustomComboBox] param_provider error: {e}",
                    "CustomComboBox",
                    Qgis.Warning,
                )

        return {"url": f"{self._backend}{self.endpoint}", "params": params, "headers": {}}

    # --------------------------- Carga en hilo --------------------------
    def load_items(self) -> None:
        """Lanza la petición en QThread. Evita cargas concurrentes."""
        if self.api_thread and self.api_thread.isRunning():
            QgsMessageLog.logMessage(
                "[CustomComboBox] Carga ya en progreso, se omite.",
                "CustomComboBox",
                Qgis.Info,
            )
            return

        self.set_initial_state(self.loading_text, False)

        api_config = self._make_api_config()
        self.api_thread = QThread(self)
        self.api_worker = GenericApiWorker(api_config, request_context="load_items")
        self.api_worker.moveToThread(self.api_thread)

        self.api_worker.success.connect(self._handle_api_success)
        self.api_worker.error.connect(self._handle_api_error)

        self.api_worker.finished_signal.connect(self.api_thread.quit)
        self.api_worker.finished_signal.connect(self.api_worker.deleteLater)
        self.api_thread.finished.connect(self.api_thread.deleteLater)
        self.api_thread.finished.connect(self._on_load_finished)

        self.api_thread.started.connect(self.api_worker.run)
        self.api_thread.start()

    def _handle_api_success(self, response_data: object, request_context: object) -> None:
        """Procesa la respuesta OK y pobla el combo."""
        if request_context != "load_items":
            return

        self.blockSignals(True)
        self.clear()

        if not isinstance(response_data, list):
            QgsMessageLog.logMessage(
                f"[CustomComboBox] Respuesta no es lista: {type(response_data)}",
                "CustomComboBox",
                Qgis.Warning,
            )
            self._handle_api_error("Respuesta API inválida", request_context)
            self.blockSignals(False)
            return

        # Transformación previa (si se definió)
        if callable(self.items_transform):
            try:
                response_data = self.items_transform(response_data) or []
            except Exception as e:
                QgsMessageLog.logMessage(
                    f"[CustomComboBox] items_transform error: {e}",
                    "CustomComboBox",
                    Qgis.Warning,
                )

        # Ordenación
        key = self.sort_key or self.value_field
        try:
            response_data = sorted(
                response_data, key=lambda x: x.get(key, 0), reverse=self.sort_reverse
            )
        except Exception:
            pass  # si falla la ordenación, se deja como vino

        # Opción "Todos"
        if self.allow_all:
            self.addItem(self.all_text, None)
        
        if self.allow_first_item_text:
            self.addItem(self.DEFAULT_FIRST_ITEM_TEXT, None)

        # Poblar ítems (¡aquí sí usamos label_formatter con el dict!)
        labels: list[str] = []
        for item in response_data:
            if not isinstance(item, dict):
                continue
            try:
                label = (
                    self.label_formatter(item)
                    if callable(self.label_formatter)
                    else str(item.get(self.label_field, ""))
                )
            except Exception:
                label = str(item.get(self.label_field, ""))
            value = item.get(self.value_field, None)
            if label == "" and value is None:
                continue
            self.addItem(label, value)
            labels.append(label)

        self._last_items = response_data
        self._labels_for_completer = labels

        self.setEnabled(self._auto_enable_on_load)
        self.setCurrentIndex(0)  # si hay "Todos": índice 0 es "Todos"

        self._setup_completer_if_needed()

        self.blockSignals(False)
        self.items_loaded.emit(self._last_items)
        self.current_value_changed.emit(self.currentData())

    def _handle_api_error(self, error_message: str, request_context: object) -> None:
        """Muestra estado de error y registra el problema."""
        if request_context != "load_items":
            return
        QgsMessageLog.logMessage(
            f"[CustomComboBox] Error al cargar: {error_message}",
            "CustomComboBox",
            Qgis.Critical,
        )
        self.set_initial_state(self.DEFAULT_ERROR_TEXT, False)

    def _on_load_finished(self) -> None:
        """Limpia referencias del hilo/worker al terminar la carga."""
        self.api_thread = None
        self.api_worker = None

    # --------------------- Completer si editable=True -------------------
    def _setup_completer_if_needed(self) -> None:
        """Configura QCompleter con filtro 'contains' (insensible a mayúsculas)."""
        if not self.isEditable():
            return
        try:
            model = QStringListModel(self._labels_for_completer, self)
            completer = QCompleter(model, self)
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            completer.setFilterMode(Qt.MatchContains)
            completer.setCompletionMode(QCompleter.PopupCompletion)
            self.setCompleter(completer)
        except Exception as e:
            QgsMessageLog.logMessage(
                f"[CustomComboBox] Error configurando completer: {e}",
                "CustomComboBox",
                Qgis.Warning,
            )


# =============================================================================
# Helpers de fechas (uso interno de CampaniasComboBox)
# =============================================================================
def _parse_date_to_str(val: Any) -> Optional[str]:
    """
    Devuelve 'YYYY-MM-DD' o None a partir de distintos formatos:
    - 'YYYY-MM-DD' puro
    - ISO con tiempo ('YYYY-MM-DDTHH:MM:SSZ')  -> recorta
    - QDate                                    -> toString
    - números (timestamp/yyyymmdd)             -> intenta parsear a ciegas
    """
    if val is None:
        return None
    if isinstance(val, QDate):
        return val.toString("yyyy-MM-dd")
    try:
        s = str(val).strip()
        # Busca un patrón yyyy-mm-dd en la cadena
        m = re.search(r"\d{4}-\d{2}-\d{2}", s)
        if m:
            return m.group(0)
        # Intenta yyyy/mm/dd
        m = re.search(r"\d{4}/\d{2}/\d{2}", s)
        if m:
            return m.group(0).replace("/", "-")
    except Exception:
        return None
    return None


# =============================================================================
# Campañas
# =============================================================================
class CampaniasComboBox(CustomComboBox):
    """
    Combo específico para Campañas.
    - No editable.
    - Orden por ID descendente (más recientes primero).
    - exclude_latest: si True, excluye la campaña más reciente (id más alto).
    - Soporte para fechas: date_from_field/date_to_field (+ fallbacks) y helpers de lectura.
    - show_dates_in_label: si True, añade el rango de fechas al texto visible.  etiqueta: "43 - C-CAMPAÑA 26 (2025-09-01→2026-08-31)"
    """

    campaigns_loaded = pyqtSignal()  # señal legacy para compatibilidad

    def __init__(
        self,
        endpoint: str = "/gis/campanias/data_combo",
        parent=None,
        *,
        exclude_latest: bool = False,
        date_from_field: str = "fecha_desde",
        date_to_field: str = "fecha_hasta",
        alt_date_from_field: str = "fecha_inicio",
        alt_date_to_field: str = "fecha_fin",
        show_dates_in_label: bool = False,
    ):
        self._exclude_latest_flag = bool(exclude_latest)
        self._date_from_field = date_from_field
        self._date_to_field = date_to_field
        self._alt_date_from_field = alt_date_from_field
        self._alt_date_to_field = alt_date_to_field
        self._show_dates_in_label = bool(show_dates_in_label)

        # Si se quiere mostrar fechas en la etiqueta, definimos un label_formatter
        def _campaign_label(it: dict[str, Any]) -> str:
            base = f"{it.get('id', '')} - {it.get('nombre', '')}"
            if self._show_dates_in_label:
                fd = it.get(self._date_from_field) or it.get(self._alt_date_from_field)
                fh = it.get(self._date_to_field) or it.get(self._alt_date_to_field)
                s_fd = _parse_date_to_str(fd) or ""
                s_fh = _parse_date_to_str(fh) or ""
                if s_fd or s_fh:
                    base = f"{base} ({s_fd}→{s_fh})"
            return base

        super().__init__(
            endpoint=endpoint,
            parent=parent,
            label_field="nombre",
            value_field="id",
            allow_all=False,
            editable=False,
            sort_key="id",
            sort_reverse=True,
            param_provider=None,
            label_formatter=_campaign_label if self._show_dates_in_label else None,
            items_transform=self._make_items_transform(),  # exclusión + normalización fechas
        )
        # Alias de señal para compatibilidad con código previo
        self.current_campaign_changed = self.current_value_changed
        # Reenvío: items_loaded -> campaigns_loaded (legacy)
        self.items_loaded.connect(lambda _items: self.campaigns_loaded.emit())

    # --- Control público para excluir/incluir la última campaña ---
    def set_exclude_latest(self, exclude: bool, *, refresh: bool = True) -> None:
        """Activa/desactiva la exclusión de la campaña más reciente (id más alto)."""
        self._exclude_latest_flag = bool(exclude)
        self.set_items_transform(self._make_items_transform(), refresh=refresh)

    # --- Genera la transformación de items: exclude_latest + normaliza fechas ---
    def _make_items_transform(self) -> Callable[[list[dict[str, Any]]], list[dict[str, Any]]] | None:
        def _transform(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
            if not items:
                return items

            # 1) Normaliza/asegura date_from/date_to en cada item (si existen)
            out: list[dict[str, Any]] = []
            for it in items:
                if not isinstance(it, dict):
                    continue
                fd = it.get(self._date_from_field) or it.get(self._alt_date_from_field)
                fh = it.get(self._date_to_field) or it.get(self._alt_date_to_field)
                s_fd = _parse_date_to_str(fd)
                s_fh = _parse_date_to_str(fh)
                if s_fd is not None:
                    it[self._date_from_field] = s_fd
                if s_fh is not None:
                    it[self._date_to_field] = s_fh
                out.append(it)

            items = out

            # 2) Excluir la campaña con id más alto si se pide
            if self._exclude_latest_flag:
                max_id = None
                max_idx = -1
                for i, it in enumerate(items):
                    try:
                        v = it.get("id")
                        if isinstance(v, str) and v.isdigit():
                            v_int = int(v)
                        elif isinstance(v, (int, float)):
                            v_int = int(v)
                        else:
                            continue
                        if max_id is None or v_int > max_id:
                            max_id = v_int
                            max_idx = i
                    except Exception:
                        continue
                if max_idx >= 0:
                    items = [it for j, it in enumerate(items) if j != max_idx]

            return items

        return _transform

    # --- Helpers de lectura de datos “puros” ---
    def get_current_campaign_id(self) -> int | None:
        return self.get_current_id()

    def get_current_campaign_name(self) -> str | None:
        """
        Devuelve el nombre 'puro' de la campaña (campo 'nombre' del dict).
        Si no encuentra el dict, intenta deducirlo desde la etiqueta.
        """
        it = self.get_current_item()
        if isinstance(it, dict):
            return it.get("nombre")
        txt = self.get_current_label()
        if " - " in txt:  # por si el label fuera "ID - Nombre"
            return txt.split(" - ", 1)[1]
        return txt or None

    def get_current_campaign_date_strings(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Devuelve (fecha_desde, fecha_hasta) como strings 'YYYY-MM-DD' si están disponibles.
        """
        it = self.get_current_item()
        if not isinstance(it, dict):
            return (None, None)
        fd = it.get(self._date_from_field) or it.get(self._alt_date_from_field)
        fh = it.get(self._date_to_field) or it.get(self._alt_date_to_field)
        return (_parse_date_to_str(fd), _parse_date_to_str(fh))

    def get_current_campaign_qdates(self) -> Tuple[Optional[QDate], Optional[QDate]]:
        """
        Devuelve (fecha_desde, fecha_hasta) como QDate si están disponibles; None si no.
        """
        s_fd, s_fh = self.get_current_campaign_date_strings()
        qd = QDate.fromString(s_fd, "yyyy-MM-dd") if s_fd else QDate()
        qh = QDate.fromString(s_fh, "yyyy-MM-dd") if s_fh else QDate()

        return (qd if qd.isValid() else None, qh if qh.isValid() else None)


# =============================================================================
# Explotaciones (filtradas por Campaña)
# =============================================================================
class ExplotacionesComboBox(CustomComboBox):
    """
    Combo para Explotaciones:
    - Editable + autocompletado.
    - Etiqueta formateada "ID - Nombre".
    - Puede enlazarse a CampaniasComboBox para filtrar por ?idcampania=...
    - Incluye kickstart robusto para la primera carga.
    - Ahora soporta trabajar sin estar bindeado, y decidir si requiere campaña o no.
    """

    def __init__(self, endpoint: str = "/api/explotaciones/", parent=None):
        super().__init__(
            endpoint=endpoint,
            parent=parent,
            label_field="nombre",
            value_field="id",
            allow_all=False,
            editable=True,
            sort_key="nombre",
            sort_reverse=False,
            param_provider=None,  # se define al bindear con campañas o modo libre
            label_formatter=lambda it: f"{it.get('id', '')} - {it.get('nombre', '')}",
        )
        self._bound_campaign_combo: CampaniasComboBox | None = None
        # NUEVO: si True => sin campaña, no carga (queda vacío). Si False => sin campaña, carga sin filtro.
        self._require_campaign: bool = False

        # Param provider por defecto (modo libre, sin filtros)
        if self.param_provider is None:
            self.set_param_provider(lambda: {})

    # --- NUEVO: permitir configurar si requiere campaña o no ---
    def set_require_campaign(self, require: bool) -> None:
        self._require_campaign = require
        self._kickstart_from_campaign()

    # --- NUEVO: desbindear campañas y volver a modo libre ---
    def unbind_campaigns(self) -> None:
        self._bound_campaign_combo = None
        self.set_param_provider(lambda: {})
        self.refresh()

    def bind_to_campaigns(self, campaign_combo: CampaniasComboBox, require_campaign: bool | None = None) -> None:
        """
        Vincula el combo de Explotaciones al de Campañas.
        - Cada cambio de campaña produce un refresh filtrado.
        - Kickstart inicial: sólo si ya existe un ID de campaña válido.
        - NUEVO: require_campaign (opcional):
            True  -> si no hay campaña, no cargar (vacío)
            False -> si no hay campaña, cargar sin filtro
            None  -> mantener configuración actual
        """
        self._bound_campaign_combo = campaign_combo
        if require_campaign is not None:
            self._require_campaign = require_campaign

        def _params() -> dict[str, Any]:
            cid = campaign_combo.get_current_campaign_id()
            return {"idcampania": cid} if cid is not None else {}

        self.set_param_provider(_params)

        # Cambios de campaña del usuario
        campaign_combo.current_value_changed.connect(
            self._on_campaign_changed, type=Qt.QueuedConnection
        )
        # Cuando campañas termina de cargar
        campaign_combo.items_loaded.connect(
            self._kickstart_from_campaign, type=Qt.QueuedConnection
        )
        # Señal legacy (si existe)
        try:
            campaign_combo.campaigns_loaded.connect(
                self._kickstart_from_campaign, type=Qt.QueuedConnection
            )
        except Exception:
            pass

        # Si este combo inició una carga “en vacío”, fuerza refresh al terminar
        if self.api_thread and self.api_thread.isRunning():
            self.api_thread.finished.connect(
                self._kickstart_from_campaign, type=Qt.QueuedConnection
            )

        # Patada inicial diferida (sólo si ya hay campaña)
        QTimer.singleShot(0, self._kickstart_from_campaign)

    def _on_campaign_changed(self, _value: object) -> None:
        """Recarga según haya campaña o no, respetando _require_campaign. (No toca tu threading.)"""
        if self._bound_campaign_combo is None:
            # No hay binding => refresca sin filtro
            self.refresh()
            return

        cid = self._bound_campaign_combo.get_current_campaign_id()
        if cid is None:
            if self._require_campaign:
                self._clear_items_safe()
                return
            # No requiere campaña: refrescar sin filtro temporalmente
            self._temporarily_use_default_params_and_refresh()
            return

        # Hay campaña válida => cargar filtrado
        self.refresh()

    def _kickstart_from_campaign(self) -> None:
        """Primera carga filtrada cuando la campaña actual ya está disponible."""
        if self._bound_campaign_combo is None:
            # Modo libre
            self.refresh()
            return
        cid = self._bound_campaign_combo.get_current_campaign_id()
        if cid is None:
            if self._require_campaign:
                self._clear_items_safe()
                return
            # No requiere: carga sin filtro
            self._temporarily_use_default_params_and_refresh()
            return
        self.refresh()

    # --- Helpers de lectura de datos “puros” (sin cambios) ---
    def get_current_explotacion_id(self) -> int | None:
        return self.get_current_id()

    def get_current_explotacion_name(self) -> str | None:
        """
        Devuelve el nombre 'puro' de la explotación (campo 'nombre' del dict).
        Si no encuentra el dict, intenta deducirlo desde la etiqueta "ID - Nombre".
        """
        it = self.get_current_item()
        if isinstance(it, dict):
            return it.get("nombre")
        txt = self.get_current_label()
        if " - " in txt:
            return txt.split(" - ", 1)[1]
        return txt or None

    # --- NUEVOS helpers internos, no afectan tu threading ---
    def _temporarily_use_default_params_and_refresh(self) -> None:
        """Refresca sin filtro una vez, preservando el provider original (si está bindeado)."""
        original_provider = getattr(self, "_param_provider", None)
        self.set_param_provider(lambda: {})
        try:
            self.refresh()
        finally:
            # Restaurar provider original si seguimos bindeados
            if self._bound_campaign_combo is not None and callable(original_provider):
                self.set_param_provider(original_provider)
            else:
                self.set_param_provider(lambda: {})

    def _clear_items_safe(self) -> None:
        try:
            self.clear()
        except Exception:
            pass

# =============================================================================
# Cultivos 
# =============================================================================
class CultivosComboBox(CustomComboBox):
    """
    Combo para Cultivos:
    - Soporta editable True/False desde init.
    - Soporta filtro opcional por (idcampania, idexplotacion).
    - Modo multi_select mantiene su lógica actual (checkboxes).
    """

    def __init__(
        self,
        endpoint: str = "/gis/cultivos/data_combo/",
        allow_all: bool = False,
        all_text: str = "Todos los cultivos...",
        auto_enable_on_load: bool = False,
        parent=None,
        *,
        multi_select: bool = False,
        editable: bool = True,
        filter_enabled: bool = False,
    ):
        # ---- flags internos (multi-select) ----
        self._multi_select = bool(multi_select)

        # ---- estado filtros ----
        self._filter_enabled: bool = bool(filter_enabled)
        self._filter_idcampania: int | None = None
        self._filter_idexplotacion: int | None = None

        # si falta contexto (campaña/exp) y filtro está ON:
        self._require_filter_context: bool = True
        # si require_filter_context=False y faltan ids:
        self._load_without_filter_if_missing: bool = False

        # combos bindeados (opcionales)
        self._bound_campaign_combo: CampaniasComboBox | None = None
        self._bound_explotacion_combo: ExplotacionesComboBox | None = None

        # comportamiento base (tu lógica actual)
        if self._multi_select:
            effective_allow_all = True
            effective_first_item = False
            effective_editable = True  # multi-select requiere editable para mostrar lineEdit
        else:
            effective_allow_all = allow_all
            effective_first_item = True
            effective_editable = bool(editable)

        super().__init__(
            endpoint=endpoint,
            parent=parent,
            label_field="nombre",
            value_field="id",
            allow_all=effective_allow_all,
            all_text=all_text,
            editable=effective_editable,
            sort_key="nombre",
            sort_reverse=False,
            auto_enable_on_load=auto_enable_on_load,
            first_item_text=effective_first_item,
            param_provider=self._params,  # <- clave: params dinámicos
        )

        if self._multi_select:
            self._init_multi_select_mode()

        self._kickstart_filtering()

    # ------------------- API pública: filtros -------------------
    def set_filtering_enabled(self, enabled: bool, *, refresh: bool = True) -> None:
        self._filter_enabled = bool(enabled)
        if refresh:
            self._kickstart_filtering()

    def set_filter_context(
        self,
        *,
        idcampania: int | None = None,
        idexplotacion: int | None = None,
        require_context: bool | None = None,
        load_without_filter_if_missing: bool | None = None,
        refresh: bool = True,
    ) -> None:
        """Setea filtros sin bindear combos."""
        self._bound_campaign_combo = None
        self._bound_explotacion_combo = None
        self._filter_idcampania = idcampania
        self._filter_idexplotacion = idexplotacion

        if require_context is not None:
            self._require_filter_context = bool(require_context)
        if load_without_filter_if_missing is not None:
            self._load_without_filter_if_missing = bool(load_without_filter_if_missing)

        if refresh:
            self._kickstart_filtering()

    def bind_filters(
        self,
        campaign_combo: "CampaniasComboBox",
        explotacion_combo: "ExplotacionesComboBox",
        *,
        enabled: bool = True,
        require_context: bool = True,
        load_without_filter_if_missing: bool = False,
    ) -> None:
        """Se engancha a campaña+explotación y recarga en cascada."""
        self._bound_campaign_combo = campaign_combo
        self._bound_explotacion_combo = explotacion_combo
        self._filter_enabled = bool(enabled)
        self._require_filter_context = bool(require_context)
        self._load_without_filter_if_missing = bool(load_without_filter_if_missing)

        campaign_combo.current_value_changed.connect(self._on_context_changed, type=Qt.QueuedConnection)
        explotacion_combo.current_value_changed.connect(self._on_context_changed, type=Qt.QueuedConnection)

        campaign_combo.items_loaded.connect(self._kickstart_filtering, type=Qt.QueuedConnection)
        explotacion_combo.items_loaded.connect(self._kickstart_filtering, type=Qt.QueuedConnection)

        try:
            campaign_combo.campaigns_loaded.connect(self._kickstart_filtering, type=Qt.QueuedConnection)
        except Exception:
            pass

        QTimer.singleShot(0, self._kickstart_filtering)

    def unbind_filters(self, *, refresh: bool = True) -> None:
        self._bound_campaign_combo = None
        self._bound_explotacion_combo = None
        if refresh:
            self._kickstart_filtering()

    # ------------------- internals -------------------
    def _params(self) -> dict[str, Any]:
        """Param provider para el endpoint."""
        if not self._filter_enabled:
            return {}

        if self._bound_campaign_combo is not None:
            self._filter_idcampania = self._bound_campaign_combo.get_current_campaign_id()
        if self._bound_explotacion_combo is not None:
            self._filter_idexplotacion = self._bound_explotacion_combo.get_current_explotacion_id()

        if self._filter_idcampania is None or self._filter_idexplotacion is None:
            return {}

        return {"idcampania": self._filter_idcampania, "idexplotacion": self._filter_idexplotacion}

    def _on_context_changed(self, _val: object) -> None:
        self._kickstart_filtering()

    def _kickstart_filtering(self) -> None:
        """Decide si carga filtrado, libre o vacío."""
        if not self._filter_enabled:
            self.refresh()
            return

        params = self._params()
        if params:
            self.refresh()
            return

        # filtro activo pero falta contexto
        if self._require_filter_context:
            self._clear_items_safe()
            return

        if self._load_without_filter_if_missing:
            self._temporarily_use_default_params_and_refresh()
            return

        self._clear_items_safe()

    def _temporarily_use_default_params_and_refresh(self) -> None:
        original_provider = getattr(self, "param_provider", None)
        self.set_param_provider(lambda: {})
        try:
            self.refresh()
        finally:
            self.set_param_provider(original_provider if callable(original_provider) else lambda: {})

    def _clear_items_safe(self) -> None:
        try:
            self.clear()
        except Exception:
            pass
    # ------------------------------------------------------------------
    # API pública extra para multi-select
    # ------------------------------------------------------------------
    def is_multi_select_enabled(self) -> bool:
        return self._multi_select

    def get_selected_ids(self) -> list:
        """
        Devuelve la lista de IDs seleccionados cuando multi_select=True.
        Si multi_select=False, devuelve [id_actual] o [] si no hay ID.

        Nota:
        - En modo multi, "Todos los cultivos..." tiene userData=None,
          así que NO se incluye en la lista (equivale a "no filtrar").
          
        """
        if not self._multi_select:
            cid = self.get_current_id()
            return [cid] if cid is not None else []

        model = self.model()
        selected: list = []
        if isinstance(model, QStandardItemModel):
            for row in range(model.rowCount()):
                item = model.item(row)
                if not isinstance(item, QStandardItem):
                    continue
                if item.checkState() == Qt.Checked:
                    data = self.itemData(row)
                    if data is not None:  # ignoramos el "Todos..." (userData=None)
                        selected.append(data)
        return selected

    # ------------------------------------------------------------------
    # Configuración del modo multi-select
    # ------------------------------------------------------------------
    def _init_multi_select_mode(self) -> None:
        """
        Configura el combo para trabajar en modo multi-select:
        - la línea de edición es solo lectura
        - las filas del modelo son checkables
        - se interceptan clics en el popup para alternar check
        """
        self.setEditable(True)
        if self.lineEdit() is not None:
            self.lineEdit().setReadOnly(True)

        # Cuando se cargan items desde el backend, configuramos checkboxes
        self.items_loaded.connect(self._make_items_checkable)

        # Actualizar el texto visible cuando cambien los checks
        if self.model() is not None:
            self.model().dataChanged.connect(self._update_display_text)

        # Interceptar clics en el popup para alternar check sin cerrar
        if self.view() is not None and self.view().viewport() is not None:
            self.view().viewport().installEventFilter(self)

        # Forzar un primer update del texto (por si ya hay datos)
        self._update_display_text()

    def _make_items_checkable(self, _items: object) -> None:
        """
        Marca todos los items como checkables (solo en modo multi-select).
        En esta función también:
        - marca "Todos los cultivos..." (fila 0) como Checked
        - desmarca el resto
        """
        if not self._multi_select:
            return

        model = self.model()
        if not isinstance(model, QStandardItemModel):
            return

        for row in range(model.rowCount()):
            item = model.item(row)
            if not isinstance(item, QStandardItem):
                continue

            # Hacemos el item checkable
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)

            if row == 0:
                # Primera fila -> "Todos los cultivos..."
                item.setData(Qt.Checked, Qt.CheckStateRole)
            else:
                item.setData(Qt.Unchecked, Qt.CheckStateRole)

        # Tras hacerlos checkables, refrescamos el texto
        self._update_display_text()

    def _update_display_text(self) -> None:
        """
        Construye el texto que se muestra en la línea de edición
        con los nombres de los cultivos seleccionados.
        """
        if not self._multi_select:
            return

        model = self.model()
        if not isinstance(model, QStandardItemModel):
            return

        texts: list[str] = []
        for row in range(model.rowCount()):
            item = model.item(row)
            if not isinstance(item, QStandardItem):
                continue
            if item.checkState() == Qt.Checked:
                txt = item.text()
                if txt:
                    texts.append(txt)

        full_text = ", ".join(texts)

        if self.lineEdit() is not None:
            metrics = QFontMetrics(self.lineEdit().font())
            elided = metrics.elidedText(full_text, Qt.ElideRight, self.lineEdit().width())
            self.lineEdit().setText(elided)

    # ------------------------------------------------------------------
    # Overrides suaves para integrar el eventFilter en modo multi-select
    # ------------------------------------------------------------------
    def eventFilter(self, obj, event):
        """
        Intercepta clics en el popup para marcar/desmarcar sin cerrar.
        Lógica especial:
        - Si se hace click en "Todos los cultivos..." (fila 0):
            * se marca "Todos" y se desmarcan todos los demás.
        - Si se hace click en cualquier otro cultivo:
            * se alterna ese cultivo
            * se desmarca "Todos los cultivos..." automáticamente.
        """
        if self._multi_select and self.view() is not None and obj == self.view().viewport():
            if event.type() == QEvent.MouseButtonRelease:
                index = self.view().indexAt(event.pos())
                if not index.isValid():
                    return False

                model = self.model()
                if not isinstance(model, QStandardItemModel):
                    return False

                item = model.itemFromIndex(index)
                if not isinstance(item, QStandardItem):
                    return False

                row = index.row()

                if row == 0:
                    # Click sobre "Todos los cultivos..."
                    for r in range(model.rowCount()):
                        it = model.item(r)
                        if not isinstance(it, QStandardItem):
                            continue
                        it.setCheckState(Qt.Checked if r == 0 else Qt.Unchecked)
                else:
                    # Click sobre un cultivo concreto
                    current_state = item.checkState()
                    new_state = Qt.Unchecked if current_state == Qt.Checked else Qt.Checked
                    item.setCheckState(new_state)

                    # Si se marca cualquiera de los otros, desmarcamos "Todos"
                    first_item = model.item(0)
                    if isinstance(first_item, QStandardItem):
                        first_item.setCheckState(Qt.Unchecked)

                self._update_display_text()
                # Evitamos que cambie el currentIndex o cierre el popup
                return True

        return super().eventFilter(obj, event)

    def resizeEvent(self, event):
        """
        Cuando cambia el tamaño, recalculamos el elided text.
        """
        if self._multi_select:
            self._update_display_text()
        super().resizeEvent(event)

    
class RegimenComboBox(CustomComboBox):
    """
    Combo para Régimen:
    - editable True/False desde init
    - filtro opcional por (idcampania, idexplotacion, idcultivo)
    """

    def __init__(
        self,
        endpoint: str = "/gis/regimen/data_combo/",
        auto_enable_on_load: bool = False,
        parent=None,
        *,
        editable: bool = True,
        filter_enabled: bool = False,
    ):
        # ---- estado filtros ----
        self._filter_enabled: bool = bool(filter_enabled)
        self._filter_idcampania: int | None = None
        self._filter_idexplotacion: int | None = None
        self._filter_idcultivo: int | None = None

        self._require_filter_context: bool = True
        self._load_without_filter_if_missing: bool = False

        self._bound_campaign_combo: CampaniasComboBox | None = None
        self._bound_explotacion_combo: ExplotacionesComboBox | None = None
        self._bound_cultivo_combo: CultivosComboBox | None = None

        super().__init__(
            endpoint=endpoint,
            parent=parent,
            label_field="nombre",
            value_field="id",
            allow_all=False,
            editable=bool(editable),
            sort_key="nombre",
            sort_reverse=False,
            auto_enable_on_load=auto_enable_on_load,
            first_item_text=True,
            param_provider=self._params,
        )

        self._kickstart_filtering()

    # ------------------- API pública: filtros -------------------
    def set_filtering_enabled(self, enabled: bool, *, refresh: bool = True) -> None:
        self._filter_enabled = bool(enabled)
        if refresh:
            self._kickstart_filtering()

    def set_filter_context(
        self,
        *,
        idcampania: int | None = None,
        idexplotacion: int | None = None,
        idcultivo: int | None = None,
        require_context: bool | None = None,
        load_without_filter_if_missing: bool | None = None,
        refresh: bool = True,
    ) -> None:
        self._bound_campaign_combo = None
        self._bound_explotacion_combo = None
        self._bound_cultivo_combo = None

        self._filter_idcampania = idcampania
        self._filter_idexplotacion = idexplotacion
        self._filter_idcultivo = idcultivo

        if require_context is not None:
            self._require_filter_context = bool(require_context)
        if load_without_filter_if_missing is not None:
            self._load_without_filter_if_missing = bool(load_without_filter_if_missing)

        if refresh:
            self._kickstart_filtering()

    def bind_filters(
        self,
        campaign_combo: "CampaniasComboBox",
        explotacion_combo: "ExplotacionesComboBox",
        cultivo_combo: "CultivosComboBox",
        *,
        enabled: bool = True,
        require_context: bool = True,
        load_without_filter_if_missing: bool = False,
    ) -> None:
        self._bound_campaign_combo = campaign_combo
        self._bound_explotacion_combo = explotacion_combo
        self._bound_cultivo_combo = cultivo_combo

        self._filter_enabled = bool(enabled)
        self._require_filter_context = bool(require_context)
        self._load_without_filter_if_missing = bool(load_without_filter_if_missing)

        campaign_combo.current_value_changed.connect(self._on_context_changed, type=Qt.QueuedConnection)
        explotacion_combo.current_value_changed.connect(self._on_context_changed, type=Qt.QueuedConnection)
        cultivo_combo.current_value_changed.connect(self._on_context_changed, type=Qt.QueuedConnection)

        campaign_combo.items_loaded.connect(self._kickstart_filtering, type=Qt.QueuedConnection)
        explotacion_combo.items_loaded.connect(self._kickstart_filtering, type=Qt.QueuedConnection)
        cultivo_combo.items_loaded.connect(self._kickstart_filtering, type=Qt.QueuedConnection)

        try:
            campaign_combo.campaigns_loaded.connect(self._kickstart_filtering, type=Qt.QueuedConnection)
        except Exception:
            pass

        QTimer.singleShot(0, self._kickstart_filtering)

    def unbind_filters(self, *, refresh: bool = True) -> None:
        self._bound_campaign_combo = None
        self._bound_explotacion_combo = None
        self._bound_cultivo_combo = None
        if refresh:
            self._kickstart_filtering()

    # ------------------- internals -------------------
    def _params(self) -> dict[str, Any]:
        if not self._filter_enabled:
            return {}

        if self._bound_campaign_combo is not None:
            self._filter_idcampania = self._bound_campaign_combo.get_current_campaign_id()
        if self._bound_explotacion_combo is not None:
            self._filter_idexplotacion = self._bound_explotacion_combo.get_current_explotacion_id()
        if self._bound_cultivo_combo is not None:
            self._filter_idcultivo = self._bound_cultivo_combo.get_current_id()

        if (
            self._filter_idcampania is None
            or self._filter_idexplotacion is None
            or self._filter_idcultivo is None
        ):
            return {}

        return {
            "idcampania": self._filter_idcampania,
            "idexplotacion": self._filter_idexplotacion,
            "idcultivo": self._filter_idcultivo,
        }

    def _on_context_changed(self, _val: object) -> None:
        self._kickstart_filtering()

    def _kickstart_filtering(self) -> None:
        if not self._filter_enabled:
            self.refresh()
            return

        params = self._params()
        if params:
            self.refresh()
            return

        if self._require_filter_context:
            self._clear_items_safe()
            return

        if self._load_without_filter_if_missing:
            self._temporarily_use_default_params_and_refresh()
            return

        self._clear_items_safe()

    def _temporarily_use_default_params_and_refresh(self) -> None:
        original_provider = getattr(self, "param_provider", None)
        self.set_param_provider(lambda: {})
        try:
            self.refresh()
        finally:
            self.set_param_provider(original_provider if callable(original_provider) else lambda: {})

    def _clear_items_safe(self) -> None:
        try:
            self.clear()
        except Exception:
            pass
    """
    Combo para Regimen:
    - Editable + autocompletado.
    - Etiqueta formateada "Nombre".
    - auto_enable_on_load=False por defecto: el dock controla su estado (modo edición).
    """


# ================================================================================
# Contratos y Facturacion
# ================================================================================


class PlanesComboBox(CustomComboBox):
    """
    Combo para Planes (/billing/planes):
    - Sin filtros (por ahora).
    - value_field = idplan (según response).
    - Señal plan_changed emite el dict completo del plan actual.
    - Puede filtrar sólo activos (activo=True).
    """

    plan_changed = pyqtSignal(object)  # emite dict del plan o None

    def __init__(
        self,
        endpoint: str = "/billing/planes",
        parent=None,
        *,
        editable: bool = True,
        only_active: bool = True,
        auto_enable_on_load: bool = False,
        show_details_in_label: bool = True,
    ):
        self._only_active = bool(only_active)
        self._show_details_in_label = bool(show_details_in_label)

        def _label(it: dict) -> str:
            # Nombre "bonito" y estable (sin depender de campos que vayan a desaparecer)
            nombre = str(it.get("nombre", "") or "").strip()
            codigo = str(it.get("codigo", "") or "").strip()

            if not self._show_details_in_label:
                # Si hay código, lo ponemos delante
                return f"{codigo} - {nombre}" if codigo else (nombre or "-")

            pm = str(it.get("pricing_model", "") or "").strip()
            pb = it.get("precio_base", None)
            mh = it.get("max_ha", None)

            # Ojo: precio_base / max_ha te pueden venir como string; lo mostramos tal cual
            parts = []
            if pm:
                parts.append(pm)
            if pb not in (None, ""):
                parts.append(f"Base {pb}")
            if mh not in (None, ""):
                parts.append(f"Max {mh} ha")

            suffix = f" ({' | '.join(parts)})" if parts else ""
            base = f"{codigo} - {nombre}" if codigo else (nombre or "-")
            return f"{base}{suffix}"

        def _transform(items: list[dict]) -> list[dict]:
            out = [it for it in items if isinstance(it, dict)]
            if self._only_active:
                out = [it for it in out if it.get("activo", True) is True]
            return out

        super().__init__(
            endpoint=endpoint,
            parent=parent,
            label_field="nombre",
            value_field="idplan",              # <-- CLAVE
            allow_all=False,
            editable=bool(editable),
            sort_key="nombre",
            sort_reverse=False,
            auto_enable_on_load=bool(auto_enable_on_load),
            first_item_text=True,
            param_provider=lambda: {},         # <-- sin filtros
            label_formatter=_label,
            items_transform=_transform,
        )

        # Emitir dict completo cuando cambie
        self.current_value_changed.connect(self._emit_plan_changed)

        # Al cargar items, también emitimos el plan actual
        self.items_loaded.connect(lambda _items: self._emit_plan_changed(self.currentData()))

    # ------------------- API pública -------------------
    def set_only_active(self, flag: bool, *, refresh: bool = True) -> None:
        self._only_active = bool(flag)
        # Reaplicamos la transform
        self.set_items_transform(self._items_transform_dynamic(), refresh=refresh)

    def set_show_details_in_label(self, flag: bool, *, refresh: bool = True) -> None:
        self._show_details_in_label = bool(flag)
        # Reaplicamos formatter (y refrescamos para repintar labels)
        self.set_label_formatter(self._label_formatter_dynamic())
        if refresh:
            self.refresh()

    def get_current_plan(self) -> dict | None:
        return self.get_current_item()

    def get_current_plan_id(self) -> int | None:
        return self.get_current_id()

    def get_current_plan_name(self) -> str | None:
        it = self.get_current_plan()
        if isinstance(it, dict):
            return it.get("nombre")
        return None

    # ------------------- Internals -------------------
    def _emit_plan_changed(self, _value: object) -> None:
        self.plan_changed.emit(self.get_current_plan())

    def _label_formatter_dynamic(self):
        # reusa el mismo formateador con el estado actual
        def _label(it: dict) -> str:
            nombre = str(it.get("nombre", "") or "").strip()
            codigo = str(it.get("codigo", "") or "").strip()

            if not self._show_details_in_label:
                return f"{codigo} - {nombre}" if codigo else (nombre or "-")

            pm = str(it.get("pricing_model", "") or "").strip()
            pb = it.get("precio_base", None)
            mh = it.get("max_ha", None)

            parts = []
            if pm:
                parts.append(pm)
            if pb not in (None, ""):
                parts.append(f"Base {pb}")
            if mh not in (None, ""):
                parts.append(f"Max {mh} ha")

            suffix = f" ({' | '.join(parts)})" if parts else ""
            base = f"{codigo} - {nombre}" if codigo else (nombre or "-")
            return f"{base}{suffix}"

        return _label

    def _items_transform_dynamic(self):
        def _transform(items: list[dict]) -> list[dict]:
            out = [it for it in items if isinstance(it, dict)]
            if self._only_active:
                out = [it for it in out if it.get("activo", True) is True]
            return out

        return _transform


class SeriesComboBox(CustomComboBox):
    """
    Combo para Series de Facturación (/billing/series):
    - Sin filtros (por ahora).
    - value_field = idserie (según response).
    - label_field = nombre (según response).
    """

    def __init__(
        self,
        endpoint: str = "billing/series",
        parent=None,
        *,
        editable: bool = False,
        auto_enable_on_load: bool = True,
    ):
        super().__init__(
            endpoint=endpoint,
            parent=parent,
            label_field="letra",
            value_field="idserie",  # <-- CLAVE
            allow_all=False,
            editable=bool(editable),
            sort_key="letra",
            sort_reverse=False,
            auto_enable_on_load=bool(auto_enable_on_load),
            first_item_text=False,
            param_provider=lambda: {},  # <-- sin filtros
        )  

    def get_current_serie(self) -> dict | None:
        return self.get_current_item()
    

    def _custom_label_formatter(self, it: dict) -> str:
        letra = str(it.get("letra", "") or "").strip()
        anio = str(it.get("anio", "") or "").strip()
        return f"{letra} → {anio}" if anio else (letra or "-")
    

class ContratosComboBox(CustomComboBox):
    def __init__(
        self,
        endpoint: str = "/billing/contratos",
        parent=None,
        *,
        editable: bool = False,
        auto_enable_on_load: bool = True,
    ):
        super().__init__(
            endpoint=endpoint,
            parent=parent,
            label_field="nombre",
            value_field="idcontrato",  # <-- CLAVE
            allow_all=False,
            editable=bool(editable),
            sort_key="nombre",
            sort_reverse=False,
            auto_enable_on_load=bool(auto_enable_on_load),
            first_item_text=False,
            param_provider=lambda: {},  # <-- sin filtros
        )