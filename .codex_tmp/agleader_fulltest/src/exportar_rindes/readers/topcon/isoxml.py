"""ISOXML time-log decoding for the observed TOPCON export."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import PurePosixPath
import configparser
import io
import struct
from typing import BinaryIO, Iterator
import xml.etree.ElementTree as ET
import zipfile

from exportar_rindes.core.models import SourceRecord


EPOCH = datetime(1980, 1, 1, tzinfo=timezone.utc)
PTN_LAYOUT = {
    "A": ("<i", 4),
    "B": ("<i", 4),
    "C": ("<i", 4),
    "D": ("<B", 1),
    "E": ("<H", 2),
    "F": ("<H", 2),
    "G": ("<B", 1),
    "H": ("<I", 4),
    "I": ("<H", 2),
}
YIELD_DDIS = {"0054", "00B5", "0063", "0043"}


@dataclass(frozen=True)
class ValueDefinition:
    ddi: str
    device_element: str
    label: str | None
    offset: int
    scale: float
    unit: str | None
    initial_raw: int | None

    def display(self, raw: int | None) -> float | None:
        if raw is None or raw == -2147483648:
            return None
        return (raw + self.offset) * self.scale


def _xml(archive: zipfile.ZipFile, path: str) -> ET.Element:
    with archive.open(path) as handle:
        return ET.parse(handle).getroot()


def _task_context(path: str) -> dict[str, str | None]:
    parts = PurePosixPath(path).parts
    result = {"client": None, "farm": None, "field": None, "job": None}
    try:
        client_index = parts.index("Clients")
        jobs_index = parts.index("Jobs")
    except ValueError:
        return result
    if jobs_index >= client_index + 4 and len(parts) > jobs_index + 1:
        result.update(
            client=parts[client_index + 1],
            farm=parts[client_index + 2],
            field=parts[client_index + 3],
            job=parts[jobs_index + 1],
        )
    return result


def _job_product(archive: zipfile.ZipFile, task_dir: PurePosixPath) -> str | None:
    job_dir = task_dir.parent
    ini_path = str(job_dir / f"{job_dir.name}.ini")
    try:
        with archive.open(ini_path) as handle:
            text = io.TextIOWrapper(handle, encoding="utf-8", errors="replace").read()
    except KeyError:
        return None
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    parser.optionxform = str
    try:
        parser.read_string(text)
    except configparser.Error:
        return None
    for section in parser.sections():
        for key, value in parser.items(section):
            if key.endswith(r"\Product") and value.strip():
                return value.strip()
    return None


def _device_model(
    archive: zipfile.ZipFile, task_dir: PurePosixPath
) -> tuple[dict[tuple[str, str], tuple[str | None, int, float, str | None]], str | None]:
    root = _xml(archive, str(task_dir / "DVC00000.xml"))
    definitions = {}
    machine = None
    for device in root.findall(".//DVC"):
        if machine is None and "TOPCON" not in device.attrib.get("B", "").upper():
            machine = device.attrib.get("B")
        presentations = {
            item.attrib["A"]: (
                int(item.attrib.get("B", "0")),
                float(item.attrib.get("C", "1")),
                item.attrib.get("E"),
            )
            for item in device.findall("./DVP")
        }
        process_data = {item.attrib["A"]: item for item in device.findall("./DPD")}
        for element in device.findall("./DET"):
            for reference in element.findall("./DOR"):
                definition = process_data.get(reference.attrib.get("A", ""))
                if definition is None:
                    continue
                offset, scale, unit = presentations.get(
                    definition.attrib.get("F", ""), (0, 1.0, None)
                )
                definitions[(element.attrib["A"], definition.attrib["B"].upper())] = (
                    definition.attrib.get("E"),
                    offset,
                    scale,
                    unit,
                )
    return definitions, machine


def _time_log_template(archive, xml_path, definitions):
    root = _xml(archive, xml_path)
    position = root.find("./PTN")
    if position is None:
        raise ValueError(f"{xml_path}: falta la plantilla PTN.")
    fields = [name for name in PTN_LAYOUT if name in position.attrib]
    columns = []
    for item in root.findall("./DLV"):
        ddi = item.attrib["A"].upper()
        element = item.attrib["C"]
        label, offset, scale, unit = definitions.get(
            (element, ddi), (None, 0, 1.0, None)
        )
        raw = item.attrib.get("B", "")
        columns.append(
            ValueDefinition(
                ddi, element, label, offset, scale, unit, int(raw) if raw else None
            )
        )
    return fields, columns


def _read_exact(handle: BinaryIO, size: int, context: str) -> bytes:
    value = handle.read(size)
    if len(value) != size:
        raise ValueError(f"{context}: registro binario truncado.")
    return value


def _decode_rows(handle, fields, columns, context):
    state = [column.initial_raw for column in columns]
    record_number = 0
    while True:
        offset = handle.tell()
        time_bytes = handle.read(6)
        if not time_bytes:
            return
        if len(time_bytes) != 6:
            raise ValueError(f"{context}: tiempo truncado en offset {offset}.")
        milliseconds, days = struct.unpack("<IH", time_bytes)
        position = {}
        for field in fields:
            fmt, size = PTN_LAYOUT[field]
            position[field] = struct.unpack(
                fmt, _read_exact(handle, size, f"{context} offset {offset}")
            )[0]
        changed_count = _read_exact(handle, 1, f"{context} offset {offset}")[0]
        changed = []
        for _ in range(changed_count):
            index = _read_exact(handle, 1, f"{context} offset {offset}")[0]
            if index >= len(columns):
                raise ValueError(
                    f"{context}: índice DLV {index} fuera de {len(columns)} columnas "
                    f"en offset {offset}."
                )
            state[index] = struct.unpack(
                "<i", _read_exact(handle, 4, f"{context} offset {offset}")
            )[0]
            changed.append(index)
        record_number += 1
        timestamp = None
        if milliseconds != 0xFFFFFFFF and days != 0xFFFF:
            timestamp = EPOCH + timedelta(days=days, milliseconds=milliseconds)
        yield {
            "record_number": record_number,
            "offset": offset,
            "timestamp": timestamp,
            "position": position,
            "state": tuple(state),
            "changed": tuple(changed),
        }


def iter_topcon_records(source) -> Iterator[SourceRecord]:
    """Yield ISOXML points with member, record, and byte-offset provenance."""
    with zipfile.ZipFile(source) as archive:
        names = set(archive.namelist())
        xml_paths = sorted(
            name
            for name in names
            if PurePosixPath(name).name.upper().startswith("TLG")
            and name.lower().endswith(".xml")
        )
        model_cache = {}
        product_cache = {}
        for xml_path in xml_paths:
            task_dir = PurePosixPath(xml_path).parent
            bin_path = str(PurePosixPath(xml_path).with_suffix(".bin"))
            dvc_path = str(task_dir / "DVC00000.xml")
            if bin_path not in names or dvc_path not in names:
                continue
            cache_key = str(task_dir)
            if cache_key not in model_cache:
                model_cache[cache_key] = _device_model(archive, task_dir)
                product_cache[cache_key] = _job_product(archive, task_dir)
            definitions, machine = model_cache[cache_key]
            fields, columns = _time_log_template(archive, xml_path, definitions)
            context = _task_context(xml_path)
            with archive.open(bin_path) as handle:
                for row in _decode_rows(handle, fields, columns, bin_path):
                    position = row["position"]
                    latitude = position.get("A")
                    longitude = position.get("B")
                    if latitude is None or longitude is None:
                        continue
                    values, units, raw_values = {}, {}, {}
                    for column, raw in zip(columns, row["state"]):
                        if column.device_element != "DET-1" or column.ddi not in YIELD_DDIS:
                            continue
                        values[column.ddi] = column.display(raw)
                        units[column.ddi] = column.unit
                        raw_values[column.ddi] = raw
                    wet, dry = values.get("0054"), values.get("00B5")
                    metadata = {
                        "archive_member": bin_path,
                        "byte_offset": row["offset"],
                        "job": context["job"],
                        "client": context["client"],
                        "farm": context["farm"],
                        "position_status": position.get("D"),
                        "elevation_m": (
                            position.get("C") / 1000 if "C" in position else None
                        ),
                        "pdop": position.get("E") / 10 if "E" in position else None,
                        "hdop": position.get("F") / 10 if "F" in position else None,
                        "satellites": position.get("G"),
                        "changed_column_indexes": list(row["changed"]),
                        "raw_by_ddi": raw_values,
                        "unit_by_ddi": units,
                        "crs": "EPSG:4326",
                    }
                    yield SourceRecord(
                        manufacturer="TOPCON",
                        source_file=source,
                        source_record=row["record_number"],
                        timestamp=row["timestamp"],
                        longitude=longitude / 10_000_000,
                        latitude=latitude / 10_000_000,
                        yield_wet_t_ha=wet / 1000 if wet is not None else None,
                        yield_dry_t_ha=dry / 1000 if dry is not None else None,
                        moisture_pct=values.get("0063"),
                        width_m=values.get("0043"),
                        crop=product_cache[cache_key],
                        field=context["field"],
                        machine=machine,
                        metadata=metadata,
                    )
