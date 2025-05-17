
from qgis.PyQt.QtWidgets import QTreeWidget, QTreeWidgetItem, QHeaderView, QWidget # type: ignore
from qgis.PyQt.QtCore import Qt, pyqtSignal # type: ignore
from qgis.core import QgsMessageLog, Qgis # type: ignore

class CustomTreeWidget(QTreeWidget):
    """
    TreeWidget personalizado para mostrar datos tabulares o jerárquicos simples,
    con configuración y métodos de llenado comunes.
    """
    # Señal emitida cuando un ítem es doble clickeado, pasando los datos asociados.
    itemDoubleClickedWithData = pyqtSignal(object) 

    def __init__(self, headers: list, hidden_columns: list = None, parent: QWidget = None):
        super().__init__(parent)
        
        self.setHeaderLabels(headers)
        
        if hidden_columns:
            for col_index in hidden_columns:
                if 0 <= col_index < len(headers):
                    self.setColumnHidden(col_index, True)
                else:
                    QgsMessageLog.logMessage(f"Advertencia: Índice de columna a ocultar fuera de rango: {col_index}", "CustomTreeWidget", Qgis.Warning)
        
        # Configuración básica de la tabla (similar a QTableWidget)
        self.setEditTriggers(QTreeWidget.NoEditTriggers) # Hacer los ítems no editables
        self.setSelectionBehavior(QTreeWidget.SelectRows) # Seleccionar filas enteras
        self.setAlternatingRowColors(True)
        self.setUniformRowHeights(True) # Puede mejorar el rendimiento con muchos ítems
        
        # Ajustar ancho de columnas visibles (ejemplo: estirar la primera columna visible)
        header = self.header()
        # En un TreeWidget plano, la columna 0 es la principal.
        # Si la columna 0 no está oculta, estiramos esa. Si está oculta, buscamos la primera visible.
        first_visible_col = -1
        for i in range(len(headers)):
            if not self.isColumnHidden(i):
                first_visible_col = i
                break
        if first_visible_col != -1:
             header.setSectionResizeMode(first_visible_col, QHeaderView.Stretch)
        
        # Conectar la señal interna para emitir nuestra señal personalizada
        self.itemDoubleClicked.connect(self._on_item_double_clicked)

    def populate_from_list(self, data: list, data_key_map: dict):
        """
        Limpia el árbol y lo llena con datos de una lista de diccionarios.
        data: Lista de diccionarios.
        data_key_map: Diccionario mapeando índice de columna a clave del diccionario.
                      Ej: {0: 'id', 1: 'nombre', 2: 'valor'}
        """
        self.clear() # Limpiar árbol

        if not data: # Si la lista está vacía
            item_no_data = QTreeWidgetItem(self, ["No hay datos para mostrar."])
            # Puedes hacer que este ítem ocupe todas las columnas visibles si quieres
            # self.setFirstColumnSpanned(self.indexOfTopLevelItem(item_no_data), True) # Esto puede ser complicado con columnas ocultas
            self.addTopLevelItem(item_no_data)
        else:
            for row_data in data:
                if isinstance(row_data, dict):
                    item = QTreeWidgetItem(self)
                    # Llenar las columnas usando el mapeo
                    for col_index, key in data_key_map.items():
                        value = row_data.get(key, '') # Usar .get() para evitar KeyError si la clave falta
                        item.setText(col_index, str(value))
                        # Opcional: guardar el diccionario completo o el ID en el ítem
                        if col_index == 0 and 'idexplotacion' in row_data: # Ejemplo: guardar el ID en la primera columna
                             item.setData(col_index, Qt.UserRole, row_data['idexplotacion'])
                        # Puedes guardar el diccionario completo en el primer ítem si lo necesitas al hacer doble click
                        if col_index == 0:
                             item.setData(col_index, Qt.UserRole + 1, row_data)

                    self.addTopLevelItem(item)
                else:
                     QgsMessageLog.logMessage(f"Formato de fila inesperado en datos: {row_data}", "CustomTreeWidget", Qgis.Warning)

        self.expandAll() # Opcional: expandir todos los ítems por defecto
        # self.resizeColumnToContents(0) # Ajustar ancho de la primera columna visible
        # Puedes ajustar otras columnas si es necesario
    
    def show_loading_message(self):
        """Limpia el árbol y muestra un mensaje de 'Cargando...'."""
        self.clear()
        loading_item = QTreeWidgetItem(self)
        loading_item.setText(0, "Cargando datos...")

    def show_error_message(self, error_message: str):
        """Muestra un mensaje de error en el árbol."""
        self.clear()
        item_error = QTreeWidgetItem(self, [f"Error: {error_message.split(':')[0]}"])
        self.addTopLevelItem(item_error)
        # self.setFirstColumnSpanned(self.indexOfTopLevelItem(item_error), True) # Opcional: span el mensaje de error

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Maneja el doble click interno y emite la señal personalizada."""
        # Recuperar los datos asociados si los guardaste (ej. en UserRole  1)
        row_data = item.data(0, Qt.UserRole + 1) # Asumiendo que guardaste el dict en la col 0, UserRole1
        if row_data is not None:
            self.itemDoubleClickedWithData.emit(row_data)
        else:
            # Si no guardaste el dict completo, puedes intentar reconstruir o pasar solo el ID
            id_data = item.data(0, Qt.UserRole) # Asumiendo que guardaste el ID en la col 0, UserRole
            if id_data is not None:
                 # Emitir solo el ID o una estructura parcial si no tienes el dict completo
                 self.itemDoubleClickedWithData.emit({'idexplotacion': id_data}) # Ejemplo
            else:
                 QgsMessageLog.logMessage("No se pudieron recuperar datos asociados al ítem doble clickeado.", "CustomTreeWidget", Qgis.Warning)
