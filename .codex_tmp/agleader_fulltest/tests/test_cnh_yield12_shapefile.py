import pytest

from exportar_rindes.exporters.cnh_yield12_shapefile import _yield12_row


def test_yield12_fields_are_derived_without_discarding_raw_values() -> None:
    source = {
        "mfr": "CNH", "src_file": "x.tlo", "src_rec": 1, "src_off": 74,
        "rec_id": 2, "pos_time": "2025-01-01T00:00:00", "harv_time": None,
        "flow_dly": None, "hyp_lat": 1.0, "hyp_lon": 2.0,
        "h_u34": 500, "h_u36": 10_000, "moist_pc": 20.0,
        "speed_ms": 2.0, "width_m": 5.0, "elev_m": 1.0,
        "head_deg": 90.0, "t_u33": 12, "o_u55": 1,
    }
    row = _yield12_row(source)
    assert row["yield_raw"] == 10_000
    assert row["yldwet_th"] == pytest.approx(10.0)
    assert row["yld12_th"] == pytest.approx(9.09090909)
    assert row["yld12_qc"] == "plausible"
    assert all(len(name) <= 10 for name in row)
