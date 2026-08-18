from pathlib import Path
import struct
import zipfile

from exportar_rindes.quality.monitor_presets import detect_monitor, presets_for_monitor
from exportar_rindes.readers.cnh.record_analysis import RECORD_SIZES


def test_detects_cxcr_software_without_claiming_exact_hardware(tmp_path: Path) -> None:
    source = tmp_path / "sample.zip"
    tlt = bytearray(RECORD_SIZES[".tlt"])
    tlt[:4] = b"CNH1"
    struct.pack_into("<H", tlt, 39, 760)
    log = "\n".join(
        [
            "Cosechadora CX/CR.exe, SWID: 1300, Version 28.8.0.0",
            "Monitor rendimiento.dll, SWID: 1303, Version 28.5.0.0",
            "Ordenador de a bordo.dll, SWID: 1308, Version 28.3.0.0",
        ]
    )
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("CARD.cn1/log/run.txt", log)
        archive.writestr("CARD.cn1/shared/A.tlt", tlt)

    detection = detect_monitor(source)
    presets = presets_for_monitor(detection)

    assert detection.probable_monitor == "New Holland IntelliView IV"
    assert detection.confidence == "medium"
    assert detection.yield_software == "28.5.0.0"
    assert detection.dominant_width_m == 7.6
    assert presets[0].settings.min_width_m == 3.8
    assert presets[-1].settings.standard_deviation
