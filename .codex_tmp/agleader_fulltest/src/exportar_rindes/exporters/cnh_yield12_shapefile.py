"""Experimental CNH point export with candidate yield normalized to 12% moisture."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Any
import zipfile

from exportar_rindes.exporters.cnh_all_fields_shapefile import iter_all_field_rows
from exportar_rindes.exporters.cnh_named_hypothesis_shapefile import _named_row
from exportar_rindes.exporters.experimental_shapefile import _sha256_file, _write_batch
from exportar_rindes.normalization import (
    normalize_yield_moisture,
    yield_plausibility_flag,
)


YIELD12_FIELD_CATALOG = {
    "yldwet_th": {
        "source": "TLH h_u36 / 1000",
        "title": "Rendimiento bruto candidato a humedad observada",
        "unit_hypothesis": "t/ha",
        "confidence": "moderate",
    },
    "yld12_th": {
        "source": "yldwet_th * (100 - moist_hyp) / 88",
        "title": "Rendimiento candidato estandarizado al 12% de humedad",
        "unit_hypothesis": "t/ha at 12% moisture",
        "confidence": "derived from two candidate fields",
    },
    "yld12_qc": {
        "source": "range classification of yld12_th",
        "title": "Control de plausibilidad del rendimiento al 12%",
        "unit_hypothesis": "plausible when 0 <= t/ha <= 11",
        "confidence": "user-supplied agronomic reference",
    },
}


def _yield12_row(source_row: dict[str, Any]) -> dict[str, Any]:
    row = _named_row(source_row)
    yield_kg_ha = row["yield_hyp"]
    yield_wet_t_ha = yield_kg_ha / 1000 if yield_kg_ha is not None else None
    yield_12_t_ha = normalize_yield_moisture(yield_wet_t_ha, row["moist_hyp"])
    row["yldwet_th"] = yield_wet_t_ha
    row["yld12_th"] = yield_12_t_ha
    row["yld12_qc"] = yield_plausibility_flag(yield_12_t_ha)
    return row


def write_cnh_yield12_shapefile(
    source: Path, output: Path, *, batch_size: int = 50_000
) -> dict[str, Any]:
    """Write all named candidate fields plus wet and 12%-moisture yield."""
    source, output = Path(source), Path(output)
    if not zipfile.is_zipfile(source):
        raise ValueError("La extracción CNH requiere un ZIP válido.")
    if output.suffix.lower() != ".shp":
        raise ValueError("La salida debe terminar en .shp.")
    existing = list(output.parent.glob(f"{output.stem}.*")) if output.parent.exists() else []
    if existing:
        raise FileExistsError(f"La salida ya existe: {existing[0]}")
    output.parent.mkdir(parents=True, exist_ok=True)

    source_counters: Counter[str] = Counter()
    output_counters: Counter[str] = Counter()
    rows: list[dict[str, Any]] = []
    append = False
    for source_row in iter_all_field_rows(source, source_counters):
        row = _yield12_row(source_row)
        output_counters["exported_count"] += 1
        output_counters[f"yield_12_{row['yld12_qc']}"] += 1
        output_counters["with_wet_yield"] += int(row["yldwet_th"] is not None)
        output_counters["with_yield_12"] += int(row["yld12_th"] is not None)
        rows.append(row)
        if len(rows) >= batch_size:
            _write_batch(rows, output, append=append)
            rows.clear()
            append = True
    if rows:
        _write_batch(rows, output, append=append)
        append = True
    if not append:
        raise ValueError("No hay registros exportables.")

    report = {
        "schema_version": 1,
        "status": "EXPERIMENTAL_FIELD_AND_COORDINATE_HYPOTHESES",
        "source": source.as_posix(),
        "source_sha256": _sha256_file(source),
        "output": output.as_posix(),
        "geometry": {"type": "Point", "crs": "EPSG:4326", "validated": False},
        "source_counts": dict(sorted(source_counters.items())),
        "output_counts": dict(sorted(output_counters.items())),
        "yield_normalization": {
            "wet_yield_field": "yldwet_th",
            "observed_moisture_field": "moist_hyp",
            "normalized_yield_field": "yld12_th",
            "target_moisture_pct": 12.0,
            "formula": "yldwet_th * (100 - moist_hyp) / (100 - 12)",
            "plausible_reference_t_ha": [0.0, 11.0],
            "policy": "flag only; raw and out-of-range values are retained",
        },
        "added_field_catalog": YIELD12_FIELD_CATALOG,
        "warnings": [
            "Todos los campos agronómicos con sufijo _hyp son hipótesis.",
            "La corrección al 12% presupone rendimiento húmedo másico y humedad en porcentaje.",
            "El rango 0-11 t/ha es un control de plausibilidad, no prueba la identificación.",
            "El rendimiento podría representar volumen; falta una densidad verificada para convertirlo.",
            "La geometría también es experimental y aún no está validada externamente.",
        ],
    }
    output.with_suffix(".quality.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return report
