"""Auditable first-milestone decoder for Ag Leader ILF2 logs.

Only framing, timestamps and WGS84 positions demonstrated by the supplied
sample are interpreted. Agronomic channels remain numbered until comparison
with an official SMS export proves their meaning and units.
"""

from datetime import datetime, timezone
import math
import struct
import zlib

ILF2_HEADER_SIZE = 272
GPS_GUID = bytes.fromhex("b463d1b9cbb2bd47b6d4fec1894ba6a5")
SENSOR_GUID = bytes.fromhex("a3edeee7ee0bdf45a550a11c7fc6d664")


def decompress_ilf2(data: bytes) -> bytes:
    if len(data) <= ILF2_HEADER_SIZE:
        raise ValueError("ILF2 demasiado corto.")
    try:
        return zlib.decompress(data[ILF2_HEADER_SIZE:], -zlib.MAX_WBITS)
    except zlib.error as error:
        raise ValueError(f"Flujo DEFLATE ILF2 no reconocido: {error}") from error


def iter_framed_records(decoded: bytes):
    """Yield (byte_offset, type_bytes, payload) from length-framed records."""
    cursor = 0
    limit = len(decoded)
    while cursor + 12 <= limit:
        marker = decoded.find(b"\xff\xff", cursor)
        if marker < 0 or marker + 12 > limit:
            return
        payload_size = struct.unpack_from("<I", decoded, marker + 4)[0]
        end = marker + 12 + payload_size
        if payload_size < 16 or end > limit:
            cursor = marker + 2
            continue
        yield marker, decoded[marker + 8:marker + 12], decoded[marker + 12:end]
        cursor = end


def _double(payload: bytes, offset: int):
    if offset + 8 > len(payload):
        return None
    value = struct.unpack_from("<d", payload, offset)[0]
    return value if math.isfinite(value) else None


def decode_gps(payload: bytes):
    if len(payload) < 56 or payload[:16] != GPS_GUID:
        return None
    epoch_ms = struct.unpack_from("<Q", payload, 16)[0]
    longitude = _double(payload, 32)
    latitude = _double(payload, 40)
    if longitude is None or latitude is None:
        return None
    if not (-180 <= longitude <= 180 and -90 <= latitude <= 90):
        return None
    try:
        timestamp = datetime.fromtimestamp(epoch_ms / 1000.0, timezone.utc)
    except (OverflowError, OSError, ValueError):
        timestamp = None
    return {
        "timestamp": timestamp,
        "epoch_ms": epoch_ms,
        "longitude": longitude,
        "latitude": latitude,
        "altitude_m": _double(payload, 48),
        "gps_aux_01": _double(payload, 76),
        "gps_aux_02": _double(payload, 84),
        "gps_aux_03": _double(payload, 100),
        "gps_aux_04": _double(payload, 108),
        "gps_aux_05": _double(payload, 116),
    }


def decode_sensor_channels(payload: bytes):
    if len(payload) < 32 or payload[:16] != SENSOR_GUID:
        return None
    first_count = struct.unpack_from("<I", payload, 28)[0]
    if first_count > 64 or 32 + first_count * 8 > len(payload):
        return None
    values = [_double(payload, 32 + index * 8) for index in range(first_count)]
    next_offset = 32 + first_count * 8
    if next_offset + 4 <= len(payload):
        second_count = struct.unpack_from("<I", payload, next_offset)[0]
        values_offset = next_offset + 4
        if second_count <= 64 and values_offset + second_count * 8 <= len(payload):
            values.extend(
                _double(payload, values_offset + index * 8)
                for index in range(second_count)
            )
    return values


def iter_ilf2_points(data: bytes):
    """Associate each sensor message with the most recent valid GPS message."""
    decoded = decompress_ilf2(data)
    last_gps = None
    record_number = 0
    for offset, record_type, payload in iter_framed_records(decoded):
        record_number += 1
        gps = decode_gps(payload)
        if gps is not None:
            last_gps = gps
            continue
        channels = decode_sensor_channels(payload)
        if channels is None or last_gps is None:
            continue
        row = dict(last_gps)
        row.update({
            "source_record": record_number,
            "byte_offset": offset,
            "record_type": record_type.hex(),
            "sensor_count": len(channels),
        })
        for index, value in enumerate(channels, start=1):
            row[f"sensor_{index:02d}"] = value
        yield row
