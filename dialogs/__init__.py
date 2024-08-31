from .datos_base_dialog import CrearLotesDialog, GestionDatosBaseDialog


class aGraeDialogs():
    def __init__(self):
        pass

    def cargarLotesDialog(self):
        dlg = CrearLotesDialog()
        dlg.exec()

    def cargarCEDialog(self):
        dlg = GestionDatosBaseDialog()
        dlg.tabWidget.setCurrentIndex(0)
        dlg.exec()

    def cargarSegmentoDialog(self):
        dlg = GestionDatosBaseDialog()
        dlg.tabWidget.setCurrentIndex(1)
        dlg.exec()
    def cargarAmbienteDialog(self):
        dlg = GestionDatosBaseDialog()
        dlg.tabWidget.setCurrentIndex(2)
        dlg.exec()