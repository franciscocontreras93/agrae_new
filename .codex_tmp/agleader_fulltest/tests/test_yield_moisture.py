import pytest

from exportar_rindes.normalization import (
    normalize_yield_moisture,
    yield_plausibility_flag,
)


def test_normalizes_wet_yield_to_twelve_percent_moisture() -> None:
    assert normalize_yield_moisture(10.0, 20.0) == pytest.approx(9.09090909)
    assert normalize_yield_moisture(10.0, 12.0) == pytest.approx(10.0)


@pytest.mark.parametrize(
    ("wet_yield", "moisture"),
    [(None, 15.0), (5.0, None), (-1.0, 15.0), (5.0, -0.1), (5.0, 100.0)],
)
def test_invalid_input_is_not_normalized(wet_yield, moisture) -> None:
    assert normalize_yield_moisture(wet_yield, moisture) is None


def test_rejects_invalid_target_moisture() -> None:
    with pytest.raises(ValueError):
        normalize_yield_moisture(5.0, 15.0, target_moisture_pct=100.0)


@pytest.mark.parametrize(
    ("value", "expected"),
    [(None, "missing"), (-0.1, "below"), (0.0, "plausible"),
     (11.0, "plausible"), (11.1, "above")],
)
def test_yield_plausibility_flags(value, expected) -> None:
    assert yield_plausibility_flag(value) == expected
