"""Collection-level inventory for multiple CLAAS TASKDATA directory exports."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from exportar_rindes.readers.claas.inspection import build_technical_inventory


def _is_export_directory(path: Path) -> bool:
    return path.is_dir() and any(
        item.is_file() and item.name.upper() == "TASKDATA.XML"
        for item in path.iterdir()
    )


def build_collection_inventory(source: Path) -> dict[str, Any]:
    source = Path(source)
    if not source.is_dir():
        raise ValueError("El inventario conjunto CLAAS requiere un directorio.")
    export_paths = sorted(item for item in source.iterdir() if _is_export_directory(item))
    if not export_paths:
        raise ValueError(f"{source}: no contiene carpetas TASKDATA exportadas.")

    exports = []
    data_signatures = set()
    taskdata_hashes = set()
    total_points = 0
    for path in export_paths:
        inventory = build_technical_inventory(path)
        members = inventory["files"]["members"]
        taskdata = next(
            item for item in members if Path(item["path"]).name.upper() == "TASKDATA.XML"
        )
        cm_members = sorted(
            item["sha256"] for item in members if item["extension"] == ".cm"
        )
        point_count = inventory["cm"]["point_count"]
        if point_count:
            data_signatures.add(tuple(cm_members))
        taskdata_hashes.add(taskdata["sha256"])
        total_points += point_count
        exports.append(
            {
                "directory": path.name,
                "classification": inventory["manufacturer_evidence"]["classification"],
                "file_count": inventory["files"]["count"],
                "total_bytes": inventory["files"]["total_bytes"],
                "taskdata_sha256": taskdata["sha256"],
                "task_count": inventory["isoxml"]["task_count"],
                "tlg_bin_count": inventory["isoxml"]["tlg_bin_count"],
                "tlg_nonempty_bin_count": inventory["isoxml"][
                    "tlg_nonempty_bin_count"
                ],
                "cm_file_count": inventory["cm"]["file_count"],
                "cm_point_count": point_count,
                "cm_sha256": cm_members,
            }
        )
    data_bearing = sum(item["cm_point_count"] > 0 for item in exports)
    independent = len(data_signatures)
    return {
        "schema_version": 1,
        "source": str(source),
        "classification": (
            "CLAAS"
            if all(item["classification"] == "CLAAS" for item in exports)
            else "MIXED_OR_UNCONFIRMED"
        ),
        "counts": {
            "export_directories": len(exports),
            "unique_taskdata_files": len(taskdata_hashes),
            "data_bearing_exports": data_bearing,
            "independent_cm_signatures": independent,
            "total_cm_points_in_collection": total_points,
        },
        "completion_evidence": {
            "required_independent_exports": 2,
            "observed_independent_cm_exports": independent,
            "criterion_met": independent >= 2,
        },
        "exports": exports,
        "warnings": [
            "Una carpeta con TASKDATA.XML pero sin CM o TLG BIN no aporta un recorrido.",
            "La independencia CM se calcula con el conjunto de hashes SHA-256 de sus CM.",
            "La suma de puntos no implica independencia si dos exportaciones comparten CM.",
        ],
    }
