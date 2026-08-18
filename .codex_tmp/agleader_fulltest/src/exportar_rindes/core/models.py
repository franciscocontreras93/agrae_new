from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class SourceRecord(BaseModel):
    manufacturer: str
    source_file: Path
    source_record: int | None = None
    timestamp: datetime | None = None
    longitude: float | None = None
    latitude: float | None = None
    yield_wet_t_ha: float | None = None
    yield_dry_t_ha: float | None = None
    moisture_pct: float | None = None
    speed_kmh: float | None = None
    width_m: float | None = None
    crop: str | None = None
    field: str | None = None
    machine: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class InspectionResult(BaseModel):
    manufacturer: str
    source: Path
    file_count: int
    total_bytes: int
    extensions: dict[str, int]
    candidate_files: list[str]
    warnings: list[str] = Field(default_factory=list)
