"""Helpers puros para construir fuentes WFS del plugin."""

from urllib.parse import quote, urlencode


LOTES_WFS_URL = "https://gis.agrae.es/geoserver/agrae/wfs"
LOTES_WFS_TYPENAME = "agrae:lotes_campania"


def _positive_int(value, parameter):
    """Devuelve un identificador positivo o informa claramente del error."""
    if isinstance(value, bool):
        raise ValueError(f"{parameter} debe ser un entero positivo")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{parameter} debe ser un entero positivo") from exc
    if parsed <= 0 or str(value).strip() != str(parsed):
        raise ValueError(f"{parameter} debe ser un entero positivo")
    return parsed


def build_lotes_wfs_uri(idcampania, idexplotacion):
    """Construye la URI QGIS WFS, limitada a una campaña y explotación."""
    campaign_id = _positive_int(idcampania, "idcampania")
    holding_id = _positive_int(idexplotacion, "idexplotacion")
    view_params = f"idcampania:{campaign_id};idexplotacion:{holding_id}"
    url = f"{LOTES_WFS_URL}?{urlencode({'VIEWPARAMS': view_params}, quote_via=quote)}"
    return (
        "pagingEnabled='false' "
        "preferCoordinatesForWfsT11='false' restrictToRequestBBOX='0' "
        f"srsname='EPSG:4326' typename='{LOTES_WFS_TYPENAME}' "
        f"url='{url}' version='auto'"
    )
