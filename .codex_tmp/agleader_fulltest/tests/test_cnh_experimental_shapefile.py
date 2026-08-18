from pathlib import Path
import struct
import zipfile

import pyogrio
import pytest

from exportar_rindes.exporters.experimental_shapefile import (
    FIELD_EQUIVALENCE,
    write_experimental_cnh_shapefile,
)
from exportar_rindes.readers.cnh.record_analysis import RECORD_SIZES


def make_tlo_record(second: int, raw_a: int, raw_b: int) -> bytes:
    record = bytearray(RECORD_SIZES[".tlo"])
    record[:4] = b"CNH1"
    record[27:33] = bytes((55, 6, 28, 11, 33, second))
    struct.pack_into("<ii", record, 39, raw_a, raw_b)
    return bytes(record)


def test_experimental_shapefile_is_traceable_and_qc_reported(tmp_path: Path):
    source = tmp_path / "sample.cn1.zip"
    records = b"".join(
        [
            make_tlo_record(57, 45_000_000, -15_000_000),
            make_tlo_record(58, -2_147_483_647, -2_147_483_647),
            make_tlo_record(59, 1_000_000_000, -15_000_000),
        ]
    )
    with zipfile.ZipFile(source, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("sample/shared/A.fmd/B.fld/C.tlo", records)
    output = tmp_path / "shape" / "cnh_pts.shp"

    report = write_experimental_cnh_shapefile(source, output, batch_size=1)
    result = pyogrio.read_dataframe(output)

    assert report["status"].startswith("EXPERIMENTAL")
    assert report["counts"]["record_count"] == 3
    assert report["counts"]["exported_count"] == 1
    assert report["counts"]["skipped_missing_pair"] == 1
    assert report["counts"]["skipped_out_of_range"] == 1
    assert len(result) == 1
    assert result.iloc[0]["src_rec"] == 0
    assert result.iloc[0]["raw_a"] == 45_000_000
    assert result.crs.to_epsg() == 4326
    assert all(len(name) <= 10 for name in result.columns if name != "geometry")
    assert all(len(name) <= 10 for name in FIELD_EQUIVALENCE)
    assert output.with_suffix(".quality.json").exists()


def test_experimental_shapefile_refuses_overwrite(tmp_path: Path):
    source = tmp_path / "sample.cn1.zip"
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr(
            "sample/shared/A.fmd/B.fld/C.tlo",
            make_tlo_record(57, 45_000_000, -15_000_000),
        )
    output = tmp_path / "cnh_pts.shp"
    write_experimental_cnh_shapefile(source, output)
    with pytest.raises(FileExistsError):
        write_experimental_cnh_shapefile(source, output)
