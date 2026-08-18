"""Web-oriented CNH Shapefile export with progress and configurable output CRS."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Any, Callable
import zipfile

import geopandas as gpd
import pandas as pd
import pyogrio
import shapely

from exportar_rindes.exporters.cnh_all_fields_shapefile import iter_all_field_rows
from exportar_rindes.exporters.cnh_named_hypothesis_shapefile import (
    NAMED_FIELD_CATALOG,
)
from exportar_rindes.exporters.cnh_yield12_shapefile import (
    YIELD12_FIELD_CATALOG,
    _yield12_row,
)
from exportar_rindes.exporters.experimental_shapefile import (
    EXPERIMENTAL_CRS,
    _sha256_file,
)
from exportar_rindes.readers.cnh.record_analysis import RECORD_SIZES


ProgressCallback = Callable[[int, int], None]


def count_candidate_records(source: Path) -> int:
    """Estimate work from fixed-size TLO members without reading their payload."""
    record_size = RECORD_SIZES[".tlo"]
    with zipfile.ZipFile(source) as archive:
        return sum(
            info.file_size // record_size
            for info in archive.infolist()
            if not info.is_dir() and Path(info.filename).suffix.lower() == ".tlo"
        )


def _write_batch(
    rows: list[dict[str, Any]], output: Path, *, append: bool, target_crs: str
) -> None:
    frame = pd.DataFrame.from_records(rows)
    geometry = shapely.points(frame["hyp_lon"].to_numpy(), frame["hyp_lat"].to_numpy())
    geodata = gpd.GeoDataFrame(frame, geometry=geometry, crs=EXPERIMENTAL_CRS)
    if target_crs != EXPERIMENTAL_CRS:
        geodata = geodata.to_crs(target_crs)
    pyogrio.write_dataframe(
        geodata,
        output,
        driver="ESRI Shapefile",
        encoding="UTF-8",
        append=append,
    )


def write_cnh_web_shapefile(
    source: Path,
    output: Path,
    *,
    target_crs: str = "EPSG:25830",
    batch_size: int = 50_000,
    progress_callback: ProgressCallback | None = None,
) -> dict[str, Any]:
    """Write the guided application's auditable CNH Shapefile result."""
    source, output = Path(source), Path(output)
    if not zipfile.is_zipfile(source):
        raise ValueError("El archivo seleccionado no es un ZIP válido.")
    if target_crs not in {"EPSG:25830", "EPSG:4326"}:
        raise ValueError("CRS de salida no permitido.")
    if output.suffix.lower() != ".shp":
        raise ValueError("La salida debe terminar en .shp.")
    if output.parent.exists() and list(output.parent.glob(f"{output.stem}.*")):
        raise FileExistsError("El conjunto de salida ya existe.")
    output.parent.mkdir(parents=True, exist_ok=True)

    total = count_candidate_records(source)
    counters: Counter[str] = Counter()
    result_counts: Counter[str] = Counter()
    rows: list[dict[str, Any]] = []
    append = False
    for source_row in iter_all_field_rows(source, counters):
        row = _yield12_row(source_row)
        result_counts["exported_count"] += 1
        result_counts["with_wet_yield"] += int(row["yldwet_th"] is not None)
        result_counts["with_yield_12"] += int(row["yld12_th"] is not None)
        result_counts[f"yield_12_{row['yld12_qc']}"] += 1
        rows.append(row)
        if len(rows) >= batch_size:
            _write_batch(rows, output, append=append, target_crs=target_crs)
            rows.clear()
            append = True
            if progress_callback:
                progress_callback(counters["record_count"], total)
    if rows:
        _write_batch(rows, output, append=append, target_crs=target_crs)
        append = True
    if not append:
        raise ValueError("No se encontraron registros CNH exportables.")
    if progress_callback:
        progress_callback(total, total)

    normalized = result_counts["with_yield_12"]
    plausible = result_counts["yield_12_plausible"]
    report = {
        "schema_version": 1,
        "status": "EXPERIMENTAL_CNH_HYPOTHESES",
        "source_name": source.name,
        "source_size_bytes": source.stat().st_size,
        "source_sha256": _sha256_file(source),
        "output_name": output.name,
        "driver": "ESRI Shapefile",
        "geometry": {
            "type": "Point",
            "internal_crs": EXPERIMENTAL_CRS,
            "output_crs": target_crs,
            "validated": False,
        },
        "source_counts": dict(sorted(counters.items())),
        "output_counts": dict(sorted(result_counts.items())),
        "summary": {
            "points": result_counts["exported_count"],
            "yield_12_count": normalized,
            "yield_12_plausible": plausible,
            "yield_12_plausible_pct": round(plausible * 100 / normalized, 2)
            if normalized
            else None,
        },
        "yield_normalization": {
            "wet_yield_field": "yldwet_th",
            "observed_moisture_field": "moist_hyp",
            "normalized_yield_field": "yld12_th",
            "target_moisture_pct": 12.0,
            "formula": "yldwet_th * (100 - moist_hyp) / 88",
            "plausible_reference_t_ha": [0.0, 11.0],
            "policy": "flag only; original and out-of-range values are retained",
        },
        "field_catalog": NAMED_FIELD_CATALOG | YIELD12_FIELD_CATALOG,
        "warnings": [
            "Las coordenadas y los campos agronómicos son hipótesis aún no validadas.",
            "La corrección al 12% presupone rendimiento húmedo másico.",
            "El canal podría ser volumétrico; no se aplica densidad sin evidencia.",
            "El rango 0-11 t/ha controla plausibilidad, pero no identifica el campo por sí solo.",
        ],
    }
    output.with_suffix(".quality.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report
