r"""Estima producción por lote desde una capa puntual de monitor de cosecha.

Uso desde la consola Python de QGIS:

    exec(open(r"C:\ruta\calcular_produccion_lotes_rindes.py", encoding="utf-8").read())

El script no modifica la capa original ni la base de datos. Crea una tabla
temporal ``RINDES_RESUMEN_LOTES`` dentro del proyecto QGIS.

Hipótesis principal:
    ``VRYIELDMAS`` está expresado en toneladas por hectárea.

La producción estimada se obtiene como rendimiento medio ponderado por la
huella de cada observación (DISTANCE * SWATHWIDTH), multiplicado por la
superficie oficial del lote. También se entrega una estimación basada en la
mediana, que es la estadística usada por la guía de ajuste de rindes.
"""

from collections import defaultdict
from math import isfinite

from qgis.PyQt.QtCore import QVariant
from qgis.core import (
    QgsFeature,
    QgsFeatureRequest,
    QgsField,
    QgsProject,
    QgsVectorLayer,
)
from qgis.utils import iface


# ---------------------------------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------------------------------

SOURCE_LAYER_NAME = "RINDES_UNIDOS"

# Solo se utiliza si RINDES_UNIDOS no está ya cargada en el proyecto.
SOURCE_GPKG = (
    r"C:\Users\Ing_G\OneDrive - AGRAE SOLUTIONS\General - AGRAE SOLUTIONS"
    r"\100_SIG_AGRAE\120_ARCHIVOS MAPAS RENDIMIENTO\Cosecha 2026"
    r"\LUIS REAL\LUISREAL_RINDES_UNIFICADOS.gpkg"
)

# Se considera que VRYIELDMAS está en t/ha.
YIELD_FIELD = "VRYIELDMAS"
MOISTURE_FIELD = "Moisture"
DISTANCE_FIELD = "DISTANCE"
SWATH_FIELD = "SWATHWIDTH"

# Criterios mínimos para aceptar un lote.
MIN_VALID_POINTS = 500
MIN_VALID_PERCENT = 70.0
MIN_COVERAGE_PERCENT = 30.0

# Controles básicos de cada registro.
MIN_YIELD_T_HA = 0.01
MAX_YIELD_T_HA_ABSOLUTE = 100.0
MIN_DISTANCE_M = 0.01
MIN_SWATH_M = 0.10
MAX_MOISTURE_PERCENT = 60.0

# Filtro robusto: Q1 - k*IQR y Q3 + k*IQR, limitado además a 0-100 t/ha.
IQR_MULTIPLIER = 3.0

# La corrección se deja desactivada hasta confirmar si VRYIELDMAS ya viene
# corregido por la máquina. Para activarla, poner True y completar el diccionario.
APPLY_MOISTURE_CORRECTION = False
REFERENCE_MOISTURE_BY_CROP_ID = {
    # 53: 14.0,  # Ejemplo: trigo; sustituir por el valor real de agrae.cultivo
    # 22: 9.0,   # Ejemplo: colza; sustituir por el valor real
}

OUTPUT_LAYER_NAME = "RINDES_RESUMEN_LOTES"


# ---------------------------------------------------------------------------
# FUNCIONES AUXILIARES
# ---------------------------------------------------------------------------

def _as_float(value):
    try:
        number = float(value)
        return number if isfinite(number) else None
    except (TypeError, ValueError):
        return None


def _as_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _percentile(sorted_values, fraction):
    """Percentil con interpolación lineal; la entrada debe estar ordenada."""
    if not sorted_values:
        return None
    if len(sorted_values) == 1:
        return sorted_values[0]
    position = (len(sorted_values) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = position - lower
    return sorted_values[lower] * (1.0 - weight) + sorted_values[upper] * weight


def _source_layer():
    loaded = QgsProject.instance().mapLayersByName(SOURCE_LAYER_NAME)
    if loaded:
        layer = loaded[0]
    else:
        uri = f"{SOURCE_GPKG}|layername={SOURCE_LAYER_NAME}"
        layer = QgsVectorLayer(uri, SOURCE_LAYER_NAME, "ogr")
        if not layer.isValid():
            raise RuntimeError(
                f"No se pudo abrir {SOURCE_LAYER_NAME} desde:\n{SOURCE_GPKG}"
            )
        QgsProject.instance().addMapLayer(layer)
    return layer


def _check_fields(layer, names):
    available = {field.name() for field in layer.fields()}
    missing = [name for name in names if name not in available]
    if missing:
        raise RuntimeError(
            "Faltan campos obligatorios en la capa: " + ", ".join(missing)
        )


def _create_output_layer(rows):
    previous = QgsProject.instance().mapLayersByName(OUTPUT_LAYER_NAME)
    for layer in previous:
        QgsProject.instance().removeMapLayer(layer.id())

    output = QgsVectorLayer("None", OUTPUT_LAYER_NAME, "memory")
    provider = output.dataProvider()
    provider.addAttributes(
        [
            QgsField("iddata", QVariant.Int),
            QgsField("idlote", QVariant.Int),
            QgsField("idexplot", QVariant.Int),
            QgsField("idcultivo", QVariant.Int),
            QgsField("cultivo", QVariant.String, len=80),
            QgsField("area_ha", QVariant.Double),
            QgsField("n_total", QVariant.Int),
            QgsField("n_basicos", QVariant.Int),
            QgsField("n_usados", QVariant.Int),
            QgsField("valid_pct", QVariant.Double),
            QgsField("cobertura", QVariant.Double),
            QgsField("hum_ref", QVariant.Double),
            QgsField("rinde_med", QVariant.Double),
            QgsField("rinde_pond", QVariant.Double),
            QgsField("prod_med_t", QVariant.Double),
            QgsField("prod_pond_t", QVariant.Double),
            QgsField("q1", QVariant.Double),
            QgsField("q3", QVariant.Double),
            QgsField("lim_inf", QVariant.Double),
            QgsField("lim_sup", QVariant.Double),
            QgsField("estado", QVariant.String, len=40),
            QgsField("motivo", QVariant.String, len=250),
        ]
    )
    output.updateFields()

    features = []
    for row in rows:
        feature = QgsFeature(output.fields())
        feature.setAttributes(
            [
                row["iddata"],
                row["idlote"],
                row["idexplotacion"],
                row["idcultivo"],
                row["cultivo"],
                row["area_ha"],
                row["n_total"],
                row["n_basic"],
                row["n_used"],
                row["valid_pct"],
                row["coverage_pct"],
                row["reference_moisture"],
                row["yield_median"],
                row["yield_weighted"],
                row["production_median_t"],
                row["production_weighted_t"],
                row["q1"],
                row["q3"],
                row["lower_limit"],
                row["upper_limit"],
                row["status"],
                row["reason"],
            ]
        )
        features.append(feature)

    provider.addFeatures(features)
    output.updateExtents()
    QgsProject.instance().addMapLayer(output)
    return output


# ---------------------------------------------------------------------------
# PROCESAMIENTO
# ---------------------------------------------------------------------------

source = _source_layer()

required_fields = [
    "iddata",
    "idlote",
    "idexplotacion",
    "idcultivo",
    "cultivo",
    "area_ha",
    YIELD_FIELD,
    MOISTURE_FIELD,
    DISTANCE_FIELD,
    SWATH_FIELD,
]
_check_fields(source, required_fields)

request = QgsFeatureRequest()
# Usamos nombres, no índices. Esta sobrecarga es compatible con versiones de
# PyQGIS que interpretan una lista de enteros como QStringList y generan:
# "index 0 has type 'int' but 'str' is expected".
request.setSubsetOfAttributes(required_fields, source.fields())
request.setFlags(QgsFeatureRequest.NoGeometry)

# Cada muestra guardada es (rinde, humedad, superficie representada en m²).
samples_by_lot = defaultdict(list)
metadata_by_lot = {}
total_by_lot = defaultdict(int)
basic_by_lot = defaultdict(int)
skipped_without_lot = 0

feature_count = source.featureCount()
print(f"Procesando {feature_count:,} puntos de {SOURCE_LAYER_NAME}...")

for position, feature in enumerate(source.getFeatures(request), start=1):
    iddata = _as_int(feature["iddata"])
    idlote = _as_int(feature["idlote"])
    idexplotacion = _as_int(feature["idexplotacion"])
    idcultivo = _as_int(feature["idcultivo"])
    area_ha = _as_float(feature["area_ha"])

    if iddata is None or idlote is None or area_ha is None or area_ha <= 0:
        skipped_without_lot += 1
        continue

    total_by_lot[iddata] += 1
    metadata_by_lot[iddata] = {
        "iddata": iddata,
        "idlote": idlote,
        "idexplotacion": idexplotacion,
        "idcultivo": idcultivo,
        "cultivo": str(feature["cultivo"] or ""),
        "area_ha": area_ha,
    }

    yield_value = _as_float(feature[YIELD_FIELD])
    moisture = _as_float(feature[MOISTURE_FIELD])
    distance = _as_float(feature[DISTANCE_FIELD])
    swath = _as_float(feature[SWATH_FIELD])

    if (
        yield_value is None
        or moisture is None
        or distance is None
        or swath is None
        or yield_value < MIN_YIELD_T_HA
        or yield_value > MAX_YIELD_T_HA_ABSOLUTE
        or moisture < 0
        or moisture >= MAX_MOISTURE_PERCENT
        or distance < MIN_DISTANCE_M
        or swath < MIN_SWATH_M
    ):
        continue

    basic_by_lot[iddata] += 1
    samples_by_lot[iddata].append((yield_value, moisture, distance * swath))

    if position % 25000 == 0:
        print(f"  {position:,}/{feature_count:,} puntos leídos")


rows = []
for iddata in sorted(metadata_by_lot):
    metadata = metadata_by_lot[iddata]
    idcultivo = metadata["idcultivo"]
    total_count = total_by_lot[iddata]
    basic_count = basic_by_lot[iddata]
    samples = samples_by_lot[iddata]
    valid_percent = 100.0 * basic_count / total_count if total_count else 0.0

    values = sorted(sample[0] for sample in samples)
    q1 = _percentile(values, 0.25)
    q3 = _percentile(values, 0.75)

    if q1 is None or q3 is None:
        lower_limit = None
        upper_limit = None
        filtered = []
    else:
        iqr = q3 - q1
        lower_limit = max(MIN_YIELD_T_HA, q1 - IQR_MULTIPLIER * iqr)
        upper_limit = min(MAX_YIELD_T_HA_ABSOLUTE, q3 + IQR_MULTIPLIER * iqr)
        filtered = [
            sample for sample in samples if lower_limit <= sample[0] <= upper_limit
        ]

    reference_moisture = None
    corrected = []
    moisture_error = False
    if APPLY_MOISTURE_CORRECTION:
        reference_moisture = REFERENCE_MOISTURE_BY_CROP_ID.get(idcultivo)
        if reference_moisture is None or not 0 <= reference_moisture < 100:
            moisture_error = True
        else:
            for yield_value, moisture, sample_area_m2 in filtered:
                corrected_yield = (
                    yield_value
                    * (1.0 - moisture / 100.0)
                    / (1.0 - reference_moisture / 100.0)
                )
                corrected.append((corrected_yield, sample_area_m2))
    else:
        corrected = [(sample[0], sample[2]) for sample in filtered]

    used_count = len(corrected)
    used_area_m2 = sum(sample[1] for sample in corrected)
    coverage_percent = (
        100.0 * used_area_m2 / (metadata["area_ha"] * 10000.0)
        if metadata["area_ha"] > 0
        else 0.0
    )

    corrected_values = sorted(sample[0] for sample in corrected)
    yield_median = _percentile(corrected_values, 0.5)
    yield_weighted = (
        sum(yield_value * sample_area for yield_value, sample_area in corrected)
        / used_area_m2
        if used_area_m2 > 0
        else None
    )

    production_median_t = (
        yield_median * metadata["area_ha"] if yield_median is not None else None
    )
    production_weighted_t = (
        yield_weighted * metadata["area_ha"] if yield_weighted is not None else None
    )

    reasons = []
    if moisture_error:
        reasons.append("humedad de referencia no configurada")
    if used_count < MIN_VALID_POINTS:
        reasons.append(f"menos de {MIN_VALID_POINTS} puntos válidos")
    if valid_percent < MIN_VALID_PERCENT:
        reasons.append(f"menos del {MIN_VALID_PERCENT:.0f}% de registros válidos")
    if coverage_percent < MIN_COVERAGE_PERCENT:
        reasons.append(f"cobertura inferior al {MIN_COVERAGE_PERCENT:.0f}%")

    if reasons:
        status = "DESCARTADO"
    elif coverage_percent > 120.0:
        status = "REVISAR_SOLAPE"
        reasons.append("cobertura acumulada superior al 120%")
    else:
        status = "ACEPTADO"

    rows.append(
        {
            **metadata,
            "n_total": total_count,
            "n_basic": basic_count,
            "n_used": used_count,
            "valid_pct": round(valid_percent, 2),
            "coverage_pct": round(coverage_percent, 2),
            "reference_moisture": reference_moisture,
            "yield_median": round(yield_median, 4) if yield_median is not None else None,
            "yield_weighted": round(yield_weighted, 4) if yield_weighted is not None else None,
            "production_median_t": (
                round(production_median_t, 3)
                if production_median_t is not None
                else None
            ),
            "production_weighted_t": (
                round(production_weighted_t, 3)
                if production_weighted_t is not None
                else None
            ),
            "q1": round(q1, 4) if q1 is not None else None,
            "q3": round(q3, 4) if q3 is not None else None,
            "lower_limit": round(lower_limit, 4) if lower_limit is not None else None,
            "upper_limit": round(upper_limit, 4) if upper_limit is not None else None,
            "status": status,
            "reason": "; ".join(reasons),
        }
    )


output = _create_output_layer(rows)
accepted = sum(row["status"] == "ACEPTADO" for row in rows)
review = sum(row["status"] == "REVISAR_SOLAPE" for row in rows)
discarded = sum(row["status"] == "DESCARTADO" for row in rows)

print("\nProceso terminado")
print(f"  Lotes analizados: {len(rows)}")
print(f"  Aceptados: {accepted}")
print(f"  Revisar por solape: {review}")
print(f"  Descartados: {discarded}")
print(f"  Puntos sin identificación de lote: {skipped_without_lot}")
print(f"  Resultado: {OUTPUT_LAYER_NAME}")
print("  Producción recomendada provisional: campo prod_pond_t")

iface.messageBar().pushSuccess(
    "Rindes",
    f"Calculados {len(rows)} lotes: {accepted} aceptados y {discarded} descartados",
)
iface.showAttributeTable(output)
