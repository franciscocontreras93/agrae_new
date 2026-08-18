"""Evidence-labelled monitor detection and default filter profiles."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
import re
import struct
from typing import Any
import zipfile

from exportar_rindes.quality.yield_filters import FilterSettings
from exportar_rindes.readers.cnh.record_analysis import RECORD_SIZES


@dataclass(frozen=True)
class MonitorDetection:
    family: str
    probable_monitor: str
    confidence: str
    machine_software: str | None
    yield_software: str | None
    onboard_software: str | None
    dominant_width_m: float | None
    evidence: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FilterPreset:
    id: str
    title: str
    description: str
    confidence: str
    settings: FilterSettings

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "confidence": self.confidence,
            "settings": self.settings.as_dict(),
        }


VERSION_PATTERNS = {
    "machine": re.compile(r"Cosechadora CX/CR\.exe.*?Version\s+([0-9.]+)", re.I),
    "yield": re.compile(r"Monitor rendimiento\.dll.*?Version\s+([0-9.]+)", re.I),
    "onboard": re.compile(r"Ordenador de a bordo\.dll.*?Version\s+([0-9.]+)", re.I),
}


def _software_evidence(archive: zipfile.ZipFile) -> tuple[dict[str, str], list[str]]:
    versions: dict[str, str] = {}
    evidence: list[str] = []
    for info in archive.infolist():
        if not info.filename.lower().endswith(".txt"):
            continue
        with archive.open(info) as handle:
            tail = b""
            while chunk := handle.read(1024 * 1024):
                tail = (tail + chunk)[-131_072:]
        text = tail.decode("utf-8", "replace")
        for key, pattern in VERSION_PATTERNS.items():
            if key in versions:
                continue
            match = pattern.search(text)
            if match:
                versions[key] = match.group(1)
                evidence.append(f"{key} software {match.group(1)} in {info.filename}")
        if len(versions) == len(VERSION_PATTERNS):
            break
    return versions, evidence


def _dominant_width(archive: zipfile.ZipFile) -> float | None:
    counts: Counter[int] = Counter()
    size = RECORD_SIZES[".tlt"]
    for info in archive.infolist():
        if Path(info.filename).suffix.lower() != ".tlt":
            continue
        with archive.open(info) as handle:
            while record := handle.read(size):
                if len(record) != size:
                    break
                value = struct.unpack_from("<H", record, 39)[0]
                if 0 < value < 65_535:
                    counts[value] += 1
    return counts.most_common(1)[0][0] / 100 if counts else None


def detect_monitor(source: Path) -> MonitorDetection:
    """Detect only what is supported by CN1 structure and explicit log evidence."""
    source = Path(source)
    if not zipfile.is_zipfile(source):
        raise ValueError("El archivo no es un ZIP válido.")
    with zipfile.ZipFile(source) as archive:
        cn1 = any(".cn1/" in info.filename.lower() for info in archive.infolist())
        if not cn1:
            raise ValueError("No se ha detectado una estructura CN1.")
        versions, evidence = _software_evidence(archive)
        width = _dominant_width(archive)
    if width is not None:
        evidence.append(f"dominant candidate work width {width:.2f} m")
    is_cxcr = "machine" in versions
    return MonitorDetection(
        family="CNH CN1 (AFS Pro 700 / IntelliView IV)",
        probable_monitor="New Holland IntelliView IV" if is_cxcr else "CNH CN1 display",
        confidence="medium" if is_cxcr else "family-only",
        machine_software=f"CX/CR {versions['machine']}" if is_cxcr else None,
        yield_software=versions.get("yield"),
        onboard_software=versions.get("onboard"),
        dominant_width_m=width,
        evidence=tuple(evidence),
    )


def presets_for_monitor(detection: MonitorDetection) -> list[FilterPreset]:
    """Return transparent defaults; crop-dependent yield range remains explicit."""
    full_width = detection.dominant_width_m or 5.4
    half_width = round(full_width * 0.5, 2)
    conservative_width = round(full_width * 0.3, 2)
    automatic_title = (
        "CX/CR · IntelliView IV probable"
        if detection.probable_monitor == "New Holland IntelliView IV"
        else "CNH CN1 genérico"
    )
    return [
        FilterPreset(
            "auto_monitor",
            automatic_title,
            "Equilibrado; ancho mínimo adaptado al ancho dominante del archivo.",
            detection.confidence,
            FilterSettings(min_width_m=half_width),
        ),
        FilterPreset(
            "cnh_cn1_generic",
            "CNH CN1 genérico",
            "Más tolerante cuando no se conoce la cosechadora o configuración.",
            "family",
            FilterSettings(
                min_speed_m_s=0.3,
                max_speed_m_s=5.0,
                max_speed_change_ratio=0.30,
                min_width_m=half_width,
            ),
        ),
        FilterPreset(
            "conservative",
            "Conservador",
            "Descarta solo anomalías muy claras y conserva más observaciones.",
            "generic",
            FilterSettings(
                min_speed_m_s=0.2,
                max_speed_m_s=6.0,
                max_speed_change_ratio=0.50,
                min_width_m=conservative_width,
                max_moisture_pct=60.0,
            ),
        ),
        FilterPreset(
            "research",
            "Investigación · estricto",
            "Añade STDY=3; requiere dos lecturas y revisión visual posterior.",
            "generic",
            FilterSettings(min_width_m=half_width, standard_deviation=True),
        ),
    ]


def resolve_preset(source: Path, preset_id: str) -> tuple[MonitorDetection, FilterPreset]:
    detection = detect_monitor(source)
    presets = presets_for_monitor(detection)
    selected = next((preset for preset in presets if preset.id == preset_id), None)
    if selected is None:
        raise ValueError("Perfil de filtros desconocido.")
    return detection, selected
