import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

from exportar_rindes.readers.cnh.inspection import build_technical_inventory


def test_technical_inventory_records_reproducible_evidence(tmp_path: Path):
    source = tmp_path / "sample.cn1.zip"
    log = (
        b"06/28/2025  11:06:06 00 LOG Opened\r\n"
        b"06/28/2025  11:06:07 04 Latitude=40.123 Longitude=-3.456\r\n"
    )
    binary = bytes.fromhex("43 4e 48 31 00 ff")
    with zipfile.ZipFile(source, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("export/log/session.txt", log)
        archive.writestr("export/COMBINES/COMB1/COMB1.ycs", binary)

    result = build_technical_inventory(source)

    assert result["archive"]["sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert result["zip"]["file_count"] == 2
    assert result["zip"]["extensions"][".ycs"]["count"] == 1
    assert result["candidate_members"][0]["header_hex"] == "43 4e 48 31 00 ff"
    observations = result["text_record_observations"]
    assert observations["timestamped_line_count"] == 2
    assert observations["earliest_timestamp"]["value"] == "06/28/2025 11:06:06"
    assert result["geographic_evidence"]["matches"][0]["line_number"] == 2
    assert result["members"][0]["sha256"] == hashlib.sha256(log).hexdigest()
    json.dumps(result)


def test_python_module_exposes_cli():
    completed = subprocess.run(
        [sys.executable, "-m", "exportar_rindes", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert "inspect" in completed.stdout
