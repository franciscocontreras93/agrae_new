from io import BytesIO
from pathlib import Path
import struct
from tempfile import TemporaryDirectory
from threading import Thread
import time
from urllib.request import urlopen
import zipfile

from exportar_rindes.quality.monitor_presets import presets_for_monitor
from exportar_rindes.readers.cnh.record_analysis import RECORD_SIZES
from exportar_rindes.webapp_presets import PresetServer


def record(size: int, rec_id: int, second: int) -> bytearray:
    value = bytearray(size)
    value[:4] = b"CNH1"
    struct.pack_into("<I", value, 11, rec_id)
    value[27:33] = bytes((55, 6, 28, 11, 33, second))
    return value


def sample_zip() -> BytesIO:
    result = BytesIO()
    with zipfile.ZipFile(result, "w") as archive:
        base = "CARD.cn1/shared/A.fmd/B.fld/C"
        tlo = record(RECORD_SIZES[".tlo"], 1, 40)
        struct.pack_into("<ii", tlo, 39, 45_000_000, -15_000_000)
        tlt = record(RECORD_SIZES[".tlt"], 1, 40)
        struct.pack_into("<H", tlt, 35, 200)
        struct.pack_into("<H", tlt, 39, 540)
        tlh = record(RECORD_SIZES[".tlh"], 1, 57)
        struct.pack_into("<H", tlh, 36, 6000)
        struct.pack_into("<H", tlh, 38, 120)
        archive.writestr(base + ".tlo", tlo)
        archive.writestr(base + ".tlt", tlt)
        archive.writestr(base + ".tlh", tlh)
        archive.writestr(
            "CARD.cn1/log/run.txt",
            "Cosechadora CX/CR.exe, Version 28.8.0.0\n"
            "Monitor rendimiento.dll, Version 28.5.0.0\n"
            "Ordenador de a bordo.dll, Version 28.3.0.0\n",
        )
    result.seek(0)
    return result


def test_monitor_profile_job_and_download_are_auditable() -> None:
    with TemporaryDirectory() as directory:
        server = PresetServer(("127.0.0.1", 0), Path(directory))
        item = server.upload_catalog.analyze(sample_zip(), "sample.zip")
        preset = presets_for_monitor(item["detection"])[0]
        job = server.job_store.create_from_catalog(
            item, preset, preset.settings, "EPSG:4326", "clean"
        )
        deadline = time.monotonic() + 10
        while job.status not in {"completed", "failed"} and time.monotonic() < deadline:
            time.sleep(0.05)
        assert job.status == "completed", job.error
        assert job.report["monitor_detection"]["probable_monitor"] == "New Holland IntelliView IV"
        assert not job.report["filter_preset"]["parameters_modified"]

        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            url = f"http://127.0.0.1:{server.server_port}/api/jobs/{job.id}/download"
            with urlopen(url, timeout=3) as response:
                package = zipfile.ZipFile(BytesIO(response.read()))
                assert package.testzip() is None
                assert "rindes_filtrados.quality.json" in package.namelist()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)
