from qgis.PyQt.QtWidgets import ( # type: ignore
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QDialogButtonBox, QGroupBox, QMessageBox, QComboBox
)
from qgis.PyQt.QtCore import Qt, pyqtSignal, QTimer, QThread # type: ignore

from ..tools.api_worker import GenericApiWorker # Cambiado a GenericApiWorker

class SelectClientDialog(QDialog):
    client_selected = pyqtSignal(object) # Emitirá el objeto del cliente seleccionado

    def __init__(self, endpoint_url: str, parent=None): # Recibir la URL base de la API
        super().__init__(parent)
        self.setWindowTitle("Seleccionar o Crear Cliente")
        self.setMinimumSize(800, 600)
        self.selected_client_data = None
        self.endpoint_url = endpoint_url # Guardar la URL base
        self.client_api_thread = None
        self.client_api_worker = None
        self.search_timer = QTimer(self) # Timer para retrasar la búsqueda
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(500) # 500 ms de retraso

        self.sample_explotaciones_data = [
            {"id": 101, "nombre": "Explotación Principal (Córdoba)"},
            {"id": 102, "nombre": "Finca Los Girasoles (Sevilla)"},
            {"id": 103, "nombre": "Parcela Norte (Jaén)"},
        ]

        self.init_ui()
        self.load_clients_from_api() # Cargar clientes al iniciar (sin término de búsqueda)

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # --- Sección de Búsqueda y Tabla de Clientes ---
        search_group = QGroupBox("Buscar Cliente Existente")
        search_layout = QVBoxLayout(search_group)

        self.txt_search_client = QLineEdit()
        self.txt_search_client.setPlaceholderText("Buscar por CIF/DNI o Nombre/Razón Social...")
        search_layout.addWidget(self.txt_search_client)

        self.table_clients = QTableWidget()
        self.table_clients.setColumnCount(5) # Añadida columna para Explotación
        self.table_clients.setHorizontalHeaderLabels(["ID", "CIF/DNI", "Nombre Completo", "Teléfono", "Explotación"])
        self.table_clients.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch) # Nombre
        self.table_clients.hideColumn(0)
        self.table_clients.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_clients.setEditTriggers(QTableWidget.NoEditTriggers) # No editable
        self.table_clients.doubleClicked.connect(self.handle_client_selected_from_table)
        search_layout.addWidget(self.table_clients)

        self.btn_select_client_from_table = QPushButton("Seleccionar Cliente")
        self.btn_select_client_from_table.clicked.connect(self.handle_client_selected_from_table)
        search_layout.addWidget(self.btn_select_client_from_table, 0, Qt.AlignRight)
        
        main_layout.addWidget(search_group)

        # --- Sección para Crear Nuevo Cliente ---
        create_client_group = QGroupBox("Crear Nuevo Cliente")
        create_client_layout = QFormLayout(create_client_group)

        self.txt_new_cif_dni = QLineEdit()
        self.txt_new_nombre = QLineEdit()
        self.txt_new_telefono = QLineEdit()
        self.txt_new_email = QLineEdit()
        
        create_client_layout.addRow("CIF/DNI:", self.txt_new_cif_dni)
        create_client_layout.addRow("Nombre/Razón Social:", self.txt_new_nombre)
        create_client_layout.addRow("Teléfono:", self.txt_new_telefono)
        create_client_layout.addRow("Email:", self.txt_new_email)

        # Sección para asignar explotaciones al nuevo cliente
        explotaciones_layout = QHBoxLayout()
        self.combo_explotaciones = QComboBox()
        self.populate_explotaciones_combo(self.sample_explotaciones_data) # Poblar con datos de ejemplo
        self.btn_assign_explotacion = QPushButton("Asignar Explotación")
        explotaciones_layout.addWidget(QLabel("Asignar Explotación:"))
        explotaciones_layout.addWidget(self.combo_explotaciones, 1)
        explotaciones_layout.addWidget(self.btn_assign_explotacion)
        create_client_layout.addRow(explotaciones_layout)

        # (Opcional) Tabla o lista para mostrar explotaciones asignadas al nuevo cliente
        # self.table_assigned_explotaciones = QTableWidget() ...
        # create_client_layout.addRow(self.table_assigned_explotaciones)

        self.btn_save_new_client = QPushButton("Guardar y Seleccionar Nuevo Cliente")
        self.btn_save_new_client.clicked.connect(self.handle_save_new_client)
        create_client_layout.addRow(self.btn_save_new_client)

        main_layout.addWidget(create_client_group)

        # --- Botón de Cancelar General ---
        self.button_box_cancel = QDialogButtonBox(QDialogButtonBox.Cancel)
        self.button_box_cancel.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box_cancel)

        self.setLayout(main_layout)

        # Conexiones
        self.txt_search_client.textChanged.connect(self.on_search_text_changed)
        self.search_timer.timeout.connect(self.trigger_api_search)

    def load_clients_from_api(self, search_term=None):
        if self.client_api_thread and self.client_api_thread.isRunning():
            print("[SelectClientDialog] Petición de clientes ya en progreso. Cancelando anterior si es posible.")
            if self.client_api_worker:
                self.client_api_worker.stop() # Marcar para detener
            # No es necesario hacer quit() o wait() aquí si el worker se detiene y emite finished.
            # El problema es que la siguiente petición podría empezar antes de que el anterior thread se limpie.
            # Una solución más robusta sería no permitir una nueva petición hasta que la anterior termine completamente.
            # O, si se permite, asegurarse de que las referencias se manejan con cuidado.
            # self.client_api_thread.wait()

        api_params = {}
        if search_term and search_term.strip():
            api_params['search'] = search_term # Asumiendo que tu API usa un parámetro 'search'

        client_api_config = {
            "url": f"{self.endpoint_url}/api/billing/clients/", # Ajusta este endpoint
            "params": api_params,
            "headers": {} # Añade cabeceras si son necesarias (ej. autenticación)
        }

        self.table_clients.setRowCount(0) # Limpiar tabla mientras carga
        # Podrías añadir un QTableWidgetItem "Cargando..."

        self.client_api_thread = QThread(self)
        # Usar un contexto para identificar esta petición
        self.client_api_worker = GenericApiWorker(client_api_config, request_context="load_clients")
        self.client_api_worker.moveToThread(self.client_api_thread)

       # Adaptar la conexión de señales
        self.client_api_worker.success.connect(self._handle_generic_api_success)
        self.client_api_worker.error.connect(self._handle_generic_api_error)
        
        # Usar finished_signal del GenericApiWorker
        self.client_api_worker.finished_signal.connect(self.client_api_thread.quit)
        self.client_api_worker.finished_signal.connect(self.client_api_worker.deleteLater)
        self.client_api_worker.finished_signal.connect(self._clear_worker_references) # Limpiar referencias aquí
        self.client_api_thread.finished.connect(self.client_api_thread.deleteLater)
        
        self.client_api_thread.started.connect(self.client_api_worker.run)
        self.client_api_thread.start()

    def populate_clients_table(self, clients_data):
        # Este método ahora es llamado por _handle_generic_api_success
        if isinstance(clients_data, list):
            print(f"[SelectClientDialog] Poblando tabla con {len(clients_data)} clientes.")
            self.table_clients.setRowCount(0) # Limpiar tabla
            for client in clients_data:
                row_position = self.table_clients.rowCount()
                self.table_clients.insertRow(row_position)
                self.table_clients.setItem(row_position, 0, QTableWidgetItem(str(client.get("id", ""))))
                self.table_clients.setItem(row_position, 1, QTableWidgetItem(client.get("dni_cif", "")))
                nombre_completo = f"{client.get('nombre', '')} {client.get('apellidos', '')}".strip()
                self.table_clients.setItem(row_position, 2, QTableWidgetItem(nombre_completo))
                self.table_clients.setItem(row_position, 3, QTableWidgetItem(client.get("telefono", "")))
                self.table_clients.setItem(row_position, 4, QTableWidgetItem(client.get("explotacion", "")))
                # Guardar el objeto completo en el primer ítem de la fila para fácil acceso
                self.table_clients.item(row_position, 0).setData(Qt.UserRole, client)
        else:
            print(f"[SelectClientDialog] Error: populate_clients_table recibió datos no válidos: {type(clients_data)}")
            self.table_clients.setRowCount(0)
            if self.table_clients.columnCount() > 0:
                self.table_clients.insertRow(0)
                error_item = QTableWidgetItem("Error al cargar datos de clientes.")
                error_item.setTextAlignment(Qt.AlignCenter)
                self.table_clients.setItem(0, 0, error_item)
                self.table_clients.setSpan(0, 0, 1, self.table_clients.columnCount())

    def populate_explotaciones_combo(self, explotaciones_data):
        self.combo_explotaciones.clear()
        self.combo_explotaciones.addItem("--- Seleccionar Explotación ---", None)
        for expl in explotaciones_data:
            self.combo_explotaciones.addItem(expl.get("nombre", "N/A"), expl) # Guardar objeto completo

    def on_search_text_changed(self, text: str):
        """Inicia el temporizador para la búsqueda API después de un breve retraso."""
        self.search_timer.stop() # Detener cualquier temporizador anterior
        self.search_timer.start() # Iniciar nuevo temporizador

    def trigger_api_search(self):
        """Llamado por el QTimer, ejecuta la búsqueda API."""
        search_text = self.txt_search_client.text().strip()
        # Cargar clientes con el término de búsqueda (o todos si está vacío)
        # La API debería manejar un término de búsqueda vacío devolviendo todos o los primeros N.
        self.load_clients_from_api(search_text)

    def _clear_worker_references(self):
        """Limpia las referencias al worker y al thread después de que han terminado."""
        print("[SelectClientDialog] Limpiando referencias de worker y thread.")
        self.client_api_worker = None
        self.client_api_thread = None

    def handle_client_selected_from_table(self):
        current_row = self.table_clients.currentRow()
        if current_row >= 0:
            item_data_holder = self.table_clients.item(current_row, 0) # Asumimos que los datos están en la col 0
            client_data = item_data_holder.data(Qt.UserRole)
            if client_data:
                self.selected_client_data = client_data
                self.client_selected.emit(self.selected_client_data)
                self.accept() # Cerrar el diálogo
        else:
            QMessageBox.information(self, "Seleccionar Cliente", "Por favor, seleccione un cliente de la tabla.")

    def _handle_generic_api_success(self, response_data: object, request_context: object):
        if request_context == "load_clients":
            self.populate_clients_table(response_data) # response_data debería ser la lista de clientes
        # Manejar otros contextos si este diálogo hiciera más tipos de peticiones

    def _handle_generic_api_error(self, error_message: str, request_context: object):
        if request_context == "load_clients":
            print(f"[SelectClientDialog] Error API Clientes: {error_message}")
            self.table_clients.setRowCount(0) # Limpiar tabla
            QMessageBox.warning(self, "Error de API", f"No se pudieron cargar los clientes:\n{error_message}")
        # Manejar otros contextos
        
    def handle_save_new_client(self):
        # Aquí iría la lógica para validar los campos del nuevo cliente,
        # guardarlo mediante una petición API, y luego seleccionarlo.
        # Por ahora, es una simulación.
        new_client_name = self.txt_new_nombre.text().strip()
        if not new_client_name:
            QMessageBox.warning(self, "Datos Incompletos", "El nombre del nuevo cliente es obligatorio.")
            return
        
        # Simular creación y selección
        self.selected_client_data = {
            "id": "temp_new_id", # ID temporal o devuelto por la API
            "cif_dni": self.txt_new_cif_dni.text(),
            "nombre": new_client_name, # Asumiendo que el nombre va en 'nombre'
            "telefono": self.txt_new_telefono.text(),
            "email": self.txt_new_email.text(),
            "explotaciones_asignadas": [] # Aquí se añadirían las explotaciones
        }
        QMessageBox.information(self, "Cliente Creado", f"Cliente '{new_client_name}' creado (simulación).")
        self.client_selected.emit(self.selected_client_data)
        self.accept()

    def get_selected_client(self):
        return self.selected_client_data