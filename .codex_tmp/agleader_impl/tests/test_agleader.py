from io import BytesIO
from pathlib import Path
import struct
import tarfile
import zlib

from exportar_rindes.core.detector import detect_manufacturer
from exportar_rindes.readers.agleader.collection import open_collection
from exportar_rindes.readers.agleader.ilf2 import GPS_GUID, SENSOR_GUID, iter_ilf2_points


def _record(guid: bytes, body: bytes) -> bytes:
    payload = guid + body
    return b"\xff\xff\x00\x00" + struct.pack("<I", len(payload)) + b"\x01\x00\x00\x00" + payload


def _sample_ilf2() -> bytes:
    gps_body = bytearray(136)
    struct.pack_into("<Q", gps_body, 0, 1_783_329_385_053)
    struct.pack_into("<ddd", gps_body, 16, -3.89061668, 42.407876245, 918.286)
    sensor_body = bytearray(84)
    struct.pack_into("<I", sensor_body, 12, 6)
    struct.pack_into("<6d", sensor_body, 16, 8.63, 17.35, 91.268, 281.1, 1.8, 0.0)
    struct.pack_into("<I", sensor_body, 64, 2)
    struct.pack_into("<2d", sensor_body, 68, 0.938, 0.0)
    decoded = _record(GPS_GUID, bytes(gps_body)) + _record(SENSOR_GUID, bytes(sensor_body))
    compressor = zlib.compressobj(wbits=-zlib.MAX_WBITS)
    return bytes(272) + compressor.compress(decoded) + compressor.flush()


def test_decode_confirmed_agleader_fields():
    rows = list(iter_ilf2_points(_sample_ilf2()))
    assert len(rows) == 1
    assert rows[0]["longitude"] == -3.89061668
    assert rows[0]["latitude"] == 42.407876245
    assert rows[0]["sensor_04"] == 281.1
    assert rows[0]["sensor_count"] == 8


def test_detect_and_open_agdata(tmp_path: Path):
    path = tmp_path / "sample.agdata"
    archive_buffer = BytesIO()
    with tarfile.open(fileobj=archive_buffer, mode="w") as archive:
        data = _sample_ilf2()
        member = tarfile.TarInfo("log_data/sample.ilf2")
        member.size = len(data)
        archive.addfile(member, BytesIO(data))
    path.write_bytes(b"AG LEADER TECHNOLOGY".ljust(400, b" ") + archive_buffer.getvalue())
    assert detect_manufacturer(path) == "AGLEADER"
    with open_collection(path) as archive:
        assert archive.getnames() == ["log_data/sample.ilf2"]
