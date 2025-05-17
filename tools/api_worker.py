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
class GenericApiWorker(QObject): # Hereda de QObject para usar con moveToThread
    """
    Worker genérico para realizar peticiones API sin bloquear la GUI.
    Diseñado para ser movido a un QThread.
    """
    success = pyqtSignal(object, object) # respuesta_api (dict/list), contexto_peticion (any)
    error = pyqtSignal(str, object)      # mensaje_error (str), contexto_peticion (any)
    finished_signal = pyqtSignal()       # Para la limpieza del thread

    def __init__(self, api_config: dict, request_context: object = None):
        super().__init__()
        self.api_config = api_config 
        self.request_context = request_context
        self._is_running = True
        
    def run(self):
        if not self._is_running:
            self.finished_signal.emit()
            return

        url = self.api_config.get("url")
        method = self.api_config.get("method", "GET").upper()
        params = self.api_config.get("params")
        data = self.api_config.get("data") 
        headers = self.api_config.get("headers")
        timeout = self.api_config.get("timeout", 10) 

        if not url:
            if self._is_running: self.error.emit("Configuración de API inválida: URL no especificada.", self.request_context)
            if self._is_running: self.finished_signal.emit()
            return

        print(f"[GenericApiWorker] Solicitando: {method} {url} con params: {params}, data: {data}, context: {self.request_context}")
        try:
            response = requests.request(method, url, params=params, json=data, headers=headers, timeout=timeout)
            response.raise_for_status()
            
            api_response_data = None
            if response.content: # Solo intentar parsear JSON si hay contenido
                api_response_data = response.json()
            
            if self._is_running: self.success.emit(api_response_data, self.request_context)

        except requests.exceptions.Timeout:
            if self._is_running: self.error.emit(f"Error de red: Timeout al conectar con {url}", self.request_context)
        except requests.exceptions.ConnectionError:
            if self._is_running: self.error.emit(f"Error de red: No se pudo conectar con {url}", self.request_context)
        except requests.exceptions.RequestException as e:
            if self._is_running: self.error.emit(f"Error de red: {e}", self.request_context)
        except json.JSONDecodeError as e:
            error_text = response.text[:200] if hasattr(response, 'text') else "No response text"
            if self._is_running: self.error.emit(f"Error al decodificar JSON: {e}. Respuesta: {error_text}", self.request_context)
        except Exception as e:
            if self._is_running: self.error.emit(f"Error inesperado: {e}", self.request_context)
        finally:
            if self._is_running: self.finished_signal.emit()

    def stop(self):
        self._is_running = False
        print(f"[GenericApiWorker] Solicitud de parada recibida para context: {self.request_context}")

