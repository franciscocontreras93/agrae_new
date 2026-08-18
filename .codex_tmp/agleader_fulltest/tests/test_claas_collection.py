from pathlib import Path

from exportar_rindes.readers.claas.collection import build_collection_inventory
from test_claas_reader import make_claas_sample


def test_claas_collection_distinguishes_independent_cm_exports(tmp_path: Path) -> None:
    make_claas_sample(
        tmp_path / "first",
        task_number=2,
        latitude=41.44,
        longitude=-5.41,
    )
    make_claas_sample(
        tmp_path / "second",
        task_number=23,
        latitude=41.58,
        longitude=-5.33,
    )
    result = build_collection_inventory(tmp_path)
    assert result["classification"] == "CLAAS"
    assert result["counts"]["export_directories"] == 2
    assert result["counts"]["data_bearing_exports"] == 2
    assert result["counts"]["independent_cm_signatures"] == 2
    assert result["completion_evidence"]["criterion_met"] is True


def test_claas_collection_counts_metadata_only_export(tmp_path: Path) -> None:
    make_claas_sample(tmp_path / "with-data")
    metadata = tmp_path / "metadata-only"
    metadata.mkdir()
    (metadata / "TASKDATA.XML").write_text(
        '<ISO11783_TaskData ManagementSoftwareManufacturer="CLAAS"/>',
        encoding="utf-8",
    )
    result = build_collection_inventory(tmp_path)
    assert result["counts"]["export_directories"] == 2
    assert result["counts"]["data_bearing_exports"] == 1
    assert result["completion_evidence"]["criterion_met"] is False
