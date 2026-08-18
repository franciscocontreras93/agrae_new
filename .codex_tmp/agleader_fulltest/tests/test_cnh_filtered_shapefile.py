from pathlib import Path
import csv
import struct
import zipfile

import pyogrio

from exportar_rindes.exporters.cnh_filtered_shapefile import (
    write_cnh_filtered_shapefile,
)
from exportar_rindes.quality import FilterSettings
from exportar_rindes.readers.cnh.record_analysis import RECORD_SIZES


def record(size: int, rec_id: int, second: int) -> bytearray:
    value = bytearray(size)
    value[:4] = b"CNH1"
    struct.pack_into("<I", value, 11, rec_id)
    value[27:33] = bytes((55, 6, 28, 11, 33, second))
    return value


def test_filtered_export_keeps_clean_point_and_audits_rejection(tmp_path: Path) -> None:
    records = {suffix: [] for suffix in RECORD_SIZES}
    for index, yield_kg_ha in enumerate((6000, 12_000)):
        rec_id = 100 + index
        tlo = record(RECORD_SIZES[".tlo"], rec_id, 40 + index)
        struct.pack_into("<ii", tlo, 39, 45_000_000 + index, -15_000_000 + index)
        tlt = record(RECORD_SIZES[".tlt"], rec_id, 40 + index)
        struct.pack_into("<H", tlt, 35, 200)
        struct.pack_into("<H", tlt, 39, 500)
        tlh = record(RECORD_SIZES[".tlh"], rec_id, 57 + index)
        struct.pack_into("<H", tlh, 36, yield_kg_ha)
        struct.pack_into("<H", tlh, 38, 120)
        records[".tlo"].append(tlo)
        records[".tlt"].append(tlt)
        records[".tlh"].append(tlh)

    source = tmp_path / "sample.zip"
    base = "sample/shared/A.fmd/B.fld/C"
    with zipfile.ZipFile(source, "w") as archive:
        for suffix, values in records.items():
            archive.writestr(base + suffix, b"".join(values))

    output = tmp_path / "result" / "filtered.shp"
    report = write_cnh_filtered_shapefile(
        source,
        output,
        settings=FilterSettings(),
        target_crs="EPSG:4326",
        batch_size=1,
    )
    frame = pyogrio.read_dataframe(output)
    with output.with_suffix(".rejected.csv").open(encoding="utf-8") as handle:
        rejected = list(csv.DictReader(handle))

    assert len(frame) == 1
    assert frame.iloc[0]["yld12_th"] == 6
    assert bool(frame.iloc[0]["qc_keep"])
    assert rejected[0]["reasons"] == "MAXY"
    assert report["summary"] == {
        "input_points": 2,
        "kept_points": 1,
        "rejected_points": 1,
        "kept_pct": 50.0,
    }
    assert report["filter_counts"]["reason_MAXY"] == 1
