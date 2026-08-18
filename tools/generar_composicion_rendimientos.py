r"""Crea un atlas multipágina de rendimiento y eficiencia en QGIS.

Ejecución desde la consola Python de QGIS::

    exec(open(
        r"C:\Users\Ing_G\AppData\Roaming\QGIS\QGIS3\profiles\default"
        r"\python\plugins\agrae\tools\generar_composicion_rendimientos.py",
        encoding="utf-8"
    ).read())

El diseño toma como referencia la estructura A4 de ``prescripcion_dev.qpt``:
dos mapas por página, franja lateral con datos del lote, leyendas automáticas,
escala, fecha y logotipo. No modifica la capa fuente.
"""

from collections import defaultdict
from math import isfinite
import os

from qgis.PyQt.QtCore import Qt, QVariant
from qgis.PyQt.QtGui import QColor, QFont
from qgis.PyQt.QtWidgets import QInputDialog, QMessageBox
from qgis.core import (
    QgsFeature,
    QgsField,
    QgsGeometry,
    QgsGraduatedSymbolRenderer,
    QgsLayoutItemLabel,
    QgsLayoutItemLegend,
    QgsLayoutItemMap,
    QgsLayoutItemPage,
    QgsLayoutItemPicture,
    QgsLayoutItemScaleBar,
    QgsLayoutItemShape,
    QgsLayoutPoint,
    QgsLayoutSize,
    QgsLegendStyle,
    QgsPrintLayout,
    QgsProject,
    QgsRendererRange,
    QgsSymbol,
    QgsTextFormat,
    QgsUnitTypes,
    QgsVectorLayer,
    QgsWkbTypes,
)
from qgis.utils import iface


LAYOUT_NAME_DEFAULT = "Informe de rendimiento"
VALID_STATES = {"PREVIO_VALIDO", "REVISAR_SOLAPE"}
STYLE_SAMPLE_LIMIT = 25000
SEQUENTIAL = ["#d73027", "#fc8d59", "#fee08b", "#91cf60", "#1a9850"]
DIVERGING = ["#b2182b", "#ef8a62", "#f7f7f7", "#67a9cf", "#2166ac"]
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AGRAE_LOGO = os.path.join(SCRIPT_DIR, "img", "agrae_logo.png")

# Dos mapas por página. Los campos inexistentes se omiten automáticamente.
THEMES = [
    ("Rendimiento final", "rinde", "kg/ha", "quantile", None),
    # ("Rendimiento antes del corte", "rinde_pre", "kg/ha", "quantile", None),
    # ("Exceso recortado", "exceso", "kg/ha", "quantile", None),
    # ("Cobertura del monitor", "cobertura", "%", "quantile", None),
    ("Biomasa aérea", "biomasa", "kg/ha", "quantile", None),
    ("Residuo estimado", "residuo", "kg/ha", "quantile", None),
    ("Materia seca de cosecha", "ms_cosecha", "kg/ha", "quantile", None),
    ("Materia seca de residuo", "ms_residuo", "kg/ha", "quantile", None),
    ("N extraído", "n_extraido", "kg N/ha", "quantile", None),
    ("P extraído", "p_extraido", "kg P/ha", "quantile", None),
    ("K extraído", "k_extraido", "kg K/ha", "quantile", None),
    ("Balance aparente de N", "balance_n", "kg N/ha", "centered", 0.0),
    ("Balance aparente de P", "balance_p", "kg P/ha", "centered", 0.0),
    ("Balance aparente de K", "balance_k", "kg K/ha", "centered", 0.0),
    ("NUE", "nue", "kg cosecha/kg N", "quantile", None),
    ("PUE", "pue", "kg cosecha/kg P", "quantile", None),
    ("KUE", "kue", "kg cosecha/kg K", "quantile", None),
    ("Cumplimiento del objetivo", "cumpl_pct", "%", "centered", 100.0),
]


def numeric(value):
    try:
        result = float(value)
        return result if isfinite(result) else None
    except (TypeError, ValueError):
        return None


def percentile(values, fraction):
    if not values:
        return None
    if len(values) == 1:
        return values[0]
    position = (len(values) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(values) - 1)
    weight = position - lower
    return values[lower] * (1 - weight) + values[upper] * weight


def choose_from_list(title, prompt, items, default_index=0):
    value, accepted = QInputDialog.getItem(
        iface.mainWindow(), title, prompt, items, default_index, False,
    )
    if not accepted:
        raise RuntimeError("Proceso cancelado por el usuario.")
    return items.index(value)


def choose_field(layer, prompt, preferred):
    names = [field.name() for field in layer.fields()]
    default = next((names.index(name) for name in preferred if name in names), 0)
    return names[choose_from_list("Composición de rendimientos", prompt, names, default)]


def choose_layers_and_relation():
    polygon_layers = [
        layer for layer in QgsProject.instance().mapLayers().values()
        if isinstance(layer, QgsVectorLayer)
        and layer.isValid()
        and QgsWkbTypes.geometryType(layer.wkbType()) == QgsWkbTypes.PolygonGeometry
    ]
    theme_fields = {theme[1] for theme in THEMES}
    candidates = [
        layer for layer in polygon_layers
        if theme_fields.intersection(field.name() for field in layer.fields())
    ]
    if not candidates:
        raise RuntimeError("No hay una capa poligonal cargada que contenga iddata.")
    labels = [f"{layer.name()} — {layer.featureCount():,} celdas" for layer in candidates]
    default_index = next(
        (i for i, layer in enumerate(candidates) if layer.name() == "MAPA_PREVIO_RENDIMIENTO"),
        0,
    )
    source = candidates[choose_from_list(
        "Composición de rendimientos", "Capa de resultados", labels, default_index
    )]
    lot_candidates = [layer for layer in polygon_layers if layer.id() != source.id()]
    if not lot_candidates:
        raise RuntimeError("Debe cargar también la capa poligonal oficial de lotes.")
    lot_labels = [f"{layer.name()} — {layer.featureCount():,} lotes" for layer in lot_candidates]
    lot_default = next(
        (i for i, layer in enumerate(lot_candidates) if "lote" in layer.name().lower()), 0
    )
    lots = lot_candidates[choose_from_list(
        "Composición de rendimientos", "Capa oficial de lotes", lot_labels, lot_default
    )]
    source_key = choose_field(
        source, "Campo identificador del lote en rendimientos", ("idlote", "lote_id", "id")
    )
    lot_key = choose_field(
        lots, "Campo identificador correspondiente en la capa de lotes",
        ("idlote", "id", "lote_id"),
    )
    lot_name = choose_field(
        lots, "Campo con el nombre del lote", ("lote", "nombre", "name", lot_key)
    )
    return source, lots, source_key, lot_key, lot_name


def collect_style_values(layer, field_names):
    """Una sola pasada y muestra acotada para evitar bloquear QGIS."""
    result = {field_name: [] for field_name in field_names}
    has_state = layer.fields().indexOf("estado") >= 0
    stride = max(1, int(layer.featureCount() / STYLE_SAMPLE_LIMIT))
    for index, feature in enumerate(layer.getFeatures()):
        if index % stride:
            continue
        if has_state and str(feature["estado"]) not in VALID_STATES:
            continue
        for field_name in field_names:
            value = numeric(feature[field_name])
            if value is not None:
                result[field_name].append(value)
    for field_name in result:
        result[field_name].sort()
    return result


def symbol(layer, color):
    item = QgsSymbol.defaultSymbol(layer.geometryType())
    item.setColor(QColor(color))
    item.setOpacity(0.88)
    return item


def renderer_for(layer, field_name, style_type, center, style_values):
    values = style_values.get(field_name, [])
    if not values:
        return None
    ranges = []
    if style_type == "centered":
        radius = max(abs(value - center) for value in values) or 1.0
        offsets = (-radius, -0.5 * radius, -0.05 * radius,
                   0.05 * radius, 0.5 * radius, radius)
        for index, color in enumerate(DIVERGING):
            lower, upper = center + offsets[index], center + offsets[index + 1]
            ranges.append(QgsRendererRange(
                lower, upper, symbol(layer, color), f"{lower:,.1f} – {upper:,.1f}",
            ))
    elif values[0] == values[-1]:
        ranges.append(QgsRendererRange(
            values[0], values[-1], symbol(layer, SEQUENTIAL[3]), f"{values[0]:,.1f}",
        ))
    else:
        breaks = [percentile(values, index / 5.0) for index in range(6)]
        for index, color in enumerate(SEQUENTIAL):
            lower, upper = breaks[index], breaks[index + 1]
            if upper == lower and index not in (0, 4):
                continue
            ranges.append(QgsRendererRange(
                lower, upper, symbol(layer, color), f"{lower:,.1f} – {upper:,.1f}",
            ))
    return QgsGraduatedSymbolRenderer(field_name, ranges)


def make_coverage_layer(source, lots, source_key, lot_key, lot_name):
    """Copia los perímetros oficiales con resultado y los usa como atlas."""
    result_keys = set()
    crop_by_key = {}
    has_crop = source.fields().indexOf("cultivo") >= 0
    for feature in source.getFeatures():
        key = str(feature[source_key])
        result_keys.add(key)
        if has_crop and key not in crop_by_key:
            crop_by_key[key] = str(feature["cultivo"] or "")
    coverage = QgsVectorLayer(
        f"MultiPolygon?crs={source.crs().authid()}", "Lotes", "memory"
    )
    provider = coverage.dataProvider()
    provider.addAttributes([
        QgsField("join_key", QVariant.String, len=80),
        QgsField("lote", QVariant.String, len=120),
        QgsField("cultivo", QVariant.String, len=80),
        QgsField("explotacion", QVariant.String, len=120),
        QgsField("direccion", QVariant.String, len=180),
    ])
    coverage.updateFields()
    features = []
    exploitation_field = next(
        (name for name in ("explotacion", "nombre_explotacion", "finca")
         if lots.fields().indexOf(name) >= 0), None
    )
    address_field = next(
        (name for name in ("direccionenvio", "direccion", "domicilio")
         if lots.fields().indexOf(name) >= 0), None
    )
    transform = None
    if lots.crs() != source.crs():
        from qgis.core import QgsCoordinateTransform
        transform = QgsCoordinateTransform(
            lots.crs(), source.crs(), QgsProject.instance().transformContext()
        )
    for lot in lots.getFeatures():
        key = str(lot[lot_key])
        if key not in result_keys or lot.geometry().isNull():
            continue
        feature = QgsFeature(coverage.fields())
        geometry = QgsGeometry(lot.geometry())
        if transform:
            geometry.transform(transform)
        if not QgsWkbTypes.isMultiType(geometry.wkbType()):
            geometry.convertToMultiType()
        feature.setGeometry(geometry)
        feature.setAttributes([
            key, str(lot[lot_name] or key), crop_by_key.get(key, ""),
            str(lot[exploitation_field] or "") if exploitation_field else "",
            str(lot[address_field] or "") if address_field else "",
        ])
        features.append(feature)
    provider.addFeatures(features)
    coverage.updateExtents()
    return coverage


def add_item(layout, item, x, y, width, height, page):
    layout.addLayoutItem(item)
    item.attemptMove(
        QgsLayoutPoint(x, y, QgsUnitTypes.LayoutMillimeters), True, False, page
    )
    item.attemptResize(QgsLayoutSize(width, height, QgsUnitTypes.LayoutMillimeters))
    return item


def text_format(size, bold=False, color="#222222"):
    result = QgsTextFormat()
    font = QFont("Arial", size)
    font.setBold(bold)
    result.setFont(font)
    result.setSize(size)
    result.setColor(QColor(color))
    return result


def add_label(layout, text, x, y, width, height, page, size=9, bold=False,
              align=Qt.AlignLeft | Qt.AlignVCenter):
    label = QgsLayoutItemLabel(layout)
    label.setText(text)
    label.setTextFormat(text_format(size, bold))
    if align & Qt.AlignHCenter:
        horizontal = Qt.AlignHCenter
    elif align & Qt.AlignRight:
        horizontal = Qt.AlignRight
    else:
        horizontal = Qt.AlignLeft
    label.setHAlign(horizontal)
    label.setVAlign(Qt.AlignVCenter)
    add_item(layout, label, x, y, width, height, page)
    return label


source, lots, source_key, lot_key, lot_name = choose_layers_and_relation()
available = {field.name() for field in source.fields()}
themes = [theme for theme in THEMES if theme[1] in available]
if not themes:
    raise RuntimeError("La capa no contiene ninguno de los indicadores previstos.")
style_values = collect_style_values(source, [theme[1] for theme in themes])

layout_name, accepted = QInputDialog.getText(
    iface.mainWindow(), "Composición de rendimientos", "Nombre de la composición",
    text=LAYOUT_NAME_DEFAULT,
)
if not accepted or not layout_name.strip():
    raise RuntimeError("Proceso cancelado por el usuario.")
layout_name = layout_name.strip()

project = QgsProject.instance()
manager = project.layoutManager()
for previous in manager.printLayouts():
    if previous.name() == layout_name:
        manager.removeLayout(previous)

# Capas temáticas independientes: cada mapa conserva su renderer.
root = project.layerTreeRoot()
old_group = root.findGroup("_COMPOSICION_RENDIMIENTOS")
if old_group:
    root.removeChildNode(old_group)
group = root.addGroup("_COMPOSICION_RENDIMIENTOS")
group.setItemVisibilityChecked(False)
theme_layers = {}
for title, field_name, unit, style_type, center in themes:
    # clone() reutiliza el proveedor ya abierto y evita recargar 18 veces los
    # estilos guardados en la tabla layer_styles del GeoPackage.
    clone = source.clone()
    clone.setName(f"{title} [{field_name}]")
    if not clone.isValid():
        continue
    renderer = renderer_for(clone, field_name, style_type, center, style_values)
    if renderer is None:
        continue
    clone.setRenderer(renderer)
    project.addMapLayer(clone, False)
    group.addLayer(clone)
    theme_layers[field_name] = clone

themes = [theme for theme in themes if theme[1] in theme_layers]
coverage = make_coverage_layer(source, lots, source_key, lot_key, lot_name)
if coverage.featureCount() == 0:
    raise RuntimeError(
        "No se encontraron coincidencias entre los identificadores de la capa "
        "de rendimiento y la capa oficial de lotes."
    )
# Perímetro oficial visible sobre las retículas.
boundary_symbol = QgsSymbol.defaultSymbol(coverage.geometryType())
boundary_symbol.setColor(QColor(255, 255, 255, 0))
boundary_layer = boundary_symbol.symbolLayer(0)
if hasattr(boundary_layer, "setStrokeColor"):
    boundary_layer.setStrokeColor(QColor("#202020"))
if hasattr(boundary_layer, "setStrokeWidth"):
    boundary_layer.setStrokeWidth(0.6)
coverage.renderer().setSymbol(boundary_symbol)
project.addMapLayer(coverage, False)
group.addLayer(coverage)

layout = QgsPrintLayout(project)
layout.initializeDefaults()
layout.setName(layout_name)
layout.renderContext().setDpi(200)
manager.addLayout(layout)

page_count = (len(themes) + 1) // 2
pages = layout.pageCollection()
for page_index in range(page_count):
    if page_index == 0:
        page = pages.page(0)
    else:
        page = QgsLayoutItemPage(layout)
        pages.addPage(page)
    page.setPageSize("A4", QgsLayoutItemPage.Orientation.Portrait)

for page_index in range(page_count):
    # Banda lateral y cabecera inspiradas en prescripcion_dev.qpt.
    side = QgsLayoutItemShape(layout)
    side.setShapeType(QgsLayoutItemShape.Rectangle)
    side.setBackgroundColor(QColor("#f4f6f3"))
    side.setFrameEnabled(True)
    add_item(layout, side, 144, 5, 61, 287, page_index)
    add_label(layout, "INFORME DE RENDIMIENTO", 147, 7, 55, 9,
              page_index, 11, True, Qt.AlignHCenter | Qt.AlignVCenter)
    add_label(layout,
              "[% upper(attribute(@atlas_feature,'explotacion')) %]\n"
              "Lote: [% attribute(@atlas_feature,'lote') %]\n"
              "Cultivo: [% attribute(@atlas_feature,'cultivo') %]\n"
              "[% attribute(@atlas_feature,'direccion') %]",
              147, 18, 55, 25, page_index, 8, True)
    add_label(layout, "Revisado: [% format_date(now(),'dd/MM/yyyy') %]",
              147, 268, 55, 8, page_index, 7)
    if os.path.isfile(AGRAE_LOGO):
        picture = QgsLayoutItemPicture(layout)
        picture.setPicturePath(AGRAE_LOGO)
        add_item(layout, picture, 150, 277, 48, 10, page_index)

    for slot in range(2):
        theme_index = page_index * 2 + slot
        if theme_index >= len(themes):
            continue
        title, field_name, unit, _, _ = themes[theme_index]
        layer = theme_layers[field_name]
        y_title = 7 if slot == 0 else 151
        y_map = 17 if slot == 0 else 161
        y_legend = 48 if slot == 0 else 192
        add_label(layout, f"{title} ({unit})", 10, y_title, 130, 8,
                  page_index, 11, True, Qt.AlignHCenter | Qt.AlignVCenter)
        map_item = QgsLayoutItemMap(layout)
        map_item.setFrameEnabled(True)
        map_item.setLayers([coverage, layer])
        map_item.setAtlasDriven(True)
        map_item.setAtlasScalingMode(QgsLayoutItemMap.Auto)
        map_item.setAtlasMargin(0.08)
        add_item(layout, map_item, 10, y_map, 130, 125, page_index)

        legend = QgsLayoutItemLegend(layout)
        legend.setTitle(title)
        legend.setLinkedMap(map_item)
        legend.setLegendFilterByMapEnabled(True)
        legend.setAutoUpdateModel(True)
        legend.setStyleFont(QgsLegendStyle.Title, QFont("Arial", 9, QFont.Bold))
        legend.setStyleFont(QgsLegendStyle.SymbolLabel, QFont("Arial", 7))
        add_item(layout, legend, 147, y_legend, 55, 57, page_index)

        stats_y = 108 if slot == 0 else 252
        sample = style_values.get(field_name, [])
        summary = (
            f"Rango representado\n{sample[0]:,.1f} – {sample[-1]:,.1f} {unit}"
            if sample else f"Unidad: {unit}"
        )
        add_label(layout, summary, 147, stats_y, 55, 18, page_index, 7)

        scale = QgsLayoutItemScaleBar(layout)
        scale.setStyle("Single Box")
        scale.setLinkedMap(map_item)
        scale.setUnits(QgsUnitTypes.DistanceMeters)
        scale.setNumberOfSegments(2)
        scale.setNumberOfSegmentsLeft(0)
        scale.setUnitLabel("m")
        scale.setFont(QFont("Arial", 7))
        scale.applyDefaultSize()
        add_item(layout, scale, 13, y_map + 115, 45, 6, page_index)

atlas = layout.atlas()
atlas.setCoverageLayer(coverage)
atlas.setPageNameExpression("'Lote ' || \"lote\"")
atlas.setFilenameExpression("'rendimiento_' || regexp_replace(\"lote\", '[^A-Za-z0-9_-]', '_')")
atlas.setEnabled(True)
atlas.updateFeatures()
if atlas.count() > 0:
    atlas.seekTo(0)

iface.openLayoutDesigner(layout)
QMessageBox.information(
    iface.mainWindow(), "Composición creada",
    f"Se creó «{layout_name}» con {page_count} páginas temáticas y "
    f"{atlas.count()} lotes en el atlas.\n\n"
    "Abra el panel Atlas del diseñador para recorrer o exportar los lotes.",
)
