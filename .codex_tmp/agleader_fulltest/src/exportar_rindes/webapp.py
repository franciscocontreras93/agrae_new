"""Dependency-light local web application for guided CNH conversion."""

from __future__ import annotations

import cgi
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime
import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import shutil
from threading import Lock
from typing import Any
from urllib.parse import urlparse
import uuid
import webbrowser
import zipfile

from exportar_rindes.exporters.cnh_web_shapefile import write_cnh_web_shapefile


STATIC_ROOT = Path(__file__).with_name("web_static")
MAX_UPLOAD_BYTES = 1_500_000_000
ALLOWED_CRS = {"EPSG:25830", "EPSG:4326"}


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _safe_name(value: str) -> str:
    name = Path(value.replace("\\", "/")).name
    clean = "".join(char for char in name if char.isalnum() or char in "._- ").strip()
    return clean[:120] or "entrada_cnh.zip"


@dataclass
class ConversionJob:
    id: str
    source_name: str
    crs: str
    directory: Path
    status: str = "queued"
    stage: str = "Preparando conversión"
    progress: int = 0
    created_at: str = field(default_factory=_now)
    report: dict[str, Any] | None = None
    error: str | None = None

    def public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source_name": self.source_name,
            "crs": self.crs,
            "status": self.status,
            "stage": self.stage,
            "progress": self.progress,
            "created_at": self.created_at,
            "report": self.report,
            "error": self.error,
            "download_url": f"/api/jobs/{self.id}/download"
            if self.status == "completed"
            else None,
        }


class JobStore:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.jobs: dict[str, ConversionJob] = {}
        self.lock = Lock()
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="cnh-export")

    def create(self, uploaded: Any, source_name: str, crs: str) -> ConversionJob:
        if crs not in ALLOWED_CRS:
            raise ValueError("Selecciona un CRS permitido.")
        job_id = uuid.uuid4().hex
        directory = self.root / job_id
        directory.mkdir(parents=True)
        source = directory / "source.zip"
        with source.open("wb") as target:
            shutil.copyfileobj(uploaded, target, length=1024 * 1024)
        if source.stat().st_size == 0 or not zipfile.is_zipfile(source):
            shutil.rmtree(directory)
            raise ValueError("El archivo no es un ZIP válido.")
        job = ConversionJob(job_id, _safe_name(source_name), crs, directory)
        with self.lock:
            self.jobs[job_id] = job
        self.executor.submit(self._run, job)
        return job

    def get(self, job_id: str) -> ConversionJob | None:
        with self.lock:
            return self.jobs.get(job_id)

    def _update(self, job: ConversionJob, **values: Any) -> None:
        with self.lock:
            for key, value in values.items():
                setattr(job, key, value)

    def _run(self, job: ConversionJob) -> None:
        source = job.directory / "source.zip"
        result_dir = job.directory / "result"
        shp = result_dir / "rindes_cnh.shp"
        package = job.directory / "rindes_cnh_shp.zip"

        def progress(done: int, total: int) -> None:
            percent = min(96, max(4, round(done * 92 / total))) if total else 4
            self._update(
                job,
                progress=percent,
                stage=f"Extrayendo puntos CNH · {done:,} de {total:,}",
            )

        try:
            self._update(job, status="running", stage="Leyendo estructura CNH", progress=2)
            report = write_cnh_web_shapefile(
                source, shp, target_crs=job.crs, progress_callback=progress
            )
            self._update(job, stage="Empaquetando SHP e informe", progress=98)
            with zipfile.ZipFile(package, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for path in sorted(result_dir.iterdir()):
                    archive.write(path, arcname=path.name)
            self._update(
                job,
                status="completed",
                stage="Conversión completada",
                progress=100,
                report=report,
            )
        except Exception as exc:  # background boundary: expose a safe, useful message
            self._update(job, status="failed", stage="No se pudo convertir", error=str(exc))


class AppServer(ThreadingHTTPServer):
    def __init__(self, address: tuple[str, int], storage: Path) -> None:
        super().__init__(address, AppHandler)
        self.job_store = JobStore(storage)


class AppHandler(BaseHTTPRequestHandler):
    server: AppServer

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _json(self, payload: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _file(self, path: Path, *, download_name: str | None = None) -> None:
        if not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mimetypes.guess_type(path.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(path.stat().st_size))
        if download_name:
            self.send_header("Content-Disposition", f'attachment; filename="{download_name}"')
        self.end_headers()
        with path.open("rb") as handle:
            shutil.copyfileobj(handle, self.wfile, length=1024 * 1024)

    def do_GET(self) -> None:  # noqa: N802
        route = urlparse(self.path).path
        if route == "/api/health":
            self._json({"status": "ok", "service": "exportar-rindes"})
            return
        if route.startswith("/api/jobs/"):
            parts = route.strip("/").split("/")
            job = self.server.job_store.get(parts[2]) if len(parts) >= 3 else None
            if not job:
                self._json({"error": "Trabajo no encontrado."}, HTTPStatus.NOT_FOUND)
            elif len(parts) == 4 and parts[3] == "download":
                if job.status != "completed":
                    self._json({"error": "La descarga todavía no está disponible."}, 409)
                else:
                    self._file(job.directory / "rindes_cnh_shp.zip", download_name="rindes_cnh_shp.zip")
            else:
                self._json(job.public())
            return
        static_name = "index.html" if route == "/" else route.lstrip("/")
        if static_name not in {"index.html", "app.css", "app.js"}:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        self._file(STATIC_ROOT / static_name)

    def do_POST(self) -> None:  # noqa: N802
        if urlparse(self.path).path != "/api/jobs":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > MAX_UPLOAD_BYTES:
            self._json({"error": "Tamaño de carga vacío o superior a 1,5 GB."}, 413)
            return
        content_type = self.headers.get("Content-Type", "")
        if not content_type.startswith("multipart/form-data"):
            self._json({"error": "La carga debe ser multipart/form-data."}, 415)
            return
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": content_type,
                "CONTENT_LENGTH": str(length),
            },
        )
        upload = form["file"] if "file" in form else None
        crs = form.getfirst("crs", "EPSG:25830")
        accepted = form.getfirst("accept_hypotheses", "false") == "true"
        if upload is None or not getattr(upload, "filename", ""):
            self._json({"error": "Selecciona una exportación CNH en ZIP."}, 400)
            return
        if not accepted:
            self._json({"error": "Debes aceptar el carácter experimental de los campos."}, 400)
            return
        try:
            job = self.server.job_store.create(upload.file, upload.filename, crs)
        except ValueError as exc:
            self._json({"error": str(exc)}, 400)
            return
        self._json(job.public(), HTTPStatus.ACCEPTED)


def serve(
    host: str = "127.0.0.1",
    port: int = 8765,
    *,
    storage: Path = Path("outputs/web_jobs"),
    open_browser: bool = True,
) -> None:
    """Run the local-only guided converter until interrupted."""
    server = AppServer((host, port), storage)
    url = f"http://{host}:{server.server_port}/"
    print(f"Exportar Rindes disponible en {url}")
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        server.server_close()
