"""Experimental Shapefile export preserving every observed CNH TL payload byte."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import struct
from typing import Any, Iterator
import zipfile

from exportar_rindes.exporters.experimental_shapefile import (
    EXPERIMENTAL_SCALE_DIVISOR,
    _sha256_file,
    _write_batch,
)
from exportar_rindes.readers.cnh.coordinate_hypothesis import MISSING_SENTINELS
from exportar_rindes.readers.cnh.record_analysis import (
    MAGIC,
    RECORD_SIZES,
    decode_observed_timestamp,
)


MISSING_U16 = 65_535
FIELD_CATALOG = {
    "mfr": {"source": "constant", "status": "verified", "meaning": "manufacturer"},
    "src_file": {"source": "ZIP", "status": "verified", "meaning": "TLO member path"},
    "src_rec": {"source": "TLO", "status": "verified", "meaning": "zero-based record"},
    "src_off": {"source": "TLO", "status": "verified", "meaning": "byte offset"},
    "rec_id": {"source": "all@11:u32le", "status": "verified", "meaning": "join id"},
    "pos_time": {"source": "TLO@27:6B", "status": "verified", "meaning": "position time"},
    "harv_time": {"source": "TLH@27:6B", "status": "verified", "meaning": "delayed harvest time"},
    "flow_dly": {"source": "TLH-TLO", "status": "verified", "meaning": "delay seconds"},
    "hyp_lat": {"source": "TLO@39:i32le/1e7", "status": "experimental", "meaning": "latitude"},
    "hyp_lon": {"source": "TLO@43:i32le/1e7", "status": "experimental", "meaning": "longitude"},
    "elev_m": {"source": "TLO@47:i32le/1000", "status": "candidate", "meaning": "elevation m"},
    "head_deg": {"source": "TLO@56:u16le/10", "status": "candidate", "meaning": "heading degrees"},
    "speed_ms": {"source": "TLT@35:u16le/100", "status": "candidate", "meaning": "speed m/s"},
    "width_m": {"source": "TLT@39:u16le/100", "status": "candidate", "meaning": "width m"},
    "moist_pc": {"source": "TLH@38:u16le/10", "status": "candidate", "meaning": "moisture percent"},
    "h_u34": {"source": "TLH@34:u16le", "status": "unknown", "meaning": "harvest channel A"},
    "h_u36": {"source": "TLH@36:u16le", "status": "unknown", "meaning": "harvest channel B"},
    "h_u38": {"source": "TLH@38:u16le", "status": "candidate", "meaning": "moisture raw"},
    "t_u35": {"source": "TLT@35:u16le", "status": "candidate", "meaning": "speed raw"},
    "t_u39": {"source": "TLT@39:u16le", "status": "candidate", "meaning": "width raw"},
    "o_hex": {"source": "TLO@33:41B", "status": "raw", "meaning": "complete payload hex"},
    "t_hex": {"source": "TLT@33:14B", "status": "raw", "meaning": "complete payload hex"},
    "h_hex": {"source": "TLH@33:17B", "status": "raw", "meaning": "complete payload hex"},
}


def _u16(record: bytes | None, offset: int) -> int:
    return -1 if record is None else struct.unpack_from("<H", record, offset)[0]


def _candidate_scaled(raw: int, divisor: float) -> float | None:
    return None if raw in (-1, MISSING_U16) else raw / divisor


def _record_map(data: bytes, size: int) -> dict[int, bytes]:
    return {
        struct.unpack_from("<I", data, offset + 11)[0]: data[offset : offset + size]
        for offset in range(0, len(data), size)
    }


def iter_all_field_rows(source: Path, counters: Counter[str]) -> Iterator[dict[str, Any]]:
    """Join TLO/TLT/TLH by the verified id and preserve aligned fields plus raw payloads."""
    groups: defaultdict[str, dict[str, zipfile.ZipInfo]] = defaultdict(dict)
    with zipfile.ZipFile(source) as archive:
        for info in archive.infolist():
            suffix = Path(info.filename).suffix.lower()
            if not info.is_dir() and suffix in RECORD_SIZES:
                groups[info.filename[:-4]][suffix] = info
        counters["triplet_count"] = len(groups)

        for base in sorted(groups):
            infos = groups[base]
            tlo_info = infos[".tlo"]
            tlt_map = _record_map(archive.read(infos[".tlt"]), RECORD_SIZES[".tlt"])
            tlh_map = _record_map(archive.read(infos[".tlh"]), RECORD_SIZES[".tlh"])
            size = RECORD_SIZES[".tlo"]
            with archive.open(tlo_info) as handle:
                for record_index in range(tlo_info.file_size // size):
                    counters["record_count"] += 1
                    tlo = handle.read(size)
                    if len(tlo) != size or tlo[:4] != MAGIC:
                        counters["skipped_invalid_tlo"] += 1
                        continue
                    rec_id = struct.unpack_from("<I", tlo, 11)[0]
                    tlt = tlt_map.get(rec_id)
                    tlh = tlh_map.get(rec_id)
                    counters["missing_tlt"] += int(tlt is None)
                    counters["missing_tlh"] += int(tlh is None)
                    raw_a, raw_b = struct.unpack_from("<ii", tlo, 39)
                    if raw_a in MISSING_SENTINELS or raw_b in MISSING_SENTINELS:
                        counters["skipped_missing_xy"] += 1
                        continue
                    latitude = raw_a / EXPERIMENTAL_SCALE_DIVISOR
                    longitude = raw_b / EXPERIMENTAL_SCALE_DIVISOR
                    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
                        counters["skipped_range_xy"] += 1
                        continue
                    pos_time = decode_observed_timestamp(tlo)
                    harvest_time = decode_observed_timestamp(tlh) if tlh is not None else None
                    h_u38 = _u16(tlh, 38)
                    t_u35 = _u16(tlt, 35)
                    t_u39 = _u16(tlt, 39)
                    o_i47 = struct.unpack_from("<i", tlo, 47)[0]
                    o_u56 = struct.unpack_from("<H", tlo, 56)[0]
                    o_a2, o_b2 = struct.unpack_from("<ii", tlo, 58)
                    o_a3, o_b3 = struct.unpack_from("<ii", tlo, 66)
                    counters["exported_count"] += 1
                    yield {
                        "mfr": "CNH",
                        "src_file": tlo_info.filename,
                        "src_rec": record_index,
                        "src_off": record_index * size,
                        "rec_id": rec_id,
                        "pos_time": pos_time.isoformat(),
                        "harv_time": harvest_time.isoformat() if harvest_time else "",
                        "flow_dly": int((harvest_time - pos_time).total_seconds())
                        if harvest_time
                        else -1,
                        "hyp_lat": latitude,
                        "hyp_lon": longitude,
                        "elev_m": o_i47 / 1000,
                        "head_deg": o_u56 / 10,
                        "speed_ms": _candidate_scaled(t_u35, 100),
                        "width_m": _candidate_scaled(t_u39, 100),
                        "moist_pc": _candidate_scaled(h_u38, 10),
                        "o_u33": _u16(tlo, 33),
                        "o_u35": _u16(tlo, 35),
                        "o_u37": _u16(tlo, 37),
                        "raw_a": raw_a,
                        "raw_b": raw_b,
                        "o_i47": o_i47,
                        "o_u51": struct.unpack_from("<I", tlo, 51)[0],
                        "o_u55": tlo[55],
                        "o_u56": o_u56,
                        "o_a2": o_a2,
                        "o_b2": o_b2,
                        "o_a3": o_a3,
                        "o_b3": o_b3,
                        "has_t": int(tlt is not None),
                        "t_u33": _u16(tlt, 33),
                        "t_u35": t_u35,
                        "t_u37": _u16(tlt, 37),
                        "t_u39": t_u39,
                        "has_h": int(tlh is not None),
                        "h_u33": tlh[33] if tlh is not None else -1,
                        "h_u34": _u16(tlh, 34),
                        "h_u36": _u16(tlh, 36),
                        "h_u38": h_u38,
                        "h_u40": _u16(tlh, 40),
                        "h_u42": _u16(tlh, 42),
                        "h_u44": _u16(tlh, 44),
                        "h_u46": _u16(tlh, 46),
                        "h_u48": _u16(tlh, 48),
                        "o_hex": tlo[33:].hex(),
                        "t_hex": tlt[33:].hex() if tlt is not None else "",
                        "h_hex": tlh[33:].hex() if tlh is not None else "",
                    }


def write_cnh_all_fields_shapefile(
    source: Path, output: Path, *, batch_size: int = 25_000
) -> dict[str, Any]:
    """Write all observed aligned and raw CNH fields to an experimental Shapefile."""
    source, output = Path(source), Path(output)
    if not zipfile.is_zipfile(source):
        raise ValueError("La extracción CNH requiere un ZIP válido.")
    if output.suffix.lower() != ".shp":
        raise ValueError("La salida debe terminar en .shp.")
    if batch_size < 1:
        raise ValueError("batch_size debe ser al menos 1.")
    existing = list(output.parent.glob(f"{output.stem}.*")) if output.parent.exists() else []
    if existing:
        raise FileExistsError(f"La salida ya existe: {existing[0]}")
    output.parent.mkdir(parents=True, exist_ok=True)

    counters: Counter[str] = Counter()
    rows: list[dict[str, Any]] = []
    append = False
    for row in iter_all_field_rows(source, counters):
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
        "status": "EXPERIMENTAL_ALL_FIELDS_WITH_UNKNOWN_HARVEST_CHANNELS",
        "source": source.as_posix(),
        "source_sha256": _sha256_file(source),
        "output": output.as_posix(),
        "geometry": {"type": "Point", "crs": "EPSG:4326", "validated": False},
        "join": {"key": "uint32 little-endian at byte 11", "verified": True},
        "counts": dict(sorted(counters.items())),
        "field_catalog": FIELD_CATALOG,
        "candidate_scales": {
            "elev_m": "o_i47 / 1000",
            "head_deg": "o_u56 / 10",
            "speed_ms": "t_u35 / 100",
            "width_m": "t_u39 / 100",
            "moist_pc": "h_u38 / 10",
        },
        "unknown_harvest_channels": {
            "h_u34": "possible mass, volume, flow or yield channel; scale unknown",
            "h_u36": "possible mass, volume, flow or yield channel; scale unknown",
        },
        "warnings": [
            "Los campos candidate no están validados contra el SDK CN1 oficial.",
            "h_u34 y h_u36 no se renombran como rendimiento o volumen sin evidencia.",
            "o_hex, t_hex y h_hex preservan todos los bytes de payload para auditoría.",
            "La geometría conserva la hipótesis TLO39_1E7 no validada.",
        ],
    }
    report_path = output.with_suffix(".quality.json")
    import json

    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report
