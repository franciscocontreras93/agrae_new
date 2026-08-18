"""Reproducible structural inventory for CLAAS TASKDATA directories."""

from __future__ import annotations

from collections import Counter
import hashlib
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

from exportar_rindes.readers.claas.cm import iter_cm_points, read_cm_header
from exportar_rindes.readers.claas.context import find_taskdata


HEADER_BYTES = 32
CHUNK_BYTES = 1024 * 1024


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _cm_summary(path: Path) -> dict[str, Any]:
    point_count = 0
    minimum_latitude = minimum_longitude = None
    maximum_latitude = maximum_longitude = None
    with path.open("rb") as handle:
        header = read_cm_header(handle, str(path))
    for _, point in iter_cm_points(path):
        point_count += 1
        minimum_latitude = (
            point.latitude
            if minimum_latitude is None
            else min(minimum_latitude, point.latitude)
        )
        maximum_latitude = (
            point.latitude
            if maximum_latitude is None
            else max(maximum_latitude, point.latitude)
        )
        minimum_longitude = (
            point.longitude
            if minimum_longitude is None
            else min(minimum_longitude, point.longitude)
        )
        maximum_longitude = (
            point.longitude
            if maximum_longitude is None
            else max(maximum_longitude, point.longitude)
        )
    return {
        "path": path.name,
        "task_code": header.task_code,
        "secondary_code": header.secondary_code,
        "device_identifier": header.device_identifier,
        "data_offset": header.data_offset,
        "point_count": point_count,
        "bounds_wgs84": [
            minimum_longitude,
            minimum_latitude,
            maximum_longitude,
            maximum_latitude,
        ],
    }


def build_technical_inventory(source: Path) -> dict[str, Any]:
    source = Path(source)
    if not source.is_dir():
        raise ValueError("El inventario CLAAS requiere un directorio.")
    files = sorted(item for item in source.rglob("*") if item.is_file())
    taskdata = find_taskdata(source)
    root = ET.parse(taskdata).getroot()
    declarations = {
        "management_software_manufacturer": root.attrib.get(
            "ManagementSoftwareManufacturer", ""
        ),
        "task_controller_manufacturer": root.attrib.get(
            "TaskControllerManufacturer", ""
        ),
        "task_controller_version": root.attrib.get("TaskControllerVersion", ""),
        "isoxml_version": (
            f"{root.attrib.get('VersionMajor', '')}."
            f"{root.attrib.get('VersionMinor', '')}"
        ),
    }
    extensions = Counter(item.suffix.lower() or "<sin_ext>" for item in files)
    members = []
    for item in files:
        with item.open("rb") as handle:
            header = handle.read(HEADER_BYTES)
        members.append(
            {
                "path": str(item.relative_to(source)),
                "extension": item.suffix.lower() or "<sin_ext>",
                "size_bytes": item.stat().st_size,
                "sha256": _sha256(item),
                "header_hex": header.hex(" "),
            }
        )
    cm_files = [item for item in files if item.suffix.lower() == ".cm"]
    cm_summaries = [_cm_summary(item) for item in cm_files]
    dpd = [
        {
            "ddi": item.attrib.get("B", ""),
            "label": item.attrib.get("E", ""),
            "presentation": item.attrib.get("F", ""),
        }
        for item in root.findall(".//DPD")
    ]
    dpt = [
        {
            "ddi": item.attrib.get("B", ""),
            "label": item.attrib.get("D", ""),
            "presentation": item.attrib.get("E", ""),
        }
        for item in root.findall(".//DPT")
    ]
    tlg_bins = [item for item in files if item.name.upper().startswith("TLG") and item.suffix.lower() == ".bin"]
    return {
        "schema_version": 1,
        "scope": "ISOXML declarations and verified CM coordinate layout",
        "source": str(source),
        "manufacturer_evidence": {
            "classification": (
                "CLAAS"
                if "CLAAS"
                in (
                    declarations["management_software_manufacturer"]
                    + declarations["task_controller_manufacturer"]
                ).upper()
                else "UNCONFIRMED"
            ),
            **declarations,
        },
        "files": {
            "count": len(files),
            "total_bytes": sum(item.stat().st_size for item in files),
            "extensions": dict(sorted(extensions.items())),
            "members": members,
        },
        "isoxml": {
            "task_count": len(root.findall("./TSK")),
            "field_count": len(root.findall("./PFD")),
            "declared_process_data": dpd + dpt,
            "tlg_bin_count": len(tlg_bins),
            "tlg_nonempty_bin_count": sum(item.stat().st_size > 0 for item in tlg_bins),
        },
        "cm": {
            "file_count": len(cm_files),
            "point_count": sum(item["point_count"] for item in cm_summaries),
            "files": cm_summaries,
        },
        "warnings": [
            "Los BIN TLG de las muestras tienen cero bytes.",
            "Solo latitud y longitud de CM reciben semántica; los demás valores se conservan.",
            "No se observan DDI declarados de rendimiento ni humedad.",
        ],
    }
