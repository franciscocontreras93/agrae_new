"""Conservative, auditable filters for normalized TOPCON yield points."""

from __future__ import annotations

import math

from exportar_rindes.core.models import SourceRecord


def topcon_rejection_reasons(
    record: SourceRecord, *, maximum_yield_t_ha: float = 30.0
) -> list[str]:
    reasons = []
    coordinate_missing = record.latitude is None or record.longitude is None
    coordinate_nonfinite = (
        not coordinate_missing
        and (
            not math.isfinite(record.latitude)
            or not math.isfinite(record.longitude)
        )
    )
    coordinate_outside_wgs84 = (
        not coordinate_missing
        and not coordinate_nonfinite
        and (
            not (-90 <= record.latitude <= 90)
            or not (-180 <= record.longitude <= 180)
        )
    )
    coordinate_zero = (
        not coordinate_missing
        and record.latitude == 0
        and record.longitude == 0
    )
    if (
        coordinate_missing
        or coordinate_nonfinite
        or coordinate_outside_wgs84
        or coordinate_zero
    ):
        reasons.append("INVALID_COORDINATE")
    if record.timestamp is None:
        reasons.append("MISSING_TIMESTAMP")
    if record.yield_wet_t_ha is None:
        reasons.append("MISSING_WET_YIELD")
    elif record.yield_wet_t_ha < 0:
        reasons.append("NEGATIVE_WET_YIELD")
    elif record.yield_wet_t_ha > maximum_yield_t_ha:
        reasons.append("WET_YIELD_ABOVE_LIMIT")
    if record.moisture_pct is not None and not (0 <= record.moisture_pct <= 100):
        reasons.append("MOISTURE_OUT_OF_RANGE")
    return reasons
