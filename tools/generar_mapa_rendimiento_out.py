r"""Genera el mapa maestro y capas temáticas de rendimiento y fertilización.

Fuentes del proyecto QGIS:
    - RINDES_UNIDOS: puntos del monitor de cosecha.
    - mapa_sig: polígonos del mapa de prescripción.

Ejecución desde la consola Python de QGIS:

    exec(open(
        r"C:\Users\Ing_G\AppData\Roaming\QGIS\QGIS3\profiles\default"
        r"\python\plugins\agrae\tools\generar_mapa_rendimiento_out.py",
        encoding="utf-8"
    ).read())

No modifica las capas originales. Solicita un GeoPackage de destino y crea o
reemplaza solamente la capa de salida indicada, formada por cuadrados regulares.
Lee siempre la hoja OUT de un cuaderno XLSM y considera exclusivamente los
aportes 1 a 4. Los aportes 5 a 7 y nec_final se ignoran deliberadamente.

Unidades de salida:
    - Rendimiento, biomasa y materia seca: kg/ha.
    - Área útil de cada celda: hectáreas.
    - Extracciones, aportes y balances: kg nutriente/ha.
    - NUE/PUE/KUE: kg cosecha por kg de nutriente aplicado según OUT.

PRECAUCIÓN:
    Si no se informa producción de báscula en REAL_PRODUCTION_T_BY_IDDATA, el
    llamado "rinde real" es una estimación limpiada de la cosechadora.
"""

from collections import defaultdict
import csv
from math import ceil, floor, isfinite
import os
import re
import zipfile
from xml.etree import ElementTree as ET

from qgis.PyQt.QtCore import Qt, QRectF, QVariant
from qgis.PyQt.QtGui import QColor, QPainter, QPen
from qgis.PyQt.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QAbstractItemView,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from qgis.core import (
    QgsApplication,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsFeature,
    QgsFeatureRequest,
    QgsField,
    QgsGraduatedSymbolRenderer,
    QgsGeometry,
    QgsMapLayerStyle,
    QgsProject,
    QgsRuleBasedRenderer,
    QgsRendererRange,
    QgsRectangle,
    QgsSpatialIndex,
    QgsSymbol,
    QgsVectorFileWriter,
    QgsVectorLayer,
    QgsWkbTypes,
)
from qgis.utils import iface


# ---------------------------------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------------------------------

OUTPUT_LAYER_NAME = "00_ANALISIS_GENERAL"

# Retícula regular. Para la localización de este trabajo se utiliza UTM 30N.
# Cambiar GRID_CRS si el proyecto se ejecuta en otra zona.
GRID_SIZE_M = 10.0
GRID_CRS = "EPSG:25830"

DEFAULT_OUTPUT_GPKG = ""

# Calidad mínima a nivel de lote.
MIN_VALID_POINTS_LOT = 500
MIN_VALID_PERCENT_LOT = 70.0
MIN_COVERAGE_PERCENT_LOT = 30.0

# Calidad mínima del resultado dentro de cada polígono de prescripción.
MIN_VALID_POINTS_POLYGON = 5
MIN_COVERAGE_PERCENT_POLYGON = 10.0

# Filtros básicos del sensor.
MIN_YIELD_T_HA = 0.01
MAX_YIELD_T_HA = 100.0
MIN_DISTANCE_M = 0.01
MIN_SWATH_M = 0.10
MAX_MOISTURE_PERCENT = 60.0
IQR_MULTIPLIER = 3.0

# La evidencia del fichero indica que VRYIELDMAS se comporta como rinde húmedo
# para trigo y colza. Se corrige a la humedad de referencia de agrae.cultivo.
APPLY_MOISTURE_CORRECTION = True

# Producción confirmada por báscula, en toneladas, si estuviera disponible.
# Ejemplo: {8501: 95.4, 8502: 81.7}
REAL_PRODUCTION_T_BY_IDDATA = {}

# TOTAL conserva exactamente las toneladas reales. PPT_MEDIAN fuerza la
# mediana del mapa a RL, como la presentación, pero no garantiza el total.
ADJUSTMENT_METHOD = "TOTAL"  # "TOTAL" o "PPT_MEDIAN"


# Parámetros confirmados de agrae.cultivo para los cultivos presentes.
CROP_PARAMETERS = {
    6: {
        "name": "ALFALFA", "n_crop": 0.025, "p_crop": 0.0142,
        "k_crop": 0.02223, "n_res": 0.00001, "p_res": 0.00001,
        "k_res": 0.00001, "ic": 0.9, "ms_crop": 0.88,
        "ms_res": 0.88, "humidity": 12.0, "price": 0.0,
    },
    19: {
        "name": "CEBOLLA", "n_crop": 0.0147, "p_crop": 0.010966,
        "k_crop": 0.0238, "n_res": 0.0062, "p_res": 0.000621,
        "k_res": 0.00015, "ic": 0.8, "ms_crop": 0.125,
        "ms_res": 0.25, "humidity": 12.0, "price": 0.0,
    },
    22: {
        "name": "COLZA", "n_crop": 0.043, "p_crop": 0.0142,
        "k_crop": 0.012, "n_res": 0.008, "p_res": 0.009,
        "k_res": 0.015, "ic": 0.35, "ms_crop": 0.9,
        "ms_res": 0.7, "humidity": 12.0, "price": 0.0,
    },
    27: {
        "name": "GIRASOL", "n_crop": 0.0295, "p_crop": 0.014427,
        "k_crop": 0.008784, "n_res": 0.008, "p_res": 0.003206,
        "k_res": 0.019257, "ic": 0.3, "ms_crop": 0.8,
        "ms_res": 0.52, "humidity": 9.0, "price": 0.0,
    },
    44: {
        "name": "REMOLACHA AZUCARERA", "n_crop": 0.0082752,
        "p_crop": 0.00325, "k_crop": 0.01270801, "n_res": 0.012,
        "p_res": 0.0046, "k_res": 0.0242, "ic": 0.8,
        "ms_crop": 0.2, "ms_res": 0.1, "humidity": 12.0,
        "price": 0.0,
    },
    53: {
        "name": "TRIGO BLANDO", "n_crop": 0.021, "p_crop": 0.0096,
        "k_crop": 0.0061, "n_res": 0.0065, "p_res": 0.00145,
        "k_res": 0.0143, "ic": 0.45, "ms_crop": 0.87,
        "ms_res": 0.89, "humidity": 12.0, "price": 0.0,
    },
    71: {
        "name": "ADORMIDERA 201", "n_crop": 0.040036,
        "p_crop": 0.019, "k_crop": 0.0232, "n_res": 0.0394,
        "p_res": 0.0053, "k_res": 0.107898106, "ic": 0.5,
        "ms_crop": 0.86, "ms_res": 0.88, "humidity": None,
        "price": None,
    },
}


def load_crop_parameters_csv():
    """Carga la tabla completa compartida de agrae.cultivo."""
    tools_directory = os.path.join(
        QgsApplication.qgisSettingsDirPath(), "python", "plugins", "agrae", "tools"
    )
    path = os.path.join(tools_directory, "data", "cultivos_parametros.csv")
    if not os.path.isfile(path):
        raise RuntimeError(f"No se encuentra la tabla de cultivos: {path}")

    def number(row, field):
        value = str(row.get(field, "") or "").strip().replace(",", ".")
        try:
            return float(value) if value else None
        except ValueError:
            return None

    parameters = {}
    with open(path, encoding="utf-8-sig", newline="") as source:
        for row in csv.DictReader(source):
            try:
                crop_id = int(row["idcultivo"])
            except (KeyError, TypeError, ValueError):
                continue
            parameters[crop_id] = {
                "name": str(row.get("nombre") or ""),
                "n_crop": number(row, "extraccioncosechan"),
                "p_crop": number(row, "extraccioncosechap"),
                "k_crop": number(row, "extraccioncosechak"),
                "n_res": number(row, "extraccionresiduon"),
                "p_res": number(row, "extraccionresiduop"),
                "k_res": number(row, "extraccionresiduok"),
                "ic": number(row, "indice_cosecha"),
                "ms_crop": number(row, "ms_cosecha"),
                "ms_res": number(row, "ms_residuo"),
                "humidity": number(row, "humedad"),
                "price": number(row, "precio"),
            }
    return parameters


# La tabla completa sustituye el subconjunto histórico usado para LUIS REAL.
CROP_PARAMETERS.update(load_crop_parameters_csv())


# ---------------------------------------------------------------------------
# UTILIDADES
# ---------------------------------------------------------------------------

def as_float(value):
    try:
        number = float(value)
        return number if isfinite(number) else None
    except (TypeError, ValueError):
        return None


def as_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def percentile(sorted_values, fraction):
    if not sorted_values:
        return None
    if len(sorted_values) == 1:
        return sorted_values[0]
    position = (len(sorted_values) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = position - lower
    return sorted_values[lower] * (1.0 - weight) + sorted_values[upper] * weight


def safe_div(numerator, denominator):
    if numerator is None or denominator is None or denominator == 0:
        return None
    return numerator / denominator


def percent_ratio(numerator, denominator):
    """Devuelve una relaciÃ³n porcentual o NULL si no puede calcularse."""
    ratio = safe_div(numerator, denominator)
    return 100.0 * ratio if ratio is not None else None


def base_iddata(code):
    """El iddata base se obtiene quitando los dos últimos dígitos."""
    text = str(code).strip()
    if len(text) < 3 or not text.isdigit():
        return None
    return int(text[:-2])


def corrected_yield_kg_ha(yield_t_ha, moisture, crop_parameters):
    value = yield_t_ha * 1000.0
    if not APPLY_MOISTURE_CORRECTION:
        return value
    reference = crop_parameters.get("humidity") if crop_parameters else None
    if reference is None or not 0 <= reference < 100:
        return None
    return value * (1.0 - moisture / 100.0) / (1.0 - reference / 100.0)


def parse_fertilizer_formula(formula):
    """Convierte F18-46-00 en las fracciones (0.18, 0.46, 0.00)."""
    if formula is None:
        return None
    text = str(formula).strip().upper()
    if not text or "SIN INFORM" in text:
        return (0.0, 0.0, 0.0)
    numbers = re.findall(r"\d+(?:[.,]\d+)?", text)
    if len(numbers) < 3:
        return None
    return tuple(float(number.replace(",", ".")) / 100.0 for number in numbers[:3])


def normalize_code(value):
    """Normaliza claves Excel/QGIS sin perder identificadores enteros."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        number = float(text)
        if number.is_integer():
            return str(int(number))
    except ValueError:
        pass
    return text


def _excel_column_index(reference):
    letters = re.match(r"[A-Z]+", reference.upper())
    result = 0
    for letter in letters.group() if letters else "":
        result = result * 26 + ord(letter) - 64
    return result - 1


def read_out_sheet(workbook_path):
    """Lee valores cacheados de OUT directamente del XLSX/XLSM, sin Excel."""
    main_ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    rel_ns = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    package_ns = "http://schemas.openxmlformats.org/package/2006/relationships"
    with zipfile.ZipFile(workbook_path) as archive:
        shared = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in root.findall(f"{{{main_ns}}}si"):
                shared.append("".join(
                    node.text or "" for node in item.iter(f"{{{main_ns}}}t")
                ))

        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        relationship_id = None
        for sheet in workbook.findall(f".//{{{main_ns}}}sheet"):
            if str(sheet.attrib.get("name", "")).strip().upper() == "OUT":
                relationship_id = sheet.attrib.get(f"{{{rel_ns}}}id")
                break
        if not relationship_id:
            raise RuntimeError("El cuaderno no contiene una hoja llamada OUT.")

        relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        target = None
        for relation in relationships.findall(f"{{{package_ns}}}Relationship"):
            if relation.attrib.get("Id") == relationship_id:
                target = relation.attrib.get("Target")
                break
        if not target:
            raise RuntimeError("No se pudo localizar internamente la hoja OUT.")
        sheet_path = target.lstrip("/")
        if not sheet_path.startswith("xl/"):
            sheet_path = "xl/" + sheet_path
        sheet_root = ET.fromstring(archive.read(sheet_path))

        rows = []
        for row in sheet_root.findall(f".//{{{main_ns}}}row"):
            values = {}
            for cell in row.findall(f"{{{main_ns}}}c"):
                reference = cell.attrib.get("r", "")
                column = _excel_column_index(reference)
                cell_type = cell.attrib.get("t")
                value_node = cell.find(f"{{{main_ns}}}v")
                inline_node = cell.find(f"{{{main_ns}}}is")
                raw = value_node.text if value_node is not None else None
                if cell_type == "s" and raw is not None:
                    value = shared[int(raw)]
                elif cell_type == "inlineStr" and inline_node is not None:
                    value = "".join(
                        node.text or "" for node in inline_node.iter(f"{{{main_ns}}}t")
                    )
                elif cell_type == "str":
                    value = raw
                elif raw is None:
                    value = None
                else:
                    try:
                        value = float(raw)
                    except ValueError:
                        value = raw
                values[column] = value
            rows.append(values)

    if not rows:
        raise RuntimeError("La hoja OUT está vacía.")
    headers = {
        str(value).strip().lower(): column for column, value in rows[0].items()
        if value is not None
    }
    required = ["iddata"] + [
        name for index in range(1, 5)
        for name in (f"f_aporte{index}", f"aporte{index}")
    ]
    missing = [name for name in required if name not in headers]
    if missing:
        raise RuntimeError("Faltan columnas en OUT: " + ", ".join(missing))

    result = {}
    for row in rows[1:]:
        key = normalize_code(row.get(headers["iddata"]))
        if not key or not key.isdigit() or int(key) <= 0:
            continue
        totals = [0.0, 0.0, 0.0]
        total_dose = 0.0
        applications = []
        for index in range(1, 5):
            formula = row.get(headers[f"f_aporte{index}"])
            dose = as_float(row.get(headers[f"aporte{index}"])) or 0.0
            composition = parse_fertilizer_formula(formula)
            applications.append((str(formula or ""), dose))
            if composition is None:
                continue
            total_dose += dose
            for nutrient in range(3):
                totals[nutrient] += dose * composition[nutrient]
        result[key] = {
            "n": totals[0], "p": totals[1], "k": totals[2],
            "dose": total_dose, "applications": applications,
        }
    if not result:
        raise RuntimeError("OUT no contiene registros con IDDATA válido.")
    return result


def planned_nutrients(feature):
    totals = [0.0, 0.0, 0.0]
    total_dose = 0.0
    complete = True
    for formula_key, dose_key in (
        ("f_fondo", "d_fondo"),
        ("f_cob1", "d_cob1"),
        ("f_cob2", "d_cob2"),
        ("f_cob3", "d_cob3"),
    ):
        formula_field = PRESCRIPTION_FIELDS[formula_key]
        dose_field = PRESCRIPTION_FIELDS[dose_key]
        dose = as_float(feature[dose_field]) or 0.0
        total_dose += dose
        formula = parse_fertilizer_formula(feature[formula_field])
        if formula is None:
            complete = False
            continue
        for index in range(3):
            totals[index] += dose * formula[index]
    return totals[0], totals[1], totals[2], total_dose, complete


def comparison_status(proposed, applied):
    if proposed is None or applied is None:
        return "SIN_DATOS"
    if proposed == 0:
        return "COINCIDE" if applied == 0 else "NO_PROPUESTO"
    difference_percent = 100.0 * (applied - proposed) / proposed
    if difference_percent < -15:
        return "MUY_INFERIOR"
    if difference_percent < -5:
        return "LIGERAMENTE_INFERIOR"
    if difference_percent <= 5:
        return "COINCIDE"
    if difference_percent <= 15:
        return "LIGERAMENTE_SUPERIOR"
    return "MUY_SUPERIOR"


def require_fields(layer, names):
    available = {field.name() for field in layer.fields()}
    missing = [name for name in names if name not in available]
    if missing:
        raise RuntimeError(
            f"La capa {layer.name()} no contiene: " + ", ".join(missing)
        )


def rounded(value, digits=3):
    return round(value, digits) if value is not None and isfinite(value) else None


YIELD_FIELD_DEFAULTS = {
    "iddata": "iddata", "idlote": "idlote", "idcultivo": "idcultivo",
    "cultivo": "cultivo", "area_ha": "area_ha", "yield": "VRYIELDMAS",
    "moisture": "Moisture", "distance": "DISTANCE", "swath": "SWATHWIDTH",
}
PRESCRIPTION_FIELD_DEFAULTS = {
    "iddata": "iddata", "cultivo": "cultivo", "uf_etiqueta": "uf_etiqueta",
    "ambiente": "ambiente", "expected": "prod_ponderada",
    "f_fondo": "f_fondo", "d_fondo": "d_fondo",
    "f_cob1": "f_cob1", "d_cob1": "d_cob1", "f_cob2": "f_cob2",
    "d_cob2": "d_cob2", "f_cob3": "f_cob3", "d_cob3": "d_cob3",
}
FIELD_LABELS = {
    "iddata": "Código iddata", "idlote": "Identificador de lote",
    "idcultivo": "Identificador de cultivo", "cultivo": "Nombre del cultivo",
    "area_ha": "Área del lote (ha)", "yield": "Rendimiento del sensor (t/ha)",
    "moisture": "Humedad (%)", "distance": "Distancia recorrida (m)",
    "swath": "Anchura de corte (m)", "uf_etiqueta": "Etiqueta de unidad",
    "ambiente": "Código de ambiente (20/40/60)",
    "expected": "Producción esperada SIG (kg/ha)", "f_fondo": "Fórmula fondo",
    "d_fondo": "Dosis fondo", "f_cob1": "Fórmula cobertera 1",
    "d_cob1": "Dosis cobertera 1", "f_cob2": "Fórmula cobertera 2",
    "d_cob2": "Dosis cobertera 2", "f_cob3": "Fórmula cobertera 3",
    "d_cob3": "Dosis cobertera 3",
}


class ConfigurationDialog(QDialog):
    """Selecciona capas, correspondencia de campos y destino GeoPackage."""

    def __init__(self, layers, parent=None):
        super().__init__(parent)
        self.layers = layers
        self.setWindowTitle("Generar mapa previo de rendimiento")
        self.resize(650, 760)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            "Seleccione las capas cargadas, asocie sus campos y defina el GeoPackage de salida."
        ))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        body = QWidget()
        form = QFormLayout(body)
        scroll.setWidget(body)
        layout.addWidget(scroll)

        self.yield_layer_combo = QComboBox()
        self.prescription_layer_combo = QComboBox()
        for layer in layers:
            label = f"{layer.name()} — {layer.featureCount():,} objetos"
            self.yield_layer_combo.addItem(label, layer.id())
            self.prescription_layer_combo.addItem(label, layer.id())
        form.addRow("Capa de puntos de rendimiento", self.yield_layer_combo)
        form.addRow("Capa de prescripción (polígonos)", self.prescription_layer_combo)

        self.workbook_path = QLineEdit()
        workbook_browse = QPushButton("Examinar…")
        workbook_browse.clicked.connect(self.choose_workbook)
        workbook_row = QHBoxLayout()
        workbook_row.addWidget(self.workbook_path)
        workbook_row.addWidget(workbook_browse)
        form.addRow("Cuaderno Excel (hoja OUT)", workbook_row)

        self.yield_combos = {}
        self.prescription_combos = {}
        form.addRow(QLabel("CAMPOS DE RENDIMIENTO"))
        for key in YIELD_FIELD_DEFAULTS:
            combo = QComboBox()
            self.yield_combos[key] = combo
            form.addRow(FIELD_LABELS[key], combo)
        form.addRow(QLabel("CAMPOS DE PRESCRIPCIÓN"))
        for key in PRESCRIPTION_FIELD_DEFAULTS:
            combo = QComboBox()
            self.prescription_combos[key] = combo
            form.addRow(FIELD_LABELS[key], combo)

        self.output_path = QLineEdit(DEFAULT_OUTPUT_GPKG)
        browse = QPushButton("Examinar…")
        browse.clicked.connect(self.choose_output)
        path_row = QHBoxLayout()
        path_row.addWidget(self.output_path)
        path_row.addWidget(browse)
        form.addRow("GeoPackage de salida", path_row)
        self.output_name = QLineEdit(OUTPUT_LAYER_NAME)
        form.addRow("Nombre de la capa de salida", self.output_name)
        self.grid_size = QLineEdit(str(GRID_SIZE_M))
        form.addRow("Tamaño de retícula (m)", self.grid_size)
        self.grid_crs = QLineEdit(GRID_CRS)
        form.addRow("CRS métrico de la retícula", self.grid_crs)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.yield_layer_combo.currentIndexChanged.connect(self.populate_yield_fields)
        self.prescription_layer_combo.currentIndexChanged.connect(self.populate_prescription_fields)
        self._select_suggested_layers()
        self.populate_yield_fields()
        self.populate_prescription_fields()

    def layer_for_combo(self, combo):
        return QgsProject.instance().mapLayer(combo.currentData())

    def _select_suggested_layers(self):
        for index, layer in enumerate(self.layers):
            if layer.name().lower() == "rindes_unidos":
                self.yield_layer_combo.setCurrentIndex(index)
            if layer.name().lower() == "mapa_sig":
                self.prescription_layer_combo.setCurrentIndex(index)

    @staticmethod
    def fill_field_combo(combo, layer, default):
        combo.clear()
        names = [field.name() for field in layer.fields()] if layer else []
        combo.addItems(names)
        if default in names:
            combo.setCurrentText(default)

    def populate_yield_fields(self):
        layer = self.layer_for_combo(self.yield_layer_combo)
        for key, combo in self.yield_combos.items():
            self.fill_field_combo(combo, layer, YIELD_FIELD_DEFAULTS[key])

    def populate_prescription_fields(self):
        layer = self.layer_for_combo(self.prescription_layer_combo)
        for key, combo in self.prescription_combos.items():
            self.fill_field_combo(combo, layer, PRESCRIPTION_FIELD_DEFAULTS[key])

    def choose_output(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar mapa previo", self.output_path.text(),
            "GeoPackage (*.gpkg)",
        )
        if path:
            if not path.lower().endswith(".gpkg"):
                path += ".gpkg"
            self.output_path.setText(path)

    def choose_workbook(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar cuaderno de fertilización", self.workbook_path.text(),
            "Cuadernos Excel (*.xlsm *.xlsx)",
        )
        if path:
            self.workbook_path.setText(path)

    def validate_and_accept(self):
        yield_layer = self.layer_for_combo(self.yield_layer_combo)
        prescription_layer = self.layer_for_combo(self.prescription_layer_combo)
        errors = []
        if not yield_layer or QgsWkbTypes.geometryType(yield_layer.wkbType()) != QgsWkbTypes.PointGeometry:
            errors.append("La capa de rendimiento debe ser de puntos.")
        if not prescription_layer or QgsWkbTypes.geometryType(prescription_layer.wkbType()) != QgsWkbTypes.PolygonGeometry:
            errors.append("La capa de prescripción debe ser de polígonos.")
        if not self.output_path.text().strip():
            errors.append("Debe indicar el GeoPackage de salida.")
        workbook_path = self.workbook_path.text().strip()
        if not workbook_path or not os.path.isfile(workbook_path):
            errors.append("Debe seleccionar un cuaderno Excel válido con hoja OUT.")
        if not self.output_name.text().strip():
            errors.append("Debe indicar el nombre de la capa de salida.")
        try:
            if float(self.grid_size.text().replace(",", ".")) <= 0:
                raise ValueError
        except ValueError:
            errors.append("El tamaño de retícula debe ser un número positivo.")
        if not QgsCoordinateReferenceSystem(self.grid_crs.text().strip()).isValid():
            errors.append("El CRS de la retícula no es válido.")
        if errors:
            QMessageBox.warning(self, "Configuración incompleta", "\n".join(errors))
            return
        self.accept()

    def configuration(self):
        return {
            "yield_layer": self.layer_for_combo(self.yield_layer_combo),
            "prescription_layer": self.layer_for_combo(self.prescription_layer_combo),
            "yield_fields": {key: combo.currentText() for key, combo in self.yield_combos.items()},
            "prescription_fields": {
                key: combo.currentText() for key, combo in self.prescription_combos.items()
            },
            "output_path": self.output_path.text().strip(),
            "workbook_path": self.workbook_path.text().strip(),
            "output_name": self.output_name.text().strip(),
            "grid_size": float(self.grid_size.text().replace(",", ".")),
            "grid_crs": self.grid_crs.text().strip(),
        }


class DeliveryDialog(QDialog):
    """Selecciona capas públicas para un GeoPackage independiente."""

    def __init__(self, layer_names, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Crear GeoPackage de entrega")
        self.resize(500, 520)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            "Seleccione únicamente los análisis que se entregarán al agricultor."
        ))
        self.layers = QListWidget()
        self.layers.setSelectionMode(QAbstractItemView.MultiSelection)
        self.layers.addItems(layer_names)
        layout.addWidget(self.layers)
        self.path = QLineEdit()
        browse = QPushButton("Examinar…")
        browse.clicked.connect(self.choose_path)
        row = QHBoxLayout()
        row.addWidget(self.path)
        row.addWidget(browse)
        layout.addLayout(row)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def choose_path(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar entrega", self.path.text(), "GeoPackage (*.gpkg)"
        )
        if path:
            self.path.setText(path if path.lower().endswith(".gpkg") else path + ".gpkg")

    def validate_and_accept(self):
        if not self.layers.selectedItems() or not self.path.text().strip():
            QMessageBox.warning(
                self, "Entrega incompleta", "Seleccione capas y una ruta de salida."
            )
            return
        self.accept()

    def selection(self):
        return self.path.text().strip(), [item.text() for item in self.layers.selectedItems()]


class HistogramWidget(QWidget):
    """Histograma ligero dibujado con Qt, sin dependencias externas."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.values = []
        self.cutoff = None
        self.setMinimumHeight(280)

    def set_data(self, values, cutoff):
        self.values = sorted(values)
        self.cutoff = cutoff
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(58, 20, -22, -42)
        painter.fillRect(self.rect(), self.palette().base())
        painter.setPen(QPen(self.palette().mid().color(), 1))
        painter.drawLine(rect.bottomLeft(), rect.bottomRight())
        painter.drawLine(rect.bottomLeft(), rect.topLeft())
        if not self.values:
            painter.drawText(rect, Qt.AlignCenter, "Sin datos válidos")
            return

        low, high = self.values[0], self.values[-1]
        if high <= low:
            high = low + 1.0
        bin_count = min(40, max(10, int(len(self.values) ** 0.5)))
        counts = [0] * bin_count
        for value in self.values:
            index = min(bin_count - 1, int((value - low) / (high - low) * bin_count))
            counts[index] += 1
        max_count = max(counts) or 1
        width = rect.width() / bin_count
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#5b8ff9"))
        for index, count in enumerate(counts):
            height = rect.height() * count / max_count
            painter.drawRect(QRectF(
                rect.left() + index * width + 1,
                rect.bottom() - height,
                max(1.0, width - 2),
                height,
            ))

        if self.cutoff is not None:
            x = rect.left() + (self.cutoff - low) / (high - low) * rect.width()
            x = max(rect.left(), min(rect.right(), x))
            painter.setPen(QPen(QColor("#d73027"), 3))
            painter.drawLine(int(x), rect.top(), int(x), rect.bottom())
            painter.drawText(
                QRectF(max(rect.left(), x - 80), rect.top(), 160, 24),
                Qt.AlignCenter,
                f"Corte {self.cutoff:,.0f}",
            )

        painter.setPen(self.palette().text().color())
        painter.drawText(QRectF(rect.left() - 20, rect.bottom() + 8, 100, 24),
                         Qt.AlignLeft, f"{low:,.0f}")
        painter.drawText(QRectF(rect.right() - 100, rect.bottom() + 8, 100, 24),
                         Qt.AlignRight, f"{high:,.0f} kg/ha")
        painter.drawText(QRectF(0, rect.top(), 52, 24), Qt.AlignRight, str(max_count))


class CutoffDialog(QDialog):
    """Permite revisar y modificar el corte superior automático por lote."""

    def __init__(self, distributions, automatic_cutoffs, details, parent=None):
        super().__init__(parent)
        self.distributions = distributions
        self.automatic = automatic_cutoffs
        self.details = details
        self.selected = dict(automatic_cutoffs)
        self.setWindowTitle("Validar cortes superiores de rendimiento")
        self.resize(820, 570)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            "La línea roja es el corte automático. Los rendimientos inferiores "
            "se conservan; solo se recortarán valores situados a su derecha."
        ))
        self.lot_combo = QComboBox()
        for iddata in sorted(distributions):
            self.lot_combo.addItem(f"Lote iddata {iddata}", iddata)
        layout.addWidget(self.lot_combo)
        self.info = QLabel()
        layout.addWidget(self.info)
        self.histogram = HistogramWidget()
        layout.addWidget(self.histogram)

        control = QHBoxLayout()
        control.addWidget(QLabel("Corte superior:"))
        self.slider = QSlider(Qt.Horizontal)
        self.spin = QSpinBox()
        self.spin.setSuffix(" kg/ha")
        self.spin.setSingleStep(100)
        control.addWidget(self.slider, 1)
        control.addWidget(self.spin)
        reset = QPushButton("Restablecer automático")
        reset.clicked.connect(self.reset_current)
        control.addWidget(reset)
        layout.addLayout(control)

        buttons = QDialogButtonBox()
        accept = buttons.addButton("Validar y continuar", QDialogButtonBox.AcceptRole)
        cancel = buttons.addButton(QDialogButtonBox.Cancel)
        accept.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        layout.addWidget(buttons)
        self.lot_combo.currentIndexChanged.connect(self.load_lot)
        self.slider.valueChanged.connect(self.slider_changed)
        self.spin.valueChanged.connect(self.spin_changed)
        self.load_lot()

    def current_iddata(self):
        return self.lot_combo.currentData()

    def load_lot(self):
        iddata = self.current_iddata()
        if iddata is None:
            return
        values = self.distributions[iddata]
        maximum = max(values + [self.automatic[iddata]])
        slider_max = max(1000, int(ceil(maximum / 1000.0) * 1000))
        self.slider.blockSignals(True)
        self.spin.blockSignals(True)
        self.slider.setRange(0, slider_max)
        self.spin.setRange(0, slider_max)
        value = int(round(self.selected[iddata]))
        self.slider.setValue(value)
        self.spin.setValue(value)
        self.slider.blockSignals(False)
        self.spin.blockSignals(False)
        detail = self.details[iddata]
        self.info.setText(
            f"{detail['label']}: {detail['reference']:,.0f} kg/ha · "
            f"IQR utilizado: {detail['iqr']:,.0f} · "
            f"Corte automático: {self.automatic[iddata]:,.0f} kg/ha"
        )
        self.histogram.set_data(values, value)

    def slider_changed(self, value):
        self.spin.blockSignals(True)
        self.spin.setValue(value)
        self.spin.blockSignals(False)
        self.selected[self.current_iddata()] = float(value)
        self.histogram.set_data(self.distributions[self.current_iddata()], value)

    def spin_changed(self, value):
        self.slider.setValue(value)

    def reset_current(self):
        self.slider.setValue(int(round(self.automatic[self.current_iddata()])))


# ---------------------------------------------------------------------------
# 1. CARGA Y VALIDACIÓN
# ---------------------------------------------------------------------------

candidate_layers = [
    layer for layer in QgsProject.instance().mapLayers().values()
    if isinstance(layer, QgsVectorLayer) and layer.isValid()
]
if len(candidate_layers) < 2:
    raise RuntimeError(
        "Cargue en QGIS una capa de puntos de rendimiento y una capa poligonal "
        "de prescripción antes de ejecutar el script."
    )

dialog = ConfigurationDialog(candidate_layers, iface.mainWindow())
if dialog.exec_() != QDialog.Accepted:
    raise RuntimeError("Proceso cancelado por el usuario.")
config = dialog.configuration()

yield_layer = config["yield_layer"]
prescription_layer = config["prescription_layer"]
YIELD_FIELDS = config["yield_fields"]
PRESCRIPTION_FIELDS = config["prescription_fields"]
OUTPUT_GPKG = config["output_path"]
WORKBOOK_PATH = config["workbook_path"]
OUTPUT_LAYER_NAME = config["output_name"]
GRID_SIZE_M = config["grid_size"]
GRID_CRS = config["grid_crs"]

print("Leyendo fertilización realizada desde la hoja OUT (aportes 1–4)…")
OUT_APPLICATIONS = read_out_sheet(WORKBOOK_PATH)
print(f"  Unidades OUT válidas: {len(OUT_APPLICATIONS):,}")

YIELD_FIELD = YIELD_FIELDS["yield"]
MOISTURE_FIELD = YIELD_FIELDS["moisture"]
DISTANCE_FIELD = YIELD_FIELDS["distance"]
SWATH_FIELD = YIELD_FIELDS["swath"]

yield_fields = list(dict.fromkeys(YIELD_FIELDS.values()))
prescription_fields = list(dict.fromkeys(PRESCRIPTION_FIELDS.values()))
require_fields(yield_layer, yield_fields)
require_fields(prescription_layer, prescription_fields)


# ---------------------------------------------------------------------------
# 2. CONTROL DE CALIDAD Y FACTOR POR LOTE
# ---------------------------------------------------------------------------

request = QgsFeatureRequest()
request.setSubsetOfAttributes(yield_fields, yield_layer.fields())
request.setFlags(QgsFeatureRequest.NoGeometry)

lot_metadata = {}
lot_total_count = defaultdict(int)
lot_basic_samples = defaultdict(list)

print(f"Analizando {yield_layer.featureCount():,} registros de rendimiento...")

for position, feature in enumerate(yield_layer.getFeatures(request), start=1):
    iddata = as_int(feature[YIELD_FIELDS["iddata"]])
    idcultivo = as_int(feature[YIELD_FIELDS["idcultivo"]])
    area_ha = as_float(feature[YIELD_FIELDS["area_ha"]])
    if iddata is None or idcultivo is None or area_ha is None or area_ha <= 0:
        continue

    lot_total_count[iddata] += 1
    lot_metadata[iddata] = {
        "iddata": iddata,
        "idlote": as_int(feature[YIELD_FIELDS["idlote"]]),
        "idcultivo": idcultivo,
        "cultivo": str(feature[YIELD_FIELDS["cultivo"]] or ""),
        "area_ha": area_ha,
    }

    yield_value = as_float(feature[YIELD_FIELD])
    moisture = as_float(feature[MOISTURE_FIELD])
    distance = as_float(feature[DISTANCE_FIELD])
    swath = as_float(feature[SWATH_FIELD])
    if (
        yield_value is None or moisture is None or distance is None or swath is None
        or not MIN_YIELD_T_HA <= yield_value <= MAX_YIELD_T_HA
        or not 0 <= moisture < MAX_MOISTURE_PERCENT
        or distance < MIN_DISTANCE_M or swath < MIN_SWATH_M
    ):
        continue
    lot_basic_samples[iddata].append((yield_value, moisture, distance * swath))

    if position % 25000 == 0:
        print(f"  {position:,}/{yield_layer.featureCount():,}")


lot_quality = {}
for iddata, metadata in lot_metadata.items():
    samples = lot_basic_samples[iddata]
    raw_values = sorted(sample[0] for sample in samples)
    q1 = percentile(raw_values, 0.25)
    q3 = percentile(raw_values, 0.75)
    if q1 is None or q3 is None:
        lower, upper, filtered = None, None, []
    else:
        iqr = q3 - q1
        lower = max(MIN_YIELD_T_HA, q1 - IQR_MULTIPLIER * iqr)
        upper = min(MAX_YIELD_T_HA, q3 + IQR_MULTIPLIER * iqr)
        filtered = [sample for sample in samples if lower <= sample[0] <= upper]

    crop = CROP_PARAMETERS.get(metadata["idcultivo"])
    corrected = []
    for yield_value, moisture, sample_area in filtered:
        value = corrected_yield_kg_ha(yield_value, moisture, crop)
        if value is not None:
            corrected.append((value, sample_area))

    used_area_m2 = sum(sample[1] for sample in corrected)
    coverage = 100.0 * used_area_m2 / (metadata["area_ha"] * 10000.0)
    valid_percent = (
        100.0 * len(samples) / lot_total_count[iddata]
        if lot_total_count[iddata] else 0.0
    )
    corrected_values = sorted(sample[0] for sample in corrected)
    map_median = percentile(corrected_values, 0.5)
    map_weighted = (
        sum(value * area for value, area in corrected) / used_area_m2
        if used_area_m2 else None
    )
    estimated_production_t = (
        map_weighted * metadata["area_ha"] / 1000.0
        if map_weighted is not None else None
    )

    reasons = []
    if crop is None:
        reasons.append("cultivo sin parámetros")
    elif APPLY_MOISTURE_CORRECTION and crop.get("humidity") is None:
        reasons.append("cultivo sin humedad de referencia")
    if len(corrected) < MIN_VALID_POINTS_LOT:
        reasons.append(f"menos de {MIN_VALID_POINTS_LOT} puntos")
    if valid_percent < MIN_VALID_PERCENT_LOT:
        reasons.append(f"menos del {MIN_VALID_PERCENT_LOT:.0f}% válido")
    if coverage < MIN_COVERAGE_PERCENT_LOT:
        reasons.append(f"cobertura menor del {MIN_COVERAGE_PERCENT_LOT:.0f}%")

    real_production_t = REAL_PRODUCTION_T_BY_IDDATA.get(iddata)
    factor = 1.0
    origin = "ESTIMACION_COSECHADORA"
    real_yield_kg_ha = map_weighted
    if real_production_t is not None and not reasons:
        real_yield_kg_ha = real_production_t * 1000.0 / metadata["area_ha"]
        if ADJUSTMENT_METHOD == "PPT_MEDIAN":
            factor = safe_div(real_yield_kg_ha, map_median)
        else:
            factor = safe_div(real_production_t, estimated_production_t)
        if factor is None:
            reasons.append("factor de ajuste no calculable")
            factor = 1.0
        else:
            origin = "PRODUCCION_BASCULA"

    lot_quality[iddata] = {
        **metadata,
        "accepted": not reasons,
        "reason": "; ".join(reasons),
        "lower": lower,
        "upper": upper,
        "coverage": coverage,
        "valid_percent": valid_percent,
        "map_median": map_median,
        "map_weighted": map_weighted,
        "real_yield": real_yield_kg_ha,
        "estimated_production_t": estimated_production_t,
        "real_production_t": real_production_t,
        "factor": factor,
        "origin": origin,
    }


# ---------------------------------------------------------------------------
# 3. RETÍCULA CUADRADA Y CONTEXTO DEL MAPA DE PRESCRIPCIÓN
# ---------------------------------------------------------------------------

grid_crs = QgsCoordinateReferenceSystem(GRID_CRS)
project = QgsProject.instance()
prescription_transform = QgsCoordinateTransform(
    prescription_layer.crs(), grid_crs, project.transformContext()
)
point_transform = QgsCoordinateTransform(
    yield_layer.crs(), grid_crs, project.transformContext()
)

prescription_index = QgsSpatialIndex()
prescription_features = {}
prescription_geometries = {}
prescription_extent = None
accepted_yield_ids = {
    iddata for iddata, quality in lot_quality.items() if quality["accepted"]
}
excluded_prescription_polygons = 0

for source_polygon in prescription_layer.getFeatures():
    polygon_base_id = base_iddata(
        source_polygon[PRESCRIPTION_FIELDS["iddata"]]
    )
    if polygon_base_id not in accepted_yield_ids:
        excluded_prescription_polygons += 1
        continue
    polygon = QgsFeature(source_polygon)
    geometry = source_polygon.geometry()
    geometry.transform(prescription_transform)
    polygon.setGeometry(geometry)
    prescription_index.addFeature(polygon)
    prescription_features[polygon.id()] = polygon
    prescription_geometries[polygon.id()] = geometry
    if prescription_extent is None:
        prescription_extent = QgsRectangle(geometry.boundingBox())
    else:
        prescription_extent.combineExtentWith(geometry.boundingBox())

if prescription_extent is None:
    raise RuntimeError(
        "No hay unidades del mapa SIG relacionadas con lotes de rendimiento "
        "que hayan superado los controles de calidad."
    )

print(
    f"Unidades SIG incluidas: {len(prescription_features):,}; "
    f"excluidas por no tener rinde aceptado: {excluded_prescription_polygons:,}"
)

origin_x = floor(prescription_extent.xMinimum() / GRID_SIZE_M) * GRID_SIZE_M
origin_y = floor(prescription_extent.yMinimum() / GRID_SIZE_M) * GRID_SIZE_M
max_col = int(ceil((prescription_extent.xMaximum() - origin_x) / GRID_SIZE_M))
max_row = int(ceil((prescription_extent.yMaximum() - origin_y) / GRID_SIZE_M))

# grid_cells[key] = (geometría cuadrada, fid prescripción dominante, área útil m²)
grid_cells = {}
print(f"Creando retícula de {GRID_SIZE_M:g} × {GRID_SIZE_M:g} m...")
for row in range(max_row):
    y_min = origin_y + row * GRID_SIZE_M
    for column in range(max_col):
        x_min = origin_x + column * GRID_SIZE_M
        rectangle = QgsRectangle(x_min, y_min, x_min + GRID_SIZE_M, y_min + GRID_SIZE_M)
        candidates = prescription_index.intersects(rectangle)
        if not candidates:
            continue
        cell_geometry = QgsGeometry.fromRect(rectangle)
        overlaps = []
        for fid in candidates:
            intersection = prescription_geometries[fid].intersection(cell_geometry)
            if not intersection.isEmpty():
                area = intersection.area()
                if area > 0:
                    overlaps.append((area, fid))
        if overlaps:
            useful_area, dominant_fid = max(overlaps)
            grid_cells[(column, row)] = (cell_geometry, dominant_fid, useful_area)


# ---------------------------------------------------------------------------
# 4. ASIGNACIÓN DE PUNTOS A CELDAS Y DERIVADOS POR PUNTO
# ---------------------------------------------------------------------------

# Cada muestra contiene los campos que después se agregan por mediana, igual
# que rindes_layer_query.sql.
grid_samples = defaultdict(list)
point_request = QgsFeatureRequest()
point_request.setSubsetOfAttributes(yield_fields, yield_layer.fields())

assigned_points = 0
for position, point in enumerate(yield_layer.getFeatures(point_request), start=1):
    iddata = as_int(point[YIELD_FIELDS["iddata"]])
    quality = lot_quality.get(iddata)
    if not quality or not quality["accepted"]:
        continue

    yield_t_ha = as_float(point[YIELD_FIELD])
    moisture = as_float(point[MOISTURE_FIELD])
    distance = as_float(point[DISTANCE_FIELD])
    swath = as_float(point[SWATH_FIELD])
    if None in (yield_t_ha, moisture, distance, swath):
        continue
    if (
        yield_t_ha < quality["lower"] or yield_t_ha > quality["upper"]
        or not 0 <= moisture < MAX_MOISTURE_PERCENT
        or distance < MIN_DISTANCE_M or swath < MIN_SWATH_M
    ):
        continue

    crop = CROP_PARAMETERS.get(quality["idcultivo"])
    adjusted_moisture = corrected_yield_kg_ha(yield_t_ha, moisture, crop)
    if adjusted_moisture is None:
        continue
    final_yield = adjusted_moisture * quality["factor"]

    geometry = point.geometry()
    if geometry.isNull() or geometry.isEmpty():
        continue
    geometry.transform(point_transform)
    coordinate = geometry.asPoint()
    column = int(floor((coordinate.x() - origin_x) / GRID_SIZE_M))
    row = int(floor((coordinate.y() - origin_y) / GRID_SIZE_M))
    key = (column, row)
    if key not in grid_cells:
        continue

    _, prescription_fid, _ = grid_cells[key]
    prescription = prescription_features[prescription_fid]
    if base_iddata(prescription[PRESCRIPTION_FIELDS["iddata"]]) != iddata:
        continue

    biomass = residue = ms_crop = ms_residue = None
    n_extracted = p_extracted = k_extracted = None
    if crop and crop["ic"] not in (None, 0):
        biomass = final_yield / crop["ic"]
        residue = biomass - final_yield
        ms_crop = final_yield * crop["ms_crop"]
        ms_residue = residue * crop["ms_res"]
        n_extracted = ms_crop * crop["n_crop"] + ms_residue * crop["n_res"]
        p_extracted = ms_crop * crop["p_crop"] + ms_residue * crop["p_res"]
        k_extracted = ms_crop * crop["k_crop"] + ms_residue * crop["k_res"]

    grid_samples[key].append({
        "rinde_bruto": yield_t_ha * 1000.0,
        "humedad": moisture,
        "ajuste": adjusted_moisture,
        "rinde": final_yield,
        "biomasa": biomass,
        "residuo": residue,
        "ms_cosecha": ms_crop,
        "ms_residuo": ms_residue,
        "n_extraido": n_extracted,
        "p_extraido": p_extracted,
        "k_extraido": k_extracted,
        "area_m2": distance * swath,
    })
    assigned_points += 1

    if position % 25000 == 0:
        print(f"  {position:,}/{yield_layer.featureCount():,} puntos espacializados")


# ---------------------------------------------------------------------------
# 4B. CORTE SUPERIOR AUTOMÁTICO Y VALIDACIÓN DEL OPERADOR
# ---------------------------------------------------------------------------

def environment_code(value):
    match = re.search(r"\d+", str(value or ""))
    return int(match.group()) if match else None


lot_distributions = defaultdict(list)
high_zone_values = defaultdict(list)
high_zone_references = defaultdict(list)

for key, (_, prescription_fid, _) in grid_cells.items():
    samples = grid_samples.get(key, [])
    yields = sorted(
        sample["rinde"] for sample in samples if sample.get("rinde") is not None
    )
    if not yields:
        continue
    cell_yield = percentile(yields, 0.5)
    prescription = prescription_features[prescription_fid]
    iddata = base_iddata(prescription[PRESCRIPTION_FIELDS["iddata"]])
    if iddata is None:
        continue
    lot_distributions[iddata].append(cell_yield)
    environment = environment_code(prescription[PRESCRIPTION_FIELDS["ambiente"]])
    expected = as_float(prescription[PRESCRIPTION_FIELDS["expected"]])
    if environment is not None and 60 <= environment < 70:
        high_zone_values[iddata].append(cell_yield)
        if expected is not None and expected > 0:
            high_zone_references[iddata].append(expected)

automatic_cutoffs = {}
cutoff_details = {}
for iddata, values in lot_distributions.items():
    values.sort()
    high_values = sorted(high_zone_values.get(iddata) or values)
    q1 = percentile(high_values, 0.25)
    q3 = percentile(high_values, 0.75)
    iqr = (q3 - q1) if q1 is not None and q3 is not None else 0.0
    references = high_zone_references.get(iddata, [])
    if references:
        # La zona 60 representa el máximo diseñado: no se promedia con la 40.
        reference = max(references)
        method = "PROD_ESPERADA_60_MAS_IQR"
        label = "Referencia máxima ambiente 60"
        cutoff = reference + 1.5 * iqr
    else:
        # Fallback explícito cuando el lote carece de ambiente 60 utilizable.
        reference = q3 or max(values)
        method = "FALLBACK_TUKEY_SIN_ZONA_60"
        label = "Referencia Q3 (sin ambiente 60)"
        cutoff = reference + 1.5 * iqr
    automatic_cutoffs[iddata] = max(cutoff, reference)
    cutoff_details[iddata] = {
        "reference": reference,
        "iqr": iqr,
        "method": method,
        "label": label,
    }

if not lot_distributions:
    raise RuntimeError("No existen celdas con rendimientos válidos para representar.")

cutoff_dialog = CutoffDialog(
    lot_distributions,
    automatic_cutoffs,
    cutoff_details,
    iface.mainWindow(),
)
if cutoff_dialog.exec_() != QDialog.Accepted:
    raise RuntimeError("Cortes no validados; proceso cancelado por el usuario.")
selected_cutoffs = cutoff_dialog.selected


# ---------------------------------------------------------------------------
# 5. CAPA DE RETÍCULA: CAMPOS DE RINDES_LAYER_QUERY + INDICADORES
# ---------------------------------------------------------------------------

for previous in QgsProject.instance().mapLayersByName(OUTPUT_LAYER_NAME):
    QgsProject.instance().removeMapLayer(previous.id())

output = QgsVectorLayer(f"Polygon?crs={GRID_CRS}", OUTPUT_LAYER_NAME, "memory")
provider = output.dataProvider()
provider.addAttributes([
    QgsField("idgrid", QVariant.String, len=50),
    QgsField("iddata", QVariant.Int),
    QgsField("iddata_sig", QVariant.String, len=40),
    QgsField("idlote", QVariant.Int),
    QgsField("idcultivo", QVariant.Int),
    QgsField("cultivo", QVariant.String, len=80),
    QgsField("uf_etiqueta", QVariant.String, len=30),
    QgsField("area_ha", QVariant.Double),
    QgsField("n_puntos", QVariant.Int),
    QgsField("cobertura", QVariant.Double),
    QgsField("estado", QVariant.String, len=40),
    QgsField("rinde_bruto", QVariant.Double),
    QgsField("humedad", QVariant.Double),
    QgsField("ajuste", QVariant.Double),
    QgsField("rinde_pre", QVariant.Double),
    QgsField("lim_sup", QVariant.Double),
    QgsField("recortado", QVariant.Int),
    QgsField("exceso", QVariant.Double),
    QgsField("metodo_aj", QVariant.String, len=40),
    QgsField("rinde", QVariant.Double),
    QgsField("biomasa", QVariant.Double),
    QgsField("residuo", QVariant.Double),
    QgsField("ms_cosecha", QVariant.Double),
    QgsField("ms_residuo", QVariant.Double),
    QgsField("n_extraido", QVariant.Double),
    QgsField("p_extraido", QVariant.Double),
    QgsField("k_extraido", QVariant.Double),
    QgsField("prod_esper", QVariant.Double),
    QgsField("dif_rinde", QVariant.Double),
    QgsField("cumpl_pct", QVariant.Double),
    QgsField("idx_rinde", QVariant.Double),
    QgsField("idx_bruto", QVariant.Double),
    QgsField("idx_pre", QVariant.Double),
    QgsField("n_plan", QVariant.Double),
    QgsField("p_plan", QVariant.Double),
    QgsField("k_plan", QVariant.Double),
    QgsField("dosis_plan", QVariant.Double),
    QgsField("n_aplic", QVariant.Double),
    QgsField("p_aplic", QVariant.Double),
    QgsField("k_aplic", QVariant.Double),
    QgsField("dosis_aplic", QVariant.Double),
    QgsField("dif_n", QVariant.Double),
    QgsField("dif_p", QVariant.Double),
    QgsField("dif_k", QVariant.Double),
    QgsField("dif_dosis", QVariant.Double),
    QgsField("dif_n_pct", QVariant.Double),
    QgsField("dif_p_pct", QVariant.Double),
    QgsField("dif_k_pct", QVariant.Double),
    QgsField("estado_n", QVariant.String, len=30),
    QgsField("estado_p", QVariant.String, len=30),
    QgsField("estado_k", QVariant.String, len=30),
    QgsField("idx_n", QVariant.Double),
    QgsField("idx_p", QVariant.Double),
    QgsField("idx_k", QVariant.Double),
    QgsField("balance_n", QVariant.Double),
    QgsField("balance_p", QVariant.Double),
    QgsField("balance_k", QVariant.Double),
    QgsField("idx_cob_n", QVariant.Double),
    QgsField("idx_cob_p", QVariant.Double),
    QgsField("idx_cob_k", QVariant.Double),
    QgsField("nue", QVariant.Double),
    QgsField("pue", QVariant.Double),
    QgsField("kue", QVariant.Double),
    QgsField("factor_aj", QVariant.Double),
    QgsField("origen", QVariant.String, len=40),
])
output.updateFields()


def median_sample(samples, field):
    values = sorted(
        sample[field] for sample in samples if sample.get(field) is not None
    )
    return percentile(values, 0.5)


output_features = []
for (column, row), (geometry, prescription_fid, useful_area_m2) in grid_cells.items():
    prescription = prescription_features[prescription_fid]
    iddata_sig = normalize_code(prescription[PRESCRIPTION_FIELDS["iddata"]])
    iddata = base_iddata(iddata_sig)
    quality = lot_quality.get(iddata)
    samples = grid_samples.get((column, row), [])
    coverage = 100.0 * sum(sample["area_m2"] for sample in samples) / useful_area_m2

    values = {
        field: median_sample(samples, field)
        for field in (
            "rinde_bruto", "humedad", "ajuste", "rinde", "biomasa",
            "residuo", "ms_cosecha", "ms_residuo", "n_extraido",
            "p_extraido", "k_extraido",
        )
    }

    # El corte actúa únicamente sobre excesos superiores. Los rendimientos
    # bajos y todos los valores normales, incluida la zona 40, se conservan.
    rinde_pre = values["rinde"]
    upper_limit = selected_cutoffs.get(iddata)
    was_clipped = bool(
        rinde_pre is not None and upper_limit is not None and rinde_pre > upper_limit
    )
    excess = rinde_pre - upper_limit if was_clipped else 0.0 if rinde_pre is not None else None
    if was_clipped:
        values["rinde"] = upper_limit

    # Los derivados se recalculan desde el rendimiento final para mantener
    # coherencia entre rinde, biomasa, materia seca y extracciones.
    crop = CROP_PARAMETERS.get(quality["idcultivo"]) if quality else None
    if values["rinde"] is not None and crop and crop["ic"] not in (None, 0):
        values["biomasa"] = values["rinde"] / crop["ic"]
        values["residuo"] = values["biomasa"] - values["rinde"]
        values["ms_cosecha"] = values["rinde"] * crop["ms_crop"]
        values["ms_residuo"] = values["residuo"] * crop["ms_res"]
        values["n_extraido"] = (
            values["ms_cosecha"] * crop["n_crop"]
            + values["ms_residuo"] * crop["n_res"]
        )
        values["p_extraido"] = (
            values["ms_cosecha"] * crop["p_crop"]
            + values["ms_residuo"] * crop["p_res"]
        )
        values["k_extraido"] = (
            values["ms_cosecha"] * crop["k_crop"]
            + values["ms_residuo"] * crop["k_res"]
        )

    if quality is None:
        status = "SIN_RINDES"
    elif not quality["accepted"]:
        status = "LOTE_DESCARTADO"
    elif len(samples) < MIN_VALID_POINTS_POLYGON:
        status = "BAJA_CONFIANZA"
    elif coverage < MIN_COVERAGE_PERCENT_POLYGON:
        status = "BAJA_CONFIANZA"
    elif coverage > 120.0:
        status = "REVISAR_SOLAPE"
    else:
        status = "PREVIO_VALIDO"

    expected = as_float(prescription[PRESCRIPTION_FIELDS["expected"]])
    difference = (
        values["rinde"] - expected
        if values["rinde"] is not None and expected is not None else None
    )
    compliance = (
        100.0 * values["rinde"] / expected
        if values["rinde"] is not None and expected not in (None, 0) else None
    )
    idx_rinde = compliance
    idx_bruto = percent_ratio(values["rinde_bruto"], expected)
    idx_pre = percent_ratio(rinde_pre, expected)
    n_plan, p_plan, k_plan, dose_plan, _ = planned_nutrients(prescription)
    applied = OUT_APPLICATIONS.get(iddata_sig)
    n_aplic = applied["n"] if applied else None
    p_aplic = applied["p"] if applied else None
    k_aplic = applied["k"] if applied else None
    dose_aplic = applied["dose"] if applied else None
    dif_n = n_aplic - n_plan if n_aplic is not None else None
    dif_p = p_aplic - p_plan if p_aplic is not None else None
    dif_k = k_aplic - k_plan if k_aplic is not None else None
    dif_dose = dose_aplic - dose_plan if dose_aplic is not None else None
    dif_n_pct = percent_ratio(dif_n, n_plan)
    dif_p_pct = percent_ratio(dif_p, p_plan)
    dif_k_pct = percent_ratio(dif_k, k_plan)
    idx_n = percent_ratio(n_aplic, n_plan)
    idx_p = percent_ratio(p_aplic, p_plan)
    idx_k = percent_ratio(k_aplic, k_plan)
    balance_n = n_aplic - values["n_extraido"] if n_aplic is not None and values["n_extraido"] is not None else None
    balance_p = p_aplic - values["p_extraido"] if p_aplic is not None and values["p_extraido"] is not None else None
    balance_k = k_aplic - values["k_extraido"] if k_aplic is not None and values["k_extraido"] is not None else None
    idx_cob_n = percent_ratio(n_aplic, values["n_extraido"])
    idx_cob_p = percent_ratio(p_aplic, values["p_extraido"])
    idx_cob_k = percent_ratio(k_aplic, values["k_extraido"])
    nue = safe_div(values["rinde"], n_aplic)
    pue = safe_div(values["rinde"], p_aplic)
    kue = safe_div(values["rinde"], k_aplic)

    feature = QgsFeature(output.fields())
    feature.setGeometry(geometry)
    feature.setAttributes([
        f"{column}_{row}", iddata, iddata_sig, quality["idlote"] if quality else None,
        quality["idcultivo"] if quality else None,
        quality["cultivo"] if quality else str(prescription[PRESCRIPTION_FIELDS["cultivo"]] or ""),
        str(prescription[PRESCRIPTION_FIELDS["uf_etiqueta"]] or ""), rounded(useful_area_m2 / 10000.0, 4),
        len(samples), rounded(coverage, 2), status,
        rounded(values["rinde_bruto"]), rounded(values["humedad"]),
        rounded(values["ajuste"]), rounded(rinde_pre), rounded(upper_limit),
        int(was_clipped), rounded(excess),
        cutoff_details.get(iddata, {}).get("method", "SIN_CORTE"),
        rounded(values["rinde"]),
        rounded(values["biomasa"]), rounded(values["residuo"]),
        rounded(values["ms_cosecha"]), rounded(values["ms_residuo"]),
        rounded(values["n_extraido"]), rounded(values["p_extraido"]),
        rounded(values["k_extraido"]), rounded(expected), rounded(difference),
        rounded(compliance, 2), rounded(idx_rinde, 2), rounded(idx_bruto, 2),
        rounded(idx_pre, 2), rounded(n_plan), rounded(p_plan), rounded(k_plan),
        rounded(dose_plan), rounded(n_aplic), rounded(p_aplic), rounded(k_aplic),
        rounded(dose_aplic), rounded(dif_n), rounded(dif_p), rounded(dif_k),
        rounded(dif_dose), rounded(dif_n_pct, 2), rounded(dif_p_pct, 2),
        rounded(dif_k_pct, 2), comparison_status(n_plan, n_aplic),
        comparison_status(p_plan, p_aplic), comparison_status(k_plan, k_aplic),
        rounded(idx_n, 2), rounded(idx_p, 2), rounded(idx_k, 2),
        rounded(balance_n), rounded(balance_p), rounded(balance_k),
        rounded(idx_cob_n, 2), rounded(idx_cob_p, 2), rounded(idx_cob_k, 2),
        rounded(nue), rounded(pue), rounded(kue),
        rounded(quality["factor"], 6) if quality else None,
        quality["origin"] if quality else "SIN_RINDES",
    ])
    output_features.append(feature)

provider.addFeatures(output_features)
output.updateExtents()


# ---------------------------------------------------------------------------
# 6. ESTILOS TEMÁTICOS GUARDADOS EN LA CAPA
# ---------------------------------------------------------------------------

STYLE_STATES = {"PREVIO_VALIDO", "REVISAR_SOLAPE"}
SEQUENTIAL_COLORS = ["#d73027", "#fc8d59", "#fee08b", "#91cf60", "#1a9850"]
DIVERGING_COLORS = ["#b2182b", "#ef8a62", "#f7f7f7", "#67a9cf", "#2166ac"]


def thematic_values(layer, field_name):
    """Valores fiables empleados para calcular los cortes de simbología."""
    return sorted(
        value
        for feature in layer.getFeatures()
        for value in [as_float(feature[field_name])]
        if value is not None and str(feature["estado"]) in STYLE_STATES
    )


def new_symbol(layer, color):
    symbol = QgsSymbol.defaultSymbol(layer.geometryType())
    symbol.setColor(QColor(color))
    symbol.setOpacity(0.86)
    return symbol


def apply_quantile_style(layer, field_name, unit):
    """Aplica cinco clases por cuantiles; soporta también valores constantes."""
    values = thematic_values(layer, field_name)
    if not values:
        return False

    if values[0] == values[-1]:
        ranges = [QgsRendererRange(
            values[0], values[-1], new_symbol(layer, SEQUENTIAL_COLORS[3]),
            f"{values[0]:.2f} {unit}".strip(),
        )]
    else:
        breaks = [percentile(values, index / 5.0) for index in range(6)]
        ranges = []
        for index, color in enumerate(SEQUENTIAL_COLORS):
            lower, upper = breaks[index], breaks[index + 1]
            if upper < lower or (upper == lower and index not in (0, 4)):
                continue
            ranges.append(QgsRendererRange(
                lower, upper, new_symbol(layer, color),
                f"{lower:.2f} – {upper:.2f} {unit}".strip(),
            ))
    layer.setRenderer(QgsGraduatedSymbolRenderer(field_name, ranges))
    return True


def apply_centered_style(layer, field_name, center, unit):
    """Rampa divergente simétrica alrededor de cero o del objetivo indicado."""
    values = thematic_values(layer, field_name)
    if not values:
        return False
    radius = max(abs(value - center) for value in values)
    if radius == 0:
        radius = max(abs(center) * 0.01, 1.0)
    offsets = (-radius, -0.5 * radius, -0.05 * radius,
               0.05 * radius, 0.5 * radius, radius)
    ranges = []
    for index, color in enumerate(DIVERGING_COLORS):
        lower = center + offsets[index]
        upper = center + offsets[index + 1]
        ranges.append(QgsRendererRange(
            lower, upper, new_symbol(layer, color),
            f"{lower:.2f} – {upper:.2f} {unit}".strip(),
        ))
    layer.setRenderer(QgsGraduatedSymbolRenderer(field_name, ranges))
    return True


def apply_crop_rule_style(layer, field_name, unit):
    """Cinco cuantiles independientes dentro de cada cultivo."""
    crops = defaultdict(list)
    for feature in layer.getFeatures():
        value = as_float(feature[field_name])
        crop = str(feature["cultivo"] or "SIN CULTIVO").strip()
        if value is not None and str(feature["estado"]) in STYLE_STATES:
            crops[crop].append(value)
    if not crops:
        return False
    root = QgsRuleBasedRenderer.Rule(None)
    for crop in sorted(crops):
        values = sorted(crops[crop])
        quoted_crop = crop.replace("'", "''")
        crop_filter = f'"cultivo" = \'{quoted_crop}\''
        crop_rule = QgsRuleBasedRenderer.Rule(None, 0, 0, crop_filter, crop)
        if values[0] == values[-1]:
            value = values[0]
            rule_filter = (
                f'"{field_name}" = {value:.12g} AND '
                '"estado" IN (\'PREVIO_VALIDO\',\'REVISAR_SOLAPE\')'
            )
            crop_rule.appendChild(QgsRuleBasedRenderer.Rule(
                new_symbol(layer, SEQUENTIAL_COLORS[2]), 0, 0,
                rule_filter, f"{value:.1f} {unit}".strip()
            ))
            root.appendChild(crop_rule)
            continue
        breaks = [percentile(values, index / 5.0) for index in range(6)]
        for index, color in enumerate(SEQUENTIAL_COLORS):
            lower, upper = breaks[index], breaks[index + 1]
            if upper == lower and index > 0:
                continue
            operator = "<=" if index == 4 else "<"
            rule_filter = (
                f'"{field_name}" >= {lower:.12g} AND '
                f'"{field_name}" {operator} {upper:.12g} AND '
                '"estado" IN (\'PREVIO_VALIDO\',\'REVISAR_SOLAPE\')'
            )
            label = f"{lower:.1f} – {upper:.1f} {unit}".strip()
            crop_rule.appendChild(QgsRuleBasedRenderer.Rule(
                new_symbol(layer, color), 0, 0, rule_filter, label
            ))
        root.appendChild(crop_rule)
    layer.setRenderer(QgsRuleBasedRenderer(root))
    return True


def apply_global_index_style(layer, field_name, unit="%"):
    """Reglas fijas comparables globalmente, centradas alrededor de 100 %."""
    if not thematic_values(layer, field_name):
        return False
    ranges = [
        (-1e12, 70.0, "#b2182b", "< 70 · Muy inferior"),
        (70.0, 90.0, "#ef8a62", "70–90 · Inferior"),
        (90.0, 110.0, "#f7f7f7", "90–110 · Próximo a referencia"),
        (110.0, 130.0, "#67a9cf", "110–130 · Superior"),
        (130.0, 1e12, "#2166ac", "> 130 · Muy superior"),
    ]
    renderer_ranges = [
        QgsRendererRange(lower, upper, new_symbol(layer, color), f"{label} {unit}")
        for lower, upper, color, label in ranges
    ]
    layer.setRenderer(QgsGraduatedSymbolRenderer(field_name, renderer_ranges))
    return True


QgsProject.instance().addMapLayer(output)
style_manager = output.styleManager()

# Nombre visible, campo, tipo de rampa, centro (si procede) y unidad.
style_specs = [
    ("01 Rendimiento ajustado por cultivo", "rinde", "crop", None, "kg/ha"),
    ("02 Rendimiento bruto por cultivo", "rinde_bruto", "crop", None, "kg/ha"),
    ("03 Diferencia de rendimiento", "dif_rinde", "centered", 0.0, "kg/ha"),
    ("04 Cumplimiento del objetivo", "cumpl_pct", "centered", 100.0, "%"),
    ("05 Biomasa por cultivo", "biomasa", "crop", None, "kg/ha"),
    ("06 Residuo por cultivo", "residuo", "crop", None, "kg/ha"),
    ("07 Materia seca cosecha por cultivo", "ms_cosecha", "crop", None, "kg/ha"),
    ("08 Materia seca residuo por cultivo", "ms_residuo", "crop", None, "kg/ha"),
    ("09 N extraído por cultivo", "n_extraido", "crop", None, "kg N/ha"),
    ("10 P extraído por cultivo", "p_extraido", "crop", None, "kg P/ha"),
    ("11 K extraído por cultivo", "k_extraido", "crop", None, "kg K/ha"),
    ("12 N propuesto", "n_plan", "quantile", None, "kg N/ha"),
    ("13 P propuesto", "p_plan", "quantile", None, "kg P/ha"),
    ("14 K propuesto", "k_plan", "quantile", None, "kg K/ha"),
    ("15 Balance N", "balance_n", "centered", 0.0, "kg N/ha"),
    ("16 Balance P", "balance_p", "centered", 0.0, "kg P/ha"),
    ("17 Balance K", "balance_k", "centered", 0.0, "kg K/ha"),
    ("18 NUE por cultivo", "nue", "crop", None, "kg/kg N"),
    ("19 PUE por cultivo", "pue", "crop", None, "kg/kg P"),
    ("20 KUE por cultivo", "kue", "crop", None, "kg/kg K"),
    ("21 Cobertura", "cobertura", "quantile", None, "%"),
    ("22 Rendimiento antes del corte por cultivo", "rinde_pre", "crop", None, "kg/ha"),
    ("23 Límite superior", "lim_sup", "quantile", None, "kg/ha"),
    ("24 Exceso recortado", "exceso", "quantile", None, "kg/ha"),
    ("25 N aplicado OUT", "n_aplic", "quantile", None, "kg N/ha"),
    ("26 P aplicado OUT", "p_aplic", "quantile", None, "kg P/ha"),
    ("27 K aplicado OUT", "k_aplic", "quantile", None, "kg K/ha"),
    ("28 Diferencia N aplicado-propuesto", "dif_n", "centered", 0.0, "kg N/ha"),
    ("29 Diferencia P aplicado-propuesto", "dif_p", "centered", 0.0, "kg P/ha"),
    ("30 Diferencia K aplicado-propuesto", "dif_k", "centered", 0.0, "kg K/ha"),
    ("31 Diferencia porcentual N", "dif_n_pct", "centered", 0.0, "%"),
    ("32 Diferencia porcentual P", "dif_p_pct", "centered", 0.0, "%"),
    ("33 Diferencia porcentual K", "dif_k_pct", "centered", 0.0, "%"),
    ("34 Índice global de rendimiento", "idx_rinde", "index", 100.0, "%"),
    ("35 Índice global de rendimiento bruto", "idx_bruto", "index", 100.0, "%"),
    ("36 Índice global previo al corte", "idx_pre", "index", 100.0, "%"),
    ("37 Índice N aplicado-propuesto", "idx_n", "index", 100.0, "%"),
    ("38 Índice P aplicado-propuesto", "idx_p", "index", 100.0, "%"),
    ("39 Índice K aplicado-propuesto", "idx_k", "index", 100.0, "%"),
    ("40 Cobertura aparente extracción N", "idx_cob_n", "index", 100.0, "%"),
    ("41 Cobertura aparente extracción P", "idx_cob_p", "index", 100.0, "%"),
    ("42 Cobertura aparente extracción K", "idx_cob_k", "index", 100.0, "%"),
]

saved_styles = []
for style_name, field_name, style_type, center, unit in style_specs:
    if style_type == "centered":
        styled = apply_centered_style(output, field_name, center, unit)
    elif style_type == "crop":
        styled = apply_crop_rule_style(output, field_name, unit)
    elif style_type == "index":
        styled = apply_global_index_style(output, field_name, unit)
    else:
        styled = apply_quantile_style(output, field_name, unit)
    if styled and style_manager.addStyleFromLayer(style_name):
        saved_styles.append(style_name)

if "01 Rendimiento ajustado por cultivo" in saved_styles:
    style_manager.setCurrentStyle("01 Rendimiento ajustado por cultivo")
output.triggerRepaint()

# Persistir geometrías, atributos y estilos en el GeoPackage elegido.
write_options = QgsVectorFileWriter.SaveVectorOptions()
write_options.driverName = "GPKG"
write_options.layerName = OUTPUT_LAYER_NAME
write_options.fileEncoding = "UTF-8"
if os.path.isfile(OUTPUT_GPKG):
    write_options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
else:
    write_options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteFile
write_result = QgsVectorFileWriter.writeAsVectorFormatV3(
    output,
    OUTPUT_GPKG,
    QgsProject.instance().transformContext(),
    write_options,
)
if write_result[0] != QgsVectorFileWriter.NoError:
    raise RuntimeError(f"No se pudo escribir el GeoPackage: {write_result[1]}")

saved_uri = f"{OUTPUT_GPKG}|layername={OUTPUT_LAYER_NAME}"
saved_layer = QgsVectorLayer(saved_uri, OUTPUT_LAYER_NAME, "ogr")
if not saved_layer.isValid():
    raise RuntimeError(f"Se escribió el archivo, pero no se pudo abrir {saved_uri}")

database_styles = []
style_errors = []
target_manager = saved_layer.styleManager()
for style_name in saved_styles:
    style_manager.setCurrentStyle(style_name)
    map_style = QgsMapLayerStyle()
    map_style.readFromLayer(output)
    map_style.writeToLayer(saved_layer)
    target_manager.addStyleFromLayer(style_name)
    error = saved_layer.saveStyleToDatabase(
        style_name,
        "Generado automáticamente por Ajuste de Rindes",
        style_name == "01 Rendimiento ajustado por cultivo",
        "",
    )
    if error:
        style_errors.append(f"{style_name}: {error}")
    else:
        database_styles.append(style_name)

if "01 Rendimiento ajustado por cultivo" in target_manager.styles():
    target_manager.setCurrentStyle("01 Rendimiento ajustado por cultivo")
saved_layer.triggerRepaint()


# ---------------------------------------------------------------------------
# 7. CAPAS TEMÁTICAS PÚBLICAS CON CAMPOS MÍNIMOS
# ---------------------------------------------------------------------------

COMMON_PUBLIC_FIELDS = ["idgrid", "idlote", "cultivo", "area_ha", "estado"]
THEMATIC_SPECS = [
    ("01_RENDIMIENTO", ["rinde"], "rinde", "crop", None, "kg/ha"),
    ("02_CUMPLIMIENTO", ["rinde", "prod_esper", "dif_rinde", "cumpl_pct"],
     "cumpl_pct", "centered", 100.0, "%"),
    ("03_BIOMASA_RESIDUO", ["rinde", "biomasa", "residuo", "ms_cosecha", "ms_residuo"],
     "biomasa", "crop", None, "kg/ha"),
    ("04_EXTRACCION_N", ["rinde", "n_extraido"], "n_extraido", "crop", None, "kg N/ha"),
    ("05_EXTRACCION_P", ["rinde", "p_extraido"], "p_extraido", "crop", None, "kg P/ha"),
    ("06_EXTRACCION_K", ["rinde", "k_extraido"], "k_extraido", "crop", None, "kg K/ha"),
    ("07_N_PROPUESTO", ["n_plan"], "n_plan", "quantile", None, "kg N/ha"),
    ("08_P_PROPUESTO", ["p_plan"], "p_plan", "quantile", None, "kg P/ha"),
    ("09_K_PROPUESTO", ["k_plan"], "k_plan", "quantile", None, "kg K/ha"),
    ("10_N_APLICADO", ["n_aplic"], "n_aplic", "quantile", None, "kg N/ha"),
    ("11_P_APLICADO", ["p_aplic"], "p_aplic", "quantile", None, "kg P/ha"),
    ("12_K_APLICADO", ["k_aplic"], "k_aplic", "quantile", None, "kg K/ha"),
    ("13_DIFERENCIA_N", ["n_plan", "n_aplic", "dif_n", "dif_n_pct", "estado_n"],
     "dif_n", "centered", 0.0, "kg N/ha"),
    ("14_DIFERENCIA_P", ["p_plan", "p_aplic", "dif_p", "dif_p_pct", "estado_p"],
     "dif_p", "centered", 0.0, "kg P/ha"),
    ("15_DIFERENCIA_K", ["k_plan", "k_aplic", "dif_k", "dif_k_pct", "estado_k"],
     "dif_k", "centered", 0.0, "kg K/ha"),
    ("16_BALANCE_N", ["rinde", "n_aplic", "n_extraido", "balance_n"],
     "balance_n", "centered", 0.0, "kg N/ha"),
    ("17_BALANCE_P", ["rinde", "p_aplic", "p_extraido", "balance_p"],
     "balance_p", "centered", 0.0, "kg P/ha"),
    ("18_BALANCE_K", ["rinde", "k_aplic", "k_extraido", "balance_k"],
     "balance_k", "centered", 0.0, "kg K/ha"),
    ("19_NUE", ["rinde", "n_aplic", "nue"], "nue", "crop", None, "kg/kg N"),
    ("20_PUE", ["rinde", "p_aplic", "pue"], "pue", "crop", None, "kg/kg P"),
    ("21_KUE", ["rinde", "k_aplic", "kue"], "kue", "crop", None, "kg/kg K"),
    ("22_INDICE_RENDIMIENTO", ["rinde", "prod_esper", "idx_rinde"],
     "idx_rinde", "index", 100.0, "%"),
    ("23_INDICE_N_APLICADO_PROPUESTO", ["n_plan", "n_aplic", "idx_n"],
     "idx_n", "index", 100.0, "%"),
    ("24_INDICE_P_APLICADO_PROPUESTO", ["p_plan", "p_aplic", "idx_p"],
     "idx_p", "index", 100.0, "%"),
    ("25_INDICE_K_APLICADO_PROPUESTO", ["k_plan", "k_aplic", "idx_k"],
     "idx_k", "index", 100.0, "%"),
    ("26_COBERTURA_EXTRACCION_N", ["n_aplic", "n_extraido", "idx_cob_n"],
     "idx_cob_n", "index", 100.0, "%"),
    ("27_COBERTURA_EXTRACCION_P", ["p_aplic", "p_extraido", "idx_cob_p"],
     "idx_cob_p", "index", 100.0, "%"),
    ("28_COBERTURA_EXTRACCION_K", ["k_aplic", "k_extraido", "idx_cob_k"],
     "idx_cob_k", "index", 100.0, "%"),
]


def make_thematic_layer(source_layer, layer_name, extra_fields,
                        style_field, style_type, center, unit):
    field_names = list(dict.fromkeys(COMMON_PUBLIC_FIELDS + extra_fields))
    thematic = QgsVectorLayer(f"Polygon?crs={GRID_CRS}", layer_name, "memory")
    thematic_provider = thematic.dataProvider()
    thematic_provider.addAttributes([
        QgsField(source_layer.fields()[source_layer.fields().indexOf(name)])
        for name in field_names
    ])
    thematic.updateFields()
    features = []
    for source_feature in source_layer.getFeatures():
        if source_feature[style_field] is None:
            continue
        feature = QgsFeature(thematic.fields())
        feature.setGeometry(source_feature.geometry())
        feature.setAttributes([source_feature[name] for name in field_names])
        features.append(feature)
    thematic_provider.addFeatures(features)
    thematic.updateExtents()
    if style_type == "centered":
        apply_centered_style(thematic, style_field, center, unit)
    elif style_type == "crop":
        apply_crop_rule_style(thematic, style_field, unit)
    elif style_type == "index":
        apply_global_index_style(thematic, style_field, unit)
    else:
        apply_quantile_style(thematic, style_field, unit)
    return thematic


def write_layer_to_gpkg(layer, path, layer_name, overwrite_file=False):
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "GPKG"
    options.layerName = layer_name
    options.fileEncoding = "UTF-8"
    options.actionOnExistingFile = (
        QgsVectorFileWriter.CreateOrOverwriteFile
        if overwrite_file else QgsVectorFileWriter.CreateOrOverwriteLayer
    )
    result = QgsVectorFileWriter.writeAsVectorFormatV3(
        layer, path, QgsProject.instance().transformContext(), options
    )
    if result[0] != QgsVectorFileWriter.NoError:
        raise RuntimeError(f"No se pudo escribir {layer_name}: {result[1]}")


thematic_layers = {}
for layer_name, fields, style_field, style_type, center, unit in THEMATIC_SPECS:
    for previous in QgsProject.instance().mapLayersByName(layer_name):
        QgsProject.instance().removeMapLayer(previous.id())
    thematic_memory = make_thematic_layer(
        output, layer_name, fields, style_field, style_type, center, unit
    )
    write_layer_to_gpkg(thematic_memory, OUTPUT_GPKG, layer_name)
    thematic_saved = QgsVectorLayer(
        f"{OUTPUT_GPKG}|layername={layer_name}", layer_name, "ogr"
    )
    if not thematic_saved.isValid():
        raise RuntimeError(f"No se pudo abrir la capa temática {layer_name}.")
    map_style = QgsMapLayerStyle()
    map_style.readFromLayer(thematic_memory)
    map_style.writeToLayer(thematic_saved)
    thematic_saved.saveStyleToDatabase(
        layer_name, "Estilo temático para entrega", True, ""
    )
    thematic_layers[layer_name] = thematic_saved

theme_group = QgsProject.instance().layerTreeRoot().findGroup("ANALISIS_TEMATICOS")
if theme_group is None:
    theme_group = QgsProject.instance().layerTreeRoot().addGroup("ANALISIS_TEMATICOS")
for layer in thematic_layers.values():
    QgsProject.instance().addMapLayer(layer, False)
    theme_group.addLayer(layer)


# ---------------------------------------------------------------------------
# 8. INFORME TEXTUAL INTERNO
# ---------------------------------------------------------------------------

REPORT_FIELDS = (
    "rinde", "prod_esper", "idx_rinde",
    "n_plan", "n_aplic", "dif_n", "balance_n", "nue",
    "p_plan", "p_aplic", "dif_p", "balance_p", "pue",
    "k_plan", "k_aplic", "dif_k", "balance_k", "kue",
)


def weighted_value(group, field_name):
    """Media ponderada por el Ã¡rea Ãºtil representada en cada celda."""
    numerator = 0.0
    denominator = 0.0
    for feature in group:
        value = as_float(feature[field_name])
        area = as_float(feature["area_ha"])
        if value is not None and area is not None and area > 0:
            numerator += value * area
            denominator += area
    return numerator / denominator if denominator else None


def report_number(value, decimals=2):
    return "s/d" if value is None else f"{value:,.{decimals}f}"


def write_text_report(layer, report_path):
    groups = defaultdict(list)
    all_valid = []
    status_counts = defaultdict(int)
    for feature in layer.getFeatures():
        status = str(feature["estado"] or "SIN_ESTADO")
        status_counts[status] += 1
        if status not in STYLE_STATES:
            continue
        all_valid.append(feature)
        groups[(feature["idlote"], str(feature["cultivo"] or "SIN CULTIVO"))].append(feature)

    total_area = sum(as_float(feature["area_ha"]) or 0.0 for feature in all_valid)
    total_production_t = sum(
        (as_float(feature["rinde"]) or 0.0)
        * (as_float(feature["area_ha"]) or 0.0) / 1000.0
        for feature in all_valid
    )
    clipped = sum(int(as_float(feature["recortado"]) or 0) for feature in all_valid)

    lines = [
        "INFORME INTERNO DE RENDIMIENTO Y FERTILIZACIÃ“N",
        "=" * 55,
        "",
        "FUENTES Y CRITERIOS",
        f"- Capa de rindes: {yield_layer.name()}",
        f"- Capa de prescripciÃ³n: {prescription_layer.name()}",
        f"- Cuaderno: {WORKBOOK_PATH}",
        "- Hoja leÃ­da: OUT; aportes considerados: 1 a 4.",
        f"- RetÃ­cula: {GRID_SIZE_M:g} x {GRID_SIZE_M:g} m ({GRID_CRS}).",
        "- Las medias del informe estÃ¡n ponderadas por superficie Ãºtil.",
        "- Los Ã­ndices globales expresan referencia = 100 %.",
        "- NUE/PUE/KUE se mantienen como valores absolutos por cultivo.",
        "",
        "RESUMEN GENERAL",
        f"- Celdas representadas: {len(all_valid):,}",
        f"- Superficie representada: {total_area:,.2f} ha",
        f"- ProducciÃ³n estimada: {total_production_t:,.2f} t",
        f"- Rendimiento medio ponderado: {report_number(weighted_value(all_valid, 'rinde'))} kg/ha",
        f"- ProducciÃ³n esperada media ponderada: {report_number(weighted_value(all_valid, 'prod_esper'))} kg/ha",
        f"- Ãndice global de rendimiento: {report_number(weighted_value(all_valid, 'idx_rinde'))} %",
        f"- Celdas con recorte superior: {clipped:,}",
        "- Estados: " + ", ".join(
            f"{name}={count:,}" for name, count in sorted(status_counts.items())
        ),
        "",
        "RESUMEN POR LOTE Y CULTIVO",
        "-" * 55,
    ]

    for (idlote, crop), group in sorted(
        groups.items(), key=lambda item: (str(item[0][0]), item[0][1])
    ):
        area = sum(as_float(feature["area_ha"]) or 0.0 for feature in group)
        production_t = sum(
            (as_float(feature["rinde"]) or 0.0)
            * (as_float(feature["area_ha"]) or 0.0) / 1000.0
            for feature in group
        )
        lines.extend([
            "",
            f"Lote {idlote if idlote is not None else 's/d'} | {crop}",
            f"  Celdas: {len(group):,} | Superficie: {area:,.2f} ha | ProducciÃ³n: {production_t:,.2f} t",
            "  Rendimiento: "
            f"{report_number(weighted_value(group, 'rinde'))} kg/ha | "
            f"Esperado: {report_number(weighted_value(group, 'prod_esper'))} kg/ha | "
            f"Ãndice: {report_number(weighted_value(group, 'idx_rinde'))} %",
            "  N propuesto/aplicado/diferencia/balance/NUE: "
            f"{report_number(weighted_value(group, 'n_plan'))} / "
            f"{report_number(weighted_value(group, 'n_aplic'))} / "
            f"{report_number(weighted_value(group, 'dif_n'))} / "
            f"{report_number(weighted_value(group, 'balance_n'))} / "
            f"{report_number(weighted_value(group, 'nue'))}",
            "  P propuesto/aplicado/diferencia/balance/PUE: "
            f"{report_number(weighted_value(group, 'p_plan'))} / "
            f"{report_number(weighted_value(group, 'p_aplic'))} / "
            f"{report_number(weighted_value(group, 'dif_p'))} / "
            f"{report_number(weighted_value(group, 'balance_p'))} / "
            f"{report_number(weighted_value(group, 'pue'))}",
            "  K propuesto/aplicado/diferencia/balance/KUE: "
            f"{report_number(weighted_value(group, 'k_plan'))} / "
            f"{report_number(weighted_value(group, 'k_aplic'))} / "
            f"{report_number(weighted_value(group, 'dif_k'))} / "
            f"{report_number(weighted_value(group, 'balance_k'))} / "
            f"{report_number(weighted_value(group, 'kue'))}",
        ])

    lines.extend([
        "", "DEFINICIONES",
        "- Ãndice de rendimiento = 100 x rendimiento ajustado / producciÃ³n esperada.",
        "- Ãndice aplicado/propuesto = 100 x nutriente aplicado / nutriente propuesto.",
        "- Cobertura de extracciÃ³n = 100 x nutriente aplicado / nutriente extraÃ­do.",
        "- Balance = nutriente aplicado - nutriente extraÃ­do.",
        "- La producciÃ³n es una estimaciÃ³n espacial; no sustituye un pesaje de bÃ¡scula.",
        "", "Este informe acompaÃ±a al GeoPackage maestro y contiene informaciÃ³n interna.",
    ])
    with open(report_path, "w", encoding="utf-8-sig", newline="\n") as report:
        report.write("\n".join(lines) + "\n")


REPORT_PATH = os.path.splitext(OUTPUT_GPKG)[0] + "_informe.txt"
write_text_report(output, REPORT_PATH)

# Un archivo de entrega independiente evita exponer 00_ANALISIS_GENERAL.
create_delivery = QMessageBox.question(
    iface.mainWindow(), "GeoPackage de entrega",
    "¿Desea crear ahora un GeoPackage independiente para el agricultor?",
    QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
)
delivery_path = None
if create_delivery == QMessageBox.Yes:
    delivery_dialog = DeliveryDialog(sorted(thematic_layers), iface.mainWindow())
    if delivery_dialog.exec_() == QDialog.Accepted:
        delivery_path, selected_names = delivery_dialog.selection()
        first = True
        for layer_name in selected_names:
            source_theme = thematic_layers[layer_name]
            write_layer_to_gpkg(
                source_theme, delivery_path, layer_name,
                overwrite_file=first,
            )
            first = False
            delivered = QgsVectorLayer(
                f"{delivery_path}|layername={layer_name}", layer_name, "ogr"
            )
            if delivered.isValid():
                style = QgsMapLayerStyle()
                style.readFromLayer(source_theme)
                style.writeToLayer(delivered)
                delivered.saveStyleToDatabase(
                    layer_name, "Estilo de entrega", True, ""
                )

# Calcular el resumen antes de retirar la capa temporal: removeMapLayer elimina
# inmediatamente el objeto C++ asociado y ya no permite llamar getFeatures().
valid_cells = sum(
    1 for feature in output.getFeatures()
    if str(feature["estado"]) == "PREVIO_VALIDO"
)
QgsProject.instance().addMapLayer(saved_layer)
QgsProject.instance().removeMapLayer(output.id())
print("\nMapa previo en retícula terminado")
print(f"  Tamaño de celda: {GRID_SIZE_M:g} × {GRID_SIZE_M:g} m")
print(f"  Puntos asignados: {assigned_points:,}")
print(f"  Celdas generadas: {len(output_features):,}")
print(f"  Celdas válidas: {valid_cells:,}")
print(f"  GeoPackage: {OUTPUT_GPKG}")
print(f"  Informe interno: {REPORT_PATH}")
print(f"  Capa creada: {OUTPUT_LAYER_NAME}")
print("  Simbología activa: rinde (kg/ha)")
print(f"  Estilos guardados en GeoPackage: {len(database_styles)}")
print(f"  Capas temáticas públicas: {len(thematic_layers)}")
if delivery_path:
    print(f"  GeoPackage de entrega: {delivery_path}")
if style_errors:
    print("  Avisos al guardar estilos:")
    for error in style_errors:
        print(f"    - {error}")
print("  Cambiar estilo: clic derecho en la capa > Estilos")

iface.messageBar().pushSuccess(
    "Rendimiento",
    f"Retícula creada: {valid_cells:,} celdas válidas",
)
