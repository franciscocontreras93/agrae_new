"""Evidence-based structural analysis of CNH fixed-size records.

This module deliberately does not assign units, coordinate systems, or agronomic
meaning to proprietary payload fields.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from pathlib import Path
import struct
from typing import Any
import zipfile


MAGIC = b"CNH1"
RECORD_SIZES = {".tlh": 50, ".tlo": 74, ".tlt": 47}
TIMESTAMP_SLICE = slice(27, 33)
TLO_RAW_PAIR_OFFSETS = (39, 58, 66)


def decode_observed_timestamp(record: bytes) -> datetime:
    """Decode the six-byte timestamp pattern corroborated by logs and ZIP dates."""
    if len(record) < TIMESTAMP_SLICE.stop:
        raise ValueError("Registro demasiado corto para la marca temporal observada.")
    if record[:4] != MAGIC:
        raise ValueError("El registro no comienza por la firma CNH1 observada.")
    year_offset, month, day, hour, minute, second = record[TIMESTAMP_SLICE]
    return datetime(1970 + year_offset, month, day, hour, minute, second)


def _new_pair_stats() -> dict[str, Any]:
    return {
        "record_count": 0,
        "nonzero_primary_count": 0,
        "copy_at_58_equal_count": 0,
        "copy_at_66_equal_count": 0,
        "raw_a_min": None,
        "raw_a_max": None,
        "raw_b_min": None,
        "raw_b_max": None,
        "examples": [],
    }


def _update_pair_stats(
    stats: dict[str, Any], record: bytes, path: str, record_index: int
) -> None:
    primary = struct.unpack_from("<ii", record, TLO_RAW_PAIR_OFFSETS[0])
    copy_58 = struct.unpack_from("<ii", record, TLO_RAW_PAIR_OFFSETS[1])
    copy_66 = struct.unpack_from("<ii", record, TLO_RAW_PAIR_OFFSETS[2])
    stats["record_count"] += 1
    stats["nonzero_primary_count"] += int(primary != (0, 0))
    stats["copy_at_58_equal_count"] += int(primary == copy_58)
    stats["copy_at_66_equal_count"] += int(primary == copy_66)
    stats["raw_a_min"] = primary[0] if stats["raw_a_min"] is None else min(
        stats["raw_a_min"], primary[0]
    )
    stats["raw_a_max"] = primary[0] if stats["raw_a_max"] is None else max(
        stats["raw_a_max"], primary[0]
    )
    stats["raw_b_min"] = primary[1] if stats["raw_b_min"] is None else min(
        stats["raw_b_min"], primary[1]
    )
    stats["raw_b_max"] = primary[1] if stats["raw_b_max"] is None else max(
        stats["raw_b_max"], primary[1]
    )
    if len(stats["examples"]) < 10:
        stats["examples"].append(
            {
                "path": path,
                "record_index": record_index,
                "byte_offset": record_index * RECORD_SIZES[".tlo"],
                "raw_a": primary[0],
                "raw_b": primary[1],
            }
        )


def _member_summary(
    archive: zipfile.ZipFile,
    info: zipfile.ZipInfo,
    pair_stats: dict[str, Any],
) -> dict[str, Any]:
    suffix = Path(info.filename).suffix.lower()
    record_size = RECORD_SIZES[suffix]
    record_count, trailing_bytes = divmod(info.file_size, record_size)
    invalid_magic_count = 0
    invalid_timestamp_count = 0
    first_timestamp: str | None = None
    last_timestamp: str | None = None

    with archive.open(info) as handle:
        for record_index in range(record_count):
            record = handle.read(record_size)
            if len(record) != record_size:
                trailing_bytes += len(record)
                break
            if record[:4] != MAGIC:
                invalid_magic_count += 1
            try:
                timestamp = decode_observed_timestamp(record)
            except ValueError:
                invalid_timestamp_count += 1
            else:
                value = timestamp.isoformat()
                first_timestamp = value if first_timestamp is None else min(first_timestamp, value)
                last_timestamp = value if last_timestamp is None else max(last_timestamp, value)
            if suffix == ".tlo":
                _update_pair_stats(pair_stats, record, info.filename, record_index)
        remainder = handle.read()
        trailing_bytes += len(remainder)

    return {
        "path": info.filename,
        "extension": suffix,
        "record_size_bytes": record_size,
        "record_count": record_count,
        "trailing_bytes": trailing_bytes,
        "invalid_magic_count": invalid_magic_count,
        "invalid_timestamp_count": invalid_timestamp_count,
        "first_timestamp": first_timestamp,
        "last_timestamp": last_timestamp,
    }


def analyze_fixed_records(source: Path) -> dict[str, Any]:
    """Analyze the observed TLH/TLO/TLT fixed-record families in a CNH ZIP."""
    source = Path(source)
    if not zipfile.is_zipfile(source):
        raise ValueError("El análisis de registros CNH requiere un ZIP válido.")

    pair_stats = _new_pair_stats()
    members: list[dict[str, Any]] = []
    triplets: defaultdict[str, dict[str, int]] = defaultdict(dict)

    with zipfile.ZipFile(source) as archive:
        infos = [
            info
            for info in archive.infolist()
            if not info.is_dir() and Path(info.filename).suffix.lower() in RECORD_SIZES
        ]
        for info in infos:
            summary = _member_summary(archive, info, pair_stats)
            members.append(summary)
            triplets[info.filename[:-4]][summary["extension"]] = summary["record_count"]

    complete_triplets = [counts for counts in triplets.values() if len(counts) == 3]
    equal_count_triplets = [counts for counts in complete_triplets if len(set(counts.values())) == 1]
    count_differences = [
        {"base_path": base, "record_counts": counts}
        for base, counts in sorted(triplets.items())
        if len(counts) != 3 or len(set(counts.values())) != 1
    ]

    return {
        "schema_version": 1,
        "scope": "structural analysis; payload scale, units, CRS and meaning are unknown",
        "source": source.as_posix(),
        "record_families": {
            "observed_sizes_bytes": RECORD_SIZES,
            "member_count": len(members),
            "complete_triplet_count": len(complete_triplets),
            "equal_record_count_triplet_count": len(equal_count_triplets),
            "record_count_differences": count_differences,
            "totals_by_extension": {
                suffix: sum(
                    member["record_count"]
                    for member in members
                    if member["extension"] == suffix
                )
                for suffix in RECORD_SIZES
            },
            "invalid_magic_count": sum(item["invalid_magic_count"] for item in members),
            "invalid_timestamp_count": sum(
                item["invalid_timestamp_count"] for item in members
            ),
            "trailing_bytes": sum(item["trailing_bytes"] for item in members),
        },
        "timestamp_observation": {
            "byte_offsets_zero_based": [27, 28, 29, 30, 31, 32],
            "interpretation": [
                "year_since_1970",
                "month",
                "day",
                "hour",
                "minute",
                "second",
            ],
            "evidence": (
                "Values form valid datetimes, advance with records, agree with ZIP dates, "
                "and exact seconds occur in text logs."
            ),
        },
        "tlo_repeated_raw_pair": {
            "interpretation": "unknown; no scale, units, axis order or CRS assigned",
            "signed_little_endian_int32_pair_offsets_zero_based": list(TLO_RAW_PAIR_OFFSETS),
            **pair_stats,
        },
        "members": members,
        "warnings": [
            "La pareja TLO repetida es solo un candidato estructural, no una coordenada.",
            "No se genera geometría hasta validar escala, ejes, unidades, CRS y ubicación.",
        ],
    }
