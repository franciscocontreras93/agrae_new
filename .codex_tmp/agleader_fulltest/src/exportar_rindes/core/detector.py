from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

from exportar_rindes.readers.agleader.collection import is_agdata


def _directory_isoxml_manufacturer(path: Path) -> str | None:
    taskdata = next(
        (
            item
            for item in path.rglob("*")
            if item.is_file() and item.name.upper() == "TASKDATA.XML"
        ),
        None,
    )
    if taskdata is None:
        return None
    try:
        root = ET.parse(taskdata).getroot()
    except ET.ParseError:
        return None
    declarations = " ".join(
        (
            root.attrib.get("ManagementSoftwareManufacturer", ""),
            root.attrib.get("TaskControllerManufacturer", ""),
        )
    ).upper()
    if "CLAAS" in declarations:
        return "CLAAS"
    return "ISOXML"


def detect_manufacturer(path: Path) -> str:
    path = Path(path)
    name = path.name.lower()
    if name.endswith(".agdata") and is_agdata(path):
        return "AGLEADER"
    if name.endswith(".cn1") or ".cn1." in name:
        return "CNH"
    if path.is_dir() and (path / "COMBINES").exists():
        return "CNH"
    if path.is_dir():
        detected = _directory_isoxml_manufacturer(path)
        if detected:
            return detected
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            names = [item.upper() for item in archive.namelist()]
            if any("/COMBINES/" in f"/{item}" for item in names):
                return "CNH"
            taskdata = [
                item
                for item in archive.namelist()
                if item.upper().endswith("TASKDATA.XML")
            ]
            for member in taskdata:
                with archive.open(member) as handle:
                    header = handle.read(65536).upper()
                if (
                    b"TOPCON AGRICULTURE" in header
                    or b"TOPCON PRECISION AGRICULTURE" in header
                ):
                    return "TOPCON"
                if b"CLAAS" in header:
                    return "CLAAS"
            if any("TASKDATA.XML" in item for item in names):
                return "ISOXML"
    return "UNKNOWN"
