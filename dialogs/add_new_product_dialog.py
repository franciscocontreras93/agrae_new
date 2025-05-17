from qgis.PyQt.QtWidgets import ( # type: ignore
    QDialog, QVBoxLayout, QLabel, QLineEdit,
    QDialogButtonBox, QMessageBox
)

class AddNewProductDialog(QDialog):
    def __init__(self, existing_items, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Añadir Nuevo Producto/Servicio")
        self.existing_items_lower = [item.lower() for item in existing_items]
        self.new_product_name = None

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Nombre del nuevo producto o servicio:"))
        self.txt_new_product = QLineEdit()
        layout.addWidget(self.txt_new_product)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def accept(self):
        name = self.txt_new_product.text().strip()
        if not name:
            QMessageBox.warning(self, "Entrada Inválida", "El nombre no puede estar vacío.")
            return
        if name.lower() in self.existing_items_lower:
            QMessageBox.warning(self, "Duplicado", f"El producto/servicio '{name}' ya existe.")
            return
        self.new_product_name = name
        super().accept()

    def get_new_product_name(self):
        return self.new_product_name