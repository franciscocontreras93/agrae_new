from qgis.PyQt.QtWidgets import QFrame, QVBoxLayout, QLabel, QSizePolicy, QWidget # type: ignore
from qgis.PyQt.QtCore import Qt, pyqtSignal # type: ignore

# Estilo completo para la tarjeta KPI, incluyendo los estados del valor
KPI_CARD_WIDGET_STYLE = """
QFrame#kpiCard {
    border: 1px solid #D3D3D3;
    border-radius: 8px;
    background-color: white;
    min-width: 180px; /* Ajustar según necesidad */
    max-width: 220px; /* Ajustar según necesidad */
    min-height: 90px; /* Ajustar según necesidad */
    max-height: 110px; /* Ajustar según necesidad */
}
QFrame#kpiCard:hover {
    background-color: #E6F2FF;
    border: 1px solid #B0C4DE;
}
QLabel#kpiTitle {
    font-size: 10pt;
    color: #555555;
    padding-bottom: 5px;
}
QLabel#kpiValue { /* Este es el QLabel interno de KpiCard */
    font-size: 14pt;
    font-weight: bold;
    color: #005A9C; /* Color por defecto para 'ok' */
}
QLabel#kpiValue[status="loading"] { color: #FFA500; }
QLabel#kpiValue[status="error"] { color: #FF0000; font-size: 11pt; }
QLabel#kpiValue[status="ok"] { color: #005A9C; }
QLabel#kpiValue[status="idle"] { color: #808080; }
"""

class KpiCard(QFrame):
    """
    Un widget reutilizable para mostrar un Indicador Clave de Rendimiento (KPI).
    Ahora maneja su propio QLabel para el valor y su estilo.
    """
    # Señal emitida cuando la tarjeta recibe un doble clic.
    # Emite el texto del título de la tarjeta.
    doubleClicked = pyqtSignal(str)
    def __init__(self, title_text: str, parent: QWidget = None):
        super().__init__(parent)
        self.setObjectName("kpiCard") # Para aplicar el estilo CSS
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setStyleSheet(KPI_CARD_WIDGET_STYLE) # Aplicar el estilo al propio widget

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        title_label_widget = QLabel(title_text)
        self.title_label_widget = title_label_widget # Guardar referencia al título
        title_label_widget.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        title_label_widget.setWordWrap(True)

        self.value_label_widget = QLabel("N/A") # Valor inicial
        self.value_label_widget.setObjectName("kpiValue") # Para el estilo CSS
        self.value_label_widget.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.value_label_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.value_label_widget.setWordWrap(True)
        self.status = "idle" # Estado inicial
        self.value_label_widget.setProperty("status", self.status)

        layout.addWidget(title_label_widget)
        layout.addWidget(self.value_label_widget)
        layout.setStretchFactor(self.value_label_widget, 1)
        self._apply_style_refresh(self.value_label_widget) # Aplicar estilo inicial

    def _apply_style_refresh(self, widget: QWidget):
        """Refresca el estilo del widget para aplicar cambios de propiedades."""
        if widget:
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            widget.update()

    def update_value(self, value_text: str, status: str = "ok"):
        """
        Actualiza el valor y el estado del KPI.
        status puede ser "ok", "loading", "error", "idle".
        """
        self.status = status # Guardar el estado
        self.value_label_widget.setText(str(value_text))
        self.value_label_widget.setProperty("status", status)
        self._apply_style_refresh(self.value_label_widget)

    def mouseDoubleClickEvent(self, event):
        """Maneja el evento de doble clic del ratón."""
        if event.button() == Qt.LeftButton:
            self.doubleClicked.emit(self.title_label_widget.text())