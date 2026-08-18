from pathlib import Path
from exportar_rindes.core.detector import detect_manufacturer


def test_detect_cnh_sample():
    sample = Path("data/raw/CNH/250805L6.cn1.zip")
    assert detect_manufacturer(sample) == "CNH"
