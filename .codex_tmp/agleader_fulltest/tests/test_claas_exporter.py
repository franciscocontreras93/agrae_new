import json
from pathlib import Path
import struct

import geopandas as gpd

from exportar_rindes.exporters.claas_gpkg import write_claas_gpkg
from test_claas_reader import make_claas_sample


def test_claas_exporter_writes_tracks_blocks_and_quality_report(tmp_path: Path) -> None:
    source = tmp_path / "claas"
    cm_path = make_claas_sample(source)
    content = cm_path.read_bytes()
    extra_point = b"\x03" + struct.pack(
        "<ddd f",
        41.651485,
        -5.244450,
        785.4,
        264.2,
    )
    cm_path.write_bytes(content[:-1] + extra_point + content[-1:])
    output = tmp_path / "claas.gpkg"
    report = write_claas_gpkg(source, output)
    points = gpd.read_file(output, layer="track_points")
    blocks = gpd.read_file(output, layer="cm_blocks")
    saved_report = json.loads(output.with_suffix(".quality.json").read_text("utf-8"))
    assert len(points) == 3
    assert len(blocks) == 1
    assert points.crs.to_epsg() == 25830
    assert blocks.crs.to_epsg() == 25830
    assert report["counts"]["track_points"] == 3
    assert report["counts"]["cm_blocks"] == 1
    assert saved_report["status"] == "CLAAS_CM_COORDINATES_AND_BLOCKS"
    assert saved_report["heading_candidate"]["segment_count"] == 1
    assert {"src_member", "src_record", "src_offset", "heading_c"} <= set(
        points.columns
    )
