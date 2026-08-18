"""Batch GeoPackage export for decoded TOPCON ISOXML points."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd

from exportar_rindes.quality.topcon import topcon_rejection_reasons
from exportar_rindes.readers.topcon.isoxml import iter_topcon_records


def _frame(rows: list[dict[str, Any]], target_crs: str) -> gpd.GeoDataFrame:
    frame = pd.DataFrame(rows)
    geometry = gpd.points_from_xy(
        frame.pop("longitude"), frame.pop("latitude"), crs="EPSG:4326"
    )
    return gpd.GeoDataFrame(frame, geometry=geometry).to_crs(target_crs)


def write_topcon_gpkg(
    source: Path,
    output: Path,
    *,
    target_crs: str = "EPSG:25830",
    maximum_yield_t_ha: float = 30.0,
    batch_size: int = 50_000,
) -> dict[str, Any]:
    source, output = Path(source), Path(output)
    if output.exists():
        raise FileExistsError(f"La salida ya existe: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    counters: Counter[str] = Counter()
    raw_rows: list[dict[str, Any]] = []
    clean_rows: list[dict[str, Any]] = []
    raw_written = clean_written = False

    def flush(rows, layer, append):
        if not rows:
            return append
        _frame(rows, target_crs).to_file(
            output, layer=layer, driver="GPKG", mode="a" if append else "w"
        )
        rows.clear()
        return True

    for record in iter_topcon_records(source):
        reasons = topcon_rejection_reasons(
            record, maximum_yield_t_ha=maximum_yield_t_ha
        )
        row = {
            "src_member": record.metadata["archive_member"],
            "src_record": record.source_record,
            "src_offset": record.metadata["byte_offset"],
            "timestamp": record.timestamp,
            "client": record.metadata["client"],
            "farm": record.metadata["farm"],
            "field_name": record.field,
            "job_name": record.metadata["job"],
            "machine": record.machine,
            "crop": record.crop,
            "yield_wet_t_ha": record.yield_wet_t_ha,
            "yield_dry_t_ha": record.yield_dry_t_ha,
            "moisture_pct": record.moisture_pct,
            "width_m": record.width_m,
            "position_status": record.metadata["position_status"],
            "hdop": record.metadata["hdop"],
            "satellites": record.metadata["satellites"],
            "qc_keep": not reasons,
            "qc_reason": "|".join(reasons),
            "longitude": record.longitude,
            "latitude": record.latitude,
        }
        raw_rows.append(row)
        counters["track_points"] += 1
        if reasons:
            counters["rejected_yield_points"] += 1
            for reason in reasons:
                counters[f"reason_{reason}"] += 1
        else:
            clean_rows.append(row.copy())
            counters["yield_points"] += 1
        if len(raw_rows) >= batch_size:
            raw_written = flush(raw_rows, "track_points", raw_written)
        if len(clean_rows) >= batch_size:
            clean_written = flush(clean_rows, "yield_filtered", clean_written)
    raw_written = flush(raw_rows, "track_points", raw_written)
    clean_written = flush(clean_rows, "yield_filtered", clean_written)
    if not raw_written:
        raise ValueError("No se encontraron posiciones TOPCON ISOXML exportables.")
    report = {
        "schema_version": 1,
        "status": "TOPCON_ISOXML_FIRST_MILESTONE",
        "source": str(source),
        "output": str(output),
        "internal_crs": "EPSG:4326",
        "output_crs": target_crs,
        "filter": {
            "maximum_yield_t_ha": maximum_yield_t_ha,
            "rules": [
                "WGS84 finite and in range",
                "timestamp present",
                "wet yield present and between 0 and maximum",
                "moisture absent or between 0 and 100 percent",
            ],
        },
        "counts": dict(sorted(counters.items())),
        "traceability": ["src_member", "src_record", "src_offset"],
        "warnings": [
            "No se aplican correcciones espaciales ni temporales inventadas.",
            "Velocidad no se exporta porque no está declarada en los TLG observados.",
            "La validación completa exige otra exportación TOPCON independiente.",
        ],
    }
    output.with_suffix(".quality.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report
