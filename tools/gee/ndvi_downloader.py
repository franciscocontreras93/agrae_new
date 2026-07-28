# ndvi_multithread_downloader.py
# ------------------------------------------------------------
# Worker + Processor en un solo archivo (PyQGIS-friendly)
# ------------------------------------------------------------

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

from PyQt5.QtCore import QThread, pyqtSignal

from ...core.config import aGraeConfig


from ...tools import aGraeTools




# ============================================================
# 1) Processor (puro Python): POST lista + normalizar + helpers
# ============================================================

@dataclass(frozen=True)
class IndexItem:
    fecha: str
    download_url: str


class NDVIProcessor:
    """
    Orquestador "puro" (sin QGIS): obtiene lista y la normaliza.
    El worker lo usa para no mezclar lógica en el hilo.
    """

    def __init__(self,endpoint:str, headers: Optional[Dict[str, str]] = None, timeout: int = 4000):
        self.endpoint = aGraeTools().gee_backend_url + endpoint
        self.headers = headers or {"Content-Type": "application/json"}
        self.timeout = timeout

    def fetch_list(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        r = requests.post(self.endpoint, json=payload, headers=self.headers, timeout=self.timeout)
        r.raise_for_status()
        data = r.json()

        # Ajusta esto si tu backend devuelve otra clave
        # (en tu script original: data.get("lista", []))
        items = data.get("lista", [])
        if not isinstance(items, list):
            raise ValueError("Respuesta inválida: 'lista' no es una lista.")
        return items

    @staticmethod
    def normalize_unique(items: List[Dict[str, Any]]) -> List[IndexItem]:
        """
        Filtra y devuelve items únicos por 'fecha'.
        Espera que cada item tenga: { 'fecha': 'YYYY-MM-DD', 'download_url': 'http...' }
        """
        seen = set()
        out: List[IndexItem] = []

        for it in items:
            fecha = it.get("fecha")
            url = it.get("download_url")
            if not fecha or not url:
                continue
            if fecha in seen:
                continue
            seen.add(fecha)
            out.append(IndexItem(fecha=str(fecha), download_url=str(url)))
        
        out.sort(key=lambda x: x.fecha)

        return out


# ============================================================
# 2) Worker (Qt Thread): descargas concurrentes + señales progreso
# ============================================================

class NDVIListDownloadWorker(QThread):
    """
    QThread que:
    1) Llama al endpoint para obtener lista
    2) Normaliza a fechas únicas
    3) Descarga concurrentemente los TIFF
    4) Emite señales para progressbar y para cargar capas en UI
    """
    status = pyqtSignal(str)                # info
    progressInit = pyqtSignal(int)          # total
    progress = pyqtSignal(int)              # done
    itemReady = pyqtSignal(str, str)        # fecha, path
    orderReady = pyqtSignal(list)           # orden
    error = pyqtSignal(str)
    finishedOk = pyqtSignal()

    def __init__(
        self,
        processor: NDVIProcessor,
        payload: Dict[str, Any],
        max_workers: int = 4,
        download_timeout: int = 120,
        parent=None,
    ):
        super().__init__(parent)
        self.processor = processor
        self.payload = payload
        self.max_workers = max_workers
        self.download_timeout = download_timeout
        self._cancel = False

    def cancel(self) -> None:
        self._cancel = True

    def _download_one(self, url: str, fecha: str) -> Tuple[str, Optional[str], Optional[str]]:
        """
        Returns: (fecha, local_path or None, error_msg or None)
        """
        try:
            rr = requests.get(url, stream=True, timeout=self.download_timeout)
            rr.raise_for_status()

            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".tif")
            with tmp as f:
                for chunk in rr.iter_content(chunk_size=1024 * 256):
                    if self._cancel:
                        # Si cancelas a mitad de descarga, cerramos y limpiamos
                        try:
                            f.flush()
                        except Exception:
                            pass
                        try:
                            os.remove(tmp.name)
                        except Exception:
                            pass
                        return fecha, None, "Cancelado"
                    if chunk:
                        f.write(chunk)

            return fecha, tmp.name, None

        except Exception as e:
            return fecha, None, str(e)

    def run(self) -> None:
        try:
            if self._cancel:
                return

            self.status.emit("Procesando imagenes, esta operacion puede tardar unos minutos...")  # <-- ANTES del POST
            raw_items = self.processor.fetch_list(self.payload)

            self.status.emit("Preparando descargas…")     # <-- tras respuesta
            items = self.processor.normalize_unique(raw_items)

            ordered_fechas = [it.fecha for it in items]
            self.orderReady.emit(ordered_fechas)

            total = len(items)
            self.progressInit.emit(total)

            if total == 0:
                self.status.emit("Sin resultados.")
                self.finishedOk.emit()
                return

            self.status.emit(f"Descargando 0/{total}…")

            done = 0
            with ThreadPoolExecutor(max_workers=self.max_workers) as ex:
                futures = [ex.submit(self._download_one, it.download_url, it.fecha) for it in items]

                for fut in as_completed(futures):
                    if self._cancel:
                        self.status.emit("Cancelado.")
                        break

                    fecha, path, err = fut.result()
                    done += 1
                    self.progress.emit(done)
                    self.status.emit(f"Descargando {done}/{total}…")

                    if err:
                        if err != "Cancelado":
                            self.error.emit(f"[DESCARGA] {fecha}: {err}")
                        continue

                    if path:
                        self.itemReady.emit(fecha, path)

            self.status.emit("Finalizado.")
            self.finishedOk.emit()

        except Exception as e:
            self.error.emit(str(e))
            self.status.emit("Error.")
            self.finishedOk.emit()