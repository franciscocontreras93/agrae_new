import requests
import json
from qgis.PyQt.QtCore import QThread, pyqtSignal, QObject # QObject añadido

# --- ApiWorker Original (para KPIs, etc., si aún se usa) ---
class ApiWorker(QThread):
    """
    Worker thread para realizar peticiones API sin bloquear la GUI.
    Diseñado originalmente para actualizar KPIs.
    """
    # Señal emitida cuando la petición es exitosa. El argumento es el JSON de respuesta.
    # (api_response, kpi_targets_config, update_id)
    finished = pyqtSignal(object, object, int) 
    # Señal emitida cuando ocurre un error. El argumento es el mensaje de error.
    # (error_message, kpi_targets_config, update_id)
    error = pyqtSignal(str, object, int)    

    def __init__(self, endpoint_url: str, endpoint: str, kpi_targets_config: list, update_id: int, params=None, method='GET', data=None, headers=None):
        super().__init__()
        self.base_url = endpoint_url
        self.endpoint = endpoint
        self.kpi_targets_config = kpi_targets_config 
        self.update_id = update_id
        self.params = params
        self.method = method.upper()
        self.data = data
        self.headers = headers
        self.timeout = 1000 # Timeout en segundos (ajustado desde 1000)
        
    def run(self):
        try:
            url = self.base_url + self.endpoint
            print(f"[ApiWorker Original] Requesting KPI data from: {url} with params: {self.params}")
            if self.method == 'GET':
                response = requests.get(url, params=self.params, headers=self.headers, timeout=self.timeout) 
            elif self.method == 'POST':
                response = requests.post(url, json=self.data, params=self.params, headers=self.headers, timeout=self.timeout)
            else:
                self.error.emit(f"Método HTTP no soportado: {self.method}", self.kpi_targets_config, self.update_id)
                return
            response.raise_for_status()
            self.finished.emit(response.json(), self.kpi_targets_config, self.update_id)
        except requests.exceptions.Timeout:
            self.error.emit(f"Error de red: Timeout al conectar con {url}", self.kpi_targets_config, self.update_id)
        except requests.exceptions.ConnectionError:
            self.error.emit(f"Error de red: No se pudo conectar con {url}", self.kpi_targets_config, self.update_id)
        except requests.exceptions.RequestException as e:
            self.error.emit(f"Error de red: {e}", self.kpi_targets_config, self.update_id)
        except json.JSONDecodeError as e:
            self.error.emit(f"Error al decodificar JSON: {e}. Respuesta: {response.text[:200]}", self.kpi_targets_config, self.update_id)
        except Exception as e:
            self.error.emit(f"Error inesperado: {e}", self.kpi_targets_config, self.update_id)

# --- GenericApiWorker ---
class GenericApiWorker(QObject):
    success = pyqtSignal(object, object) # response_data, request_context
    error = pyqtSignal(str, object)      # error_message, request_context
    finished_signal = pyqtSignal()       # Señal propia para indicar finalización

    def __init__(self, api_config: dict, request_context: object = None, parent=None):
        super().__init__(parent)
        self.config = api_config
        self.request_context = request_context
        self._stop_flag = False
        self.session = requests.Session() # Es buena práctica usar una sesión

    def run(self):
        try:
            if self._stop_flag:
                self.error.emit("Operación cancelada por el usuario.", self.request_context)
                return # No olvides el finally

            url = self.config.get("url")
            params = self.config.get("params")
            headers = self.config.get("headers")
            method = self.config.get("method", "GET").upper()
            data_payload = self.config.get("data") # Para cuerpos de solicitud
            timeout = self.config.get("timeout", 30) # Timeout por defecto de 30 segundos

            if self._stop_flag: # Comprobar de nuevo antes de la llamada de red
                self.error.emit("Operación cancelada antes de la petición de red.", self.request_context)
                return

            response = self.session.request(
                method,
                url,
                params=params,
                headers=headers,
                json=data_payload if method in ["POST", "PUT", "PATCH"] and isinstance(data_payload, (dict, list)) else None,
                data=data_payload if method in ["POST", "PUT", "PATCH"] and not isinstance(data_payload, (dict, list)) else None,
                timeout=timeout,
                verify=False
            )
            response.raise_for_status()

            if self._stop_flag: # Comprobar después de la llamada, antes de procesar
                self.error.emit("Operación cancelada después de la petición, antes de procesar.", self.request_context)
                return

            content_type = response.headers.get('Content-Type', '').lower()
            if 'application/json' in content_type:
                response_data = response.json()
            else:
                response_data = response.text # O response.content si esperas binarios

            self.success.emit(response_data, self.request_context)

        except requests.exceptions.Timeout:
            self.error.emit(f"Error: Timeout ({timeout}s) durante la petición API a {url}.", self.request_context)
        except requests.exceptions.HTTPError as e:
            err_msg = f"Error HTTP {e.response.status_code} ({e.response.reason}) para {url}."
            try:
                error_details = e.response.json()
                err_msg += f" Detalles: {error_details}"
            except requests.exceptions.JSONDecodeError:
                err_msg += f" Cuerpo: {e.response.text[:200]}"
            self.error.emit(err_msg, self.request_context)
        except requests.exceptions.RequestException as e:
            self.error.emit(f"Error de red o conexión para {url}: {str(e)}", self.request_context)
        except Exception as e:
            self.error.emit(f"Error inesperado en worker API ({url}): {str(e)}", self.request_context)
        finally:
            # Aquí es donde cerraremos la sesión
            self.finished_signal.emit()

    def stop(self):
        self._stop_flag = True
        # Si la sesión de requests tuviera un método .cancel() o similar, se podría llamar aquí.
        # Por ahora, _stop_flag se revisa antes y después de la llamada bloqueante.