from exportar_rindes.core.models import SourceRecord
from exportar_rindes.quality.topcon import topcon_rejection_reasons


def test_topcon_filter_rejects_zero_coordinate() -> None:
    record = SourceRecord(
        manufacturer="TOPCON",
        source_file="sample.zip",
        longitude=0,
        latitude=0,
        yield_wet_t_ha=3.5,
    )
    reasons = topcon_rejection_reasons(record)
    assert "INVALID_COORDINATE" in reasons
    assert "MISSING_TIMESTAMP" in reasons
