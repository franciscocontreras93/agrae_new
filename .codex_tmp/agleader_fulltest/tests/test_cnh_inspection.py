from pathlib import Path
from exportar_rindes.readers.cnh import CnhReader


def test_cnh_inventory_has_yield_candidates():
    result = CnhReader().inspect(Path("data/raw/CNH/250805L6.cn1.zip"))
    assert result.manufacturer == "CNH"
    assert result.file_count > 0
    assert any(name.lower().endswith(".ycs") for name in result.candidate_files)
