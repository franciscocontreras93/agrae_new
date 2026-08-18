"""Experimental, traceable GeoPackage export for Ag Leader AGDATA."""

from collections import Counter
import json
from pathlib import Path

import geopandas as gpd
import pandas as pd

from exportar_rindes.readers.agleader.collection import open_collection, safe_members
from exportar_rindes.readers.agleader.ilf2 import iter_ilf2_points

MAX_EXPORTED_SENSOR_CHANNELS = 16


def _frame(rows, target_crs):
    frame = pd.DataFrame(rows)
    geometry = gpd.points_from_xy(
        frame.pop("longitude"), frame.pop("latitude"), crs="EPSG:4326"
    )
    return gpd.GeoDataFrame(frame, geometry=geometry).to_crs(target_crs)


def write_agleader_gpkg(
    source: Path,
    output: Path,
    *,
    target_crs: str = "EPSG:25830",
    batch_size: int = 50_000,
):
    source, output = Path(source), Path(output)
    if output.exists():
        raise FileExistsError(f"La salida ya existe: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    counters = Counter()
    skipped = []
    written = False

    def flush():
        nonlocal written
        if not rows:
            return
        _frame(rows, target_crs).to_file(
            output,
            layer="agleader_raw_points",
            driver="GPKG",
            mode="a" if written else "w",
        )
        rows.clear()
        written = True

    with open_collection(source) as archive:
        for member in safe_members(archive):
            if not member.name.lower().endswith(".ilf2"):
                continue
            counters["ilf2_members"] += 1
            handle = archive.extractfile(member)
            if handle is None:
                skipped.append(member.name)
                continue
            try:
                for point in iter_ilf2_points(handle.read()):
                    sensor_columns = {
                        f"sensor_{index:02d}": point.get(f"sensor_{index:02d}")
                        for index in range(1, MAX_EXPORTED_SENSOR_CHANNELS + 1)
                    }
                    row = {
                        "src_member": member.name,
                        "src_record": point.pop("source_record"),
                        "src_offset": point.pop("byte_offset"),
                        **{
                            key: value for key, value in point.items()
                            if not key.startswith("sensor_")
                        },
                        **sensor_columns,
                    }
                    rows.append(row)
                    counters["raw_points"] += 1
                    if len(rows) >= batch_size:
                        flush()
            except ValueError:
                skipped.append(member.name)
    flush()
    if not written:
        raise ValueError("No se encontraron posiciones AGDATA/ILF2 exportables.")

    report = {
        "schema_version": 1,
        "status": "AGLEADER_EXPERIMENTAL_COORDINATES_ONLY",
        "source": str(source),
        "output": str(output),
        "internal_crs": "EPSG:4326",
        "output_crs": target_crs,
        "counts": dict(sorted(counters.items())),
        "skipped_ilf2_members": skipped,
        "confirmed": [
            "AGDATA header and embedded TAR collection",
            "ILF2 raw DEFLATE stream",
            "length-framed records",
            "UTC timestamp in Unix milliseconds",
            "longitude, latitude and altitude as little-endian float64",
        ],
        "unconfirmed": [
            "sensor_01..sensor_N semantic meaning and units",
            "yield wet/dry, moisture, speed and working width",
            "crop, grower, farm and field relationships",
        ],
        "traceability": ["src_member", "src_record", "src_offset", "record_type"],
        "warnings": [
            "No usar sensor_XX como datos agronÃ³micos hasta validarlos con SMS.",
            "Este resultado reproduce recorridos, no constituye aÃºn un mapa de rendimiento.",
            "El criterio de terminado exige una segunda exportaciÃ³n independiente.",
        ],
    }
    output.with_suffix(".quality.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report
