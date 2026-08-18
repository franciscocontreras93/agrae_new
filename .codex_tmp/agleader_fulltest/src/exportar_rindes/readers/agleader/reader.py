from collections import Counter
from pathlib import Path

from exportar_rindes.core.models import InspectionResult, SourceRecord
from exportar_rindes.readers.agleader.collection import open_collection, safe_members
from exportar_rindes.readers.agleader.ilf2 import iter_ilf2_points
from exportar_rindes.readers.base import YieldReader


class AgLeaderReader(YieldReader):
    """Read the demonstrably decoded subset of Ag Leader AGDATA/ILF2."""

    def inspect(self, source: Path) -> InspectionResult:
        with open_collection(source) as archive:
            files = safe_members(archive)
        extensions = Counter(Path(item.name).suffix.lower() or "<sin_ext>" for item in files)
        candidates = [item.name for item in files if item.name.lower().endswith(".ilf2")]
        return InspectionResult(
            manufacturer="AGLEADER",
            source=Path(source),
            file_count=len(files),
            total_bytes=sum(item.size for item in files),
            extensions=dict(sorted(extensions.items())),
            candidate_files=candidates,
            warnings=[
                "Hito experimental validado con una sola exportaciÃ³n Ag Leader Integra.",
                "Se decodifican contenedor, registros, fecha y coordenadas WGS84.",
                "Los canales agronÃ³micos se conservan como sensor_01..sensor_N sin inferir unidades.",
                "Rendimiento, humedad, velocidad y ancho requieren comparaciÃ³n con Ag Leader SMS.",
            ],
        )

    def read(self, source: Path) -> list[SourceRecord]:
        records = []
        with open_collection(source) as archive:
            for member in safe_members(archive):
                if not member.name.lower().endswith(".ilf2"):
                    continue
                handle = archive.extractfile(member)
                if handle is None:
                    continue
                try:
                    for row in iter_ilf2_points(handle.read()):
                        records.append(SourceRecord(
                            manufacturer="AGLEADER",
                            source_file=Path(source),
                            source_record=row["source_record"],
                            timestamp=row["timestamp"],
                            longitude=row["longitude"],
                            latitude=row["latitude"],
                            metadata={"archive_member": member.name, **row},
                        ))
                except ValueError:
                    continue
        return records
