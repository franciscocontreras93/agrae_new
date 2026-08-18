"""Guided local web application with an auditable yield-cleaning panel."""

from __future__ import annotations

import cgi
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import shutil
from threading import Lock
from typing import Any
from urllib.parse import urlparse
import uuid
import webbrowser
import zipfile

from exportar_rindes.exporters.cnh_filtered_shapefile import (
    write_cnh_filtered_shapefile,
)
from exportar_rindes.quality import FilterSettings
from exportar_rindes.webapp import (
    ALLOWED_CRS,
    MAX_UPLOAD_BYTES,
    AppHandler,
    ConversionJob,
    ThreadingHTTPServer,
    _safe_name,
)


FILTERED_STATIC = Path(__file__).with_name("web_static")


class FilteredJobStore:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.jobs: dict[str, ConversionJob] = {}
        self.lock = Lock()
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="cnh-filter")

    def create(
        self,
        uploaded: Any,
        source_name: str,
        crs: str,
        settings: FilterSettings,
        output_mode: str,
    ) -> ConversionJob:
        if crs not in ALLOWED_CRS:
            raise ValueError("Selecciona un CRS permitido.")
        settings.validate()
        if output_mode not in {"clean", "all"}:
            raise ValueError("Selecciona un modo de salida permitido.")
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
        job.settings = settings  # type: ignore[attr-defined]
        job.output_mode = output_mode  # type: ignore[attr-defined]
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
        shp = result_dir / "rindes_filtrados.shp"
        package = job.directory / "rindes_filtrados_shp.zip"
        settings: FilterSettings = job.settings  # type: ignore[attr-defined]

        def progress(done: int, total: int, stage: str) -> None:
            fraction = done / total if total else 0
            if stage.startswith("Calculando"):
                percent = 2 + round(fraction * 38)
            else:
                start = 42 if settings.standard_deviation else 3
                percent = start + round(fraction * (96 - start))
            self._update(job, progress=min(percent, 96), stage=f"{stage} · {done:,}/{total:,}")

        try:
            self._update(job, status="running", stage="Leyendo estructura CNH", progress=1)
            report = write_cnh_filtered_shapefile(
                source,
                shp,
                settings=settings,
                target_crs=job.crs,
                output_mode=job.output_mode,  # type: ignore[attr-defined]
                progress_callback=progress,
            )
            self._update(job, stage="Empaquetando mapa e informe", progress=98)
            with zipfile.ZipFile(package, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for path in sorted(result_dir.iterdir()):
                    archive.write(path, arcname=path.name)
            self._update(
                job,
                status="completed",
                stage="Limpieza completada",
                progress=100,
                report=report,
            )
        except Exception as exc:
            self._update(job, status="failed", stage="No se pudo filtrar", error=str(exc))


class FilteredServer(ThreadingHTTPServer):
    def __init__(self, address: tuple[str, int], storage: Path) -> None:
        super().__init__(address, FilteredHandler)
        self.job_store = FilteredJobStore(storage)


class FilteredHandler(AppHandler):
    server: FilteredServer

    def do_GET(self) -> None:  # noqa: N802
        route = urlparse(self.path).path
        names = {
            "/": "filtered.html",
            "/filtered.css": "filtered.css",
            "/filtered.js": "filtered.js",
        }
        if route in names:
            self._file(FILTERED_STATIC / names[route])
            return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        if urlparse(self.path).path != "/api/jobs":
            super().do_POST()
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
        if upload is None or not getattr(upload, "filename", ""):
            self._json({"error": "Selecciona una exportación CNH en ZIP."}, 400)
            return
        if form.getfirst("accept_hypotheses", "false") != "true":
            self._json({"error": "Debes aceptar el carácter experimental."}, 400)
            return

        def enabled(name: str, default: bool = True) -> bool:
            return form.getfirst(name, str(default).lower()) == "true"

        def number(name: str, default: float) -> float:
            try:
                return float(form.getfirst(name, str(default)))
            except ValueError as exc:
                raise ValueError(f"Valor numérico inválido: {name}") from exc

        try:
            settings = FilterSettings(
                yield_range=enabled("yield_range"),
                min_yield_t_ha=number("min_yield", 0),
                max_yield_t_ha=number("max_yield", 11),
                speed_range=enabled("speed_range"),
                min_speed_m_s=number("min_speed", 0.5),
                max_speed_m_s=number("max_speed", 4),
                smooth_speed=enabled("smooth_speed"),
                max_speed_change_ratio=number("speed_change_pct", 20) / 100,
                minimum_width=enabled("minimum_width"),
                min_width_m=number("min_width", 2.7),
                standard_deviation=enabled("standard_deviation", False),
                max_yield_stddev=number("stddev", 3),
                moisture_range=enabled("moisture_range"),
                min_moisture_pct=number("min_moisture", 0),
                max_moisture_pct=number("max_moisture", 40),
            )
            job = self.server.job_store.create(
                upload.file,
                upload.filename,
                form.getfirst("crs", "EPSG:25830"),
                settings,
                form.getfirst("output_mode", "clean"),
            )
        except ValueError as exc:
            self._json({"error": str(exc)}, 400)
            return
        self._json(job.public(), 202)


def serve_filtered(
    host: str = "127.0.0.1",
    port: int = 8765,
    *,
    storage: Path = Path("outputs/filtered_web_jobs"),
    open_browser: bool = True,
) -> None:
    server = FilteredServer((host, port), storage)
    url = f"http://{host}:{server.server_port}/"
    print(f"Exportar Rindes con filtros disponible en {url}")
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        server.server_close()
