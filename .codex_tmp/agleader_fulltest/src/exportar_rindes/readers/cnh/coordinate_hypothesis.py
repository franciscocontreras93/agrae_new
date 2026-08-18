"""Diagnostic evaluation of an unverified coordinate-like pair in CNH TLO records."""

from __future__ import annotations

from datetime import datetime
import math
from pathlib import Path
import struct
from typing import Any
import zipfile

from exportar_rindes.readers.cnh.record_analysis import (
    MAGIC,
    RECORD_SIZES,
    decode_observed_timestamp,
)


PAIR_OFFSET = 39
MISSING_SENTINELS = {-2_147_483_648, -2_147_483_647}
SCALE_CANDIDATES = (1_000_000, 10_000_000)


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_m = 6_371_008.8
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    delta_p = math.radians(lat2 - lat1)
    delta_l = math.radians(lon2 - lon1)
    value = (
        math.sin(delta_p / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(delta_l / 2) ** 2
    )
    return 2 * radius_m * math.asin(math.sqrt(value))


def _percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = round((len(ordered) - 1) * fraction)
    return ordered[index]


def _new_scale_stats(divisor: int) -> dict[str, Any]:
    return {
        "divisor": divisor,
        "axis_hypothesis": "raw_a=latitude, raw_b=longitude",
        "valid_range_count": 0,
        "latitude_min": None,
        "latitude_max": None,
        "longitude_min": None,
        "longitude_max": None,
        "speeds_m_s": [],
    }


def _update_bbox(stats: dict[str, Any], latitude: float, longitude: float) -> None:
    stats["valid_range_count"] += 1
    for key, value, operation in (
        ("latitude_min", latitude, min),
        ("latitude_max", latitude, max),
        ("longitude_min", longitude, min),
        ("longitude_max", longitude, max),
    ):
        stats[key] = value if stats[key] is None else operation(stats[key], value)


def scan_coordinate_hypotheses(source: Path, *, sample_stride: int = 20) -> dict[str, Any]:
    """Measure two scale hypotheses without accepting either as decoded coordinates."""
    if sample_stride < 1:
        raise ValueError("sample_stride debe ser al menos 1.")
    source = Path(source)
    if not zipfile.is_zipfile(source):
        raise ValueError("El análisis de coordenadas candidatas requiere un ZIP válido.")

    scale_stats = {divisor: _new_scale_stats(divisor) for divisor in SCALE_CANDIDATES}
    record_count = 0
    missing_pair_count = 0
    invalid_record_count = 0
    samples: list[dict[str, Any]] = []

    with zipfile.ZipFile(source) as archive:
        infos = [
            info
            for info in archive.infolist()
            if not info.is_dir() and Path(info.filename).suffix.lower() == ".tlo"
        ]
        for info in infos:
            previous: dict[int, tuple[datetime, float, float]] = {}
            size = RECORD_SIZES[".tlo"]
            with archive.open(info) as handle:
                for record_index in range(info.file_size // size):
                    record = handle.read(size)
                    record_count += 1
                    if len(record) != size or record[:4] != MAGIC:
                        invalid_record_count += 1
                        previous.clear()
                        continue
                    raw_a, raw_b = struct.unpack_from("<ii", record, PAIR_OFFSET)
                    if raw_a in MISSING_SENTINELS or raw_b in MISSING_SENTINELS:
                        missing_pair_count += 1
                        previous.clear()
                        continue
                    try:
                        timestamp = decode_observed_timestamp(record)
                    except ValueError:
                        invalid_record_count += 1
                        previous.clear()
                        continue

                    for divisor, stats in scale_stats.items():
                        latitude = raw_a / divisor
                        longitude = raw_b / divisor
                        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
                            previous.pop(divisor, None)
                            continue
                        _update_bbox(stats, latitude, longitude)
                        prior = previous.get(divisor)
                        if prior is not None:
                            elapsed = (timestamp - prior[0]).total_seconds()
                            if 0 < elapsed <= 10:
                                distance = _haversine_m(
                                    prior[1], prior[2], latitude, longitude
                                )
                                stats["speeds_m_s"].append(distance / elapsed)
                        previous[divisor] = (timestamp, latitude, longitude)

                    if record_index % sample_stride == 0:
                        samples.append(
                            {
                                "source_file": info.filename,
                                "source_record": record_index,
                                "source_byte_offset": record_index * size,
                                "timestamp": timestamp.isoformat(),
                                "raw_a": raw_a,
                                "raw_b": raw_b,
                                "hypothesis_latitude_1e7": raw_a / 10_000_000,
                                "hypothesis_longitude_1e7": raw_b / 10_000_000,
                            }
                        )

    summarized_scales = []
    for divisor in SCALE_CANDIDATES:
        stats = scale_stats[divisor]
        speeds = stats.pop("speeds_m_s")
        stats["continuity_step_count"] = len(speeds)
        stats["speed_m_s_p50"] = _percentile(speeds, 0.50)
        stats["speed_m_s_p95"] = _percentile(speeds, 0.95)
        stats["speed_m_s_p99"] = _percentile(speeds, 0.99)
        summarized_scales.append(stats)

    return {
        "schema_version": 1,
        "scope": "diagnostic hypothesis; coordinates are not validated or decoded",
        "source": source.as_posix(),
        "raw_pair": {
            "signed_little_endian_int32_offset_zero_based": PAIR_OFFSET,
            "axis_order": "unknown",
            "record_count": record_count,
            "missing_sentinels": sorted(MISSING_SENTINELS),
            "missing_pair_count": missing_pair_count,
            "invalid_record_count": invalid_record_count,
        },
        "scale_hypotheses": summarized_scales,
        "sample_stride_per_member": sample_stride,
        "samples": samples,
        "warnings": [
            "La continuidad y el rango no bastan para demostrar coordenadas.",
            "La muestra visual usa 1e-7 y orden A=lat/B=lon solo como hipótesis.",
            "No usar estos valores como geometría de producción sin referencia conocida.",
        ],
    }
