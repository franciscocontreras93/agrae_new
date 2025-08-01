import asyncio
import aiohttp
import tempfile
import os
from datetime import datetime
import json

from qgis.core import (
    QgsRasterLayer,
    QgsProject,
)

class NDVIProcessor:
    def __init__(self, idcampania, idexplotacion, fecha_inicio, fecha_fin):
        self.ENDPOINT = "http://localhost:8000/gee/ndvi_lista_2"
        self.headers = {'Content-Type': 'application/json'}
        self.payload = self.get_payload(idcampania, idexplotacion, fecha_inicio, fecha_fin)
        self.loop = asyncio.new_event_loop()



    def get_payload(self, idcampania, idexplotacion, fecha_inicio, fecha_fin):
        return {
            'idcampania': idcampania,
            'idexplotacion': idexplotacion,
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin
        }




    # --- Descargar imagen desde URL y guardarla temporalmente ---
    async def download_image(self,session, url, fecha):
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                suffix = ".tif"
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
                temp_file.write(await response.read())
                temp_file.close()
                print(f"[OK] Imagen descargada - {fecha}: {temp_file.name}")
                return fecha, temp_file.name
        except Exception as e:
            print(f"[ERROR descarga] {fecha}: {e}")
            return fecha, None

    # --- Procesar raster en QGIS ---
    def procesar_raster(self,path, fecha):
        layer_name = f"NDVI_{fecha}"
        raster = QgsRasterLayer(path, layer_name)
        if raster.isValid():
            QgsProject.instance().addMapLayer(raster)
            print(f"[OK] Capa cargada: {layer_name}")
        else:
            print(f"[ERROR] Capa inválida: {path}")

    # --- Proceso principal ---
    async def main(self):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(self.ENDPOINT,json=self.payload,headers=self.headers) as response:
                    response.raise_for_status()
                    data = await response.json()
                    imagenes = data.get('lista', [])
            except Exception as e:
                print(f"[ERROR GET]: {e}")
                return

            if not imagenes:
                print("[SKIP] No se recibieron imágenes.")
                return

            # --- Filtrar solo fechas únicas ---
            fechas_vistas = set()
            imagenes_unicas = []
            for item in imagenes:
                fecha = item.get("fecha")
                if fecha and fecha not in fechas_vistas:
                    fechas_vistas.add(fecha)
                    imagenes_unicas.append(item)

            print(f"[INFO] Total imágenes únicas: {len(imagenes_unicas)}")

            # --- Descargar todas las imágenes ---
            download_tasks = [
                self.download_image(session, item["download_url"], item["fecha"])
                for item in imagenes_unicas
            ]
            downloaded = await asyncio.gather(*download_tasks)

            # --- Procesar cada imagen ---
            for fecha, path in downloaded:
                if path:
                    self.procesar_raster(path, fecha)


    def run(self):
        # Ejecutar el bucle de eventos de asyncio
        # loop = asyncio.get_event_loop()
        # loop.run_until_complete(self.main())
        # # loop.close()

        try:
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self.main())
        finally:
            self.loop.close()


