from pathlib import Path

from exportar_rindes.readers.claas.inspection import build_technical_inventory
from test_claas_reader import make_claas_sample


def test_claas_inventory_records_evidence_and_points(tmp_path: Path) -> None:
    source = tmp_path / "claas"
    make_claas_sample(source)
    result = build_technical_inventory(source)
    assert result["manufacturer_evidence"]["classification"] == "CLAAS"
    assert result["isoxml"]["task_count"] == 1
    assert result["cm"]["file_count"] == 1
    assert result["cm"]["point_count"] == 2
    assert result["files"]["members"][0]["sha256"]
