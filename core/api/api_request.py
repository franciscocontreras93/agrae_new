import requests
from ..config import aGraeConfig

class APIRequest:
    def __init__(self, base_url:str=None):
        self.config = aGraeConfig()
        self.base_url = self.config.backend_url if base_url is None else base_url


    def get(self, endpoint, params=None, raw = False):
        url = f"{self.base_url}/{endpoint}"
        url = url.replace("//", "/").replace(":/", "://")
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            if raw:
                return response.content
            return response.json()
        except requests.RequestException as e:
            print(f"Error during GET request: {e}")
            return None

    def post(self, endpoint, data=None):
        url = f"{self.base_url}/{endpoint}"

        url = url.replace("//", "/").replace(":/", "://")  # Asegura que no haya dobles barras excepto en el esquema

        try:
            resp = requests.post(url, json=data, timeout=30)

            try:
                payload = resp.json()
                return payload
            except Exception:
                payload = None

            return {
                "http_status": resp.status_code,
                "data": payload
            }

        except Exception as e:
            # print(f"Error during POST request: {e}")
            return {
                "http_status": None,
                "data": None
            }
        
    def delete(self, endpoint, data=None):
        url = f"{self.base_url}/{endpoint}"
        url = url.replace("//", "/").replace(":/", "://")
        try:
            response = requests.delete(url, json=data)
            response.raise_for_status()
            
            return response.json() if response.content else {"http_status": response.status_code, "data": None}
        except requests.RequestException as e:
            # print(f"Error during DELETE request: {e}")
            return {
                "http_status": None,
                "data": None
            }
    
    def put(self, endpoint, data=None):
        url = f"{self.base_url}/{endpoint}"
        url = url.replace("//", "/").replace(":/", "://")
        try:
            response = requests.put(url, json=data)
            response.raise_for_status()
            return {
                "http_status": response.status_code,
                "data": response.json() if response.content else None
            }
        except requests.RequestException as e:
            # print(f"Error during PUT request: {e}")
            return {
                "http_status": None,
                "data": None
            }
    def patch(self, endpoint, data=None):
        
        url = f"{self.base_url}/{endpoint}"
        url = url.replace("//", "/").replace(":/", "://")

        try:
            response = requests.patch(url, json=data)

            response_data = None
            try:
                response_data = response.json() if response.content else None
            except Exception:
                response_data = response.text

            return {
                "http_status": response.status_code,
                "data": response_data
            }

        except requests.RequestException as e:
            return {
                "http_status": None,
                "data": str(e)
            }