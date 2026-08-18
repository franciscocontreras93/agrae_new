from datetime import datetime
from pathlib import Path
import struct
import zipfile

import pytest

from exportar_rindes.readers.cnh.record_analysis import (
    RECORD_SIZES,
    analyze_fixed_records,
    decode_observed_timestamp,
)


def make_record(size: int, second: int, raw_pair: tuple[int, int] | None = None) -> bytes:
    record = bytearray(size)
    record[:4] = b"CNH1"
    record[27:33] = bytes((55, 6, 28, 11, 33, second))
    if raw_pair is not None:
        for offset in (39, 58, 66):
            struct.pack_into("<ii", record, offset, *raw_pair)
    return bytes(record)


def test_decode_observed_timestamp():
    record = make_record(RECORD_SIZES[".tlo"], 57, (45_279_054, -15_931_603))
    assert decode_observed_timestamp(record) == datetime(2025, 6, 28, 11, 33, 57)


def test_decode_observed_timestamp_rejects_unobserved_magic():
    record = bytearray(make_record(RECORD_SIZES[".tlh"], 57))
    record[:4] = b"NOPE"
    with pytest.raises(ValueError, match="CNH1"):
        decode_observed_timestamp(bytes(record))


def test_analyze_fixed_records_preserves_raw_pair_as_unknown(tmp_path: Path):
    source = tmp_path / "sample.cn1.zip"
    base = "sample/shared/A.fmd/B.fld/C"
    with zipfile.ZipFile(source, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for suffix, size in RECORD_SIZES.items():
            records = []
            for second in (57, 58):
                pair = (45_279_054 + second, -15_931_603 + second)
                records.append(make_record(size, second, pair if suffix == ".tlo" else None))
            archive.writestr(base + suffix, b"".join(records))

    result = analyze_fixed_records(source)

    families = result["record_families"]
    assert families["complete_triplet_count"] == 1
    assert families["equal_record_count_triplet_count"] == 1
    assert families["invalid_magic_count"] == 0
    assert families["invalid_timestamp_count"] == 0
    pair = result["tlo_repeated_raw_pair"]
    assert pair["record_count"] == 2
    assert pair["copy_at_58_equal_count"] == 2
    assert pair["copy_at_66_equal_count"] == 2
    assert pair["interpretation"].startswith("unknown")
