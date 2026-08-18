"""GeoPackage export for verified CLAAS CM coordinates and CM blocks."""

from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString

from exportar_rindes.quality.claas import claas_rejection_reasons
from exportar_rindes.readers.claas import ClaasReader
from exportar_rindes.readers.claas.analysis import HeadingEvidence


def _point_frame(rows, target_crs):
    frame = pd.DataFrame(rows)
    geometry = gpd.points_from_xy(
        frame.pop("longitude"), frame.pop("latitude"), crs="EPSG:4326"
    )
    return gpd.GeoDataFrame(frame, geometry=geometry).to_crs(target_crs)


def _line_frame(rows, target_crs):
    return gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326").to_crs(
        target_crs
    )


def write_claas_gpkg(
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
    point_rows = []
    block_rows = []
    point_written = False
    block_written = False
    counters = Counter()
    heading_evidence = HeadingEvidence()
    task_stats = defaultdict(
        lambda: {
            "point_count": 0,
            "block_count": 0,
            "minimum_longitude": None,
            "minimum_latitude": None,
            "maximum_longitude": None,
            "maximum_latitude": None,
        }
    )

    def flush_points():
        nonlocal point_written
        if not point_rows:
            return
        _point_frame(point_rows, target_crs).to_file(
            output,
            layer="track_points",
            driver="GPKG",
            mode="a" if point_written else "w",
        )
        point_rows.clear()
        point_written = True

    def flush_blocks():
        nonlocal block_written
        if not block_rows:
            return
        _line_frame(block_rows, target_crs).to_file(
            output,
            layer="cm_blocks",
            driver="GPKG",
            mode="a" if block_written else "a",
        )
        block_rows.clear()
        block_written = True

    current_key = None
    current_coordinates = []
    current_metadata = None
    previous_record = None

    def finish_block():
        nonlocal current_coordinates
        if len(current_coordinates) < 2 or current_metadata is None:
            current_coordinates = []
            return
        block_rows.append(
            {
                **current_metadata,
                "point_count": len(current_coordinates),
                "geometry": LineString(current_coordinates),
            }
        )
        counters["cm_blocks"] += 1
        task_stats[current_metadata["task_id"]]["block_count"] += 1
        current_coordinates = []
        if len(block_rows) >= max(1_000, batch_size // 5):
            flush_blocks()

    for record in ClaasReader().iter_records(source):
        reasons = claas_rejection_reasons(record)
        member = record.metadata["source_member"]
        block_number = record.metadata["cm_block_number"]
        task_id = record.metadata["task_identifier"] or "UNLINKED"
        block_key = (member, block_number)
        if block_key != current_key:
            finish_block()
            current_key = block_key
            previous_record = None
            current_metadata = {
                "src_member": member,
                "task_id": task_id,
                "task_name": record.metadata["task_designator"],
                "field_name": record.field,
                "block_id": block_number,
            }
        if previous_record is not None:
            heading_evidence.add(
                previous_record.latitude,
                previous_record.longitude,
                record.latitude,
                record.longitude,
                record.metadata["cm_value_float_4"],
            )
        previous_record = record
        current_coordinates.append((record.longitude, record.latitude))

        stats = task_stats[task_id]
        stats["point_count"] += 1
        for key, value, function in (
            ("minimum_longitude", record.longitude, min),
            ("minimum_latitude", record.latitude, min),
            ("maximum_longitude", record.longitude, max),
            ("maximum_latitude", record.latitude, max),
        ):
            stats[key] = value if stats[key] is None else function(stats[key], value)

        counters["track_points"] += 1
        if reasons:
            counters["rejected_points"] += 1
        point_rows.append(
            {
                "src_member": member,
                "src_record": record.source_record,
                "src_offset": record.metadata["byte_offset"],
                "task_id": task_id,
                "task_name": record.metadata["task_designator"],
                "field_name": record.field,
                "machine": record.machine,
                "cm_device": record.metadata["cm_device_identifier"],
                "cm_value_3": record.metadata["cm_value_double_3"],
                "cm_value_4": record.metadata["cm_value_float_4"],
                "heading_c": record.metadata["cm_value_float_4"],
                "qc_keep": not reasons,
                "qc_reason": "|".join(reasons),
                "longitude": record.longitude,
                "latitude": record.latitude,
            }
        )
        if len(point_rows) >= batch_size:
            flush_points()
    finish_block()
    flush_points()
    flush_blocks()
    if not point_written:
        raise ValueError("No se encontraron posiciones CLAAS CM exportables.")

    summaries = {}
    for task_id, values in sorted(task_stats.items()):
        summaries[task_id] = {
            "point_count": values["point_count"],
            "block_count": values["block_count"],
            "bounds_wgs84": [
                values["minimum_longitude"],
                values["minimum_latitude"],
                values["maximum_longitude"],
                values["maximum_latitude"],
            ],
        }
    report = {
        "schema_version": 2,
        "status": "CLAAS_CM_COORDINATES_AND_BLOCKS",
        "source": str(source),
        "output": str(output),
        "internal_crs": "EPSG:4326",
        "output_crs": target_crs,
        "counts": dict(sorted(counters.items())),
        "traceability": ["src_member", "src_record", "src_offset"],
        "heading_candidate": heading_evidence.report(),
        "tasks": summaries,
        "warnings": [
            "No se exporta rendimiento, humedad, velocidad, ancho ni tiempo por punto.",
            "cm_value_3 se conserva sin unidad ni semántica asignadas.",
            "heading_c es una hipótesis geométrica, no una declaración del fabricante.",
            "Solo una carpeta contiene CM con recorridos; falta otra muestra independiente.",
        ],
    }
    output.with_suffix(".quality.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report
