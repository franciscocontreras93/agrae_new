# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import requests

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QSizePolicy, QWidget
)
from qgis.core import QgsTask, QgsApplication, QgsMessageLog, Qgis

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import matplotlib.cm as cm
import matplotlib.patches as mpatches


# -----------------------------
# Helpers
# -----------------------------
def _parse_date(date_str: str) -> datetime:
    return datetime.strptime(date_str, "%Y-%m-%d")


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        if v is None:
            return default
        return float(v)
    except Exception:
        return default


def _group_consecutive_ranges(rows: List[Dict[str, Any]], key: str) -> List[Tuple[str, int, int]]:
    """(value, i0, i1) inclusive for consecutive blocks of rows[i][key]."""
    if not rows:
        return []
    ranges: List[Tuple[str, int, int]] = []
    cur = rows[0].get(key)
    start = 0
    for i in range(1, len(rows)):
        v = rows[i].get(key)
        if v != cur:
            ranges.append((str(cur) if cur is not None else "", start, i - 1))
            cur = v
            start = i
    ranges.append((str(cur) if cur is not None else "", start, len(rows) - 1))
    return ranges


# -----------------------------
# Background task
# -----------------------------
class FetchGDDDetailTask(QgsTask):
    def __init__(self, url: str, params: Optional[dict] = None):
        super().__init__("Cargando integral térmica", QgsTask.CanCancel)
        self.url = url
        self.params = params or {}
        self.result_data: Optional[List[Dict[str, Any]]] = None
        self.error: Optional[str] = None

    def run(self) -> bool:
        try:
            r = requests.get(self.url, params=self.params, timeout=60)
            r.raise_for_status()
            data = r.json()
            if not isinstance(data, list):
                raise ValueError("La respuesta del endpoint no es una lista.")
            self.result_data = data
            return True
        except Exception as e:
            self.error = str(e)
            return False


# -----------------------------
# Dialog
# -----------------------------
class IntegralTermicaDialog(QDialog):
    """
    Endpoint: /gis/integral_termica/gdd_detail/{iddata}
    """

    def __init__(
        self,
        parent=None,
        base_url: str = "http://127.0.0.1:8000",
        iddata: Optional[int] = None,
        params: Optional[dict] = None,
        phase_key: str = "etapa_actual",  # o "tramo"
        phase_alpha: float = 0.22,
        draw_hito_vlines: bool = True,   # líneas negras (sin puntos/labels)
    ):
        super().__init__(parent)
        self.setWindowTitle("Detalle Integral Térmica (GDD)")
        self.resize(1200, 680)

        self.base_url = base_url.rstrip("/")
        self.iddata = iddata
        self.params = params or {}
        self.phase_key = phase_key
        self.phase_alpha = phase_alpha
        self.draw_hito_vlines = draw_hito_vlines

        self.rows: List[Dict[str, Any]] = []
        self.dates: List[datetime] = []
        self.gdd_acum: List[float] = []

        # Hover artists
        self._hover_idx: Optional[int] = None
        self._hover_vline = None
        self._hover_marker = None
        self._hover_annot = None

        # ---------------- UI
        main = QVBoxLayout(self)

        top = QHBoxLayout()
        self.lbl_title = QLabel("Integral térmica — detalle")
        self.lbl_title.setStyleSheet("font-weight:700; font-size:14px;")
        top.addWidget(self.lbl_title)
        top.addStretch(1)

        self.btn_reload = QPushButton("Recargar")
        self.btn_reload.clicked.connect(self.reload_async)
        top.addWidget(self.btn_reload)
        main.addLayout(top)

        plot_container = QWidget(self)
        plot_layout = QVBoxLayout(plot_container)
        plot_layout.setContentsMargins(0, 0, 0, 0)
        plot_layout.setSpacing(4)

        self.fig = Figure(figsize=(8, 4), dpi=100)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.ax = self.fig.add_subplot(111)

        self.toolbar = NavigationToolbar(self.canvas, self)
        plot_layout.addWidget(self.toolbar)
        plot_layout.addWidget(self.canvas)
        main.addWidget(plot_container)

        # Loading overlay
        self.loading = QFrame(self.canvas)
        self.loading.setStyleSheet(
            "QFrame { background: rgba(255,255,255,215); border: 1px solid #e5e7eb; border-radius: 10px; }"
            "QLabel { font-size: 13px; font-weight: 700; }"
        )
        self.loading.setVisible(False)
        self.loading_label = QLabel("Cargando…", self.loading)
        self.loading_label.setAlignment(Qt.AlignCenter)
        l = QVBoxLayout(self.loading)
        l.addWidget(self.loading_label)

        # Tooltip events
        self._cid_motion = self.canvas.mpl_connect("motion_notify_event", self._on_motion)
        self._cid_leave = self.canvas.mpl_connect("figure_leave_event", self._on_leave)

        self._reposition_loading_overlay()
        self.reload_async()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._reposition_loading_overlay()

    def _reposition_loading_overlay(self):
        w = int(self.canvas.width() * 0.35)
        h = 70
        x = int((self.canvas.width() - w) / 2)
        y = 10
        self.loading.setGeometry(x, y, w, h)

    def _set_loading(self, on: bool, text: str = "Cargando…"):
        self.loading_label.setText(text)
        self.loading.setVisible(on)
        self.btn_reload.setEnabled(not on)

    # ---------------- Async load
    def reload_async(self):
        if self.iddata is None:
            self.lbl_title.setText("Falta iddata")
            return

        self._set_loading(True)
        url = f"{self.base_url}/gis/integral_termica/gdd_detail/{int(self.iddata)}"
        task = FetchGDDDetailTask(url, self.params)

        def _done():
            self._set_loading(False)

            if task.error:
                self.lbl_title.setText(f"Error cargando datos (iddata={self.iddata})")
                QgsMessageLog.logMessage(task.error, "aGrae", Qgis.Critical)
                self._clear_plot("Error cargando datos")
                return

            rows = task.result_data or []
            if not rows:
                self.lbl_title.setText(f"Sin datos (iddata={self.iddata})")
                self._clear_plot("Sin datos")
                return

            rows.sort(key=lambda r: r.get("fecha") or "")
            self.rows = rows
            self._build_series()
            self._draw()

            self.lbl_title.setText(f"GDD detail (iddata={self.iddata}) — {len(rows)} días")

        task.taskCompleted.connect(_done)
        task.taskTerminated.connect(_done)
        QgsApplication.taskManager().addTask(task)

    # ---------------- Data
    def _build_series(self):
        self.dates = []
        self.gdd_acum = []
        for r in self.rows:
            self.dates.append(_parse_date(r["fecha"]))
            self.gdd_acum.append(_safe_float(r.get("gdd_acum"), 0.0))

    # ---------------- Plot
    def _clear_plot(self, message: str = ""):
        self.ax.clear()
        if message:
            self.ax.text(0.5, 0.5, message, transform=self.ax.transAxes, ha="center", va="center")
        self.canvas.draw_idle()

    def _draw(self):
        self.ax.clear()

        # Relleno por etapas hasta la curva + leyenda
        phase_patches = self._draw_phase_fill_to_curve_and_legend()

        # Curva principal
        self.ax.plot(self.dates, self.gdd_acum, lw=2, label="GDD acumulada", zorder=10)

        # Líneas negras (opcional) en hitos, SIN puntos ni etiquetas
        if self.draw_hito_vlines:
            self._draw_hito_vlines_to_curve()

        # Formato
        self.ax.set_ylabel("GDD acumulada")
        self.ax.set_xlabel("Fecha")
        self.ax.grid(True, alpha=0.25)
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
        self.fig.autofmt_xdate()

        ymax = max(self.gdd_acum) if self.gdd_acum else 1.0
        if ymax <= 0:
            ymax = 1.0
        self.ax.set_ylim(0, ymax * 1.10)

        # Leyendas: serie arriba-izq, etapas a la derecha
        leg1 = self.ax.legend(loc="upper left", fontsize=9)
        if phase_patches:
            leg2 = self.ax.legend(
                handles=phase_patches,
                title=self.phase_key,
                loc="upper left",
                bbox_to_anchor=(1.01, 1.0),
                borderaxespad=0.0,
                fontsize=8,
                title_fontsize=9,
                frameon=True
            )
            self.ax.add_artist(leg1)

        # margen para leyenda derecha
        self.fig.subplots_adjust(right=0.80)

        self._reset_hover_artists()
        self.canvas.draw_idle()

    def _draw_phase_fill_to_curve_and_legend(self) -> List[mpatches.Patch]:
        """
        Rellena por tramos desde y=0 hasta y=GDD_acum (corta con la curva).
        Además evita gaps extendiendo cada tramo hasta el día siguiente del último punto.
        """
        if not self.rows:
            return []

        ranges = _group_consecutive_ranges(self.rows, self.phase_key)
        if not ranges:
            return []

        # colores estables por orden de aparición
        cmap = cm.get_cmap("tab20")
        unique_vals: List[str] = []
        for v, _, _ in ranges:
            if v not in unique_vals:
                unique_vals.append(v)

        color_map = {v: cmap(i % 20) for i, v in enumerate(unique_vals)}

        # --- fill por tramo (0 -> curva)
        n = len(self.dates)
        for v, i0, i1 in ranges:
            if i0 < 0 or i1 >= n:
                continue

            c = color_map.get(v, (0.8, 0.9, 1.0, 1.0))

            # segmento base
            x_seg = self.dates[i0:i1 + 1]
            y_seg = self.gdd_acum[i0:i1 + 1]

            # extender al día siguiente para NO dejar huecos
            # (cierra el último rectángulo del tramo)
            last_x = self.dates[i1]
            last_y = self.gdd_acum[i1]
            x_seg = x_seg + [last_x + timedelta(days=1)]
            y_seg = y_seg + [last_y]

            self.ax.fill_between(
                x_seg,
                0,
                y_seg,
                step="post",           # clave para que no queden gaps en cambios
                color=c,
                alpha=self.phase_alpha,
                linewidth=0.0,
                zorder=1
            )

        # patches de leyenda (una por etapa)
        patches: List[mpatches.Patch] = []
        for v in unique_vals:
            label = v if v else "(vacío)"
            patches.append(mpatches.Patch(color=color_map[v], alpha=self.phase_alpha, label=label))
        return patches

    def _draw_hito_vlines_to_curve(self):
        """Dibuja líneas negras cortas (0->curva) solo donde is_hito=True."""
        for i, r in enumerate(self.rows):
            if not r.get("is_hito"):
                continue
            dt = self.dates[i]
            y = self.gdd_acum[i]
            self.ax.vlines(dt, 0, y, colors="black", linewidth=1.1, alpha=0.70, zorder=9)

    # ---------------- Hover / tooltip
    def _reset_hover_artists(self):
        for art in (self._hover_vline, self._hover_marker, self._hover_annot):
            if art is None:
                continue
            try:
                art.remove()
            except Exception:
                pass
        self._hover_vline = None
        self._hover_marker = None
        self._hover_annot = None
        self._hover_idx = None

    def _nearest_index_by_x(self, xdate_num: float) -> Optional[int]:
        if not self.dates:
            return None
        best_i = 0
        best_d = None
        for i, d in enumerate(self.dates):
            dn = mdates.date2num(d)
            dd = abs(dn - xdate_num)
            if best_d is None or dd < best_d:
                best_d = dd
                best_i = i
        return best_i

    def _on_motion(self, event):
        # Respeta pan/zoom
        if self.toolbar.mode != "":
            return
        if event.inaxes != self.ax or event.xdata is None:
            return

        idx = self._nearest_index_by_x(event.xdata)
        if idx is None or idx == self._hover_idx:
            return

        self._hover_idx = idx
        dt = self.dates[idx]
        y = self.gdd_acum[idx]
        r = self.rows[idx]

        if self._hover_vline is None:
            self._hover_vline = self.ax.axvline(dt, color="gray", lw=1, alpha=0.35, zorder=50)
        else:
            self._hover_vline.set_xdata([dt, dt])

        if self._hover_marker is None:
            (self._hover_marker,) = self.ax.plot([dt], [y], marker="o", markersize=6, alpha=0.9, zorder=51)
        else:
            self._hover_marker.set_data([dt], [y])

        text = self._format_tooltip(dt, r)
        if self._hover_annot is None:
            self._hover_annot = self.ax.annotate(
                text,
                xy=(dt, y),
                xytext=(15, 15),
                textcoords="offset points",
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#e5e7eb", alpha=0.95),
                fontsize=9,
                zorder=52
            )
        else:
            self._hover_annot.xy = (dt, y)
            self._hover_annot.set_text(text)

        self.canvas.draw_idle()

    def _on_leave(self, event):
        self._reset_hover_artists()
        self.canvas.draw_idle()

    def _format_tooltip(self, dt: datetime, r: Dict[str, Any]) -> str:
        is_hito = "✅" if r.get("is_hito") else ""
        tramo = r.get("tramo", "")
        etapa = r.get("etapa_actual", "")
        umbral = r.get("umbral_etapa_actual", "")
        gdd_d = _safe_float(r.get("gdd_dia"), 0.0)
        gdd_a = _safe_float(r.get("gdd_acum"), 0.0)
        tmean = r.get("tmean_corr", "")

        return (
            f"{dt.strftime('%d/%m/%Y')} {is_hito}\n"
            f"Tramo: {tramo}\n"
            f"Etapa: {etapa}  Umbral: {umbral}\n"
            f"Tmean corr: {tmean}\n"
            f"GDD día: {gdd_d:.2f}\n"
            f"GDD acum: {gdd_a:.2f}"
        )


# -----------------------------
# USO
# -----------------------------
# dlg = IntegralTermicaDialog(
#     parent=iface.mainWindow(),
#     base_url="http://TU_SERVIDOR:8000",
#     iddata=12345,
#     phase_key="etapa_actual",   # o "tramo"
#     draw_hito_vlines=True
# )
# dlg.exec_()
