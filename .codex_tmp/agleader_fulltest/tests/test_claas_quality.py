from exportar_rindes.core.models import SourceRecord
from exportar_rindes.quality.claas import claas_rejection_reasons


def test_claas_quality_accepts_wgs84_and_rejects_zero() -> None:
    valid = SourceRecord(
        manufacturer="CLAAS",
        source_file="sample",
        latitude=41.65,
        longitude=-5.24,
    )
    zero = SourceRecord(
        manufacturer="CLAAS",
        source_file="sample",
        latitude=0,
        longitude=0,
    )
    assert claas_rejection_reasons(valid) == []
    assert claas_rejection_reasons(zero) == ["INVALID_COORDINATE"]
