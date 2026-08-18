"""Monitor-aware guided web application with auditable default filter profiles."""

from __future__ import annotations

import cgi
from pathlib import Path
import json
import shutil
from threading import Lock
from typing import Any
from urllib.parse import urlparse
import uuid
import webbrowser
import zipfile

from exportar_rindes.exporters.cnh_filtered_shapefile import write_cnh_filtered_shapefile
from exportar_rindes.quality import FilterSettings
from exportar_rindes.quality.monitor_presets import (
    FilterPreset,
    MonitorDetection,
    detect_monitor,
    presets_for_monitor,
)
from exportar_rindes.webapp import ALLOWED_CRS, MAX_UPLOAD_BYTES, ConversionJob
from exportar_rindes.webapp_filtered import (
    FILTERED_STATIC,
    FilteredHandler,
    FilteredJobStore,
    ThreadingHTTPServer,
)


class UploadCatalog:
    def __init__(self, root: Path) -> None:
        self.root = root / "_uploads"
        self.root.mkdir(parents=True, exist_ok=True)
        self.items: dict[str, dict[str, Any]] = {}
        self.lock = Lock()

    def analyze(self, uploaded: Any, source_name: str) -> dict[str, Any]:
        token = uuid.uuid4().hex
        directory = self.root / token
        directory.mkdir(parents=True)
        source = directory / "source.zip"
        with source.open("wb") as target:
            shutil.copyfileobj(uploaded, target, length=1024 * 1024)
        try:
            detection = detect_monitor(source)
            presets = presets_for_monitor(detection)
        except Exception:
            shutil.rmtree(directory)
            raise
        item = {
            "token": token,
            "source": source,
            "source_name": source_name,
            "detection": detection,
            "presets": presets,
        }
        with self.lock:
            self.items[token] = item
        return item

    def get(self, token: str) -> dict[str, Any] | None:
        with self.lock:
            return self.items.get(token)


class PresetJobStore(FilteredJobStore):
    def create_from_catalog(
        self,
        item: dict[str, Any],
        preset: FilterPreset,
        settings: FilterSettings,
        crs: str,
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
        shutil.copy2(item["source"], directory / "source.zip")
        job = ConversionJob(job_id, item["source_name"], crs, directory)
        job.settings = settings  # type: ignore[attr-defined]
        job.output_mode = output_mode  # type: ignore[attr-defined]
        job.detection = item["detection"]  # type: ignore[attr-defined]
        job.preset = preset  # type: ignore[attr-defined]
        with self.lock:
            self.jobs[job_id] = job
        self.executor.submit(self._run, job)
        return job

    def _run(self, job: ConversionJob) -> None:
        source = job.directory / "source.zip"
        result_dir = job.directory / "result"
        shp = result_dir / "rindes_filtrados.shp"
        package = job.directory / "rindes_filtrados_shp.zip"
        settings: FilterSettings = job.settings  # type: ignore[attr-defined]
        detection: MonitorDetection = job.detection  # type: ignore[attr-defined]
        preset: FilterPreset = job.preset  # type: ignore[attr-defined]

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
            report["monitor_detection"] = detection.as_dict()
            report["filter_preset"] = {
                "selected": preset.as_dict(),
                "parameters_modified": settings.as_dict() != preset.settings.as_dict(),
                "effective_settings": settings.as_dict(),
            }
            shp.with_suffix(".quality.json").write_text(
                json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
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


class PresetServer(ThreadingHTTPServer):
    def __init__(self, address: tuple[str, int], storage: Path) -> None:
        super().__init__(address, PresetHandler)
        self.job_store = PresetJobStore(storage)
        self.upload_catalog = UploadCatalog(storage)


class PresetHandler(FilteredHandler):
    server: PresetServer

    def _multipart(self) -> cgi.FieldStorage:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > MAX_UPLOAD_BYTES:
            raise ValueError("Tamaño de carga vacío o superior al límite local.")
        content_type = self.headers.get("Content-Type", "")
        if not content_type.startswith("multipart/form-data"):
            raise ValueError("La petición debe ser multipart/form-data.")
        return cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": content_type,
                "CONTENT_LENGTH": str(length),
            },
        )

    def do_GET(self) -> None:  # noqa: N802
        route = urlparse(self.path).path
        if route == "/":
            page = (FILTERED_STATIC / "filtered.html").read_text(encoding="utf-8")
            page = page.replace("</body>", '<script src="/presets.js" defer></script></body>')
            body = page.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if route == "/presets.js":
            self._file(FILTERED_STATIC / "presets.js")
            return
        if route.startswith("/api/jobs/") and route.endswith("/download"):
            parts = route.strip("/").split("/")
            job = self.server.job_store.get(parts[2]) if len(parts) == 4 else None
            if not job:
                self._json({"error": "Trabajo no encontrado."}, 404)
            elif job.status != "completed":
                self._json({"error": "La descarga todavía no está disponible."}, 409)
            else:
                self._file(
                    job.directory / "rindes_filtrados_shp.zip",
                    download_name="rindes_filtrados_shp.zip",
                )
            return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        route = urlparse(self.path).path
        if route == "/api/presets":
            try:
                form = self._multipart()
                upload = form["file"] if "file" in form else None
                if upload is None or not getattr(upload, "filename", ""):
                    raise ValueError("Selecciona un ZIP CNH.")
                item = self.server.upload_catalog.analyze(upload.file, upload.filename)
            except ValueError as exc:
                self._json({"error": str(exc)}, 400)
                return
            self._json(
                {
                    "upload_token": item["token"],
                    "detection": item["detection"].as_dict(),
                    "presets": [preset.as_dict() for preset in item["presets"]],
                    "recommended_preset": "auto_monitor",
                },
                201,
            )
            return
        if route != "/api/jobs":
            self.send_error(404)
            return
        try:
            form = self._multipart()
            item = self.server.upload_catalog.get(form.getfirst("upload_token", ""))
            if not item:
                raise ValueError("El análisis previo ha caducado; selecciona de nuevo el ZIP.")
            preset_id = form.getfirst("preset_id", "auto_monitor")
            preset = next((p for p in item["presets"] if p.id == preset_id), None)
            if preset is None:
                raise ValueError("Perfil de monitor desconocido.")

            def enabled(name: str, default: bool = True) -> bool:
                return form.getfirst(name, str(default).lower()) == "true"

            def number(name: str, default: float) -> float:
                return float(form.getfirst(name, str(default)))

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
            job = self.server.job_store.create_from_catalog(
                item,
                preset,
                settings,
                form.getfirst("crs", "EPSG:25830"),
                form.getfirst("output_mode", "clean"),
            )
        except (ValueError, TypeError) as exc:
            self._json({"error": str(exc)}, 400)
            return
        self._json(job.public(), 202)


def serve_presets(
    host: str = "127.0.0.1",
    port: int = 8765,
    *,
    storage: Path = Path("outputs/monitor_web_jobs"),
    open_browser: bool = True,
) -> None:
    server = PresetServer((host, port), storage)
    url = f"http://{host}:{server.server_port}/"
    print(f"Exportar Rindes con perfiles de monitor disponible en {url}")
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        server.server_close()
