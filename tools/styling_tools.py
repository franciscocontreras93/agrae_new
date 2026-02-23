from dataclasses import dataclass
from qgis.PyQt.QtGui import QColor
from qgis.core import (
    QgsRasterShader,
    QgsColorRampShader,
    QgsSingleBandPseudoColorRenderer,
)

@dataclass(frozen=True)
class _IndexStylePreset:
    name: str
    vmin: float
    vmax: float
    stops: list  # [(value: float, color: QColor, label: str)]


def _index_presets() -> dict[int, _IndexStylePreset]:
    """
    Diccionario index_id -> preset.
    Si mañana agregas otro índice, lo añades aquí y ya.
    """
    return {
        1: _IndexStylePreset(
            name="NDVI",
            vmin=0.0,
            vmax=1.0,
            stops=[
                (0.00, QColor("#d7191c"), "0.0000"),
                (0.25, QColor("#fdae61"), "0.2500"),
                (0.50, QColor("#ffffbf"), "0.5000"),
                (0.75, QColor("#a6d96a"), "0.7500"),
                (1.00, QColor("#1a9641"), "1.0000"),
            ],
        ),
        2: _IndexStylePreset(
            name="NDRE",
            vmin=0.0,
            vmax=1.0,
            stops=[
                (0.00, QColor("#d73027"), "0.0000"),
                (0.25, QColor("#fc8d59"), "0.2500"),
                (0.50, QColor("#fee08b"), "0.5000"),
                (0.75, QColor("#91cf60"), "0.7500"),
                (1.00, QColor("#1a9850"), "1.0000"),
            ],
        ),
        3: _IndexStylePreset(
            name="SAVI",
            vmin=0.0,
            vmax=1.0,
            stops=[
                (0.00, QColor("#6b4f2a"), "0.0000"),  # marrón: suelo desnudo
                (0.10, QColor("#d8caa8"), "0.1000"),  # beige: suelo / muy poca vegetación
                (0.25, QColor("#fee08b"), "0.2500"),  # amarillo: vegetación baja
                (0.50, QColor("#d9ef8b"), "0.5000"),  # verde pálido: moderada
                (0.75, QColor("#91cf60"), "0.7500"),  # verde oliva: buena cobertura
                (1.00, QColor("#1a9850"), "1.0000"),  # verde intenso: densa
            ],
        )
    }


def _apply_index_style( rlayer, preset: _IndexStylePreset, band: int = 1) -> None:
    """
    Aplica pseudocolor monobanda con min/max forzados.
    """
    if not rlayer or not rlayer.isValid():
        return

    provider = rlayer.dataProvider()

    ramp_shader = QgsColorRampShader()
    ramp_shader.setColorRampType(QgsColorRampShader.Interpolated)

    ramp_items = [
        QgsColorRampShader.ColorRampItem(val, color, label)
        for (val, color, label) in preset.stops
    ]
    ramp_shader.setColorRampItemList(ramp_items)
    ramp_shader.setClip(False)

    raster_shader = QgsRasterShader()
    raster_shader.setRasterShaderFunction(ramp_shader)

    renderer = QgsSingleBandPseudoColorRenderer(provider, band, raster_shader)

    # Forzar min/max (0..1)
    try:
        renderer.setClassificationMin(float(preset.vmin))
        renderer.setClassificationMax(float(preset.vmax))
    except Exception:
        pass

    rlayer.setRenderer(renderer)
    rlayer.triggerRepaint()