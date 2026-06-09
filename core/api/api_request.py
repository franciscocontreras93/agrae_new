import requests
from ..config import aGraeConfig


class APIRequest:
    def __init__(self, base_url: str = None):
        self.config = aGraeConfig()
        self.base_url = self.config.backend_url if base_url is None else base_url

    def _build_url(self, endpoint: str) -> str:
        url = f"{self.base_url}/{endpoint}"
        url = url.replace("//", "/").replace(":/", "://")
        return url

    def _parse_body(self, response):
        """
        Intenta devolver JSON y, si no se puede, devuelve texto.
        Mantiene centralizada la lectura del body para GET/POST/PATCH/PUT.
        """
        try:
            return response.json() if response.content else None
        except ValueError:
            return response.text
        except Exception:
            return None

    def _response_envelope(self, response):
        """
        Estructura estándar para llamadas donde necesitamos saber si hubo error HTTP.
        """
        return {
            "ok": response.ok,
            "http_status": response.status_code,
            "data": self._parse_body(response),
            "headers": dict(response.headers),
        }

    def _request_error_envelope(self, exc):
        return {
            "ok": False,
            "http_status": None,
            "data": {
                "detail": {
                    "code": "REQUEST_ERROR",
                    "message": str(exc),
                }
            },
            "headers": {},
        }

    def get(self, endpoint, params=None, raw=False, full_response: bool = False):
        url = self._build_url(endpoint)
        try:
            response = requests.get(url, params=params, timeout=30)

            if full_response:
                return self._response_envelope(response)

            response.raise_for_status()
            if raw:
                return response.content
            return self._parse_body(response)

        except requests.RequestException as e:
            print(f"Error during GET request: {e}")
            if full_response:
                return self._request_error_envelope(e)
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

    def post(self, endpoint, data=None, full_response: bool = False):
        """
        POST compatible con el código antiguo.

        - Por defecto devuelve el JSON directo del backend, como antes.
        - Si full_response=True devuelve envelope con ok/http_status/data/headers.

        Así podemos ir migrando pantallas poco a poco sin romper otros usos.
        """
        url = self._build_url(endpoint)

        try:
            response = requests.post(url, json=data, timeout=30)

            if full_response:
                return self._response_envelope(response)

            # Comportamiento legacy: devolver el body directo.
            try:
                return response.json()
            except Exception:
                return {
                    "http_status": response.status_code,
                    "data": response.text if response.content else None,
                }

        except requests.RequestException as e:
            if full_response:
                return self._request_error_envelope(e)

            # Comportamiento legacy.
            return {
                "http_status": None,
                "data": None,
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
        finally:
            try:
                files['file'].close()
            except Exception:
                pass

    def delete(self, endpoint, data=None, full_response: bool = False):
        url = self._build_url(endpoint)
        try:
            response = requests.delete(url, json=data, timeout=30)

            if full_response:
                return self._response_envelope(response)

            response.raise_for_status()
            return self._parse_body(response) if response.content else {"http_status": response.status_code, "data": None}

        except requests.RequestException as e:
            if full_response:
                return self._request_error_envelope(e)
            return {
                "http_status": None,
                "data": None
            }

    def put(self, endpoint, data=None):
        url = self._build_url(endpoint)

        try:
            response = requests.put(url, json=data, timeout=30)

            return {
                "ok": response.ok,
                "http_status": response.status_code,
                "data": self._parse_body(response),
                "headers": dict(response.headers),
            }

        except requests.RequestException as e:
            return self._request_error_envelope(e)

    def patch(self, endpoint, data=None, full_response: bool = True):
        """
        PATCH devuelve envelope por defecto porque normalmente se usa para ediciones
        donde interesa conocer errores 409/422 del backend.

        Si necesitas comportamiento legacy, llama con full_response=False.
        """
        url = self._build_url(endpoint)

        try:
            response = requests.patch(url, json=data, timeout=30)

            if full_response:
                return self._response_envelope(response)

            return {
                "http_status": response.status_code,
                "data": self._parse_body(response),
            }

        except requests.RequestException as e:
            if full_response:
                return self._request_error_envelope(e)
            return {
                "http_status": None,
                "data": str(e)
            }
