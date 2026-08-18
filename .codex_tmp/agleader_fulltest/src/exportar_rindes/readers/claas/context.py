"""ISOXML context used to label CLAAS coordinate-map records."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET


@dataclass(frozen=True)
class ClaasTask:
    identifier: str
    designator: str | None
    field: str | None
    time_ranges: tuple[tuple[str | None, str | None], ...]


@dataclass(frozen=True)
class ClaasContext:
    manufacturer: str
    machine: str | None
    devices: dict[str, str]
    tasks: dict[int, ClaasTask]


def find_taskdata(source: Path) -> Path:
    taskdata = next(
        (
            item
            for item in Path(source).rglob("*")
            if item.is_file() and item.name.upper() == "TASKDATA.XML"
        ),
        None,
    )
    if taskdata is None:
        raise ValueError(f"{source}: falta TASKDATA.XML.")
    return taskdata


def load_claas_context(source: Path) -> ClaasContext:
    root = ET.parse(find_taskdata(source)).getroot()
    manufacturer = (
        root.attrib.get("TaskControllerManufacturer")
        or root.attrib.get("ManagementSoftwareManufacturer")
        or ""
    )
    fields = {
        item.attrib.get("A", ""): item.attrib.get("C")
        for item in root.findall("./PFD")
    }
    devices = {
        item.attrib.get("D", ""): item.attrib.get("B", "")
        for item in root.findall("./DVC")
        if item.attrib.get("D")
    }
    machine = next(
        (
            item.attrib.get("B")
            for item in root.findall("./DVC")
            if "LEXION" in item.attrib.get("B", "").upper()
        ),
        None,
    )
    tasks = {}
    for item in root.findall("./TSK"):
        identifier = item.attrib.get("A", "")
        try:
            number = int(identifier.rsplit("-", 1)[1])
        except (IndexError, ValueError):
            continue
        tasks[number] = ClaasTask(
            identifier=identifier,
            designator=item.attrib.get("B"),
            field=fields.get(item.attrib.get("E", "")),
            time_ranges=tuple(
                (time.attrib.get("A"), time.attrib.get("B"))
                for time in item.findall("./TIM")
            ),
        )
    return ClaasContext(
        manufacturer=manufacturer,
        machine=machine,
        devices=devices,
        tasks=tasks,
    )
