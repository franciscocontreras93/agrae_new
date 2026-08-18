from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from urllib.request import urlopen

from exportar_rindes.webapp_filtered import FilteredServer


def test_filtered_server_exposes_guided_filter_panel() -> None:
    with TemporaryDirectory() as directory:
        server = FilteredServer(("127.0.0.1", 0), Path(directory))
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with urlopen(f"http://127.0.0.1:{server.server_port}/", timeout=3) as response:
                page = response.read().decode("utf-8")
                assert "Limpieza automática y auditable" in page
                assert "MINY · MAXY" in page
                assert "Corregir, filtrar y generar SHP" in page
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)
