from .datos_base_dialog import CrearLotesDialog


class aGraeDialogs():
    def __init__(self):
        pass

    def cargarLotesDialog(self):
        
        dlg = CrearLotesDialog(self.combo_campania.currentData(),self.combo_explotacion.currentData())
        # dlg.expCreated.connect(lambda e: self.tools.messages('aGrae Tools','Explotacion {} creada correctamente'.format(e),3))
        # dlg.loteCreated.connect(self.afterLotesCreated)
        dlg.exec()