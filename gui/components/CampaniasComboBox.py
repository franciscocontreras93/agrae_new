import os
from qgis.PyQt.QtWidgets import QComboBox
from qgis.PyQt.QtCore import Qt, pyqtSignal, QThread
from qgis.core import QgsMessageLog, Qgis

from ...tools import aGraeTools
from ...tools.api_worker import GenericApiWorker # Ajustado a tres puntos

class CampaniasComboBox(QComboBox):
    campaigns_loaded = pyqtSignal()
    current_campaign_changed = pyqtSignal(object) # Emite el ID de la campaña (o None)

    DEFAULT_ALL_CAMPAIGNS_TEXT = "Todas las Campañas"
    DEFAULT_LOADING_TEXT = "Cargando campañas..."
    DEFAULT_ERROR_TEXT = "Error al cargar campañas"

    def __init__(self, campaigns_api_path: str = "/api/campanias/", parent=None):
        super().__init__(parent)
        self.endpoint_url = aGraeTools().backend_endpoint
        self.campaigns_api_path = campaigns_api_path
        
        self.api_thread = None
        self.api_worker = None

        self.all_campaigns_text = self.DEFAULT_ALL_CAMPAIGNS_TEXT
        self.loading_text = self.DEFAULT_LOADING_TEXT
        self.error_text = self.DEFAULT_ERROR_TEXT
        
        
        self.set_initial_state(self.loading_text)
        self.load_campaigns()

        self.currentIndexChanged.connect(self._emit_current_campaign_changed_on_user_interaction)

    def set_initial_state(self, text: str, enabled: bool = False):
        self.blockSignals(True)
        self.clear()
        self.addItem(text, None) # userData es None para estados iniciales/error
        self.setEnabled(enabled)
        self.blockSignals(False)

    def load_campaigns(self):
        if self.api_thread and self.api_thread.isRunning():
            QgsMessageLog.logMessage("[CampaignComboBox] La carga de API ya está en progreso.", "CampaignComboBox", Qgis.Info)
            return

        self.set_initial_state(self.loading_text, False)

        api_config = {
            "url": f"{self.endpoint_url}{self.campaigns_api_path}",
            "params": {},
            "headers": {}
        }

        self.api_thread = QThread(self) 
        self.api_worker = GenericApiWorker(api_config, request_context="load_campaigns")
        self.api_worker.moveToThread(self.api_thread)

        self.api_worker.success.connect(self._handle_api_success)
        self.api_worker.error.connect(self._handle_api_error)
        
        self.api_worker.finished_signal.connect(self.api_thread.quit)
        self.api_worker.finished_signal.connect(self.api_worker.deleteLater)
        self.api_thread.finished.connect(self.api_thread.deleteLater)
        self.api_thread.finished.connect(self._on_load_finished)
        
        self.api_thread.started.connect(self.api_worker.run)
        self.api_thread.start()

    def _handle_api_success(self, response_data: object, request_context: object):
        if request_context == "load_campaigns":
            self.blockSignals(True)
            self.clear()
            # self.addItem(self.all_campaigns_text, None) 

            if isinstance(response_data, list):
                campaigns_sorted = sorted(response_data, key=lambda x: x.get("id",0), reverse=True)
                for campaign in campaigns_sorted:
                    if isinstance(campaign, dict) and 'id' in campaign and 'nombre' in campaign:
                        self.addItem(str(campaign['nombre']), campaign['id'])
                self.setEnabled(True)
                self.setCurrentIndex(0) 
                self.campaigns_loaded.emit()
            else:
                QgsMessageLog.logMessage(f"Respuesta de API para campañas no es una lista: {response_data}", "CampaignComboBox", Qgis.Warning)
                self._handle_api_error(f"Respuesta API inválida: {type(response_data)}", request_context) 
            
            self.blockSignals(False)
            if self.isEnabled(): 
                self.current_campaign_changed.emit(self.currentData()) 

    def _handle_api_error(self, error_message: str, request_context: object):
        if request_context == "load_campaigns":
            QgsMessageLog.logMessage(f"Error cargando campañas: {error_message}", "CampaignComboBox", Qgis.Critical)
            self.set_initial_state(self.error_text, False)

    def _on_load_finished(self):
        self.api_thread = None
        self.api_worker = None

    def _emit_current_campaign_changed_on_user_interaction(self, index: int):
        if index != -1: 
            self.current_campaign_changed.emit(self.currentData())

    def get_current_campaign_id(self) -> int | None:
        return self.currentData()