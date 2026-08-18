from pathlib import Path
import struct
import zipfile

import pyogrio

from exportar_rindes.exporters.cnh_named_hypothesis_shapefile import (
    NAMED_FIELD_CATALOG,
    write_cnh_named_hypothesis_shapefile,
)
from exportar_rindes.readers.cnh.record_analysis import RECORD_SIZES


def record(size: int, rec_id: int, second: int) -> bytearray:
    value = bytearray(size)
    value[:4] = b"CNH1"
    struct.pack_into("<I", value, 11, rec_id)
    value[27:33] = bytes((55, 6, 28, 11, 33, second))
    return value


def test_named_hypotheses_are_explicit_and_calculated(tmp_path: Path):
    rec_id = 42
    tlo = record(RECORD_SIZES[".tlo"], rec_id, 40)
    struct.pack_into("<ii", tlo, 39, 45_000_000, -15_000_000)
    struct.pack_into("<i", tlo, 47, 750_000)
    struct.pack_into("<H", tlo, 56, 1234)
    tlt = record(RECORD_SIZES[".tlt"], rec_id, 40)
    struct.pack_into("<H", tlt, 33, 12)
    struct.pack_into("<H", tlt, 35, 200)
    struct.pack_into("<H", tlt, 39, 500)
    tlh = record(RECORD_SIZES[".tlh"], rec_id, 57)
    tlh[33] = 1
    struct.pack_into("<H", tlh, 34, 500)
    struct.pack_into("<H", tlh, 36, 6000)
    struct.pack_into("<H", tlh, 38, 120)
    source = tmp_path / "sample.cn1.zip"
    base = "sample/shared/A.fmd/B.fld/C"
    with zipfile.ZipFile(source, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(base + ".tlo", tlo)
        archive.writestr(base + ".tlt", tlt)
        archive.writestr(base + ".tlh", tlh)

    output = tmp_path / "named" / "cnh_named.shp"
    report = write_cnh_named_hypothesis_shapefile(source, output, batch_size=1)
    row = pyogrio.read_dataframe(output).iloc[0]

    assert row["yield_raw"] == 6000
    assert row["yield_hyp"] == 6000
    assert row["flow_hyp"] == 5
    assert row["speed_hyp"] == 2
    assert row["width_hyp"] == 5
    assert row["calc_yld"] == 5000
    assert row["moist_hyp"] == 12
    assert report["status"].startswith("EXPERIMENTAL")
    assert NAMED_FIELD_CATALOG["yield_hyp"]["confidence"] == "moderate"
    assert all(len(name) <= 10 for name in row.index if name != "geometry")
