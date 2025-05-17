import os
from qgis.PyQt.QtWidgets import QComboBox, QCompleter, QMessageBox, QDialog # type: ignore
from qgis.PyQt.QtGui import QIcon, QBrush, QColor, QStandardItemModel, QStandardItem # type: ignore
from qgis.PyQt.QtCore import Qt, pyqtSignal, QThread, QVariant # type: ignore

from ...dialogs.add_new_product_dialog import AddNewProductDialog # type: ignore
from ...tools.api_worker import GenericApiWorker # Cambiado a GenericApiWorker

class ProductListModel(QStandardItemModel): # Hereda de QStandardItemModel
    def __init__(self, add_new_text, add_new_icon, parent=None):
        super().__init__(parent)
        self.add_new_text = add_new_text
        self.add_new_icon = add_new_icon
        self.add_new_background = QBrush(QColor(240, 240, 240)) # Gris claro

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return super().data(index, role) # Devolver QVariant() o delegar

        # Obtener los datos por defecto de la clase base (QStandardItemModel)
        # Esto recuperará item.text() para DisplayRole, item.data(UserRole) para UserRole, etc.
        default_data = super().data(index, role)

        # Para aplicar personalizaciones, necesitamos verificar el texto del ítem.
        # Usamos super().data() para obtener el texto de forma segura.
        item_display_text = super().data(index, Qt.DisplayRole)

        # Personalizaciones para el ítem "Agregar nuevo servicio"
        if item_display_text == self.add_new_text:
            if role == Qt.DecorationRole:
                return self.add_new_icon
            elif role == Qt.BackgroundRole:
                return self.add_new_background
        
        # Para todos los demás casos, o roles no personalizados arriba, devolver los datos por defecto.
        return default_data
    
class ProductSelectionComboBox(QComboBox):
    product_list_updated = pyqtSignal(list)
    load_finished = pyqtSignal()
    product_selected_data = pyqtSignal(object)

    def __init__(self, api_endpoint_config, parent=None):
        super().__init__(parent)
        self.api_endpoint_config = api_endpoint_config
        self.product_items_master_objects = [] 
        self.PLACEHOLDER_CHOOSE_SERVICE_TEXT = "--- Elegir servicio ---"
        self.ADD_NEW_PRODUCT_SYSTEM_TEXT = "--- Agregar nuevo servicio ---" # Corregido: sin espacio inicial
        
        current_script_path = os.path.dirname(__file__)
        plugin_gui_dir = os.path.dirname(current_script_path) 
        self.add_new_icon_path = os.path.join(plugin_gui_dir, "icons", "plus-solid.svg")
        self.add_new_icon = QIcon(self.add_new_icon_path) if os.path.exists(self.add_new_icon_path) else QIcon()

        self.api_thread = None
        self.api_worker = None

        self.setEditable(True)
        # Usar ProductListModel directamente aquí
        self.custom_model = ProductListModel(self.ADD_NEW_PRODUCT_SYSTEM_TEXT, self.add_new_icon, self)
        self.setModel(self.custom_model)
        
        self._setup_completer() 
        
        self.setEnabled(False) 
        self.clear() # Limpiar cualquier ítem por defecto del QComboBox base
        self.addItem("Cargando servicios...") # Placeholder visual mientras carga

        self.load_products_from_api()

        # Conectar señales DESPUÉS de la configuración inicial
        # self.currentIndexChanged.connect(self._on_index_changed) # Puede ser muy ruidosa
        self.activated.connect(self._on_item_activated) # Mejor para selección explícita del usuario

    def load_products_from_api(self):
        if self.api_thread and self.api_thread.isRunning():
            print("[ProductSelectionComboBox] La carga de API ya está en progreso.")
            return

        self.clear() 
        self.addItem("Cargando servicios...")
        self.setEnabled(False)

        self.api_thread = QThread(self)
        self.api_worker = GenericApiWorker(self.api_endpoint_config, request_context="load_products")
        self.api_worker.moveToThread(self.api_thread)

        self.api_worker.success.connect(self._handle_generic_api_success)
        self.api_worker.error.connect(self._handle_generic_api_error)
        
        self.api_worker.finished_signal.connect(self.api_thread.quit)
        self.api_worker.finished_signal.connect(self.api_worker.deleteLater)
        self.api_thread.finished.connect(self.api_thread.deleteLater)
        self.api_thread.finished.connect(self._on_load_finished)
        
        self.api_thread.started.connect(self.api_worker.run)
        self.api_thread.start()

    def _populate_model(self):
        """Puebla el ProductListModel (que es un QStandardItemModel) con los datos."""
        # Bloquear señales del modelo y del combo mientras se modifica
        model = self.model()
        if not isinstance(model, ProductListModel): # Debería serlo por el __init__
             print("[ProductSelectionComboBox] ERROR: El modelo no es ProductListModel en _populate_model.")
             # Recrear el modelo si es necesario, aunque esto indica un problema previo
             self.custom_model = ProductListModel(self.ADD_NEW_PRODUCT_SYSTEM_TEXT, self.add_new_icon, self)
             self.setModel(self.custom_model)
             model = self.custom_model

        model.blockSignals(True)
        self.blockSignals(True)
        
        model.clear() 

        placeholder_item = QStandardItem(self.PLACEHOLDER_CHOOSE_SERVICE_TEXT)
        placeholder_item.setData(None, Qt.UserRole) 
        placeholder_item.setSelectable(False) 
        placeholder_item.setEnabled(False) 
        model.appendRow(placeholder_item)
        
        self.product_items_master_objects.sort(key=lambda x: x.get("nombre", "").lower())
        for product_obj in self.product_items_master_objects:
            item_text = product_obj.get("nombre", "Nombre no disponible")
            item = QStandardItem(item_text)
            item.setData(product_obj, Qt.UserRole) 
            model.appendRow(item)
            
        add_new_item = QStandardItem(self.ADD_NEW_PRODUCT_SYSTEM_TEXT)
        add_new_item.setData(self.ADD_NEW_PRODUCT_SYSTEM_TEXT, Qt.UserRole) 
        # El icono y fondo se manejan por ProductListModel.data() basado en el texto
        model.appendRow(add_new_item)
        
        self.setCurrentIndex(0) # Seleccionar el placeholder por defecto
        
        model.blockSignals(False)
        self.blockSignals(False)
        self.setEnabled(True) # Habilitar el combo
        
        # Actualizar el completer si ya existe
        if hasattr(self, '_completer_instance') and self._completer_instance:
            self._completer_instance.setModel(self.model())


    def _setup_completer(self):
        if not hasattr(self, '_completer_instance'): 
            self._completer_instance = QCompleter(self.model(), self) 
            self._completer_instance.setCaseSensitivity(Qt.CaseInsensitive)
            self._completer_instance.setFilterMode(Qt.MatchContains) 
            self._completer_instance.setCompletionColumn(0) 
            self.setCompleter(self._completer_instance)
        else: 
            self._completer_instance.setModel(self.model())


    def _on_item_activated(self, index: int):
        """Se llama cuando el usuario selecciona un ítem del desplegable."""
        # No necesitamos itemText(index) si vamos a usar itemData
        item_data = self.itemData(index, Qt.UserRole) 
        current_text_display = self.itemText(index) # El texto que se muestra

        print(f"[ProductSelectionComboBox] Ítem activado: '{current_text_display}', Índice: {index}, Data: {item_data}")

        if item_data == self.ADD_NEW_PRODUCT_SYSTEM_TEXT: 
            self.blockSignals(True)
            
            existing_names = [p.get("nombre", "") for p in self.product_items_master_objects]
            dialog = AddNewProductDialog(existing_names, self.parentWidget())
            
            original_text_before_dialog = self.currentText() # Guardar texto actual por si se cancela

            if dialog.exec_() == QDialog.Accepted:
                new_product_name = dialog.get_new_product_name()
                if new_product_name:
                    new_product_obj = {"id": f"local_{new_product_name}", "nombre": new_product_name, "descripcion": "", "precio_1": 0.0}
                    self.product_items_master_objects.append(new_product_obj)
                    self._populate_model() # Repoblar el modelo
                    
                    # Encontrar el índice del nuevo producto y seleccionarlo
                    new_product_index = -1
                    for i in range(self.model().rowCount()):
                        if self.model().item(i).text() == new_product_name:
                            new_product_index = i
                            break
                    if new_product_index != -1:
                        self.setCurrentIndex(new_product_index)
                        # Emitir datos del nuevo producto seleccionado
                        self.product_selected_data.emit(new_product_obj) 
                    
                    self.product_list_updated.emit(list(self.product_items_master_objects))
            else: 
                # Si se cancela, restaurar el texto o el placeholder
                # Si el texto antes del diálogo era el de "agregar nuevo", poner placeholder
                if original_text_before_dialog == self.ADD_NEW_PRODUCT_SYSTEM_TEXT:
                    self.setCurrentIndex(0) # Volver al placeholder
                else:
                    # Intentar restaurar el texto anterior si era un producto válido
                    idx_restore = self.findText(original_text_before_dialog)
                    if idx_restore != -1:
                        self.setCurrentIndex(idx_restore)
                    else:
                        self.setCurrentIndex(0) # Fallback al placeholder
            
            self.blockSignals(False)
        elif item_data is None and current_text_display == self.PLACEHOLDER_CHOOSE_SERVICE_TEXT:
            # Es el placeholder, no emitir product_selected_data
            # El QComboBox ya está en el placeholder
            pass
        else:
            # Es un producto real
            if item_data: # item_data es el objeto producto
                self.product_selected_data.emit(item_data)
            # Si el QComboBox es editable, el texto ya se habrá actualizado.
            # Si no es editable, el currentIndex ya está puesto.

    def _on_index_changed(self, index: int):
        """
        Se llama cuando el índice actual cambia.
        Usado principalmente para asegurar que el texto editable refleje la selección
        si el usuario no está escribiendo activamente.
        """
        # current_text_in_editor = self.lineEdit().text() if self.isEditable() else ""
        # selected_item_text = self.itemText(index)
        
        # print(f"[ProductSelectionComboBox] _on_index_changed: index={index}, itemText='{selected_item_text}', editorText='{current_text_in_editor}'")
        
        # Esta señal puede ser muy "ruidosa". La lógica principal de selección está en _on_item_activated.
        # Si el QComboBox es editable, el texto se actualiza automáticamente al seleccionar del popup.
        # Si se establece el índice programáticamente, el texto también se actualiza.
        pass


    def _handle_generic_api_success(self, response_data: object, request_context: object):
        if request_context == "load_products":
            if isinstance(response_data, list):
                print(f"[ProductSelectionComboBox] Datos de productos recibidos de API: {len(response_data)} ítems")
                self.product_items_master_objects = list(response_data)
                self.blockSignals(True)
                self._populate_model() 
                self.blockSignals(False)
                # self.setEnabled(True) # _populate_model ya lo hace
            else:
                error_msg = "Respuesta de API inesperada para productos: no es una lista."
                print(f"[ProductSelectionComboBox] {error_msg} Respuesta: {response_data}")
                self._handle_generic_api_error(error_msg, request_context) # Llamar al manejador de error
        
    def _handle_generic_api_error(self, error_message: str, request_context: object):
        if request_context == "load_products":
            print(f"[ProductSelectionComboBox] Error cargando productos de API: {error_message}")
            self.blockSignals(True)
            self.model().clear() 
            self.addItem(f"Error al cargar: {error_message[:30]}...") # Este ítem se borrará con _populate_model
            
            # Llamar a _populate_model para configurar los ítems placeholder y "agregar nuevo"
            self.product_items_master_objects = [] # Asegurar que la lista de productos está vacía
            self._populate_model() # Esto pondrá el placeholder y "agregar nuevo"
            
            # self.setCurrentIndex(0) # _populate_model ya selecciona el placeholder
            self.blockSignals(False)
            # self.setEnabled(True) # _populate_model ya lo hace
            QMessageBox.warning(self, "Error de API", f"No se pudieron cargar los productos:\n{error_message}")

    def _on_load_finished(self):
        self.api_thread = None 
        self.api_worker = None
        self.load_finished.emit()
        print("[ProductSelectionComboBox] Carga de productos finalizada (éxito o error).")
        # Si la carga falló y no hay productos, _populate_model ya habrá configurado los ítems base.
        if not self.product_items_master_objects and self.model().rowCount() <= 1: # <=1 para el caso de "Cargando..."
            self.blockSignals(True)
            self._populate_model() 
            self.blockSignals(False)

    def update_product_list(self, new_product_objects_list):
        self.product_items_master_objects = list(new_product_objects_list)
        self.blockSignals(True)
        self._populate_model()
        self.blockSignals(False)

    def get_selected_product_object(self):
        current_index = self.currentIndex()
        if current_index >= 0 and self.model(): 
            # El ítem en el modelo es un QStandardItem
            item = self.model().item(current_index)
            if item:
                data = item.data(Qt.UserRole)
                # Devolver data solo si no es el placeholder (data is None) 
                # o el texto de "añadir nuevo" (data es el string ADD_NEW_PRODUCT_SYSTEM_TEXT)
                if data is not None and data != self.ADD_NEW_PRODUCT_SYSTEM_TEXT:
                    return data # Esto será el objeto producto
        return None
