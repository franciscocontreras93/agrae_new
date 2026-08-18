from datetime import datetime, timezone
from pathlib import Path
import struct
import zipfile

from exportar_rindes.core.detector import detect_manufacturer
from exportar_rindes.quality.topcon import topcon_rejection_reasons
from exportar_rindes.readers.topcon import TopconReader


def make_topcon_sample(path: Path) -> None:
    base = "TOPCON/Clients/C/F/P/Jobs/J/TASKDATA/"
    taskdata = (
        '<ISO11783_TaskData ManagementSoftwareManufacturer="Topcon Agriculture" '
        'TaskControllerManufacturer="Topcon Precision Agriculture"/>'
    )
    dvc = """<XFC><DVC A="DVC-1" B="TOPCON YieldTrakk YM-1">
      <DET A="DET-1" D="Harvester"><DOR A="1"/><DOR A="2"/><DOR A="3"/></DET>
      <DPD A="1" B="0054" E="Wet Yield" F="10"/>
      <DPD A="2" B="0063" E="Moisture" F="11"/>
      <DPD A="3" B="0043" E="Machine Width" F="12"/>
      <DVP A="10" B="0" C="0.01" E="kg/ha"/>
      <DVP A="11" B="0" C="0.0001" E="%"/>
      <DVP A="12" B="0" C="0.001" E="m"/>
    </DVC><DVC A="DVC-2" B="Machine"/></XFC>"""
    tlg = """<TIM A="" D="4"><PTN A="" B="" C="" D=""/>
      <DLV A="0054" B="" C="DET-1"/>
      <DLV A="0063" B="" C="DET-1"/>
      <DLV A="0043" B="" C="DET-1"/>
    </TIM>"""
    ini = "[AsAppliedMap]\nChannel1\\Product=TRIGO\n"
    days = (datetime(2023, 7, 21) - datetime(1980, 1, 1)).days
    time = struct.pack("<IH", 12 * 3600 * 1000, days)
    position = struct.pack("<iiiB", 424423657, -31597965, 800000, 2)
    changes = b"\x03" + b"\x00" + struct.pack("<i", 327574)
    changes += b"\x01" + struct.pack("<i", 116398)
    changes += b"\x02" + struct.pack("<i", 7600)
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(base + "TASKDATA.xml", taskdata)
        archive.writestr(base + "DVC00000.xml", dvc)
        archive.writestr(base + "TLG00001.xml", tlg)
        archive.writestr(base + "TLG00001.bin", time + position + changes)
        archive.writestr("TOPCON/Clients/C/F/P/Jobs/J/J.ini", ini)


def test_topcon_detection_and_isoxml_decode(tmp_path: Path) -> None:
    source = tmp_path / "topcon.zip"
    make_topcon_sample(source)
    assert detect_manufacturer(source) == "TOPCON"
    inspection = TopconReader().inspect(source)
    records = TopconReader().read(source)
    assert inspection.manufacturer == "TOPCON"
    assert len(records) == 1
    record = records[0]
    assert record.timestamp == datetime(2023, 7, 21, 12, tzinfo=timezone.utc)
    assert record.latitude == 42.4423657
    assert record.longitude == -3.1597965
    assert round(record.yield_wet_t_ha, 5) == 3.27574
    assert round(record.moisture_pct, 4) == 11.6398
    assert round(record.width_m, 1) == 7.6
    assert record.crop == "TRIGO"
    assert record.field == "P"
    assert record.metadata["byte_offset"] == 0
    assert topcon_rejection_reasons(record) == []
