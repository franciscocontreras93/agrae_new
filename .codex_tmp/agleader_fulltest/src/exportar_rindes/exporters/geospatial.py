from pathlib import Path
import geopandas as gpd
import pandas as pd

from exportar_rindes.core.models import SourceRecord


def to_geodataframe(records: list[SourceRecord], target_crs: str = "EPSG:25830") -> gpd.GeoDataFrame:
    rows = [record.model_dump() for record in records]
    frame = pd.DataFrame(rows)
    if frame.empty:
        raise ValueError("No hay registros para exportar.")
    valid = frame["longitude"].notna() & frame["latitude"].notna()
    frame = frame.loc[valid].copy()
    geometry = gpd.points_from_xy(frame.longitude, frame.latitude, crs="EPSG:4326")
    return gpd.GeoDataFrame(frame, geometry=geometry).to_crs(target_crs)


def write_gpkg(gdf: gpd.GeoDataFrame, output: Path, layer: str = "yield_points") -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(output, layer=layer, driver="GPKG")
