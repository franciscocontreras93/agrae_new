import sys

path = sys.argv[1]
with open(path, "r", encoding="utf-8-sig") as handle:
    rows = [line.rstrip("\r\n").split("\t") for line in handle if line.strip()]

print("rows", len(rows), "column counts", sorted({len(row) for row in rows}))
for row in rows:
    if row[0] in {"6", "19", "22", "44", "53", "71"}:
        print("\n", row[0], row[1], "columns", len(row))
        for index, value in enumerate(row):
            print(index, repr(value))
