"""Coordinate quality checks for the first CLAAS milestone."""

from __future__ import annotations

import math

from exportar_rindes.core.models import SourceRecord


def claas_rejection_reasons(record: SourceRecord) -> list[str]:
    if record.latitude is None or record.longitude is None:
        return ["INVALID_COORDINATE"]
    if not math.isfinite(record.latitude) or not math.isfinite(record.longitude):
        return ["INVALID_COORDINATE"]
    if not (-90 <= record.latitude <= 90 and -180 <= record.longitude <= 180):
        return ["INVALID_COORDINATE"]
    if record.latitude == 0 and record.longitude == 0:
        return ["INVALID_COORDINATE"]
    return []
