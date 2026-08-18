"""Experimental CNH TLO Shapefile export with explicit hypothesis labelling."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import struct
from typing import Any, Iterator
import zipfile

import geopandas as gpd
import pandas as pd
import pyogrio
import shapely

from exportar_rindes.readers.cnh.coordinate_hypothesis import (
    MISSING_SENTINELS,
    PAIR_OFFSET,
)
from exportar_rindes.readers.cnh.record_analysis import (
    MAGIC,
    RECORD_SIZES,
    decode_observed_timestamp,
)


EXPERIMENTAL_SCALE_DIVISOR = 10_000_000
EXPERIMENTAL_CRS = "EPSG:4326"
FIELD_EQUIVALENCE = {
    "mfr": "manufacturer",
    "src_file": "source archive member path",
    "src_rec": "zero-based source record index",
    "src_off": "zero-based source byte offset",
    "time_iso": "observed timestamp, timezone not assigned",
    "raw_a": "raw signed little-endian int32 A at byte 39",
    "raw_b": "raw signed little-endian int32 B at byte 43",
    "hyp_lat": "experimental raw_a / 10,000,000",
    "hyp_lon": "experimental raw_b / 10,000,000",
    "qc_flag": "experimental quality flag",
    "coord_hyp": "coordinate hypothesis identifier",
}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_m = 6_371_008.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    value = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * radius_m * math.asin(math.sqrt(value))


def iter_experimental_rows(
    source: Path, counters: Counter[str]
) -> Iterator[dict[str, Any]]:
    """Yield traceable rows under the explicitly unverified 1e-7 coordinate hypothesis."""
    size = RECORD_SIZES[".tlo"]
    with zipfile.ZipFile(source) as archive:
        infos = [
            info
            for info in archive.infolist()
            if not info.is_dir() and Path(info.filename).suffix.lower() == ".tlo"
        ]
        counters["tlo_member_count"] = len(infos)
        for info in infos:
            previous: tuple[datetime, float, float] | None = None
            with archive.open(info) as handle:
                for record_index in range(info.file_size // size):
                    counters["record_count"] += 1
                    record = handle.read(size)
                    if len(record) != size or record[:4] != MAGIC:
                        counters["skipped_invalid_record"] += 1
                        previous = None
                        continue
                    raw_a, raw_b = struct.unpack_from("<ii", record, PAIR_OFFSET)
                    if raw_a in MISSING_SENTINELS or raw_b in MISSING_SENTINELS:
                        counters["skipped_missing_pair"] += 1
                        previous = None
                        continue
                    try:
                        timestamp = decode_observed_timestamp(record)
                    except ValueError:
                        counters["skipped_invalid_timestamp"] += 1
                        previous = None
                        continue
                    latitude = raw_a / EXPERIMENTAL_SCALE_DIVISOR
                    longitude = raw_b / EXPERIMENTAL_SCALE_DIVISOR
                    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
                        counters["skipped_out_of_range"] += 1
                        previous = None
                        continue

                    qc_flag = "HYP_OK"
                    if previous is not None:
                        elapsed = (timestamp - previous[0]).total_seconds()
                        if 0 < elapsed <= 10:
                            speed_m_s = _haversine_m(
                                previous[1], previous[2], latitude, longitude
                            ) / elapsed
                            if speed_m_s > 15:
                                qc_flag = "HYP_FAST"
                                counters["flagged_fast"] += 1
                    previous = (timestamp, latitude, longitude)
                    counters["exported_count"] += 1
                    counters[f"qc_{qc_flag.lower()}"] += 1
                    yield {
                        "mfr": "CNH",
                        "src_file": info.filename,
                        "src_rec": record_index,
                        "src_off": record_index * size,
                        "time_iso": timestamp.isoformat(),
                        "raw_a": raw_a,
                        "raw_b": raw_b,
                        "hyp_lat": latitude,
                        "hyp_lon": longitude,
                        "qc_flag": qc_flag,
                        "coord_hyp": "TLO39_1E7",
                    }


def _write_batch(rows: list[dict[str, Any]], output: Path, *, append: bool) -> None:
    frame = pd.DataFrame.from_records(rows)
    geometry = shapely.points(frame["hyp_lon"].to_numpy(), frame["hyp_lat"].to_numpy())
    geodata = gpd.GeoDataFrame(frame, geometry=geometry, crs=EXPERIMENTAL_CRS)
    pyogrio.write_dataframe(
        geodata,
        output,
        driver="ESRI Shapefile",
        encoding="UTF-8",
        append=append,
    )


def write_experimental_cnh_shapefile(
    source: Path,
    output: Path,
    *,
    report_path: Path | None = None,
    batch_size: int = 50_000,
) -> dict[str, Any]:
    """Write an explicitly experimental point Shapefile and auditable QC report."""
    source = Path(source)
    output = Path(output)
    if not zipfile.is_zipfile(source):
        raise ValueError("La extracción CNH experimental requiere un ZIP válido.")
    if output.suffix.lower() != ".shp":
        raise ValueError("La salida debe terminar en .shp.")
    if batch_size < 1:
        raise ValueError("batch_size debe ser al menos 1.")
    existing = list(output.parent.glob(f"{output.stem}.*")) if output.parent.exists() else []
    if existing:
        raise FileExistsError(
            f"La salida ya existe ({existing[0]}). Elimina o mueve el conjunto conscientemente."
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    counters: Counter[str] = Counter()
    rows: list[dict[str, Any]] = []
    append = False
    bbox = [math.inf, math.inf, -math.inf, -math.inf]
    for row in iter_experimental_rows(source, counters):
        bbox[0] = min(bbox[0], row["hyp_lon"])
        bbox[1] = min(bbox[1], row["hyp_lat"])
        bbox[2] = max(bbox[2], row["hyp_lon"])
        bbox[3] = max(bbox[3], row["hyp_lat"])
        rows.append(row)
        if len(rows) >= batch_size:
            _write_batch(rows, output, append=append)
            rows.clear()
            append = True
    if rows:
        _write_batch(rows, output, append=append)
        append = True
    if not append:
        raise ValueError("No se encontraron registros exportables.")

    report = {
        "schema_version": 1,
        "status": "EXPERIMENTAL_COORDINATE_HYPOTHESIS_NOT_VALIDATED",
        "source": source.as_posix(),
        "source_size_bytes": source.stat().st_size,
        "source_sha256": _sha256_file(source),
        "output": output.as_posix(),
        "driver": "ESRI Shapefile",
        "geometry_type": "Point",
        "declared_crs": EXPERIMENTAL_CRS,
        "coordinate_hypothesis": {
            "record_family": ".tlo",
            "raw_pair_offset_zero_based": PAIR_OFFSET,
            "raw_type": "signed little-endian int32 pair",
            "axis_order": "raw_a=latitude, raw_b=longitude",
            "scale_divisor": EXPERIMENTAL_SCALE_DIVISOR,
            "validated": False,
        },
        "bbox_hypothesis": bbox,
        "counts": dict(sorted(counters.items())),
        "field_equivalence": FIELD_EQUIVALENCE,
        "warnings": [
            "La geometría es una hipótesis diagnóstica, no una descodificación CNH validada.",
            "No se ha verificado la posición contra una parcela o punto de control conocido.",
            "No se han exportado rendimiento, humedad, velocidad ni ancho.",
            "time_iso no tiene zona horaria asignada.",
        ],
    }
    report_path = report_path or output.with_suffix(".quality.json")
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report
