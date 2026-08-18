from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from exportar_rindes.core.detector import detect_manufacturer
from exportar_rindes.readers.claas import ClaasReader
from exportar_rindes.readers.cnh import CnhReader
from exportar_rindes.readers.topcon import TopconReader
from exportar_rindes.readers.agleader import AgLeaderReader

app = typer.Typer(help="Conversor extensible de mapas de rendimiento.")
console = Console()


@app.command()
def inspect(source: Path, json_output: Path | None = None) -> None:
    """Detecta el fabricante e inventaría una exportación."""
    manufacturer = detect_manufacturer(source)
    readers = {
        "CNH": CnhReader,
        "CLAAS": ClaasReader,
        "TOPCON": TopconReader,
        "AGLEADER": AgLeaderReader,
    }
    if manufacturer not in readers:
        raise typer.BadParameter(f"Formato detectado: {manufacturer}. No hay lector iniciado.")
    result = readers[manufacturer]().inspect(source)
    table = Table(title=f"Inspección {result.manufacturer}")
    table.add_column("Indicador")
    table.add_column("Valor")
    table.add_row("Archivos", str(result.file_count))
    table.add_row("Tamaño", f"{result.total_bytes / 1024 / 1024:.2f} MB")
    table.add_row("Candidatos", str(len(result.candidate_files)))
    console.print(table)
    for warning in result.warnings:
        console.print(f"[yellow]Aviso:[/yellow] {warning}")
    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(result.model_dump_json(indent=2), encoding="utf-8")
        console.print(f"Inventario guardado en {json_output}")


@app.command()
def convert(source: Path, output: Path = Path("outputs/rindes.gpkg")) -> None:
    """Convierte una exportación validada al modelo geoespacial común."""
    manufacturer = detect_manufacturer(source)
    if manufacturer == "CNH":
        CnhReader().read(source)
    elif manufacturer == "CLAAS":
        from exportar_rindes.exporters.claas_gpkg import write_claas_gpkg

        write_claas_gpkg(source, output)
        console.print(f"GeoPackage guardado en {output}")
        return
    elif manufacturer == "TOPCON":
        from exportar_rindes.exporters.topcon_gpkg import write_topcon_gpkg

        write_topcon_gpkg(source, output)
        console.print(f"GeoPackage guardado en {output}")
        return
    elif manufacturer == "AGLEADER":
        from exportar_rindes.exporters.agleader_gpkg import write_agleader_gpkg

        report = write_agleader_gpkg(source, output)
        console.print(f"GeoPackage experimental guardado en {output}")
        console.print(
            "[yellow]Advertencia:[/yellow] coordenadas y canales sensor_XX; "
            "su significado agronÃ³mico aÃºn no estÃ¡ confirmado."
        )
        console.print(f"Puntos exportados: {report['counts'].get('raw_points', 0)}")
        return
    raise typer.Exit(code=2)


if __name__ == "__main__":
    app()
