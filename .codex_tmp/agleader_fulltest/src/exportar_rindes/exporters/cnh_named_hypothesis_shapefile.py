"""Readable CNH Shapefile with explicitly hypothesis-labelled agronomic fields."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Any
import zipfile

from exportar_rindes.exporters.cnh_all_fields_shapefile import iter_all_field_rows
from exportar_rindes.exporters.experimental_shapefile import _sha256_file, _write_batch


MISSING_U16 = 65_535
NAMED_FIELD_CATALOG = {
    "yield_hyp": {
        "source": "TLH h_u36",
        "title": "Rendimiento candidato",
        "unit_hypothesis": "kg/ha",
        "confidence": "moderate",
    },
    "flow_hyp": {
        "source": "TLH h_u34 / 100",
        "title": "Caudal de cosecha candidato",
        "unit_hypothesis": "kg/s; alternatively a volumetric flow with unknown density",
        "confidence": "moderate",
    },
    "calc_yld": {
        "source": "flow_hyp * 10000 / (speed_hyp * width_hyp)",
        "title": "Rendimiento calculado de contraste",
        "unit_hypothesis": "kg/ha",
        "confidence": "diagnostic",
    },
    "moist_hyp": {
        "source": "TLH h_u38 / 10",
        "title": "Humedad candidata",
        "unit_hypothesis": "%",
        "confidence": "strong candidate",
    },
    "speed_hyp": {
        "source": "TLT t_u35 / 100",
        "title": "Velocidad candidata",
        "unit_hypothesis": "m/s",
        "confidence": "strong candidate",
    },
    "width_hyp": {
        "source": "TLT t_u39 / 100",
        "title": "Ancho de trabajo candidato",
        "unit_hypothesis": "m",
        "confidence": "strong candidate",
    },
    "elev_hyp": {
        "source": "TLO o_i47 / 1000",
        "title": "Elevación candidata",
        "unit_hypothesis": "m",
        "confidence": "strong candidate",
    },
    "head_hyp": {
        "source": "TLO o_u56 / 10",
        "title": "Rumbo candidato",
        "unit_hypothesis": "degrees",
        "confidence": "strong candidate",
    },
    "sats_hyp": {
        "source": "TLT t_u33",
        "title": "Número de satélites candidato",
        "unit_hypothesis": "count",
        "confidence": "strong candidate",
    },
    "sig_hyp": {
        "source": "TLO o_u55",
        "title": "Estado o tipo de señal candidato",
        "unit_hypothesis": "enumeration 0-4",
        "confidence": "candidate",
    },
}


def _valid_u16(value: int) -> float | None:
    return None if value in (-1, MISSING_U16) else float(value)


def _named_row(row: dict[str, Any]) -> dict[str, Any]:
    flow_raw = _valid_u16(row["h_u34"])
    yield_raw = _valid_u16(row["h_u36"])
    flow_hyp = flow_raw / 100 if flow_raw is not None else None
    speed_hyp = row["speed_ms"]
    width_hyp = row["width_m"]
    calc_yield = None
    if (
        flow_hyp is not None
        and speed_hyp is not None
        and width_hyp is not None
        and speed_hyp > 0
        and width_hyp > 0
    ):
        calc_yield = flow_hyp * 10_000 / (speed_hyp * width_hyp)
    return {
        "mfr": row["mfr"],
        "src_file": row["src_file"],
        "src_rec": row["src_rec"],
        "src_off": row["src_off"],
        "rec_id": row["rec_id"],
        "pos_time": row["pos_time"],
        "harv_time": row["harv_time"],
        "flow_dly": row["flow_dly"],
        "hyp_lat": row["hyp_lat"],
        "hyp_lon": row["hyp_lon"],
        "yield_raw": yield_raw,
        "flow_raw": flow_raw,
        "yield_hyp": yield_raw,
        "flow_hyp": flow_hyp,
        "calc_yld": calc_yield,
        "moist_hyp": row["moist_pc"],
        "speed_hyp": speed_hyp,
        "width_hyp": width_hyp,
        "elev_hyp": row["elev_m"],
        "head_hyp": row["head_deg"],
        "sats_hyp": _valid_u16(row["t_u33"]),
        "sig_hyp": row["o_u55"],
        "coord_hyp": "TLO39_1E7",
    }


def write_cnh_named_hypothesis_shapefile(
    source: Path, output: Path, *, batch_size: int = 50_000
) -> dict[str, Any]:
    """Write a readable candidate-field Shapefile while retaining raw yield channels."""
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
        row = _named_row(source_row)
        output_counters["exported_count"] += 1
        output_counters["with_yield_candidate"] += int(row["yield_hyp"] is not None)
        output_counters["with_flow_candidate"] += int(row["flow_hyp"] is not None)
        output_counters["with_moisture_candidate"] += int(row["moist_hyp"] is not None)
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
        "status": "EXPERIMENTAL_NAMED_FIELD_HYPOTHESES",
        "source": source.as_posix(),
        "source_sha256": _sha256_file(source),
        "output": output.as_posix(),
        "geometry": {"type": "Point", "crs": "EPSG:4326", "validated": False},
        "source_counts": dict(sorted(source_counters.items())),
        "output_counts": dict(sorted(output_counters.items())),
        "named_field_catalog": NAMED_FIELD_CATALOG,
        "physical_cross_check": {
            "formula": "flow_hyp * 10000 / (speed_hyp * width_hyp)",
            "filtered_records": 565_333,
            "correlation_calc_yield_vs_yield_hyp": 0.2639894456,
            "median_yield_hyp": 6_567,
            "median_calc_yield": 7_736.0911,
        },
        "warnings": [
            "Los sufijos _hyp significan hipótesis, no variables CN1 descodificadas.",
            "yield_hyp puede ser rendimiento másico o volumétrico; la unidad no está demostrada.",
            "flow_hyp puede ser caudal másico o volumétrico; falta densidad para convertirlos.",
            "No usar para decisiones agronómicas hasta contrastar con CN1 SDK o referencia conocida.",
        ],
    }
    output.with_suffix(".quality.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return report
