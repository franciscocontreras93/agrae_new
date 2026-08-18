from collections import Counter
from pathlib import Path
import zipfile

from exportar_rindes.core.models import InspectionResult, SourceRecord
from exportar_rindes.readers.base import YieldReader


CANDIDATE_EXTENSIONS = {".ycs", ".ycc", ".yms", ".nav", ".gps", ".agf", ".agp"}


class CnhReader(YieldReader):
    """Inspector CNH inicial.

    La lectura binaria todavía no se considera validada. Este lector inventaría
    el contenido y evita generar coordenadas o rindes ficticios.
    """

    def inspect(self, source: Path) -> InspectionResult:
        if not zipfile.is_zipfile(source):
            raise ValueError("La versión inicial espera una exportación CNH comprimida en ZIP.")
        with zipfile.ZipFile(source) as archive:
            files = [info for info in archive.infolist() if not info.is_dir()]
        extensions = Counter(Path(info.filename).suffix.lower() or "<sin_ext>" for info in files)
        candidates = [
            info.filename for info in files if Path(info.filename).suffix.lower() in CANDIDATE_EXTENSIONS
        ]
        return InspectionResult(
            manufacturer="CNH",
            source=source,
            file_count=len(files),
            total_bytes=sum(info.file_size for info in files),
            extensions=dict(sorted(extensions.items())),
            candidate_files=candidates,
            warnings=["Parser binario CNH pendiente de validación; no se exportan rindes todavía."],
        )

    def read(self, source: Path) -> list[SourceRecord]:
        raise NotImplementedError(
            "El parser binario CNH aún no está validado. Ejecuta primero el comando inspect."
        )
