import requests
from ..config import aGraeConfig

class APIRequest:
    def __init__(self, base_url:str=None):
        self.config = aGraeConfig()
        self.base_url = self.config.backend_url if base_url is None else base_url

    def _build_url(self, endpoint: str) -> str:
        url = f"{self.base_url}/{endpoint}"
        url = url.replace("//", "/").replace(":/", "://")
        return url


    def get(self, endpoint, params=None, raw = False):
        url = self._build_url(endpoint)
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            if raw:
                return response.content
            return response.json()
        except requests.RequestException as e:
            print(f"Error during GET request: {e}")
            return None
    
    def get_binary(self, endpoint: str, headers: dict = None):
        """
        Realiza un GET esperando una respuesta binaria, por ejemplo PDF.
        """
        url = self._build_url(endpoint)

        final_headers = {
            "Accept": "application/pdf"
        }

        if headers:
            final_headers.update(headers)

        try:
            r = requests.get(
                url,
                headers=final_headers,
                timeout=60
            )

            return {
                "http_status": r.status_code,
                "content": r.content if r.ok else None,
                "headers": dict(r.headers),
                "ok": r.ok,
                "content_type": r.headers.get("content-type", ""),
                "error": None if r.ok else r.text,
            }

        except Exception as ex:
            return {
                "http_status": 0,
                "content": None,
                "headers": {},
                "ok": False,
                "content_type": "",
                "error": str(ex),
            }

    def post(self, endpoint, data=None):
        url = self._build_url(endpoint)

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
    
    def post_binary(self, endpoint: str, data: dict, headers: dict = None) -> dict:
        """
        Realiza un POST esperando una respuesta binaria, por ejemplo PDF.
        """
        url = self._build_url(endpoint)

        if headers is None:
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/pdf",
            }

        try:
            r = requests.post(
                url,
                json=data,
                headers=headers,
                timeout=60
            )

            content_type = r.headers.get("content-type", "")

            if not r.ok:
                error_data = None

                try:
                    error_data = r.json()
                except Exception:
                    try:
                        error_data = r.text
                    except Exception:
                        error_data = None

                return {
                    "http_status": r.status_code,
                    "content": None,
                    "headers": dict(r.headers),
                    "ok": False,
                    "error": error_data,
                }

            return {
                "http_status": r.status_code,
                "content": r.content,
                "headers": dict(r.headers),
                "ok": True,
                "content_type": content_type,
            }

        except Exception as ex:
            return {
                "http_status": 0,
                "content": None,
                "headers": {},
                "ok": False,
                "error": str(ex),
            }

    def post_file(self, endpoint: str, file_path: str, additional_data: dict = None) -> dict:
        url = self._build_url(endpoint)

        files = {
            'file': open(file_path, 'rb')
        }

        data = additional_data if additional_data else {}

        try:
            r = requests.post(url, files=files, data=data, timeout=60)

            try:
                payload = r.json()
            except Exception:
                payload = None

            return {
                "http_status": r.status_code,
                "data": payload,
                "ok": r.ok,
                "error": None if r.ok else r.text
            }

        except Exception as ex:
            return {
                "http_status": 0,
                "data": None,
                "ok": False,
                "error": str(ex)
            }  
        
    def delete(self, endpoint, data=None):
        url = self._build_url(endpoint)
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
        url = self._build_url(endpoint)

        try:
            response = requests.put(url, json=data)

            try:
                body = response.json() if response.content else None
            except ValueError:
                body = response.text

            return {
                "ok": response.ok,
                "http_status": response.status_code,
                "data": body
            }

        except requests.RequestException as e:
            return {
                "ok": False,
                "http_status": None,
                "data": {
                    "detail": {
                        "code": "REQUEST_ERROR",
                        "message": str(e)
                    }
                }
            }
        

    def patch(self, endpoint, data=None):
        
        url = self._build_url(endpoint)

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