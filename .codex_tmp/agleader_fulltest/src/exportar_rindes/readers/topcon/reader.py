from collections import Counter
from pathlib import Path
import zipfile

from exportar_rindes.core.models import InspectionResult
from exportar_rindes.readers.base import YieldReader
from exportar_rindes.readers.topcon.isoxml import iter_topcon_records


CANDIDATE_EXTENSIONS = {".xml", ".bin", ".gps", ".cov", ".dfr", ".wl", ".ini"}


class TopconReader(YieldReader):
    """Read the ISOXML portion of a TOPCON export."""

    def inspect(self, source: Path) -> InspectionResult:
        if not zipfile.is_zipfile(source):
            raise ValueError("La inspección TOPCON requiere un archivo ZIP válido.")
        with zipfile.ZipFile(source) as archive:
            files = [info for info in archive.infolist() if not info.is_dir()]
        extensions = Counter(Path(info.filename).suffix.lower() or "<sin_ext>" for info in files)
        candidates = [
            info.filename
            for info in files
            if Path(info.filename).suffix.lower() in CANDIDATE_EXTENSIONS
        ]
        return InspectionResult(
            manufacturer="TOPCON",
            source=source,
            file_count=len(files),
            total_bytes=sum(info.file_size for info in files),
            extensions=dict(sorted(extensions.items())),
            candidate_files=candidates,
            warnings=[
                "La lectura validada se limita a los time logs ISOXML TLG.",
                "Los formatos propietarios COV/DFR/GPS/WL se conservan sin interpretar.",
            ],
        )

    def read(self, source: Path):
        return list(iter_topcon_records(source))
