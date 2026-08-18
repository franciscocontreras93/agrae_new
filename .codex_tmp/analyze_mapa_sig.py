import sqlite3
import sys

import pandas as pd

path = sys.argv[1]
connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
sig = pd.read_sql_query('SELECT * FROM "mapa_sig"', connection)
rindes = pd.read_sql_query(
    'SELECT iddata, idlote, idcultivo, cultivo, area_ha FROM "RINDES_UNIDOS"',
    connection,
)
connection.close()

print("MAPA SIG rows", len(sig), "iddata", sig["iddata"].nunique())
print("nulls", {k: int(v) for k, v in sig.isna().sum().items() if v})

for field in ["f_fondo", "f_cob1", "f_cob2", "f_cob3", "cultivo", "uf_etiqueta"]:
    print("\n", field, sig[field].value_counts(dropna=False).head(30).to_string())

lot_meta = rindes.groupby("iddata", as_index=False).first()
lot_meta["iddata"] = lot_meta["iddata"].astype(int)
sig["base_iddata"] = sig["iddata"].astype(str).str[:-2].astype(int)
summary = sig.groupby("base_iddata", as_index=False).agg(
    polygons=("fid", "size"),
    sig_area_ha=("area_ha", "sum"),
    prod_pond_min=("prod_ponderada", "min"),
    prod_pond_median=("prod_ponderada", "median"),
    prod_pond_max=("prod_ponderada", "max"),
    d_fondo_min=("d_fondo", "min"),
    d_fondo_max=("d_fondo", "max"),
    d_cob1_min=("d_cob1", "min"),
    d_cob1_max=("d_cob1", "max"),
    d_cob2_min=("d_cob2", "min"),
    d_cob2_max=("d_cob2", "max"),
    d_cob3_min=("d_cob3", "min"),
    d_cob3_max=("d_cob3", "max"),
)
joined = lot_meta.merge(summary, left_on="iddata", right_on="base_iddata", how="outer", indicator=True)
joined["area_ratio_pct"] = 100 * joined["sig_area_ha"] / joined["area_ha"]
print("\nBY LOT")
print(joined.to_string(index=False))

print("\nFORMULA/DOSE COMBINATIONS")
print(
    sig[["f_fondo", "d_fondo", "f_cob1", "d_cob1", "f_cob2", "d_cob2", "f_cob3", "d_cob3"]]
    .drop_duplicates()
    .sort_values(["f_fondo", "f_cob1"], na_position="last")
    .to_string(index=False)
)

connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
measurements = pd.read_sql_query(
    '''SELECT VRYIELDMAS, WetMass, Moisture, DRYMATTER, idcultivo, cultivo
       FROM "RINDES_UNIDOS"
       WHERE VRYIELDMAS > 0 AND VRYIELDMAS < 100
         AND WetMass > 0 AND WetMass < 100
         AND Moisture >= 0 AND Moisture < 60''',
    connection,
)
connection.close()
measurements["wet_times_dm"] = measurements["WetMass"] * measurements["DRYMATTER"] / 100.0
measurements["wet_times_1mh"] = measurements["WetMass"] * (1 - measurements["Moisture"] / 100.0)
measurements["ratio_vry_wet"] = measurements["VRYIELDMAS"] / measurements["WetMass"]
measurements["err_dm_pct"] = 100 * (measurements["VRYIELDMAS"] - measurements["wet_times_dm"]).abs() / measurements["VRYIELDMAS"]
measurements["err_h_pct"] = 100 * (measurements["VRYIELDMAS"] - measurements["wet_times_1mh"]).abs() / measurements["VRYIELDMAS"]
print("\nYIELD FIELD RELATIONSHIPS")
print(measurements.groupby(["idcultivo", "cultivo"]).agg(
    points=("VRYIELDMAS", "size"),
    vry_median=("VRYIELDMAS", "median"),
    wet_median=("WetMass", "median"),
    ratio_vry_wet_median=("ratio_vry_wet", "median"),
    error_vs_wet_dm_pct_median=("err_dm_pct", "median"),
    error_vs_wet_1mh_pct_median=("err_h_pct", "median"),
).to_string())
