from pathlib import Path
import struct
import zipfile

import pyogrio

from exportar_rindes.exporters.cnh_all_fields_shapefile import (
    write_cnh_all_fields_shapefile,
)
from exportar_rindes.readers.cnh.record_analysis import RECORD_SIZES


def record(size: int, rec_id: int, second: int) -> bytearray:
    value = bytearray(size)
    value[:4] = b"CNH1"
    struct.pack_into("<I", value, 11, rec_id)
    value[27:33] = bytes((55, 6, 28, 11, 33, second))
    return value


def test_all_fields_export_joins_payloads_and_preserves_raw_hex(tmp_path: Path):
    rec_id = 1234
    tlo = record(RECORD_SIZES[".tlo"], rec_id, 40)
    struct.pack_into("<ii", tlo, 39, 45_000_000, -15_000_000)
    struct.pack_into("<i", tlo, 47, 750_000)
    struct.pack_into("<H", tlo, 56, 1234)
    tlt = record(RECORD_SIZES[".tlt"], rec_id, 40)
    struct.pack_into("<H", tlt, 35, 157)
    struct.pack_into("<H", tlt, 39, 540)
    tlh = record(RECORD_SIZES[".tlh"], rec_id, 57)
    tlh[33] = 1
    struct.pack_into("<H", tlh, 34, 524)
    struct.pack_into("<H", tlh, 36, 6562)
    struct.pack_into("<H", tlh, 38, 116)
    source = tmp_path / "sample.cn1.zip"
    base = "sample/shared/A.fmd/B.fld/C"
    with zipfile.ZipFile(source, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(base + ".tlo", tlo)
        archive.writestr(base + ".tlt", tlt)
        archive.writestr(base + ".tlh", tlh)

    output = tmp_path / "all" / "cnh_all.shp"
    report = write_cnh_all_fields_shapefile(source, output, batch_size=1)
    result = pyogrio.read_dataframe(output)

    row = result.iloc[0]
    assert row["rec_id"] == rec_id
    assert row["flow_dly"] == 17
    assert row["speed_ms"] == 1.57
    assert row["width_m"] == 5.4
    assert row["moist_pc"] == 11.6
    assert row["h_u34"] == 524
    assert row["h_u36"] == 6562
    assert row["o_hex"] == bytes(tlo[33:]).hex()
    assert report["unknown_harvest_channels"]["h_u34"].startswith("possible")
    assert all(len(name) <= 10 for name in result.columns if name != "geometry")
