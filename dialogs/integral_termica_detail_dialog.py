# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import requests

import agrae
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


from ..tools import aGraeTools


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


def _range_midpoint_date(dates: List[datetime], i0: int, i1: int) -> datetime:
    """
    Midpoint temporal del rango [i0..i1] considerando el gráfico con step='post',
    por lo que el rango realmente termina en (date[i1] + 1 día).
    """
    start = dates[i0]
    end_edge = dates[i1] + timedelta(days=1)
    return start + (end_edge - start) / 2


def _build_manejo_spans(
    rows: List[Dict[str, Any]],
    dates: List[datetime],
    phase_key: str,
) -> List[Dict[str, Any]]:
    """
    Para cada is_manejo_hito=True:
      - busca el rango de etapa (por phase_key) donde cae la fecha del manejo
      - calcula mid_prev (mitad de etapa anterior) y mid_next (mitad de etapa siguiente)
      - devuelve spans [{start, end, code, name, i_manejo}]
    """
    if not rows:
        return []

    # rangos por etapa
    ranges = _group_consecutive_ranges(rows, phase_key)  # [(etapa, i0, i1), ...]
    if not ranges:
        return []

    # para buscar rápido a qué rango pertenece un índice i
    # (como ranges son consecutivos, basta con iterar)
    def range_index_for_i(i: int) -> int:
        for k, (_, a, b) in enumerate(ranges):
            if a <= i <= b:
                return k
        return 0

    spans: List[Dict[str, Any]] = []

    for i, r in enumerate(rows):
        if not r.get("is_manejo_hito"):
            continue

        k = range_index_for_i(i)

        # etapa anterior / siguiente
        k_prev = k - 1 if k > 0 else None
        k_next = k + 1 if k < len(ranges) - 1 else None

        # midpoint anterior/siguiente (si no existe, usamos borde disponible)
        if k_prev is not None:
            _, a0, a1 = ranges[k_prev]
            mid_prev = _range_midpoint_date(dates, a0, a1)
        else:
            # si no hay anterior, tomamos el inicio del rango actual
            _, a0, _ = ranges[k]
            mid_prev = dates[a0]

        if k_next is not None:
            _, b0, b1 = ranges[k_next]
            mid_next = _range_midpoint_date(dates, b0, b1)
        else:
            # si no hay siguiente, tomamos el fin del rango actual (+1 día como edge)
            _, _, b1 = ranges[k]
            mid_next = dates[b1] + timedelta(days=1)

        # asegurar orden
        if mid_next < mid_prev:
            mid_prev, mid_next = mid_next, mid_prev

        spans.append({
            "start": mid_prev,
            "end": mid_next,
            "code": r.get("manejo_hito"),
            "name": r.get("manejo_hito_nombre"),
            "i_manejo": i,
        })

    return spans


# -----------------------------
# Background task
# -----------------------------
class FetchGDDDetailTask(QgsTask):
    def __init__(self, iddata: int):
        super().__init__("Cargando integral térmica", QgsTask.CanCancel)
        self.url_base = aGraeTools().backend_endpoint
        self.url = f"{self.url_base}/gis/integral_termica/gdd_detail/{iddata}"
        self.result_data: Optional[List[Dict[str, Any]]] = None
        self.error: Optional[str] = None

    def run(self) -> bool:
        try:
            r = requests.get(self.url, timeout=60)
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

    Cambios NUEVOS:
      - Dibuja rangos de MANEJO (is_manejo_hito) desde la mitad de la etapa anterior
        hasta la mitad de la etapa siguiente (por phase_key).
    """

    def __init__(
        self,
        parent=None,
        iddata: Optional[int] = None,
        phase_key: str = "etapa_actual",  # o "tramo"
        phase_alpha: float = 0.22,
        draw_hito_vlines: bool = True,    # líneas negras (sin puntos/labels)
        draw_manejo_spans: bool = True,   # NUEVO
        manejo_alpha: float = 0.18,       # NUEVO
    ):
        super().__init__(parent)
        self.setWindowTitle("aGrae | Integral térmica detalle")
        self.resize(1200, 680)

        self.iddata = iddata
        self.phase_key = phase_key
        self.phase_alpha = phase_alpha
        self.draw_hito_vlines = draw_hito_vlines

        self.draw_manejo_spans = draw_manejo_spans
        self.manejo_alpha = manejo_alpha

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
        task = FetchGDDDetailTask(self.iddata)

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

            self.lbl_title.setText(f"GDD detail (iddata={self.iddata})")

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

        # NUEVO: spans de manejo desde mitad etapa anterior hasta mitad etapa siguiente
        manejo_patches = []
        if self.draw_manejo_spans:
            manejo_patches = self._draw_manejo_spans_prevnext_midpoints()

        # Curva principal
        self.ax.plot(self.dates, self.gdd_acum, lw=2, label="GDD acumulada", zorder=10)

        # Líneas negras (opcional) en hitos, SIN puntos ni etiquetas
        if self.draw_hito_vlines:
            self._draw_hito_vlines_to_curve()


        # HOY (línea verde)
        self._draw_today_vline_to_curve()


        # Formato
        self.ax.set_ylabel("GDD acumulada")
        self.ax.set_xlabel("Fecha")
        self.ax.grid(True, alpha=0.25)
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m/%Y"))
        self.fig.autofmt_xdate()

        ymax = max(self.gdd_acum) if self.gdd_acum else 1.0
        if ymax <= 0:
            ymax = 1.0
        self.ax.set_ylim(0, ymax * 1.10)

        # Leyendas: serie arriba-izq, etapas+manejo a la derecha
        leg1 = self.ax.legend(loc="upper left", fontsize=9)
        handles_right = []
        if phase_patches:
            handles_right.extend(phase_patches)
        if manejo_patches:
            handles_right.append(mpatches.Patch(color="none", label=""))  # separador
            handles_right.extend(manejo_patches)

        if handles_right:
            self.ax.legend(
                handles=handles_right,
                title=f"{self.phase_key} / manejo",
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

            x_seg = self.dates[i0:i1 + 1]
            y_seg = self.gdd_acum[i0:i1 + 1]

            # extender al día siguiente para NO dejar huecos
            last_x = self.dates[i1]
            last_y = self.gdd_acum[i1]
            x_seg = x_seg + [last_x + timedelta(days=1)]
            y_seg = y_seg + [last_y]

            self.ax.fill_between(
                x_seg,
                0,
                y_seg,
                step="post",
                color=c,
                alpha=self.phase_alpha,
                linewidth=0.0,
                zorder=1
            )

        patches: List[mpatches.Patch] = []
        for v in unique_vals:
            label = v if v else "(vacío)"
            patches.append(mpatches.Patch(color=color_map[v], alpha=self.phase_alpha, label=label))
        return patches

    def _draw_manejo_spans_prevnext_midpoints(self) -> List[mpatches.Patch]:
        spans = _build_manejo_spans(self.rows, self.dates, self.phase_key)
        if not spans:
            return []

        import numpy as np
        cmap = cm.get_cmap("tab10")

        # color por código de manejo (C1, C2, F, ...)
        codes: List[str] = []
        for s in spans:
            code = str(s.get("code") or "M")
            if code not in codes:
                codes.append(code)
        code_color = {code: cmap(i % 10) for i, code in enumerate(codes)}

        # preparar arrays numéricos para interpolar sobre la curva
        x_num = mdates.date2num(self.dates)
        y_arr = np.array(self.gdd_acum, dtype=float)

        def y_at(dt):
            """Interpolación lineal de y sobre la curva para un datetime dt."""
            return float(np.interp(mdates.date2num(dt), x_num, y_arr))

        def fill_span_to_curve(start_dt, end_dt, color_rgba):
            # puntos internos (días existentes) dentro del rango
            idx = [i for i, d in enumerate(self.dates) if start_dt <= d <= end_dt]

            # construir segmentos x/y incluyendo bordes exactos start/end
            xs = [start_dt]
            ys = [y_at(start_dt)]

            for i in idx:
                xs.append(self.dates[i])
                ys.append(self.gdd_acum[i])

            xs.append(end_dt)
            ys.append(y_at(end_dt))

            # asegurar orden temporal
            xs, ys = zip(*sorted(zip(xs, ys), key=lambda t: t[0]))

            # límite superior del gráfico (dinámico)
            y_top = self.ax.get_ylim()[1]

            self.ax.fill_between(
                list(xs),
                list(ys),
                [y_top] * len(ys),
                step="post",
                color=color_rgba,
                alpha=self.manejo_alpha,
                linewidth=0.0,
                zorder=2
            )

        # dibujar spans recortados con la curva
        for s in spans:
            start = s["start"]
            end = s["end"]
            code = str(s.get("code") or "M")
            c = code_color.get(code, (0.2, 0.2, 0.2, 1.0))

            fill_span_to_curve(start, end, c)

        # leyenda
        patches: List[mpatches.Patch] = []
        for code in codes:
            name = None
            for s in spans:
                if str(s.get("code") or "M") == code and s.get("name"):
                    name = s.get("name")
                    break
            label = f"{code} - {name}" if name else code
            patches.append(mpatches.Patch(color=code_color[code], alpha=self.manejo_alpha, label=label))

        return patches

    def _draw_hito_vlines_to_curve(self):
        """Dibuja líneas negras cortas (0->curva) solo donde is_hito=True."""
        for i, r in enumerate(self.rows):
            if not r.get("is_hito"):
                continue
            dt = self.dates[i]
            y = self.gdd_acum[i]
            self.ax.vlines(dt, 0, y, colors="black", linewidth=1.1, alpha=0.70, zorder=9)
    
    def _draw_today_vline_to_curve(self):
        """
        Dibuja una línea vertical para HOY (fecha local), similar a un hito.
        - Si HOY está fuera del rango de fechas del gráfico, no dibuja nada.
        - Corta la línea en la curva usando interpolación lineal simple entre puntos.
        """
        if not self.dates or not self.gdd_acum:
            return

        today = datetime.now().date()

        # rango visible de datos (por fecha)
        d0 = self.dates[0].date()
        d1 = self.dates[-1].date()
        if today < d0 or today > d1:
            return

        # buscar segmento donde cae "today" para interpolar y
        # (asumimos self.dates ordenado)
        y_today = None
        for i in range(len(self.dates) - 1):
            a = self.dates[i].date()
            b = self.dates[i + 1].date()
            if a <= today <= b:
                ya = self.gdd_acum[i]
                yb = self.gdd_acum[i + 1]

                if a == b:
                    y_today = ya
                else:
                    # interpolación por fracción de días (date -> ordinal)
                    ta = datetime.combine(a, datetime.min.time()).toordinal()
                    tb = datetime.combine(b, datetime.min.time()).toordinal()
                    tt = datetime.combine(today, datetime.min.time()).toordinal()
                    t = (tt - ta) / (tb - ta)
                    y_today = ya + (yb - ya) * t
                break

        if y_today is None:
            # por si coincide exactamente con el último punto
            if today == self.dates[-1].date():
                y_today = self.gdd_acum[-1]
            else:
                return

        x_today = datetime.combine(today, datetime.min.time())

        # Línea tipo "hito", pero diferente: verde + punteada (puedes cambiarlo)
        self.ax.vlines(
            x_today, 0, y_today,
            colors="#16a34a",           # verde
            linewidth=1.8,
            linestyles="--",
            alpha=0.95,
            zorder=11
        )

        # Opcional: etiqueta pequeñita arriba
        self.ax.annotate(
            "HOY",
            xy=(x_today, y_today),
            xytext=(0, 6),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8,
            color="#16a34a",
            zorder=12
        )


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
    
        tramo = r.get("tramo", "")
        etapa = r.get("etapa_actual", "")
        umbral = r.get("umbral_etapa_actual", "")
        gdd_d = _safe_float(r.get("gdd_dia"), 0.0)
        gdd_a = _safe_float(r.get("gdd_acum"), 0.0)
        tmean = r.get("tmean_corr", "")

        # manejo
        is_m = "🧪" if r.get("is_manejo_hito") else ""
        mh = r.get("manejo_hito")
        mh_n = r.get("manejo_hito_nombre")
        mh_u = r.get("manejo_hito_umbral")
        gdd_m = r.get("gdd_acum_en_manejo")

        manejo_line = ""
        if r.get("is_manejo_hito"):
            manejo_line = f"\nManejo: {mh} ({mh_n}) umbral={mh_u} gdd={gdd_m}"

        return (
            f"{dt.strftime('%d/%m/%Y')}\n"
            f"Etapa: {etapa}  Umbral: {umbral}\n"
            f"Tmean corr: {tmean}\n"
            f"GDD día: {gdd_d:.2f}\n"
            f"GDD acum: {gdd_a:.2f}"
            f"{manejo_line}"
        )


# -----------------------------
# USO
# -----------------------------
# dlg = IntegralTermicaDialog(
#     parent=iface.mainWindow(),
#     base_url="http://TU_SERVIDOR:8000",
#     iddata=6430,
#     phase_key="etapa_actual",
#     draw_manejo_spans=True,
# )
# dlg.exec_()
