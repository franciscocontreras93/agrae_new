from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from urllib.request import urlopen

from exportar_rindes.webapp import AppServer, _safe_name


def test_safe_name_removes_paths_and_unsafe_characters() -> None:
    assert _safe_name("../../mi<mapa>.cn1.zip") == "mimapa.cn1.zip"
    assert _safe_name("C:\\datos\\cosecha.zip") == "cosecha.zip"


def test_local_server_exposes_health_and_interface() -> None:
    with TemporaryDirectory() as directory:
        server = AppServer(("127.0.0.1", 0), Path(directory))
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            with urlopen(f"{base}/api/health", timeout=3) as response:
                assert response.status == 200
                assert b'"status": "ok"' in response.read()
            with urlopen(f"{base}/", timeout=3) as response:
                page = response.read().decode("utf-8")
                assert response.status == 200
                assert "De la cosechadora al mapa" in page
                assert "Generar Shapefile" in page
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)
