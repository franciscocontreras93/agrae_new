"""Conservative decoder for the CLAAS ``.CM`` structure observed in the samples."""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
import struct
from typing import BinaryIO, Iterator


MAGIC = b"\x00\x05"
POINT_TAG = 3
BLOCK_TAG = 4
POINT_STRUCT = struct.Struct("<ddd f")
BLOCK_STRUCT = struct.Struct("<B i d f")


@dataclass(frozen=True)
class CmHeader:
    task_code: int
    sentinel: int
    secondary_code: int
    device_identifier: str
    header_code: int
    header_flag: int
    header_value_double: float
    header_value_float: float
    data_offset: int


@dataclass(frozen=True)
class CmPoint:
    record_number: int
    byte_offset: int
    latitude: float
    longitude: float
    value_double_3: float
    value_float_4: float
    block_number: int | None


def _read_exact(handle: BinaryIO, size: int, context: str) -> bytes:
    value = handle.read(size)
    if len(value) != size:
        raise ValueError(f"{context}: estructura CM truncada.")
    return value


def read_cm_header(handle: BinaryIO, context: str = "CM") -> CmHeader:
    if _read_exact(handle, 2, context) != MAGIC:
        raise ValueError(f"{context}: firma CM no reconocida.")
    task_code, sentinel, secondary_code, identifier_length = struct.unpack(
        "<iiii", _read_exact(handle, 16, context)
    )
    if not 1 <= identifier_length <= 1024:
        raise ValueError(f"{context}: longitud de identificador no válida.")
    identifier = _read_exact(handle, identifier_length, context).decode(
        "ascii", errors="strict"
    )
    header_code = struct.unpack("<i", _read_exact(handle, 4, context))[0]
    header_flag = _read_exact(handle, 1, context)[0]
    value_double, value_float = struct.unpack(
        "<d f", _read_exact(handle, 12, context)
    )
    return CmHeader(
        task_code=task_code,
        sentinel=sentinel,
        secondary_code=secondary_code,
        device_identifier=identifier,
        header_code=header_code,
        header_flag=header_flag,
        header_value_double=value_double,
        header_value_float=value_float,
        data_offset=handle.tell(),
    )


def iter_cm_points(path: Path) -> Iterator[tuple[CmHeader, CmPoint]]:
    """Yield only coordinate records whose layout is reproducible in every sample."""
    path = Path(path)
    context = str(path)
    with path.open("rb") as handle:
        header = read_cm_header(handle, context)
        record_number = 0
        block_number = None
        while True:
            offset = handle.tell()
            tag_bytes = handle.read(1)
            if not tag_bytes:
                raise ValueError(f"{context}: falta el terminador CM.")
            tag = tag_bytes[0]
            if tag == POINT_TAG:
                latitude, longitude, value_3, value_4 = POINT_STRUCT.unpack(
                    _read_exact(handle, POINT_STRUCT.size, f"{context} offset {offset}")
                )
                if not all(
                    math.isfinite(value)
                    for value in (latitude, longitude, value_3, value_4)
                ):
                    raise ValueError(f"{context}: valor no finito en offset {offset}.")
                if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
                    raise ValueError(
                        f"{context}: coordenada fuera de WGS84 en offset {offset}."
                    )
                record_number += 1
                yield header, CmPoint(
                    record_number=record_number,
                    byte_offset=offset,
                    latitude=latitude,
                    longitude=longitude,
                    value_double_3=value_3,
                    value_float_4=value_4,
                    block_number=block_number,
                )
            elif tag == BLOCK_TAG:
                marker = handle.read(1)
                if not marker:
                    return
                subtype, block_number, _, _ = BLOCK_STRUCT.unpack(
                    marker
                    + _read_exact(
                        handle,
                        BLOCK_STRUCT.size - 1,
                        f"{context} offset {offset}",
                    )
                )
                if subtype != 2:
                    raise ValueError(
                        f"{context}: subtipo de bloque CM {subtype} no observado "
                        f"en offset {offset}."
                    )
            else:
                raise ValueError(
                    f"{context}: etiqueta CM {tag} no reconocida en offset {offset}."
                )
