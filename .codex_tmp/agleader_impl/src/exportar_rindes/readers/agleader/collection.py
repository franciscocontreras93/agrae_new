"""Non-destructive access to the TAR collection embedded in AGDATA files."""

from contextlib import contextmanager
from pathlib import Path
import tarfile

AGDATA_SIGNATURE = b"AG LEADER TECHNOLOGY"


def is_agdata(path: Path) -> bool:
    path = Path(path)
    if not path.is_file():
        return False
    with path.open("rb") as handle:
        return handle.read(len(AGDATA_SIGNATURE)) == AGDATA_SIGNATURE


def tar_offset(path: Path) -> int:
    """Locate the first USTAR header without trusting a fixed offset."""
    with Path(path).open("rb") as handle:
        header = handle.read(64 * 1024)
    if not header.startswith(AGDATA_SIGNATURE):
        raise ValueError("La cabecera no corresponde a Ag Leader AGDATA.")
    marker = header.find(b"ustar")
    if marker >= 257:
        offset = marker - 257
        if offset >= 0:
            return offset
    raise ValueError("No se localizÃ³ la colecciÃ³n TAR interna de AGDATA.")


@contextmanager
def open_collection(path: Path):
    """Open the embedded TAR without extracting members to disk."""
    handle = Path(path).open("rb")
    try:
        handle.seek(tar_offset(path))
        archive = tarfile.open(fileobj=handle, mode="r:")
        try:
            yield archive
        finally:
            archive.close()
    finally:
        handle.close()


def safe_members(archive: tarfile.TarFile) -> list[tarfile.TarInfo]:
    return [member for member in archive.getmembers() if member.isfile()]
