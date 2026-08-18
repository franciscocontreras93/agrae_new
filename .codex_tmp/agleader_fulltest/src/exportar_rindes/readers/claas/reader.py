from collections import Counter
from pathlib import Path

from exportar_rindes.core.models import InspectionResult, SourceRecord
from exportar_rindes.readers.base import YieldReader
from exportar_rindes.readers.claas.cm import iter_cm_points, read_cm_header
from exportar_rindes.readers.claas.context import load_claas_context


class ClaasReader(YieldReader):
    """Read the reproducibly verified coordinate records in CLAAS CM files."""

    def inspect(self, source: Path) -> InspectionResult:
        source = Path(source)
        if not source.is_dir():
            raise ValueError("La inspección CLAAS requiere un directorio TASKDATA.")
        files = [item for item in source.rglob("*") if item.is_file()]
        extensions = Counter(item.suffix.lower() or "<sin_ext>" for item in files)
        candidates = [
            str(item.relative_to(source))
            for item in files
            if item.suffix.lower() in {".xml", ".bin", ".cm", ".ini"}
        ]
        for item in (path for path in files if path.suffix.lower() == ".cm"):
            with item.open("rb") as handle:
                read_cm_header(handle, str(item))
        return InspectionResult(
            manufacturer="CLAAS",
            source=source,
            file_count=len(files),
            total_bytes=sum(item.stat().st_size for item in files),
            extensions=dict(sorted(extensions.items())),
            candidate_files=candidates,
            warnings=[
                "Los TLG BIN observados están vacíos; no se atribuyen datos ISOXML inexistentes.",
                "CM solo aporta coordenadas verificadas; sus otros valores siguen sin semántica.",
                "No hay DDI de rendimiento ni humedad declarados en estas muestras.",
            ],
        )

    def iter_records(self, source: Path):
        source = Path(source)
        context = load_claas_context(source)
        cm_files = sorted(
            item for item in source.rglob("*") if item.suffix.lower() == ".cm"
        )
        for cm_path in cm_files:
            for header, point in iter_cm_points(cm_path):
                task = context.tasks.get(abs(header.task_code))
                yield SourceRecord(
                    manufacturer="CLAAS",
                    source_file=source,
                    source_record=point.record_number,
                    longitude=point.longitude,
                    latitude=point.latitude,
                    field=task.field if task else None,
                    machine=context.machine,
                    metadata={
                        "source_member": str(cm_path.relative_to(source)),
                        "byte_offset": point.byte_offset,
                        "task_code": header.task_code,
                        "task_identifier": task.identifier if task else None,
                        "task_designator": task.designator if task else None,
                        "task_time_ranges": list(task.time_ranges) if task else [],
                        "cm_device_identifier": header.device_identifier,
                        "cm_value_double_3": point.value_double_3,
                        "cm_value_float_4": point.value_float_4,
                        "cm_block_number": point.block_number,
                        "crs": "EPSG:4326",
                    },
                )

    def read(self, source: Path):
        return list(self.iter_records(source))
