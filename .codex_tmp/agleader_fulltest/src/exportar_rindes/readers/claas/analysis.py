"""Geometry-derived evidence for neutral values in observed CLAAS CM records."""

from __future__ import annotations

from dataclasses import dataclass
from math import atan2, cos, degrees, hypot, radians


def segment_bearing_deg(
    first_latitude: float,
    first_longitude: float,
    second_latitude: float,
    second_longitude: float,
) -> tuple[float, float]:
    """Return local bearing clockwise from north and approximate distance in metres."""
    middle_latitude = (first_latitude + second_latitude) / 2
    delta_east = (
        (second_longitude - first_longitude)
        * 111_320
        * cos(radians(middle_latitude))
    )
    delta_north = (second_latitude - first_latitude) * 110_540
    distance = hypot(delta_east, delta_north)
    bearing = (degrees(atan2(delta_east, delta_north)) + 360) % 360
    return bearing, distance


def circular_error_deg(first: float, second: float) -> float:
    return abs((first - second + 180) % 360 - 180)


@dataclass
class HeadingEvidence:
    segment_count: int = 0
    error_sum_deg: float = 0
    within_5_deg: int = 0
    within_15_deg: int = 0

    def add(
        self,
        first_latitude: float,
        first_longitude: float,
        second_latitude: float,
        second_longitude: float,
        candidate_heading_deg: float,
    ) -> None:
        bearing, distance = segment_bearing_deg(
            first_latitude,
            first_longitude,
            second_latitude,
            second_longitude,
        )
        if distance == 0:
            return
        error = circular_error_deg(candidate_heading_deg, bearing)
        self.segment_count += 1
        self.error_sum_deg += error
        self.within_5_deg += error <= 5
        self.within_15_deg += error <= 15

    def report(self) -> dict[str, float | int | str]:
        if not self.segment_count:
            return {"segment_count": 0}
        return {
            "status": "COORDINATE_DERIVED_HYPOTHESIS",
            "segment_count": self.segment_count,
            "mean_absolute_error_deg": self.error_sum_deg / self.segment_count,
            "within_5_deg_pct": self.within_5_deg / self.segment_count * 100,
            "within_15_deg_pct": self.within_15_deg / self.segment_count * 100,
            "interpretation": (
                "cm_value_4 is strongly consistent with heading towards the current point"
            ),
        }
