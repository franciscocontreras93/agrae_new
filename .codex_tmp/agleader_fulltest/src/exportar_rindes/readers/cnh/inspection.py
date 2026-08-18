"""Reproducible, non-decoding inspection of CNH ZIP exports."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
import hashlib
from pathlib import Path, PurePosixPath
import re
from typing import Any, BinaryIO
import zipfile


HEADER_BYTES = 32
CHUNK_BYTES = 1024 * 1024
LOG_SUFFIXES = {".txt"}
TIMESTAMP_RE = re.compile(
    rb"^(?P<date>\d{2}/\d{2}/\d{4})\s+(?P<time>\d{2}:\d{2}:\d{2})\s+\d{2}\s"
)
GEOGRAPHIC_PATTERNS = (
    ("nmea_sentence", re.compile(r"\$G[PN][A-Z]{3}\b")),
    (
        "labelled_coordinate",
        re.compile(r"(?i)\b(?:lat(?:itude)?|lon(?:gitude)?|coord(?:inate|enada)s?)\b"),
    ),
    (
        "hemisphere_pair",
        re.compile(
            r"(?i)\b\d{1,2}(?:\.\d+)?\s*[NS]\b.*\b\d{1,3}(?:\.\d+)?\s*[EW]\b"
        ),
    ),
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_binary_member(handle: BinaryIO) -> tuple[str, bytes]:
    digest = hashlib.sha256()
    header = bytearray()
    for chunk in iter(lambda: handle.read(CHUNK_BYTES), b""):
        digest.update(chunk)
        if len(header) < HEADER_BYTES:
            header.extend(chunk[: HEADER_BYTES - len(header)])
    return digest.hexdigest(), bytes(header)


def _timestamp_value(match: re.Match[bytes]) -> tuple[str, datetime]:
    value = f"{match.group('date').decode()} {match.group('time').decode()}"
    return value, datetime.strptime(value, "%m/%d/%Y %H:%M:%S")


def _read_log_member(
    handle: BinaryIO, path: str, geographic_evidence_limit: int
) -> tuple[str, bytes, dict[str, Any], list[dict[str, Any]]]:
    digest = hashlib.sha256()
    header = bytearray()
    line_count = 0
    nonempty_line_count = 0
    timestamped_line_count = 0
    invalid_utf8_line_count = 0
    first_timestamp: tuple[str, datetime, int, str] | None = None
    last_timestamp: tuple[str, datetime, int, str] | None = None
    geographic_evidence: list[dict[str, Any]] = []

    for line_number, raw_line in enumerate(handle, 1):
        digest.update(raw_line)
        if len(header) < HEADER_BYTES:
            header.extend(raw_line[: HEADER_BYTES - len(header)])
        line_count += 1
        if raw_line.strip():
            nonempty_line_count += 1
        match = TIMESTAMP_RE.match(raw_line)
        try:
            text = raw_line.decode("utf-8").rstrip("\r\n")
        except UnicodeDecodeError:
            invalid_utf8_line_count += 1
            text = raw_line.decode("utf-8", errors="replace").rstrip("\r\n")
        if match:
            timestamped_line_count += 1
            value, parsed = _timestamp_value(match)
            evidence = (value, parsed, line_number, text[:500])
            if first_timestamp is None or parsed < first_timestamp[1]:
                first_timestamp = evidence
            if last_timestamp is None or parsed > last_timestamp[1]:
                last_timestamp = evidence
        if len(geographic_evidence) < geographic_evidence_limit:
            for rule, pattern in GEOGRAPHIC_PATTERNS:
                if pattern.search(text):
                    geographic_evidence.append(
                        {
                            "path": path,
                            "line_number": line_number,
                            "rule": rule,
                            "excerpt": text[:500],
                        }
                    )
                    break

    def timestamp_evidence(
        item: tuple[str, datetime, int, str] | None,
    ) -> dict[str, Any] | None:
        if item is None:
            return None
        return {"value": item[0], "line_number": item[2], "excerpt": item[3]}

    summary = {
        "path": path,
        "encoding_observation": (
            "utf-8" if invalid_utf8_line_count == 0 else "utf-8-with-invalid-sequences"
        ),
        "invalid_utf8_line_count": invalid_utf8_line_count,
        "line_count": line_count,
        "nonempty_line_count": nonempty_line_count,
        "timestamped_line_count": timestamped_line_count,
        "first_timestamp_evidence": timestamp_evidence(first_timestamp),
        "last_timestamp_evidence": timestamp_evidence(last_timestamp),
    }
    return digest.hexdigest(), bytes(header), summary, geographic_evidence


def build_technical_inventory(
    source: Path, *, geographic_evidence_limit: int = 100
) -> dict[str, Any]:
    """Inventory a CNH ZIP without assigning semantics to proprietary binary fields."""
    source = Path(source)
    if not zipfile.is_zipfile(source):
        raise ValueError("La inspección técnica CNH requiere un archivo ZIP válido.")

    archive_size = source.stat().st_size
    archive_sha256 = _sha256_file(source)
    extensions: Counter[str] = Counter()
    extension_bytes: defaultdict[str, dict[str, int]] = defaultdict(
        lambda: {"uncompressed_bytes": 0, "compressed_bytes": 0}
    )
    top_level: Counter[str] = Counter()
    members: list[dict[str, Any]] = []
    logs: list[dict[str, Any]] = []
    geographic_evidence: list[dict[str, Any]] = []
    directory_count = 0

    with zipfile.ZipFile(source) as archive:
        for info in archive.infolist():
            if info.is_dir():
                directory_count += 1
                continue
            posix_path = PurePosixPath(info.filename)
            suffix = posix_path.suffix.lower() or "<sin_ext>"
            extensions[suffix] += 1
            extension_bytes[suffix]["uncompressed_bytes"] += info.file_size
            extension_bytes[suffix]["compressed_bytes"] += info.compress_size
            top_level[posix_path.parts[0] if posix_path.parts else "<root>"] += 1

            remaining_evidence = max(0, geographic_evidence_limit - len(geographic_evidence))
            with archive.open(info) as handle:
                if suffix in LOG_SUFFIXES:
                    member_sha256, header, log_summary, found = _read_log_member(
                        handle, info.filename, remaining_evidence
                    )
                    logs.append(log_summary)
                    geographic_evidence.extend(found)
                else:
                    member_sha256, header = _read_binary_member(handle)
            members.append(
                {
                    "path": info.filename,
                    "extension": suffix,
                    "uncompressed_bytes": info.file_size,
                    "compressed_bytes": info.compress_size,
                    "crc32": f"{info.CRC:08x}",
                    "sha256": member_sha256,
                    "header_hex": header.hex(" "),
                    "zip_datetime": "%04d-%02d-%02dT%02d:%02d:%02d" % info.date_time,
                }
            )

    first_items = [
        (log["first_timestamp_evidence"]["value"], log["path"])
        for log in logs
        if log["first_timestamp_evidence"] is not None
    ]
    last_items = [
        (log["last_timestamp_evidence"]["value"], log["path"])
        for log in logs
        if log["last_timestamp_evidence"] is not None
    ]
    def parse_timestamp(item):
        return datetime.strptime(item[0], "%m/%d/%Y %H:%M:%S")
    earliest = min(first_items, key=parse_timestamp) if first_items else None
    latest = max(last_items, key=parse_timestamp) if last_items else None
    candidate_suffixes = {".ycs", ".ycc", ".yms", ".nav", ".gps", ".agf", ".agp"}

    return {
        "schema_version": 1,
        "scope": "structural inventory; proprietary binary fields are not decoded",
        "source": str(source.as_posix()),
        "archive": {"size_bytes": archive_size, "sha256": archive_sha256},
        "zip": {
            "file_count": len(members),
            "directory_count": directory_count,
            "total_uncompressed_bytes": sum(item["uncompressed_bytes"] for item in members),
            "total_compressed_bytes": sum(item["compressed_bytes"] for item in members),
            "top_level_file_counts": dict(sorted(top_level.items())),
            "extensions": {
                suffix: {"count": extensions[suffix], **extension_bytes[suffix]}
                for suffix in sorted(extensions)
            },
        },
        "candidate_members": [
            item for item in members if item["extension"] in candidate_suffixes
        ],
        "text_record_observations": {
            "definition": (
                "A possible text record is a non-empty line beginning with the observed "
                "MM/DD/YYYY HH:MM:SS plus two-digit level prefix."
            ),
            "log_file_count": len(logs),
            "line_count": sum(log["line_count"] for log in logs),
            "nonempty_line_count": sum(log["nonempty_line_count"] for log in logs),
            "timestamped_line_count": sum(log["timestamped_line_count"] for log in logs),
            "earliest_timestamp": (
                {"value": earliest[0], "path": earliest[1]} if earliest else None
            ),
            "latest_timestamp": {"value": latest[0], "path": latest[1]} if latest else None,
            "logs": logs,
        },
        "geographic_evidence": {
            "rules": [rule for rule, _ in GEOGRAPHIC_PATTERNS],
            "match_count_capped": len(geographic_evidence),
            "evidence_limit": geographic_evidence_limit,
            "matches": geographic_evidence,
        },
        "members": members,
        "warnings": [
            "No se asignan offsets, tipos, escalas, unidades ni coordenadas a datos binarios.",
            "Las extensiones candidatas son una clasificación por nombre, no una descodificación.",
        ],
    }
