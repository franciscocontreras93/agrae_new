from pathlib import Path

from exportar_rindes.readers.topcon.inspection import build_technical_inventory
from test_topcon_isoxml import make_topcon_sample


def test_topcon_inventory_records_manufacturer_and_tlg_pair(tmp_path: Path) -> None:
    source = tmp_path / "topcon.zip"
    make_topcon_sample(source)
    result = build_technical_inventory(source)
    assert result["manufacturer_evidence"]["classification"] == "TOPCON"
    assert result["isoxml"]["time_log_xml_count"] == 1
    assert result["isoxml"]["time_log_bin_count"] == 1
    assert result["archive"]["sha256"]
    assert any(
        item["label"] == "Wet Yield"
        for item in result["isoxml"]["declared_yield_fields"]
    )
