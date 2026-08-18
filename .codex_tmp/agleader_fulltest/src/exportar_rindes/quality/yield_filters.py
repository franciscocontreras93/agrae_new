"""Non-destructive yield filters based on documented Yield Editor concepts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class FilterSettings:
    """Explicit filter parameters; disabled filters never reject a point."""

    yield_range: bool = True
    min_yield_t_ha: float = 0.0
    max_yield_t_ha: float = 11.0
    speed_range: bool = True
    min_speed_m_s: float = 0.5
    max_speed_m_s: float = 4.0
    smooth_speed: bool = True
    max_speed_change_ratio: float = 0.20
    minimum_width: bool = True
    min_width_m: float = 2.7
    standard_deviation: bool = False
    max_yield_stddev: float = 3.0
    moisture_range: bool = True
    min_moisture_pct: float = 0.0
    max_moisture_pct: float = 40.0

    def validate(self) -> None:
        if self.min_yield_t_ha > self.max_yield_t_ha:
            raise ValueError("El rendimiento mínimo supera al máximo.")
        if self.min_speed_m_s < 0 or self.min_speed_m_s > self.max_speed_m_s:
            raise ValueError("El rango de velocidad no es válido.")
        if not 0 <= self.max_speed_change_ratio <= 10:
            raise ValueError("El cambio de velocidad debe ser una proporción válida.")
        if self.min_width_m < 0:
            raise ValueError("El ancho mínimo no puede ser negativo.")
        if self.max_yield_stddev <= 0:
            raise ValueError("El filtro STDY debe ser mayor que cero.")
        if self.min_moisture_pct < 0 or self.max_moisture_pct >= 100:
            raise ValueError("El rango de humedad debe estar entre 0 y 100%.")
        if self.min_moisture_pct > self.max_moisture_pct:
            raise ValueError("La humedad mínima supera a la máxima.")

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FilterState:
    previous_file: str | None = None
    previous_record: int | None = None
    previous_speed: float | None = None


def apply_filters(
    row: dict[str, Any],
    settings: FilterSettings,
    state: FilterState,
    *,
    yield_mean: float | None = None,
    yield_stddev: float | None = None,
) -> list[str]:
    """Return all filter codes triggered by one row and advance sequence state."""
    reasons: list[str] = []
    yield_value = row.get("yld12_th")
    speed = row.get("speed_hyp")
    width = row.get("width_hyp")
    moisture = row.get("moist_hyp")

    if settings.yield_range:
        if yield_value is None:
            reasons.append("MISS_YLD")
        elif yield_value < settings.min_yield_t_ha:
            reasons.append("MINY")
        elif yield_value > settings.max_yield_t_ha:
            reasons.append("MAXY")

    if settings.speed_range:
        if speed is None:
            reasons.append("MISS_SPD")
        elif speed < settings.min_speed_m_s:
            reasons.append("MINV")
        elif speed > settings.max_speed_m_s:
            reasons.append("MAXV")

    consecutive = (
        state.previous_file == row.get("src_file")
        and state.previous_record is not None
        and row.get("src_rec") == state.previous_record + 1
    )
    if (
        settings.smooth_speed
        and consecutive
        and speed is not None
        and state.previous_speed is not None
        and state.previous_speed > 0
        and abs(speed - state.previous_speed) / state.previous_speed
        > settings.max_speed_change_ratio
    ):
        reasons.append("SMV")

    if settings.minimum_width:
        if width is None:
            reasons.append("MISS_WID")
        elif width < settings.min_width_m:
            reasons.append("MINS")

    if settings.moisture_range:
        if moisture is None:
            reasons.append("MISS_MST")
        elif not settings.min_moisture_pct <= moisture <= settings.max_moisture_pct:
            reasons.append("MOIST")

    if (
        settings.standard_deviation
        and yield_value is not None
        and yield_mean is not None
        and yield_stddev is not None
        and yield_stddev > 0
        and abs(yield_value - yield_mean) > settings.max_yield_stddev * yield_stddev
    ):
        reasons.append("STDY")

    state.previous_file = row.get("src_file")
    state.previous_record = row.get("src_rec")
    state.previous_speed = speed
    return reasons
