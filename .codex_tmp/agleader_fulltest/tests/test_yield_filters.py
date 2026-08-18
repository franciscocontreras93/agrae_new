import pytest

from exportar_rindes.quality import FilterSettings, FilterState, apply_filters


def row(**updates):
    value = {
        "src_file": "a.tlo", "src_rec": 1, "yld12_th": 6.0,
        "speed_hyp": 2.0, "width_hyp": 5.4, "moist_hyp": 12.0,
    }
    value.update(updates)
    return value


def test_default_filters_keep_plausible_point() -> None:
    assert apply_filters(row(), FilterSettings(), FilterState()) == []


def test_filters_report_every_reason_without_changing_values() -> None:
    original = row(yld12_th=12.0, speed_hyp=0.2, width_hyp=1.0, moist_hyp=50.0)
    reasons = apply_filters(original, FilterSettings(), FilterState())
    assert reasons == ["MAXY", "MINV", "MINS", "MOIST"]
    assert original["yld12_th"] == 12.0


def test_smooth_velocity_only_compares_consecutive_records() -> None:
    state = FilterState()
    apply_filters(row(src_rec=1, speed_hyp=2.0), FilterSettings(), state)
    assert "SMV" in apply_filters(row(src_rec=2, speed_hyp=3.0), FilterSettings(), state)
    assert "SMV" not in apply_filters(row(src_rec=8, speed_hyp=1.0), FilterSettings(), state)


def test_standard_deviation_filter_is_optional() -> None:
    settings = FilterSettings(standard_deviation=True, max_yield_stddev=3.0)
    assert "STDY" in apply_filters(
        row(yld12_th=10.0), settings, FilterState(), yield_mean=5.0, yield_stddev=1.0
    )


def test_invalid_ranges_are_rejected() -> None:
    with pytest.raises(ValueError):
        FilterSettings(min_yield_t_ha=12, max_yield_t_ha=11).validate()
