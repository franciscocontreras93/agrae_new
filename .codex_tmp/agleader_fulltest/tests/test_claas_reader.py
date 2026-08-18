from pathlib import Path
import struct

from exportar_rindes.core.detector import detect_manufacturer
from exportar_rindes.readers.claas import ClaasReader
from exportar_rindes.readers.claas.cm import iter_cm_points


def make_claas_sample(
    path: Path,
    *,
    task_number: int = 10,
    latitude: float = 41.651465,
    longitude: float = -5.244430,
) -> Path:
    path.mkdir()
    taskdata = f"""<?xml version="1.0" encoding="UTF-8"?>
<ISO11783_TaskData VersionMajor="3" VersionMinor="0"
 TaskControllerManufacturer="Claas" TaskControllerVersion="0.1">
 <DVC A="DVC-1" B="Lexion 6600" D="A00086000002B012"/>
 <DVC A="DVC-2" B="Vario 770" D="A00C00000CE2B012"/>
 <PFD A="PFD-{task_number}" C="Field {task_number}" D="0"/>
 <TSK A="TSK-{task_number}" B="Task {task_number}" E="PFD-{task_number}" G="3">
  <TIM A="2025-07-09T15:14:12" B="2025-07-09T23:10:15" D="4"/>
 </TSK>
</ISO11783_TaskData>
"""
    (path / "TASKDATA.XML").write_text(taskdata, encoding="utf-8")
    identifier = b"0xA00C00000CE2B012"
    content = bytearray(b"\x00\x05")
    content.extend(struct.pack("<iiii", -task_number, -2147483648, -7, len(identifier)))
    content.extend(identifier)
    content.extend(struct.pack("<iBdf", 2, 0, 388.096131, 1.499))
    content.extend(b"\x03" + struct.pack("<ddd f", latitude, longitude, 785.2, 263.7))
    content.extend(b"\x04" + struct.pack("<B i d f", 2, 1, 388.096131, 1.499))
    content.extend(
        b"\x03"
        + struct.pack("<ddd f", latitude + 0.00001, longitude - 0.00001, 785.3, 264.0)
    )
    content.extend(b"\x04")
    cm_path = path / f"TASK-{task_number}_-7_0.CM"
    cm_path.write_bytes(content)
    return cm_path


def test_claas_detection_and_cm_decode(tmp_path: Path) -> None:
    source = tmp_path / "claas"
    cm_path = make_claas_sample(source)
    assert detect_manufacturer(source) == "CLAAS"
    inspection = ClaasReader().inspect(source)
    records = ClaasReader().read(source)
    assert inspection.manufacturer == "CLAAS"
    assert len(records) == 2
    assert records[0].latitude == 41.651465
    assert records[0].longitude == -5.244430
    assert records[0].field == "Field 10"
    assert records[0].machine == "Lexion 6600"
    assert records[0].metadata["source_member"] == cm_path.name
    assert records[0].metadata["byte_offset"] == 53
    assert records[1].metadata["cm_block_number"] == 1
    assert records[0].yield_wet_t_ha is None
    assert records[0].moisture_pct is None


def test_two_independent_claas_directories_decode(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    make_claas_sample(first, task_number=2, latitude=41.44, longitude=-5.41)
    make_claas_sample(second, task_number=23, latitude=41.58, longitude=-5.33)
    first_record = ClaasReader().read(first)[0]
    second_record = ClaasReader().read(second)[0]
    assert first_record.metadata["task_identifier"] == "TSK-2"
    assert second_record.metadata["task_identifier"] == "TSK-23"
    assert first_record.latitude != second_record.latitude


def test_claas_cm_requires_explicit_terminator(tmp_path: Path) -> None:
    source = tmp_path / "claas"
    cm_path = make_claas_sample(source)
    cm_path.write_bytes(cm_path.read_bytes()[:-1])
    try:
        list(iter_cm_points(cm_path))
    except ValueError as error:
        assert "terminador" in str(error)
    else:
        raise AssertionError("Un CM truncado no debe aceptarse.")
