from exportar_rindes.readers.cnh.field_catalog import ALL_FIELD_CATALOG


def test_all_fields_catalog_is_complete_and_shapefile_safe():
    assert len(ALL_FIELD_CATALOG) == 46
    assert all(len(name) <= 10 for name in ALL_FIELD_CATALOG)
    assert ALL_FIELD_CATALOG["h_u34"]["status"] == "unknown"
    assert "volume" in ALL_FIELD_CATALOG["h_u34"]["meaning"]
    assert ALL_FIELD_CATALOG["moist_pc"]["status"] == "candidate"
