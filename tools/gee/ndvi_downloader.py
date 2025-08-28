import requests
import json

class NDVIProcessor:
    def __init__(self, idcampania, idexplotacion, fecha_inicio, fecha_fin):
        print("[DEBUG] Tipos:")
        print(type(idcampania), idcampania)
        print(type(idexplotacion), idexplotacion)
        print(type(fecha_inicio), fecha_inicio)
        print(type(fecha_fin), fecha_fin)

        self.url = 'http://142.93.41.109:5050/gee/ndvi_lista_2/'  # <- barra final obligatoria
        self.headers = {'Content-Type': 'application/json', 'accept': 'application/json'}
        self.payload = {
            'idcampania': idcampania,
            'idexplotacion': idexplotacion,
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin
        }

    def run(self):
        try:
            print("[INFO] Enviando POST con requests...")
            response = requests.post(self.url, json=self.payload, headers=self.headers)
            response.raise_for_status()
            print("[OK] Respuesta:")
            print(json.dumps(response.json(), indent=2))
        except requests.exceptions.RequestException as e:
            print(f"[ERROR POST]: {e}")
