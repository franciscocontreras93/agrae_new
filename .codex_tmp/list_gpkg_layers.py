import sqlite3
import sys

path = sys.argv[1]
connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)

for table_name, data_type, identifier, srs_id in connection.execute(
    "SELECT table_name, data_type, identifier, srs_id FROM gpkg_contents ORDER BY table_name"
):
    print(f"\n### {table_name} | {data_type} | {identifier} | EPSG:{srs_id}")
    if data_type == "features":
        geometry = connection.execute(
            "SELECT column_name, geometry_type_name FROM gpkg_geometry_columns WHERE table_name = ?",
            (table_name,),
        ).fetchone()
        print("geometry=", geometry)
        print("rows=", connection.execute(f'SELECT COUNT(*) FROM "{table_name}"').fetchone()[0])
        print("fields=")
        for column in connection.execute(f'PRAGMA table_info("{table_name}")'):
            print(f"  {column[1]} | {column[2]} | notnull={column[3]} | pk={column[5]}")

connection.close()
