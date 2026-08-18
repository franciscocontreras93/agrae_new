"""Agronomic yield normalization utilities.

These functions are independent from proprietary-format decoding.  They only
operate on already interpreted yield and moisture values.
"""

from __future__ import annotations


def normalize_yield_moisture(
    wet_yield: float | None,
    observed_moisture_pct: float | None,
    *,
    target_moisture_pct: float = 12.0,
) -> float | None:
    """Return wet-basis yield corrected to ``target_moisture_pct``.

    The calculation preserves dry matter::

        corrected = wet_yield * (100 - observed) / (100 - target)

    ``None`` is returned for missing, negative, or physically invalid inputs.
    """

    if wet_yield is None or observed_moisture_pct is None:
        return None
    if wet_yield < 0:
        return None
    if not 0 <= observed_moisture_pct < 100:
        return None
    if not 0 <= target_moisture_pct < 100:
        raise ValueError("target_moisture_pct must be in [0, 100)")
    return wet_yield * (100.0 - observed_moisture_pct) / (
        100.0 - target_moisture_pct
    )


def yield_plausibility_flag(
    yield_t_ha: float | None,
    *,
    minimum_t_ha: float = 0.0,
    maximum_t_ha: float = 11.0,
) -> str:
    """Classify a candidate yield without clipping or discarding it."""

    if yield_t_ha is None:
        return "missing"
    if yield_t_ha < minimum_t_ha:
        return "below"
    if yield_t_ha > maximum_t_ha:
        return "above"
    return "plausible"
