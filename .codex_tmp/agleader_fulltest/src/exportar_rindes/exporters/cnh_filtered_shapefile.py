"""Auditable CNH cleaning export inspired by USDA-ARS Yield Editor filters."""

from __future__ import annotations

from collections import Counter
import csv
import json
import math
from pathlib import Path
from typing import Any, Callable
import zipfile

from exportar_rindes.exporters.cnh_all_fields_shapefile import iter_all_field_rows
from exportar_rindes.exporters.cnh_named_hypothesis_shapefile import NAMED_FIELD_CATALOG
from exportar_rindes.exporters.cnh_web_shapefile import (
    _write_batch,
    count_candidate_records,
)
from exportar_rindes.exporters.cnh_yield12_shapefile import (
    YIELD12_FIELD_CATALOG,
    _yield12_row,
)
from exportar_rindes.exporters.experimental_shapefile import EXPERIMENTAL_CRS, _sha256_file
from exportar_rindes.quality import FilterSettings, FilterState, apply_filters


ProgressCallback = Callable[[int, int, str], None]


class RunningStats:
    def __init__(self) -> None:
        self.count = 0
        self.mean = 0.0
        self.m2 = 0.0
        self.minimum = math.inf
        self.maximum = -math.inf

    def add(self, value: float | None) -> None:
        if value is None or not math.isfinite(value):
            return
        self.count += 1
        delta = value - self.mean
        self.mean += delta / self.count
        self.m2 += delta * (value - self.mean)
        self.minimum = min(self.minimum, value)
        self.maximum = max(self.maximum, value)

    @property
    def stddev(self) -> float | None:
        return math.sqrt(self.m2 / (self.count - 1)) if self.count > 1 else None

    def report(self) -> dict[str, float | int | None]:
        return {
            "count": self.count,
            "mean_t_ha": round(self.mean, 6) if self.count else None,
            "stddev_t_ha": round(self.stddev, 6) if self.stddev is not None else None,
            "minimum_t_ha": round(self.minimum, 6) if self.count else None,
            "maximum_t_ha": round(self.maximum, 6) if self.count else None,
        }


def _precompute_yield_stats(
    source: Path, total: int, callback: ProgressCallback | None
) -> RunningStats:
    counters: Counter[str] = Counter()
    stats = RunningStats()
    for source_row in iter_all_field_rows(source, counters):
        stats.add(_yield12_row(source_row)["yld12_th"])
        if callback and counters["record_count"] % 50_000 == 0:
            callback(counters["record_count"], total, "Calculando distribución de rendimiento")
    return stats


def write_cnh_filtered_shapefile(
    source: Path,
    output: Path,
    *,
    settings: FilterSettings,
    target_crs: str = "EPSG:25830",
    output_mode: str = "clean",
    batch_size: int = 50_000,
    progress_callback: ProgressCallback | None = None,
) -> dict[str, Any]:
    """Apply filters, write clean/all points, and retain rejected-point traceability."""
    source, output = Path(source), Path(output)
    settings.validate()
    if not zipfile.is_zipfile(source):
        raise ValueError("El archivo seleccionado no es un ZIP válido.")
    if target_crs not in {"EPSG:25830", "EPSG:4326"}:
        raise ValueError("CRS de salida no permitido.")
    if output_mode not in {"clean", "all"}:
        raise ValueError("Modo de salida no permitido.")
    if output.parent.exists() and list(output.parent.glob(f"{output.stem}.*")):
        raise FileExistsError("El conjunto de salida ya existe.")
    output.parent.mkdir(parents=True, exist_ok=True)

    total = count_candidate_records(source)
    global_stats = (
        _precompute_yield_stats(source, total, progress_callback)
        if settings.standard_deviation
        else None
    )
    source_counts: Counter[str] = Counter()
    filter_counts: Counter[str] = Counter()
    before_stats, after_stats = RunningStats(), RunningStats()
    state = FilterState()
    rows: list[dict[str, Any]] = []
    append = False
    rejected_path = output.with_suffix(".rejected.csv")
    with rejected_path.open("w", newline="", encoding="utf-8") as rejected_file:
        rejected = csv.DictWriter(
            rejected_file,
            fieldnames=["src_file", "src_rec", "src_off", "rec_id", "yld12_th", "reasons"],
        )
        rejected.writeheader()
        for source_row in iter_all_field_rows(source, source_counts):
            row = _yield12_row(source_row)
            before_stats.add(row["yld12_th"])
            reasons = apply_filters(
                row,
                settings,
                state,
                yield_mean=global_stats.mean if global_stats and global_stats.count else None,
                yield_stddev=global_stats.stddev if global_stats else None,
            )
            keep = not reasons
            row["qc_keep"] = keep
            row["qc_reason"] = "|".join(reasons)
            filter_counts["input_points"] += 1
            if keep:
                filter_counts["kept_points"] += 1
                after_stats.add(row["yld12_th"])
            else:
                filter_counts["rejected_points"] += 1
                for reason in reasons:
                    filter_counts[f"reason_{reason}"] += 1
                rejected.writerow(
                    {
                        "src_file": row["src_file"],
                        "src_rec": row["src_rec"],
                        "src_off": row["src_off"],
                        "rec_id": row["rec_id"],
                        "yld12_th": row["yld12_th"],
                        "reasons": row["qc_reason"],
                    }
                )
            if keep or output_mode == "all":
                rows.append(row)
            if len(rows) >= batch_size:
                _write_batch(rows, output, append=append, target_crs=target_crs)
                rows.clear()
                append = True
            if progress_callback and source_counts["record_count"] % 50_000 == 0:
                progress_callback(source_counts["record_count"], total, "Aplicando filtros")
    if rows:
        _write_batch(rows, output, append=append, target_crs=target_crs)
        append = True
    if not append:
        raise ValueError("Los filtros no dejaron puntos exportables.")
    if progress_callback:
        progress_callback(total, total, "Filtros completados")

    input_count = filter_counts["input_points"]
    kept_count = filter_counts["kept_points"]
    report = {
        "schema_version": 1,
        "status": "EXPERIMENTAL_CNH_FILTERED",
        "method_basis": "USDA-ARS Yield Editor concepts; independent implementation",
        "source_name": source.name,
        "source_sha256": _sha256_file(source),
        "output_name": output.name,
        "output_mode": output_mode,
        "geometry": {
            "type": "Point",
            "internal_crs": EXPERIMENTAL_CRS,
            "output_crs": target_crs,
            "validated": False,
        },
        "filter_settings": settings.as_dict(),
        "filter_counts": dict(sorted(filter_counts.items())),
        "source_counts": dict(sorted(source_counts.items())),
        "summary": {
            "input_points": input_count,
            "kept_points": kept_count,
            "rejected_points": filter_counts["rejected_points"],
            "kept_pct": round(kept_count * 100 / input_count, 2) if input_count else None,
        },
        "yield_statistics": {"before": before_stats.report(), "after": after_stats.report()},
        "field_catalog": NAMED_FIELD_CATALOG
        | YIELD12_FIELD_CATALOG
        | {
            "qc_keep": {"title": "Punto aceptado por todos los filtros", "unit": "boolean"},
            "qc_reason": {"title": "Códigos de filtros activados", "unit": "codes"},
        },
        "unavailable_filters": {
            "DELAY": "No se desplaza geometría hasta confirmar alineación temporal CNH.",
            "START_END": "Requiere identificar pasadas o estado fiable de cabezal.",
            "POS": "Requiere límite de parcela y coordenadas externamente validados.",
            "MAN": "La selección espacial manual se incorporará con la vista cartográfica.",
        },
        "warnings": [
            "Los filtros marcan observaciones; no corrigen valores inventando datos.",
            "Las variables CNH y la geometría continúan siendo hipótesis explícitas.",
            "Un punto puede activar varios filtros; los conteos por motivo se solapan.",
            "El CSV de rechazados conserva trazabilidad para revisión y restitución.",
        ],
    }
    output.with_suffix(".quality.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report
