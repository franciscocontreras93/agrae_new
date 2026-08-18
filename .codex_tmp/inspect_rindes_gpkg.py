import sqlite3
import sys

import numpy as np
import pandas as pd


path = sys.argv[1]
connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
tables = [
    row[0]
    for row in connection.execute(
        "SELECT table_name FROM gpkg_contents WHERE data_type = 'features'"
    )
]

for table in tables:
    print(f"\n### {table}")
    print("schema=", list(connection.execute(f'PRAGMA table_info("{table}")')))
    frame = pd.read_sql_query(f'SELECT * FROM "{table}"', connection)
    print("rows=", len(frame))
    print("nulls=", {name: int(value) for name, value in frame.isna().sum().items() if value})

    numeric = frame.select_dtypes(include=np.number)
    print("numeric_stats")
    if not numeric.empty:
        print(numeric.describe(percentiles=[0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99]).T.to_string())

    for column in frame.select_dtypes(exclude=np.number).columns:
        if column == "geom":
            continue
        counts = frame[column].value_counts(dropna=False)
        print(
            "categorical",
            column,
            "unique=",
            frame[column].nunique(dropna=True),
            "top=",
            counts.head(15).to_dict(),
        )

    if "geom" in frame:
        print("duplicate_geom=", int(frame["geom"].duplicated().sum()))
    comparable = frame.drop(columns=[name for name in ("fid",) if name in frame])
    print("duplicate_rows_without_fid=", int(comparable.duplicated().sum()))

    if table in ("CAPA_JOIN_LOCALIZADA", "RINDES_UNIDOS"):
        valid = frame[
            frame["VRYIELDMAS"].notna()
            & frame["Moisture"].notna()
            & frame["cultivo"].notna()
        ].copy()
        valid["sample_area_m2"] = valid["DISTANCE"] * valid["SWATHWIDTH"]
        valid["estimated_mass_kg_if_t_ha"] = valid["VRYIELDMAS"] * valid["sample_area_m2"] / 10.0
        print("crop_summary")
        summary = valid.groupby(["idcultivo", "cultivo"]).agg(
            points=("fid", "size"),
            yield_p05=("VRYIELDMAS", lambda x: x.quantile(0.05)),
            yield_median=("VRYIELDMAS", "median"),
            yield_mean=("VRYIELDMAS", "mean"),
            yield_p95=("VRYIELDMAS", lambda x: x.quantile(0.95)),
            moisture_median=("Moisture", "median"),
            drymatter_median=("DRYMATTER", "median"),
            sampled_area_ha=("sample_area_m2", lambda x: x.sum() / 10000.0),
            estimated_mass_t=("estimated_mass_kg_if_t_ha", lambda x: x.sum() / 1000.0),
        )
        print(summary.to_string())
        print("correlations")
        print(valid[["VRYIELDMAS", "WetMass", "Moisture", "DRYMATTER", "DISTANCE", "SWATHWIDTH", "VEHICLSPEED"]].corr().to_string())

    if table == "RINDES_UNIDOS":
        frame["valid_basic"] = (
            frame["VRYIELDMAS"].notna()
            & frame["Moisture"].notna()
            & (frame["VRYIELDMAS"] > 0)
            & (frame["DISTANCE"] > 0)
            & (frame["SWATHWIDTH"] > 0)
        )
        frame["sample_area_m2"] = frame["DISTANCE"].fillna(0) * frame["SWATHWIDTH"].fillna(0)
        lots = frame.groupby("iddata", dropna=False).agg(
            idlote=("idlote", "first"),
            idexplotacion=("idexplotacion", "first"),
            idcultivo=("idcultivo", "first"),
            cultivo=("cultivo", "first"),
            area_ha=("area_ha", "first"),
            points_total=("fid", "size"),
            points_valid=("valid_basic", "sum"),
            sample_area_ha=("sample_area_m2", lambda x: x.sum() / 10000.0),
            yield_median=("VRYIELDMAS", "median"),
        )
        lots["valid_pct"] = 100 * lots["points_valid"] / lots["points_total"]
        lots["coverage_pct_raw"] = 100 * lots["sample_area_ha"] / lots["area_ha"]
        print("lot_count=", len(lots))
        print("lot_distribution")
        print(lots[["points_total", "points_valid", "valid_pct", "coverage_pct_raw"]].describe(percentiles=[.05,.1,.25,.5,.75,.9,.95]).to_string())
        print("lots_by_points_ascending")
        print(lots.sort_values("points_valid").head(30).to_string())

connection.close()
