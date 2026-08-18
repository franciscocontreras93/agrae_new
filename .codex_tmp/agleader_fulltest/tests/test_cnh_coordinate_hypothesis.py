from pathlib import Path
import struct
import zipfile

from exportar_rindes.readers.cnh.coordinate_hypothesis import scan_coordinate_hypotheses
from exportar_rindes.readers.cnh.record_analysis import RECORD_SIZES


def make_tlo_record(second: int, raw_a: int, raw_b: int) -> bytes:
    record = bytearray(RECORD_SIZES[".tlo"])
    record[:4] = b"CNH1"
    record[27:33] = bytes((55, 6, 28, 11, 33, second))
    struct.pack_into("<ii", record, 39, raw_a, raw_b)
    return bytes(record)


def test_coordinate_hypotheses_remain_diagnostic(tmp_path: Path):
    source = tmp_path / "sample.cn1.zip"
    records = b"".join(
        [
            make_tlo_record(57, 45_000_000, -15_000_000),
            make_tlo_record(58, 45_000_100, -15_000_100),
        ]
    )
    with zipfile.ZipFile(source, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("sample/shared/A.fmd/B.fld/C.tlo", records)

    result = scan_coordinate_hypotheses(source, sample_stride=1)

    assert result["scope"].startswith("diagnostic hypothesis")
    assert result["raw_pair"]["record_count"] == 2
    assert result["raw_pair"]["missing_pair_count"] == 0
    assert [item["divisor"] for item in result["scale_hypotheses"]] == [1_000_000, 10_000_000]
    assert len(result["samples"]) == 2
    assert result["samples"][0]["source_record"] == 0
