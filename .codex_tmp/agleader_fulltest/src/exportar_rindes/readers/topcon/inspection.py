"""Reproducible structural inventory for TOPCON ZIP exports."""

from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
from pathlib import Path, PurePosixPath
from typing import Any, BinaryIO
import xml.etree.ElementTree as ET
import zipfile


HEADER_BYTES = 32
CHUNK_BYTES = 1024 * 1024
CANDIDATE_SUFFIXES = {".xml", ".bin", ".gps", ".cov", ".dfr", ".wl", ".ini"}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _member_digest(handle: BinaryIO) -> tuple[str, bytes]:
    digest = hashlib.sha256()
    header = bytearray()
    for chunk in iter(lambda: handle.read(CHUNK_BYTES), b""):
        digest.update(chunk)
        if len(header) < HEADER_BYTES:
            header.extend(chunk[: HEADER_BYTES - len(header)])
    return digest.hexdigest(), bytes(header)


def build_technical_inventory(source: Path) -> dict[str, Any]:
    source = Path(source)
    if not zipfile.is_zipfile(source):
        raise ValueError("La inspección técnica TOPCON requiere un archivo ZIP válido.")
    extensions: Counter[str] = Counter()
    extension_bytes: defaultdict[str, dict[str, int]] = defaultdict(
        lambda: {"uncompressed_bytes": 0, "compressed_bytes": 0}
    )
    members = []
    topcon_evidence = []
    device_evidence = []
    yield_definitions: set[tuple[str, str, str, str]] = set()
    time_log_xml = time_log_bin = directory_count = 0
    with zipfile.ZipFile(source) as archive:
        for info in archive.infolist():
            if info.is_dir():
                directory_count += 1
                continue
            suffix = PurePosixPath(info.filename).suffix.lower() or "<sin_ext>"
            extensions[suffix] += 1
            extension_bytes[suffix]["uncompressed_bytes"] += info.file_size
            extension_bytes[suffix]["compressed_bytes"] += info.compress_size
            name = PurePosixPath(info.filename).name.upper()
            time_log_xml += int(name.startswith("TLG") and suffix == ".xml")
            time_log_bin += int(name.startswith("TLG") and suffix == ".bin")
            with archive.open(info) as handle:
                digest, header = _member_digest(handle)
            members.append(
                {
                    "path": info.filename,
                    "extension": suffix,
                    "uncompressed_bytes": info.file_size,
                    "compressed_bytes": info.compress_size,
                    "crc32": f"{info.CRC:08x}",
                    "sha256": digest,
                    "header_hex": header.hex(" "),
                    "zip_datetime": "%04d-%02d-%02dT%02d:%02d:%02d" % info.date_time,
                }
            )
            if suffix != ".xml" or info.file_size > 2_000_000:
                continue
            try:
                with archive.open(info) as handle:
                    root = ET.parse(handle).getroot()
            except ET.ParseError:
                continue
            manufacturer = root.attrib.get("ManagementSoftwareManufacturer", "")
            controller = root.attrib.get("TaskControllerManufacturer", "")
            if "TOPCON" in (manufacturer + controller).upper():
                topcon_evidence.append(
                    {
                        "path": info.filename,
                        "management_software_manufacturer": manufacturer,
                        "task_controller_manufacturer": controller,
                        "management_software_version": root.attrib.get(
                            "ManagementSoftwareVersion", ""
                        ),
                    }
                )
            for device in root.findall(".//DVC"):
                designator = device.attrib.get("B", "")
                if "TOPCON" in designator.upper() or "YIELDTRAKK" in designator.upper():
                    device_evidence.append(
                        {"path": info.filename, "device_designator": designator}
                    )
                presentations = {
                    item.attrib["A"]: item for item in device.findall("./DVP")
                }
                for definition in device.findall("./DPD"):
                    label = definition.attrib.get("E", "")
                    if not any(
                        word in label.lower() for word in ("yield", "moisture", "width")
                    ):
                        continue
                    presentation = presentations.get(definition.attrib.get("F", ""))
                    yield_definitions.add(
                        (
                            definition.attrib.get("B", ""),
                            label,
                            presentation.attrib.get("C", "")
                            if presentation is not None
                            else "",
                            presentation.attrib.get("E", "")
                            if presentation is not None
                            else "",
                        )
                    )
    return {
        "schema_version": 1,
        "scope": (
            "structural inventory plus ISOXML declarations; proprietary COV/DFR/GPS/WL "
            "fields are not decoded"
        ),
        "source": str(source),
        "archive": {"size_bytes": source.stat().st_size, "sha256": _sha256_file(source)},
        "zip": {
            "file_count": len(members),
            "directory_count": directory_count,
            "total_uncompressed_bytes": sum(item["uncompressed_bytes"] for item in members),
            "total_compressed_bytes": sum(item["compressed_bytes"] for item in members),
            "extensions": {
                suffix: {"count": extensions[suffix], **extension_bytes[suffix]}
                for suffix in sorted(extensions)
            },
        },
        "manufacturer_evidence": {
            "classification": "TOPCON" if topcon_evidence and device_evidence else "UNCONFIRMED",
            "taskdata_declarations": topcon_evidence,
            "device_declarations": device_evidence,
        },
        "isoxml": {
            "time_log_xml_count": time_log_xml,
            "time_log_bin_count": time_log_bin,
            "paired_count": min(time_log_xml, time_log_bin),
            "declared_yield_fields": [
                {"ddi": ddi, "label": label, "scale": scale, "unit": unit}
                for ddi, label, scale, unit in sorted(yield_definitions)
            ],
        },
        "candidate_members": [
            item for item in members if item["extension"] in CANDIDATE_SUFFIXES
        ],
        "members": members,
        "warnings": [
            "La identificación TOPCON procede de atributos y equipos declarados en ISOXML.",
            "Solo se descodifican TLG binarios conforme a su plantilla XML y DVC/DPD/DVP.",
            "No se asigna semántica a los formatos propietarios COV, DFR, GPS o WL.",
            "Una importación completa requiere una segunda exportación TOPCON independiente.",
        ],
    }
