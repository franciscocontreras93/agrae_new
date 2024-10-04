import os

import psycopg2


from psycopg2 import extras


from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal, Qt,QDate,QSize,QSettings
from qgis.PyQt.QtGui import QIcon

from qgis.core import *
from qgis.utils import iface
from qgis.gui import QgsMapToolIdentify,QgsMapMouseEvent
from ..tools.analisis_tools import aGraeResamplearMuestras
from ..db import agraeDataBaseDriver
from ..sql import aGraeSQLTools
from ..gui import agraeGUI
from ..tools import aGraeTools

from ..dialogs import aGraeDialogs

from .explotacion_dialogs import CopyExplotacionDialog, CreateExplotacionDialog, UpdateExplotacionDialog, GestionExplotacionDialog,GestionarExplotacionesDialog
from .campania_dialogs import CloneCampaniaDialog, CreateCampaniaDialog, UpdateCampaniaDialog
from .lotes_dialog import LoteWeatherDialog
from .analitica_dialogs import agraeAnaliticaDialog
from .gestion_personas import GestionPersonasDialog
from .gestion_distribuidor import GestionDistribuidorDialog
from .gestion_agricultor import GestionAgricultorDialog
from .datos_base_dialog import GestionDatosBaseDialog, CrearLotesDialog
from .composer_dialog import agraeComposer
from .cultivos_dialog import GestionarCultivosDialog
from .parametros_dialog import GestionarParametrosDialog
from .plots_dialog import agraePlotsDialog
from .monitor_dialogs import MonitorRendimientosDialog
from .gee_dialog import aGraeGEEDialog
from .reportes_dialog import ReportesDialog
from .asignar_cultivos_dialog import AsignarCultivosDialog

toolsDialog, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'ui/agrae_tools.ui'))



class agraeToolsDockwidget(QtWidgets.QDockWidget,toolsDialog):
    def __init__(self,
                 layer:QgsVectorLayer,
                 parent=None):
        super(agraeToolsDockwidget,self).__init__(parent)
        self.instance = QgsProject.instance()
        self.setupUi(self)
        self.setWindowTitle('aGrae Tools')
        self.layer = layer
        self.conn = agraeDataBaseDriver().connection()
        self.tools = aGraeTools()
        self.UIComponents()
        # self.identifyTool = selectTool(self.layer)
        # self.identifyTool.featureSelected.connect(self.fillDataLote)
        self.currentDate = QDate().currentDate()
        # iface.mapCanvas().setMapTool(self.identifyTool)
        
        self.featureLote = None
        self.idLote = None
        self.idData = None
        self.nombreLote = None
        self.idCultivo = None
        self.idRegimen = None
        self.prodEsperada = None
        self.prodFinal = None
        
        self.fechaSiembra = ''
        self.fechaCosecha = ''
        self.FechaDesde = QDate()
        self.FechaHasta = QDate()
        

        self.getCampaniasData()
        self.getCultivosData()
        self.getRegimenData()

        
        iface.addDockWidget(Qt.RightDockWidgetArea,self)
        self.atlasLayers = dict()
        # iface.mapCanvas().contextMenuAboutToShow.connect(self.populateContextMenu)
        pass

    def UIComponents(self):
        self.setWindowIcon(agraeGUI().getIcon('main'))
        self.date_siembra.dateChanged.connect(self.dateSiembraChanged)
        # self.date_cosecha.dateChanged.connect(self.dateCosechaChanged)
        self.toolBox.setCurrentIndex(0)
        # self.toolBox.setItemIcon(0,agraeGUI().getIcon('main'))
        self.toolBox.setItemIcon(0,agraeGUI().getIcon('info'))
        self.toolBox.setItemIcon(1,agraeGUI().getIcon('info'))
        self.toolBox.currentChanged.connect(self.infoLote)
        
        for c in [self.combo_cultivo]:
            c.setEditable(True)
            c.setInsertPolicy(QtWidgets.QComboBox.NoInsert)
            # change completion mode of the default completer from InlineCompletion to PopupCompletion
            c.completer().setCompletionMode(QtWidgets.QCompleter.PopupCompletion)

        self.combo_campania.currentIndexChanged.connect(lambda: self.getExplotacionData(self.combo_campania.currentData()))
        self.combo_explotacion.currentIndexChanged.connect(self.getLotesExplotacionLayer)
        self.combo_cultivo_2.currentIndexChanged.connect(self.clearAplicacion)
        # icon = agraeGUI().getIcon('edit')
        
        self.initTools()
        

        self.check_siembra.stateChanged.connect(lambda e: self.check_status(e,self.fechaSiembra,self.date_siembra))
        self.check_cosecha.stateChanged.connect(lambda e: self.check_status(e,self.fechaCosecha,self.date_cosecha))

        # self.tool_fert_menu.addAction(self.EditarFertilizacionAction)

        self.combo_aplicacion.currentIndexChanged.connect(self.getCultivosCampaniaData)


        # self.btn_lote_analitic.setIcon(agraeGUI().getIcon('chart-bar'))
        # self.btn_lote_analitic.setToolTip()
        # self.btn_lote_analitic.clicked.connect(self.loteAnliticDialog)

    def initTools(self):
        # TOOLBUTTONS 
        # TOOL_EXP_2

        self.AsignarLotesExplotacion = QtWidgets.QAction(agraeGUI().getIcon('selection'),'Asignar Lotes Seleccionados a Explotacion',self)
        self.AsignarLotesExplotacion.triggered.connect(self.asignarLotesExp)

        self.AsignarCultivosLotes = QtWidgets.QAction(agraeGUI().getIcon('select-cultivo'),'Asignar Cultivo a Lotes Seleccionados',self)
        self.AsignarCultivosLotes.triggered.connect(self.asignarCultivosLotes)

        self.CargarCapasExplotacion = QtWidgets.QAction(agraeGUI().getIcon('add-layer'),'Generar capas de Explotacion',self)
        self.CargarCapasExplotacion.triggered.connect(self.generarCapasExplotacion)
        self.GenerarReporteFertilizacion = QtWidgets.QAction(agraeGUI().getIcon('printer'),'Generar Reporte de Preescripcion',self)
        self.GenerarReporteFertilizacion.triggered.connect(self.generateComposerDialog)

        #TODO
        self.GenerarUnidadesFertilizacion = QtWidgets.QAction(agraeGUI().getIcon('tractor'),'Exportar SHP de Preescripcion',self)
        self.GenerarUnidadesFertilizacion.triggered.connect(self.exportarUFS)
        #TODO
        self.GenerarResumenFertilizacion = QtWidgets.QAction(agraeGUI().getIcon('csv'),'Generar Resumen de Preescripcion',self)
        self.GenerarResumenFertilizacion.triggered.connect(self.exportarResumen)

        self.GenerarAmbientes = QtWidgets.QAction(agraeGUI().getIcon('satelite'),'Generar Mapas de Ambientes',self)
        self.GenerarAmbientes.triggered.connect(self.geeDialog)
        #TODO
        self.MonitorDeRendimiento = QtWidgets.QAction(agraeGUI().getIcon('rindes'),'Monitor de Rendimiento',self)
        self.MonitorDeRendimiento.triggered.connect(self.monitorRendimientoDialog)

        actions_exp = [
            self.AsignarLotesExplotacion,
            self.AsignarCultivosLotes,
            self.CargarCapasExplotacion,
            self.GenerarReporteFertilizacion,
            self.GenerarUnidadesFertilizacion,
            self.GenerarResumenFertilizacion,
            self.GenerarAmbientes,
            self.MonitorDeRendimiento]
        # actions_exp = [self.AsignarLotesExplotacion,self.CargarCapasExplotacion,self.GenerarReporteFertilizacion,self.GenerarUnidadesFertilizacion,self.GenerarResumenFertilizacion]
        self.tools.settingsToolsButtons(self.tool_exp_2,actions_exp,icon=agraeGUI().getIcon('explotacion'),setMainIcon=True)

        # TOOL_LAB
        #TODO 
        self.CargarCapaMuestras = QtWidgets.QAction(agraeGUI().getIcon('pois'),'Generar Puntos de Muestreo.',self)
        # self.CargarCapaMuestras.triggered.connect(self.createMuestreoPoints) #TODO
        self.CargarCapaMuestras.triggered.connect(aGraeDialogs.muestreoDialog)

        self.ActualziarProyectoMuestreo = QtWidgets.QAction(agraeGUI().getIcon('add-layer'),'Actualizar capas de Muestreo',self)

        self.CrearArchivoAnalisis = QtWidgets.QAction(agraeGUI().getIcon('csv'),'Generar Archivo de Laboratorio',self)
        self.CrearArchivoAnalisis.triggered.connect(self.crearFormatoAnalitica)
        self.ImportarArchivoAnalisis = QtWidgets.QAction(agraeGUI().getIcon('import'),'Cargar Archivo de Laboratorio',self)
        self.ImportarArchivoAnalisis.triggered.connect(self.cargarAnalitica)
        self.DerivarDatosAnalisis = QtWidgets.QAction(agraeGUI().getIcon('csv'),'Derivar datos de Analitica',self)
        self.DerivarDatosAnalisis.triggered.connect(self.DerivarAnalitica)

        actions_lab = [self.CargarCapaMuestras,self.ActualziarProyectoMuestreo,self.CrearArchivoAnalisis,self.ImportarArchivoAnalisis,self.DerivarDatosAnalisis]
        self.tools.settingsToolsButtons(self.tool_lab,actions_lab,icon=agraeGUI().getIcon('matraz'),setMainIcon=True)
        # TOOL_DATA
        self.GestionarPersonas = QtWidgets.QAction(agraeGUI().getIcon('users'),'Gestionar Personas',self)
        self.GestionarPersonas.triggered.connect(self.gestionPersonasDialog)
        self.GestionarExplotaciones = QtWidgets.QAction(agraeGUI().getIcon('explotacion'),'Gestionar Explotaciones',self)
        self.GestionarExplotaciones.triggered.connect(self.gestionExplotacionDialog)
        self.GestionarCampanias = QtWidgets.QAction(agraeGUI().getIcon('users'),'Gestionar Personas',self)
        self.GestionarCampanias.triggered.connect(self.gestionPersonasDialog)
        self.GestionarAgricultores = QtWidgets.QAction(agraeGUI().getIcon('farmer'),'Gestionar Agricultores',self)
        self.GestionarAgricultores.triggered.connect(self.gestionAgricultorDialog)
        self.GestionarDistribuidores = QtWidgets.QAction(agraeGUI().getIcon('handshake'),'Gestionar Distribuidores',self)
        self.GestionarDistribuidores.triggered.connect(self.gestionDistribuidorDialog)
        self.GestionarCultivos = QtWidgets.QAction(agraeGUI().getIcon('cultivo'),'Gestionar Cultivos',self)
        self.GestionarCultivos.triggered.connect(self.gestionCultivosDialog)
        self.GestionarParametros = QtWidgets.QAction(agraeGUI().getIcon('matraz'),'Gestionar Parametros',self)
        self.GestionarParametros.triggered.connect(self.gestionParametrosDialog)

        actions_data = [self.GestionarExplotaciones,self.GestionarPersonas,self.GestionarAgricultores,self.GestionarDistribuidores,self.GestionarCultivos] # DELETE FROM MASTER
        # actions_data = [self.GestionarExplotaciones,self.GestionarPersonas,self.GestionarAgricultores,self.GestionarDistribuidores,self.GestionarCultivos,self.GestionarParametros]
        
        self.tools.settingsToolsButtons(self.tool_data,actions_data,icon=agraeGUI().getIcon('list-check'),setMainIcon=True)


        # TOOL_AGRAE
        self.IndentifyLoteAction = QtWidgets.QAction(agraeGUI().getIcon('info'),'Identificar Lotes',self) 
        self.IndentifyLoteAction.triggered.connect(self.identify)
        
        self.CargarLotes = QtWidgets.QAction(agraeGUI().getIcon('add'),'Cargar Nuevos Lotes',self)
        self.CargarLotes.triggered.connect(self.cargarLotesDialog)

        self.CrearCE = QtWidgets.QAction(agraeGUI().getIcon('segmentos'),'Cargar CE',self)
        self.CrearCE.triggered.connect(lambda : self.gestionarDatosBaseDialog(0))

        self.CrearSegmentos = QtWidgets.QAction(agraeGUI().getIcon('segmentos'),'Cargar Segmentos',self)
        self.CrearSegmentos.triggered.connect(lambda : self.gestionarDatosBaseDialog(1))

        self.CrearAmbientes = QtWidgets.QAction(agraeGUI().getIcon('ambientes'),'Cargar Ambientes',self)
        self.CrearAmbientes.triggered.connect(lambda : self.gestionarDatosBaseDialog(2))

        actions_agrae = [self.IndentifyLoteAction,self.CargarLotes,self.CrearCE,self.CrearSegmentos,self.CrearAmbientes]

        self.tools.settingsToolsButtons(self.tool_agrae,actions_agrae,icon=agraeGUI().getIcon('tools'),setMainIcon=True)

        # TOOL_CAMP
        self.CrearCampaniaAction = QtWidgets.QAction(agraeGUI().getIcon('add'),'Crear Campaña',self)
        self.CrearCampaniaAction.triggered.connect(self.campaniaCreateDialog)

        # self.CrearCampaniaAction.setToolTip('Crear nueva Campania.')
        self.ClonarCampaniaAction = QtWidgets.QAction(agraeGUI().getIcon('clone'),'Clonar Campaña',self)
        self.ClonarCampaniaAction.triggered.connect(self.campaniaCloneDialog)
        # self.ClonarCampaniaAction.setToolTip('Copiar datos de la Campania.')
        self.EditarCampaniaAction = QtWidgets.QAction(agraeGUI().getIcon('edit'),'Editar Campaña',self)
        self.EditarCampaniaAction.triggered.connect(self.campaniaUpdateDialog)

        self.EliminarCampaniaAction = QtWidgets.QAction(agraeGUI().getIcon('trash'),'Eliminar Campaña',self)
        self.EliminarCampaniaAction.triggered.connect(self.deleteCampania)

        self.ReloadCampaniaAction = QtWidgets.QAction(agraeGUI().getIcon('reload'),'Recargar Campaña',self)
        self.ReloadCampaniaAction.triggered.connect(self.getCampaniasData)

        self.tool_camp_menu = self.tool_camp.menu()
        self.tools.settingsToolsButtons(self.tool_camp,[self.ReloadCampaniaAction,self.CrearCampaniaAction,self.ClonarCampaniaAction,self.EditarCampaniaAction,self.EliminarCampaniaAction])

        # TOOL_EXP
        
        
        
        self.CrearExplotacionAction= QtWidgets.QAction(agraeGUI().getIcon('add'),'Crear Explotacion',self)
        self.CrearExplotacionAction.setToolTip('Crear nueva Explotacion')
        self.CrearExplotacionAction.triggered.connect(self.explotacionCreateDialog)

        self.AsignarExplotacionCampania = QtWidgets.QAction(agraeGUI().getIcon('selection'),'Asignar Explotacion',self)
        self.AsignarExplotacionCampania.setToolTip('Asignar Explotacion a la campaña')
        self.AsignarExplotacionCampania.triggered.connect(self.getIdExplotacion)


        self.ClonarExplotacionAction = QtWidgets.QAction(agraeGUI().getIcon('clone'),'Copiar Explotacion',self)
        self.ClonarExplotacionAction.setToolTip('Clonar Explotacion')
        self.ClonarExplotacionAction.triggered.connect(self.explotacionCopyDialog)
        
        self.EditarExplotacionAction = QtWidgets.QAction(agraeGUI().getIcon('edit'),'Editar Explotacion',self)
        self.EditarExplotacionAction.triggered.connect(self.explotacionUpdateDialog)
        
        self.EliminarExplotacionAction = QtWidgets.QAction(agraeGUI().getIcon('trash'),'Eliminar Explotacion',self)
        self.EliminarExplotacionAction.triggered.connect(self.deleteExplotacion)

        self.tools.settingsToolsButtons(self.tool_exp,[self.CrearExplotacionAction,self.AsignarExplotacionCampania,self.ClonarExplotacionAction,self.EditarExplotacionAction,self.EliminarExplotacionAction])


        # TOOL_LOTE
        self.ClimaLoteAction = QtWidgets.QAction(agraeGUI().getIcon('weather'),'Clima',self) 
        self.ClimaLoteAction.triggered.connect(self.weatherLoteDialog)

        
        self.EditarLoteAction = QtWidgets.QAction(agraeGUI().getIcon('edit'),'Editar Lote',self)
        self.EditarLoteAction.setCheckable(True)
        self.EditarLoteAction.setToolTip('Editar datos del Lote')

        self.ActualizarLoteAction = QtWidgets.QAction(agraeGUI().getIcon('save'),'Actualizar Lote',self)
        self.ActualizarLoteAction.setToolTip('Actualizar datos del Lote')
        self.ActualizarLoteAction.setEnabled(False)
        self.ActualizarLoteAction.triggered.connect(self.updateLote)

        self.EliminarLoteAction = QtWidgets.QAction(agraeGUI().getIcon('trash'),'Eliminar Lote',self)
        self.EliminarLoteAction.setToolTip('Eliminar datos del Lote')
        self.EliminarLoteAction.setEnabled(False)
        self.EliminarLoteAction.triggered.connect(self.deleteLote)

        self.GenerarPanelesDialogAction = QtWidgets.QAction(agraeGUI().getIcon('chart-bar'),'Panel de Analisis Grafico',self)
        self.GenerarPanelesDialogAction.triggered.connect(self.loteAnliticDialog)

        self.EditarLoteAction.triggered.connect(lambda: self.tools.enableElements(self.EditarLoteAction,[self.line_nombre,self.line_produccion,self.combo_cultivo,self.combo_regimen,self.ActualizarLoteAction,self.EliminarLoteAction, self.check_siembra, self.check_cosecha]))
        actions_lote = [self.EditarLoteAction,self.ActualizarLoteAction,self.ClimaLoteAction,self.GenerarPanelesDialogAction,self.EliminarLoteAction,]
        self.tools.settingsToolsButtons(self.tool_lote, actions_lote)

        # TOOL_FERT
        
        self.EditarFertilizacionAction = QtWidgets.QAction(agraeGUI().getIcon('edit'),'Editar Datos',self)
        self.EditarFertilizacionAction.setCheckable(True)
        self.EditarFertilizacionAction.setToolTip('Editar Datos de Fertilizacion')

        self.ActualizarFertilizacionAction = QtWidgets.QAction(agraeGUI().getIcon('save'),'Guardar Datos',self)
        self.ActualizarFertilizacionAction.setEnabled(False)
        self.ActualizarFertilizacionAction.setToolTip('Guardar Datos de Fertilizacion')

        self.EditarFertilizacionAction.triggered.connect(lambda: self.tools.enableElements(self.EditarFertilizacionAction,[self.line_formula,self.line_precio,self.combo_ajuste,self.date_aplicacion,self.ActualizarFertilizacionAction]))
        self.ActualizarFertilizacionAction.triggered.connect(self.saveDataCampania)

        self.settingsToolsButtons(self.tool_fert,[self.EditarFertilizacionAction,self.ActualizarFertilizacionAction])
        # self.settingsToolsButtons(self.tool_fert)

        self.tool_fert_menu = self.tool_fert.menu()

    # DIALOGS
    def campaniaCreateDialog(self):
        dlg = CreateCampaniaDialog()
        dlg.campCreated.connect(self.getCampaniasData)
        dlg.exec()

    def campaniaUpdateDialog(self):
        dlg = UpdateCampaniaDialog(self.combo_campania.currentData())
        dlg.campUpdated.connect(self.getCampaniasData)
        dlg.exec()
        # print(self.combo_campania.currentData())

    def campaniaCloneDialog(self):
        dlg = CloneCampaniaDialog()
        dlg.campCloned.connect(self.getCampaniasData)
        dlg.exec()

    def explotacionCreateDialog(self):
        dlg = CreateExplotacionDialog(self.combo_campania.currentData())
        # dlg.expCreated.connect(lambda e: self.tools.messages('aGrae Tools','Explotacion {} creada correctamente'.format(e),3))
        dlg.loteCreated.connect(self.afterLotesCreated)
        dlg.exec()
    
    def explotacionUpdateDialog(self):
        dlg = UpdateExplotacionDialog(self.combo_explotacion.currentData(),self.combo_explotacion.currentText())
        dlg.expUpdated.connect(lambda: self.getExplotacionData(self.combo_campania.currentData()))
        dlg.exec()
    
    def explotacionCopyDialog(self):
        dlg = CopyExplotacionDialog(self.combo_explotacion.currentData(),self.combo_campania.currentData(),self.combo_explotacion.currentText())
        dlg.expCopied.connect(self.getCampaniasData)
        dlg.exec()

    def loteAnliticDialog(self):
        cultivo = self.combo_cultivo.currentText()
        idcultivo = self.combo_cultivo.currentData()
        produccion = str(self.line_produccion.value())

        
        with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            try:
                sql_data_base = aGraeSQLTools().getSql('data_suelo_base.sql')
                sql_data_base = sql_data_base.format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),self.idLote)
                cursor.execute(sql_data_base)
                r = cursor.fetchone()
                ic = r['indice_cosecha']
                biomasa = r['biomasa']
                residuo = r['residuo']
                ccosecha = r['contenidocosechac']
                cresiduo = r['contenidoresiduoc']
                # print(ic,biomasa,residuo,ccosecha,cresiduo)
                # self.conn.close()
                
            except Exception as ex:
                print(ex)
        data_suelo = self.getData('data_suelo.sql')

        data_extracciones = sorted(self.getData('data_extracciones.sql',True))            
        dlg = agraePlotsDialog(iddata=self.idData,lote=self.nombreLote,cultivo=cultivo, produccion_esperada=produccion,dataSuelo=data_suelo,dataExtraccion=data_extracciones,ic=ic,biomasa=biomasa,residuo=residuo,ccosecha=ccosecha,cresiduo=cresiduo)
        dlg.exec()

    def gestionPersonasDialog(self):
        dlg = GestionPersonasDialog()
        dlg.exec()
        pass

    def gestionDistribuidorDialog(self):
        dlg = GestionDistribuidorDialog()
        dlg.exec()
        pass

    def gestionExplotacionDialog(self):
        dlg = GestionarExplotacionesDialog()
        # dlg = GestionExplotacionDialog()
        # dlg.idExplotacionSignal.connect()
        dlg.exec()
    
    def getIdExplotacion(self):
        
        
        dlg = GestionExplotacionDialog()
        dlg.tableWidget.doubleClicked.disconnect()
        dlg.tableWidget.doubleClicked.connect(dlg.getExplotacionCampania)
        dlg.idExplotacionSignal.connect(self.asignarExplotacionCampania)
        dlg.exec()
        # print(idExplotacion)
    
    def gestionAgricultorDialog(self):
        dlg = GestionAgricultorDialog()
        dlg.exec()

    def gestionCultivosDialog(self):
        dlg = GestionarCultivosDialog()
        dlg.exec()
    
    def gestionParametrosDialog(self):
        dlg = GestionarParametrosDialog()
        dlg.exec()

    def gestionarDatosBaseDialog(self,i):
        dlg = GestionDatosBaseDialog()
        dlg.tabWidget.setCurrentIndex(i)
        dlg.exec()
        
        pass
    
    def cargarLotesDialog(self):
        
        dlg = CrearLotesDialog()
        dlg.exec()

    def generateComposerDialog(self):
        group  = '{}-{}'.format(self.combo_campania.currentText()[2:],self.combo_explotacion.currentText())
        

       

        dlg = agraeComposer(self.atlasLayers,self.combo_campania.currentData(),self.combo_explotacion.currentData())
        dlg.exec()

    def geeDialog(self):
        dlg = aGraeGEEDialog(self.layer,self.combo_explotacion.currentData())
        dlg.exec()

    def asignarCultivosLotes(self):
        #* NUEVO 
        iddata = [str(f['iddata']) for f in self.layer.selectedFeatures()]
        dlg = AsignarCultivosDialog(iddata)
        dlg.exec()
        pass
            #! VIEJO
        # dlg = GestionarCultivosDialog()
        # dlg.tableWidget.doubleClicked.disconnect()
        # dlg.tableWidget.doubleClicked.connect(dlg.getIdCultivoSignal)
        # dlg.idCultivoSignal.connect(self.getIdCultivo)
        
        # dlg.exec()

        # lotes = [str(f['iddata']) for f in self.layer.selectedFeatures()]
        
        # try:
        #     self.tools.asignarMultiplesCultivos(self.idCultivo,lotes)
        # except Exception as ex:
        #   print(ex)
          
        # finally:
        #   self.idCultivo = None
        

    def getIdCultivo(self,data):
        self.idCultivo = data
        

    def monitorRendimientoDialog(self):

        dlg = MonitorRendimientosDialog(
            idcampania=self.combo_campania.currentData(),
            idexplotacion= self.combo_explotacion.currentData()
        )
        dlg.exec()

    # FUCNTIONS
    def identify(self):
        self.identifyTool = selectTool(self.layer)
        self.identifyTool.featureSelected.connect(self.fillDataLote)
        iface.mapCanvas().setMapTool(self.identifyTool)

    def getData(self,query_name:str,check:bool=False) -> list:
        with self.conn.cursor() as cursor:
            sql = aGraeSQLTools().getSql(query_name)
            sql = sql.format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),self.idLote)
            try:
                cursor.execute(sql)
                data = cursor.fetchall()
                if check:
                    data = self.tools.checkData(data)
                return data
            except Exception as ex:
                print(ex)
                self.conn.rollback()

    def afterLotesCreated(self,idexp):
        self.updateComboExp()
        self.getCampaniaCultivoCombo(idexp)


    def weatherLoteDialog(self):
        if self.featureLote != None:
            dlg = LoteWeatherDialog(self.featureLote)
            dlg.exec()
        
    def settingsToolsButtons(self,toolbutton,actions=None,icon:QIcon=None,setMainIcon=False):
        """_summary_

        Args:
            toolbutton (QToolButton): QToolButton Widget
            actions (QAction, optional): Actions added to toolbutton menu, the default action must be in index 0 of list.
            

        """        
        toolbutton.setMenu(QtWidgets.QMenu())
        toolbutton.setPopupMode(QtWidgets.QToolButton.MenuButtonPopup)
        toolbutton.setIconSize(QSize(15,15))
        if actions:
           
            for i in range(len(actions)):
                toolbutton.menu().addAction(actions[i])

        if setMainIcon:
            toolbutton.setIcon(icon)
        else:
            toolbutton.setDefaultAction(actions[0])

    def dateSiembraChanged(self,e):
        self.fechaSiembra = QDate(self.date_siembra.date())
        self.date_cosecha.setMinimumDate(self.date_siembra.date().addDays(15))
        
    def dateCosechaChanged(self,e):
        # print(e)
        self.fechaCosecha = ''

        if self.fechaSiembra != '' or self.date_cosecha.date() >= self.fechaSiembra.addMonths(1):
            self.fechaCosecha = self.date_cosecha.date()
            # print(self.date_cosecha.date())
        pass

    def check_status(self,e,variable,date):
        # print(e)
        if e == 2:
            date.setEnabled(True)
            variable = date.date().toString('yyyy-MM-dd')
            # print(variable)
        else:
            date.setEnabled(False)
            # if self.EditarLoteAction.isChecked():
            #     date.setEnabled(True)
            # else:
            variable = ''
            
    def infoLote(self,i):
        if i == 1:
            iface.mapCanvas().setMapTool(self.identifyTool)

    def updateComboExp(self):
        sql = '''select distinct e.nombre , d.idexplotacion from campaign.data d
        join campaign.campanias c on c.id = d.idcampania 
        join agrae.explotacion e on e.idexplotacion = d.idexplotacion 
        where c.id = {}'''.format(self.combo_campania.currentData())

        sql_date_camp = 'select fecha_desde, fecha_hasta from campaign.campanias where id = {}'.format(self.combo_campania.currentData())
        # print(sql_date_camp)
        self.combo_explotacion.clear()
        with self.conn.cursor() as cursor:
            try:
                cursor.execute(sql)
                data = cursor.fetchall()
                if len(data) >= 1:
                    for e in data:
                        self.combo_explotacion.addItem(e[0],e[1])
            except:
                self.conn.rollback()

            try:
                cursor.execute(sql_date_camp)
                data = cursor.fetchone()
                # print(data[0])
                # self.date_siembra.setDate(self.currentDate)
                self.FechaDesde = data[0]
                self.FechaHasta = data[1]

                self.date_siembra.setMinimumDate(self.FechaDesde)
                self.date_siembra.setMaximumDate(self.FechaHasta)
                self.date_cosecha.setMinimumDate(self.FechaDesde)
                self.date_cosecha.setMaximumDate(self.FechaHasta)
                self.date_aplicacion.setMinimumDate(self.FechaDesde)
                self.date_aplicacion.setMaximumDate(self.FechaHasta)
                # print(data)



            except Exception as ex:
              self.conn.rollback()
              
            #   print(ex)
    
    def asignarLotesExp(self):
        # PRIMERO DEBE CARGAR LA CAPA LOTES AL CANVAS
        # validate
        try:
            layer = QgsProject.instance().mapLayersByName('aGrae Lotes')[0]
        except:
            print('Debe cargar la capa lotes')
            return False
        campania = self.combo_campania.currentData()
        explotacion = self.combo_explotacion.currentData()
        features = list(layer.getSelectedFeatures())
        base = '''insert into campaign.data (idcampania,idexplotacion,idlote) values\n'''
        sql = ''
        if len(features) > 0:
            try:
                for f in features:
                    sql = sql + '({},{},{}),\n'.format(campania,explotacion,f['id'])
                query = base  + sql 
                # print(query[:-2])
                with self.conn.cursor() as cursor:
                    cursor.execute(query[:-2])
                    self.conn.commit()

            except Exception as ex:
                print(ex)
                self.conn.rollback()

        else: 
            print('Debe seleccionar uno o mas lotes')

    def asignarExplotacionCampania(self,e:list):
        
        # PRIMERO DEBE CARGAR LA CAPA LOTES AL CANVAS
        # validate
        try:
            layer = QgsProject.instance().mapLayersByName('aGrae Lotes')[0]
        except:
            print('Debe cargar la capa lotes')
            return False
        
        campania = self.combo_campania.currentData()
        explotacion = e[0]
        base = '''insert into campaign.data (idcampania,idexplotacion,idlote) values\n'''
        sql = ''
        features = list(layer.getSelectedFeatures())
        if len(features) > 0:
            try:
                for f in features:
                    sql = sql + '({},{},{}),\n'.format(campania,explotacion,f['id'])
                query = base  + sql 
                # print(query[:-2])
                with self.conn.cursor() as cursor:
                    cursor.execute(query[:-2])
                    self.conn.commit()

            except Exception as ex:
                print(ex)
                self.conn.rollback()

        else: 
            print('Debe seleccionar uno o mas lotes')

    def getLotesExplotacionLayer(self):
       

        sql = aGraeSQLTools().getSql('view_lotes.sql')

        try:
            self.label_info.setText('Campaña: {} | Explotacion: {}'.format(self.combo_campania.currentData(),self.combo_explotacion.currentData()))
            sql = sql.format(self.combo_campania.currentData(),self.combo_explotacion.currentData())
            self.getCampaniaCultivoCombo(self.combo_explotacion.currentData())
            layer = self.tools.getDataBaseLayer(sql,layername='{}-Lotes'.format(self.combo_campania.currentText()[2:]),styleName='lote',memory=False,idlayer='iddata')
            if layer.id() != self.layer.id():
                QgsProject.instance().removeMapLayer(self.layer.id())

                self.layer = layer
                QgsProject.instance().addMapLayer(self.layer)
                self.identifyTool = selectTool(self.layer)
                self.identifyTool.featureSelected.connect(self.fillDataLote)
                iface.mapCanvas().setMapTool(self.identifyTool)


        except Exception as ex:
            # self.conn.rollback()
            # print(ex)
            pass

                
        self.reloadLayer()
        
        self.focusExp()

        if self.EditarLoteAction.isChecked():
            self.EditarLoteAction.trigger()

            

        pass
    
    def focusExp(self):
        reset = ''
        self.layer.setSubsetString(reset)
        if self.combo_explotacion.currentData() != None:
            # exp = QgsExpression("\"idexplotacion\"={}".format(self.combo_explotacion.currentData()))
            # it = self.layer.getFeatures(QgsFeatureRequest(exp))
            # ids = [f.id() for f in it]
            # self.layer.selectByIds(ids)
            self.layer.setSubsetString("\"idexplotacion\"={}".format(self.combo_explotacion.currentData()))
            # bbox = self.layer.boundingBoxOfSelected()
            # iface.actionZoomToSelected().trigger()
            iface.mapCanvas().setExtent(self.layer.extent())
            iface.mapCanvas().refresh()
            # self.layer.removeSelection()

    def getCampaniaCultivoCombo(self,idexp):
        self.combo_cultivo_2.clear()
        sql = '''select distinct c.nombre, d.idcultivo from campaign.data d
        join agrae.cultivo c on c.idcultivo = d.idcultivo 
        where d.idcampania = {} and d.idexplotacion = {}'''.format(self.combo_campania.currentData(),idexp)
        
        with self.conn.cursor() as cursor: 
            try:
                cursor.execute(sql)
                data = cursor.fetchall()
                for e in data:
                    self.combo_cultivo_2.addItem(e[0],e[1])
                self.getCultivosCampaniaData(self.combo_cultivo_2.currentIndex())
            except Exception as ex:
              self.conn.rollback()
            #   print('{}'.format(ex))

    def enableElements(self,widget,elements:list):
       
        if widget.isChecked():
            for e in elements:
                e.setEnabled(True)
        else:
            for e in elements:
                e.setEnabled(False)

        pass
    
    def getCampaniasData(self):
        self.combo_campania.clear()
        with self.conn.cursor() as cursor:
            # try:
                cursor.execute('''SELECT DISTINCT concat(upper(prefix),'-',UPPER(nombre)) as nombre , id  FROM campaign.campanias ORDER BY id desc''')
                data_camp = cursor.fetchall()
                self.conn.commit()
                for e in data_camp:
                    self.combo_campania.addItem(e[0],e[1])
                
                self.getExplotacionData(self.combo_campania.currentData())
                self.getLotesExplotacionLayer()
            
            # except Exception as ex:
            #     self.conn.rollback()
            #     print(ex,'Error getCampaniasData')
                
    def getExplotacionData(self,idcampania):
        self.combo_explotacion.clear()
        sql = '''select distinct e.nombre , d.idexplotacion from campaign.data d
        join campaign.campanias c on c.id = d.idcampania 
        join agrae.explotacion e on e.idexplotacion = d.idexplotacion 
        where c.id = {}
        order by e.nombre'''.format(idcampania)
        # print(idcampania)
        if idcampania != None:
            with self.conn.cursor() as cursor:
                try:
                    cursor.execute(sql)
                    data = cursor.fetchall()
                    # print(idcampania)
                    if len(data) >= 1 and self.combo_campania.currentData() != None:
                        data_completer = ['{}'.format(e[0]) for e in data]
                        for e in data:
                            self.combo_explotacion.addItem('{}'.format(e[0]),e[1])
                        
                        exp_completer = self.tools.dataCompleter(data_combo=data_completer)
                        self.combo_explotacion.setCompleter(exp_completer)
                        sql_date_camp = 'select fecha_desde, fecha_hasta from campaign.campanias where id = {}'.format(self.combo_campania.currentData())
                        cursor.execute(sql_date_camp)
                        data = cursor.fetchone()
                    
                        self.FechaDesde = data[0]
                        self.FechaHasta = data[1]
                        try:
                            self.date_siembra.setMinimumDate(data[0])
                            self.date_siembra.setMaximumDate(data[1])
                            self.date_cosecha.setMinimumDate(data[0])
                            self.date_cosecha.setMaximumDate(data[1])
                        except Exception as ex:
                            print(ex)
                            pass

                    
                        
                
                except Exception as ex:
                    self.conn.rollback()
                    print(ex,'Error getExpData')
            
    def getCultivosData(self):
        with self.conn.cursor() as cursor:
            try:
                cursor.execute('SELECT DISTINCT UPPER(nombre), idcultivo  FROM agrae.cultivo ORDER BY UPPER(nombre)')
                data_exp = cursor.fetchall() 
                self.conn.commit()
                for e in data_exp: 
                    self.combo_cultivo.addItem(e[0],e[1])
            except Exception as ex:
                self.conn.rollback()
                print(ex)
    
    def getRegimenData(self):
        with self.conn.cursor() as cursor:
            try:
                cursor.execute('SELECT DISTINCT UPPER(nombre), id  FROM analytic.regimen ORDER BY id')
                data_reg = cursor.fetchall()
                self.conn.commit()
                for e in data_reg:
                    self.combo_regimen.addItem(e[0],e[1])
            except Exception as ex:
                self.conn.rollback()
                print(ex)

    def fillCombos(self):
        self.combo_campania.clear()
        self.combo_explotacion.clear()

        with self.conn.cursor(cursor_factory=extras.DictCursor) as cursor:
            
            try:
                cursor.execute('SELECT DISTINCT UPPER(nombre), id  FROM campaign.campanias ORDER BY id desc')
                data_camp = cursor.fetchall()
                self.conn.commit()
                for e in data_camp:
                    self.combo_campania.addItem(e[0],e[1])
            
            except Exception as ex:
                self.conn.rollback()
                print(ex)

            self.updateComboExp()
            self.getLotesExplotacionLayer()

            try:
                cursor.execute('SELECT DISTINCT UPPER(nombre), idcultivo  FROM agrae.cultivo ORDER BY UPPER(nombre)')
                data_exp = cursor.fetchall() 
                self.conn.commit()
                for e in data_exp: 
                    self.combo_cultivo.addItem(e[0],e[1])
            
            except Exception as ex:
                self.conn.rollback()
                print(ex)
            
            try:
                cursor.execute('SELECT DISTINCT UPPER(nombre), id  FROM analytic.regimen ORDER BY id')
                data_reg = cursor.fetchall()
                self.conn.commit()
                for e in data_reg:
                    self.combo_regimen.addItem(e[0],e[1])
                
            except Exception as ex:
                self.conn.rollback()
                print(ex)

    
    def createMuestreoPoints(self):
        
        if len(list(self.layer.getSelectedFeatures())) > 0:
            ids  = [f['iddata'] for f in  list(self.layer.getSelectedFeatures())]
        else:
            ids = [f['iddata'] for f in  list(self.layer.getFeatures())]
        
        reply = QtWidgets.QMessageBox.question(self,'aGrae Toolbox','Quieres generar los puntos de muestreo para:\n{} Lotes de la explotacion :\n{}?'.format(len(ids) , self.combo_explotacion.currentText()),QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:

                self.tools.crearPuntosMuestreo(ids)
 
    def checkData(self,condition,label,value,widget):
        styleNormal = "QLabel { background-color : transparent; color : black; font-weight : normal }"
        styleBackgroudRed = "QLabel { background-color : red; color : white; font-weight : bold }"
        if condition:
            if isinstance(widget,QtWidgets.QComboBox):
                widget.setCurrentIndex(widget.findData(value))
            if isinstance(widget,QtWidgets.QSpinBox):
                try:
                    widget.setValue(value)
                except TypeError:
                    widget.setValue(0)
                    label.setStyleSheet(styleBackgroudRed)
           


            label.setStyleSheet(styleNormal)
            self.label_status.setText('Lote Pendiente')
            self.label_status.setStyleSheet("QLabel { background-color : orange; color : white; }")
        else:
            if isinstance(widget,QtWidgets.QComboBox):
                widget.setCurrentIndex(0)
            if isinstance(widget,QtWidgets.QSpinBox):
                widget.setValue(0)

            # self.tools.messages('aGrae Tools','El lote seleccionado no tiene toda la data necesaria, por favor, complete la misma en el formulario de datos.',1,2)
            label.setStyleSheet(styleBackgroudRed)
            self.label_status.setStyleSheet(styleBackgroudRed)
            self.label_status.setText('Datos Faltantes')
        
    def fillDataLote(self,feat):
        self.combo_cultivo.setCurrentIndex(0)
        iface.addDockWidget(Qt.RightDockWidgetArea,self)

        self.featureLote = feat

        self.date_siembra.setDate(self.FechaDesde)
        self.date_cosecha.setDate(self.FechaHasta)

        self.toolBox.setCurrentIndex(0)

        self.idLote = feat['idlote']
        self.idData = feat['iddata']
        self.nombreLote = feat['lote']
        self.idCultivo = feat['idcultivo']
        self.idRegimen = feat['idregimen']
        self.prodEsperada = feat['prod_esperada']
        self.prodFinal = feat['prod_final']
        self.line_nombre.setText(self.nombreLote)


        self.checkData(isinstance(self.idCultivo,int),self.label_2,self.idCultivo,self.combo_cultivo)
        self.checkData(isinstance(self.idRegimen,int),self.label_4,self.idRegimen,self.combo_regimen)
        self.checkData(isinstance(self.prodEsperada,int) and self.prodEsperada > 0  ,self.label_7,self.prodEsperada,self.line_produccion)

        if isinstance(feat['fechasiembra'],QDate):
            self.check_siembra.setChecked(True)
            if self.EditarLoteAction.isChecked():
                self.date_siembra.setEnabled(True)
            else:
                self.date_siembra.setEnabled(False)

            self.label_status.setText('Cultivando')
            self.label_status.setStyleSheet("QLabel { background-color : green; color : white; }")
            self.fechaSiembra = feat['fechasiembra'].toString('yyyy-MM-dd')
            self.date_siembra.setDate(feat['fechasiembra'])
        else:

            self.check_siembra.setChecked(False)
            self.fechaSiembra = ''

        if isinstance(feat['fechacosecha'],QDate):
            self.check_cosecha.setChecked(True)
            if self.EditarLoteAction.isChecked():
                self.date_cosecha.setEnabled(True)
            else:
                self.date_cosecha.setEnabled(False)
            self.fechaCosecha = feat['fechacosecha'].toString('yyyy-MM-dd')
            self.date_cosecha.setDate(feat['fechacosecha'])
            self.label_status.setText('Lote Cosechado')
            self.label_status.setStyleSheet("QLabel { background-color : blue; color : white; }")
        else:
            self.check_cosecha.setChecked(False)
            self.fechaCosecha = ''
  
        
    def updateLote(self):
        
        cultivo = self.combo_cultivo.currentData()
        regimen = self.combo_regimen.currentData() 
        nombre = self.line_nombre.text()
        produccion = self.line_produccion.value()
        # prod_final = self.line_prod_final.value()
        fechaSiembra = ''
        fechaCosecha = ''
        if self.check_siembra.isChecked():
            fechaSiembra = self.date_siembra.date().toString('yyyy-MM-dd')
       
        if self.check_cosecha.isChecked():
            fechaCosecha = self.date_cosecha.date().toString('yyyy-MM-dd')
        
        sql_lote = '''update agrae.lotes set nombre = '{}' where idlote = {}'''.format(nombre,self.idLote)

        sql_data = '''update campaign.data set idcultivo = {}, idregimen = {}, fechasiembra = nullif('{}','')::date, fechacosecha = nullif('{}','')::date, prod_esperada = {} where iddata = {} '''.format(cultivo,regimen,fechaSiembra,fechaCosecha,produccion,self.idData)
        # print(sql_data)
        with self.conn.cursor() as cursor:
            try:
                if self.nombreLote != self.line_nombre.text():
                    cursor.execute(sql_lote)
                    self.conn.commit()
                # if  self.idCultivo != cultivo or self.idRegimen != regimen or self.prodEsperada != produccion:
                # if  self.idCultivo != cultivo or self.idRegimen != regimen or self.prodEsperada != produccion or self.fechaSiembra != '' or self.fechaCosecha != '':
                   
                cursor.execute(sql_data)
                self.conn.commit()
                self.tools.messages('aGrae Tools','Lote actualizado correctamente',3)
                # self.updateLotesLayer()
                self.reloadLayer()
            
            except Exception as ex:
                self.conn.rollback()
                QgsMessageLog.logMessage('{}'.format(ex), 'aGrae Tools', 2)
                self.tools.messages('aGrae Tools','Ocurrio un error, verifica la información ingresada.',1)
            
        self.date_siembra.setDate(self.FechaDesde)
        self.date_cosecha.setDate(self.FechaDesde)

        self.fechaSiembra = ''
        self.fechaCosecha = ''

        self.EditarLoteAction.setChecked(False)
        self.tools.enableElements(self.EditarLoteAction,[self.line_nombre,self.line_produccion,self.combo_cultivo,self.combo_regimen,self.date_siembra,self.date_cosecha,self.ActualizarLoteAction,self.EliminarLoteAction])
        self.getCampaniaCultivoCombo(self.combo_explotacion.currentData())
        self.fillDataLote(self.featureLote)

        pass
                
    def reloadLayer(self):
        try:
            self.layer.reload()
            self.instance.reloadAllLayers()
        except:
            pass
        # iface.mapCanvas().setExtent(self.layer.extent())

    # CAMPANIA

    def clearAplicacion(self):
        self.date_aplicacion.setDate(self.FechaDesde)
        self.line_formula.clear()
        self.line_precio.clear()
        self.combo_ajuste.setCurrentIndex(0)


    def getCultivosCampaniaData(self,i):
        # print(i)
        self.clearAplicacion()

        querys = {
            0 : '''select distinct  fechafertilizacionfondo,fertilizantefondoformula ,fertilizantefondoprecio, fertilizantefondoajustado  
            from campaign.data d
            where d.idcampania = {} and d.idexplotacion = {} and d.idcultivo  = {}''',
            1 :  '''select distinct  fechafertilizacioncob1,fertilizantecob1formula ,fertilizantecob1precio, fertilizantecob1ajustado  
            from campaign.data d
            where d.idcampania = {} and d.idexplotacion = {} and d.idcultivo  = {}''',
            2 : '''select distinct  fechafertilizacioncob2,fertilizantecob2formula ,fertilizantecob2precio, fertilizantecob2ajustado  
            from campaign.data d
            where d.idcampania = {} and d.idexplotacion = {} and d.idcultivo  = {}''',
            3 : '''select distinct  fechafertilizacioncob3,fertilizantecob3formula ,fertilizantecob3precio, fertilizantecob3ajustado  
            from campaign.data d
            where d.idcampania = {} and d.idexplotacion = {} and d.idcultivo  = {}'''
        }
        if querys[i]:
            sql = querys[i].format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),self.combo_cultivo_2.currentData())

            with self.conn.cursor() as cursor: 
                try:
                    cursor.execute(sql)
                    data = cursor.fetchall()
                    # print(data)
                    data = [e for e in data[0]]
                    # print(data)
                    # print(sql)
                    fecha = data[0]
                    formula = data[1]
                    precio = int(round(data[2]))
                    ajuste = data[3]
                    # print(precio)

                    if isinstance(fecha,QDate):
                        self.date_aplicacion.setDate(fecha)
                    else: 
                        self.label_status_fertilizacion.setText('No existen Datos')
                        self.label_status_fertilizacion.setStyleSheet("QLabel { background-color : orange; color : white; }")
                    if isinstance(formula,str):
                        self.line_formula.setText(formula)
                    else: 
                        self.label_status_fertilizacion.setText('No existen Datos')
                        self.label_status_fertilizacion.setStyleSheet("QLabel { background-color : orange; color : white; }")
                    if isinstance(precio,int):
                        self.line_precio.setValue(precio)
                    else: 
                        self.label_status_fertilizacion.setText('No existen Datos')
                        self.label_status_fertilizacion.setStyleSheet("QLabel { background-color : orange; color : white; }")
                    if isinstance(ajuste,str):
                        self.combo_ajuste.setCurrentText(ajuste)
                    else: 
                        self.label_status_fertilizacion.setText('No existen Datos')
                        self.label_status_fertilizacion.setStyleSheet("QLabel { background-color : orange; color : white; }")

                except Exception as ex:
                    self.conn.rollback()  
                    # print(ex)    

    def saveDataCampania(self):
        fecha = self.date_aplicacion.date().toString('yyyy-MM-dd')
        formula = self.line_formula.text()
        precio = self.line_precio.value()
        ajuste = self.combo_ajuste.currentText()

        querys = {
            0 : '''UPDATE campaign.data
            SET  fechafertilizacionfondo='{}', fertilizantefondoformula='{}', fertilizantefondoprecio={}, fertilizantefondoajustado='{}'
            where idcampania = {} and idexplotacion = {} and idcultivo  = {}''',
            1 :  '''UPDATE campaign.data
            SET  fechafertilizacioncob1='{}', fertilizantecob1formula='{}', fertilizantecob1precio={}, fertilizantecob1ajustado='{}'
            where idcampania = {} and idexplotacion = {} and idcultivo  = {}''',
            2 : '''UPDATE campaign.data
            SET  fechafertilizacioncob2='{}', fertilizantecob2formula='{}', fertilizantecob2precio={}, fertilizantecob2ajustado='{}'
            where idcampania = {} and idexplotacion = {} and idcultivo  = {}''',
            3 : '''UPDATE campaign.data
            SET  fechafertilizacioncob3='{}', fertilizantecob3formula='{}', fertilizantecob3precio={}, fertilizantecob3ajustado='{}'
            where idcampania = {} and idexplotacion = {} and idcultivo  = {}'''
        }

        
        if self.combo_ajuste.currentIndex() != 0:
            reply = QtWidgets.QMessageBox.question(self,'aGrae Toolbox','Quieres guardar los datos de {}?'.format(self.combo_aplicacion.currentText()),QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)

            if reply == QtWidgets.QMessageBox.Yes:
                q = querys[self.combo_aplicacion.currentIndex()]
                sql = q.format(fecha,formula,precio,ajuste,self.combo_campania.currentData(),self.combo_explotacion.currentData(),self.combo_cultivo_2.currentData())
                
                try:
                  with self.conn.cursor() as cursor:
                        cursor.execute(sql)
                        self.conn.commit()
                        self.tools.messages('aGrae Tools','Datos de fertilizacion guardados correctamente',3,alert=True)

                except  Exception as ex:
                    self.conn.rollback()
                    QgsMessageLog.logMessage('{}'.format(ex), 'aGrae Tools', 2)
                    self.tools.messages('aGrae Tools','Ocurrio un error',2)
                    # print(ex)
        else:
            iface.messageBar().pushMessage('aGrae Toolbox','Debe seleccionar un ajuste',0,3)


        # self.enableElements(self.EditarFertilizacionAction,[self.line_formula,self.line_precio,self.combo_ajuste,self.date_aplicacion,self.btn_update_fert,self.ActualizarFertilizacionAction])
            
    
    def deleteCampania(self):
        question = 'Quieres eliminar la Campania {}?, esta acción eliminará solo los datos asociados a la campaña seleccionada.'.format(self.combo_campania.currentText())
        sql = '''delete from campaign.campanias where id = {} '''.format(self.combo_campania.currentData())
        # print(sql)
        try:
            self.tools.deleteAction(question,sql)
        except Exception as ex:
            print(ex)

        self.reloadLayer()
        self.getCampaniasData()

    def deleteExplotacion(self):
        question = 'Quieres eliminar la Explotacion {}?, esta acción eliminará\nsolo los datos asociados a la campaña seleccionada.'.format(self.combo_explotacion.currentText())
        sql = '''delete from campaign.data where idcampania = {} and idexplotacion = {}'''.format(self.combo_campania.currentData(),self.combo_explotacion.currentData())
        self.tools.deleteAction(question,sql)
        self.getExplotacionData(self.combo_campania.currentData())
        self.reloadLayer()

    def deleteLote(self):
        question = 'Quieres eliminar el lote {}?, esta acción eliminará\nsolo los datos asociados a la campaña.'.format(self.nombreLote)
        sql = '''delete from campaign.data where iddata = {}'''.format(self.idData)
        actions = [self.line_nombre,self.line_produccion,self.combo_cultivo,self.combo_regimen,self.date_siembra,self.date_cosecha,self.ActualizarLoteAction,self.EliminarLoteAction]
        try:
            self.tools.deleteAction(question,sql,self.EditarLoteAction,actions)
            self.tools.messages('aGrae Tools','Se elimino el lote {} de la explotacion actual.'.format(self.nombreLote),3,duration=5)
        except Exception as ex:
            print(ex)
            self.tools.messages('aGrae Tools','No se pudo eliminar el lote'.format(self.nombreLote),2,alert=True)


    def crearFormatoAnalitica(self):
        # METODO PARA CREAR LOS FORMATOS DE REPORTES ANALITICOS EN ARCHIVOS .CSV
        exp = self.combo_explotacion.currentText().replace(' ','_')
        camp  = self.combo_campania.currentText()[2:].replace(' ','_')
        name = '{}_{}'.format(camp,exp)
        reply = QtWidgets.QMessageBox.question(self,'aGrae Toolbox','Quieres generar el archivo de Analitica para la explotacion:\n{}?'.format(name),QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            self.tools.crearFormatoAnalitica(self.combo_campania.currentData(),self.combo_explotacion.currentData(),name)
    
    def cargarAnalitica(self):
        data = self.tools.cargarReporteAnalitica()
        if not data.empty:
            dlg = agraeAnaliticaDialog(data)
            dlg.exec()
    
    def DerivarAnalitica(self):
        file = self.tools.cargarReporteAnalitica(dataframe=False)
        if file:
            try:
                print(file)
                modulo = aGraeResamplearMuestras(file)
                modulo.processing()
                self.tools.messages('aGrae GIS','Archivo procesado Correctamente',3,True)
            except Exception as ex:
                self.tools.messages('aGrae GIS',ex,2)
            

    
    def new_generarCapasExplotacion(self):
        self.atlasLayers = {}
        self.atlasLayers['Atlas'] = self.layer.clone()
        
        dlg = ReportesDialog()
        dlg.exec()

        pass

    def generarCapasExplotacion(self):
        self.atlasLayers = {}
        self.atlasLayers['Atlas'] = self.layer.clone()

        name_camp = self.combo_campania.currentText()[2:]
        name_exp = self.combo_explotacion.currentText()
        sql_intra = '''select row_number() over () as id, explotacion,cultivo,lote,uf,uf_etiqueta,f_fondo,d_fondo,f_cob1,d_cob1,f_cob2,d_cob2,f_cob3,d_cob3,area_ha,st_asText(geom) as geom from fert_intraparcelaria'''
        # sql_intra = '''select * from mapa_sig'''

        queries = {
            # 'Ambientes': aGraeSQLTools().getSql('ambientes_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData()),
            'Segmentos': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select distinct idlote,nombre as lote,codigo as codigo_muestra,segmento,ceap,st_asText(geom) as geom from segm_analitica;'''),
            'Nitrogeno': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select distinct idlote,nombre as lote,codigo as codigo_muestra,n as valor,lower(n_tipo) as tipo, n_inc as incremento, st_asText(geom) as geom from segm_analitica;'''),
            'Fosforo': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select distinct idlote,nombre as lote,codigo as codigo_muestra,p as valor,lower(p_tipo) as tipo, p_inc as incremento,st_asText(geom) as geom from segm_analitica;'''),
            'Potasio': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select distinct idlote,nombre as lote,codigo as codigo_muestra,k as valor,lower(k_tipo) as tipo, k_inc as incremento,st_asText(geom) as geom from segm_analitica;'''),
            'PH': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select distinct idlote,nombre as lote,codigo as codigo_muestra,ph as valor,lower(ph_tipo) as tipo,st_asText(geom) as geom from segm_analitica;'''),
            'Conductividad Electrica': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select distinct idlote,nombre as lote,codigo as codigo_muestra,ce/100 as ce ,st_asText(geom) as geom from segm_analitica;'''),
            'Calcio': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select distinct idlote,nombre as lote,codigo as codigo_muestra,ca as valor,lower(ca_tipo) as tipo,st_asText(geom) as geom from segm_analitica;'''),
            'Magnesio': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select distinct idlote,nombre as lote,codigo as codigo_muestra,mg as valor,lower(mg_tipo) as tipo,st_asText(geom) as geom from segm_analitica;'''),
            'Sodio': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select distinct idlote,nombre as lote,codigo as codigo_muestra,na as valor,lower(na_tipo) as tipo,st_asText(geom) as geom from segm_analitica;'''),
            'Azufre': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select distinct idlote,nombre as lote,codigo as codigo_muestra,s as valor,st_asText(geom) as geom from segm_analitica;'''),
            'CIC': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''
            select distinct idlote,nombre as lote,codigo as codigo_muestra,
            (case when segmento = 1 then 'Rojo' when segmento = 2 then 'Verde' when segmento = 3 then 'Azul' end) as "SEGMENTO",
            round(cic::numeric,1)::double precision as "CIC", 
            round(round(ca::numeric,1) / (ca + mg + k + na)::numeric * 100,1)::double precision || '%' as "CA",
            round(round(mg::numeric,1) / (ca + mg + k + na)::numeric * 100,1)::double precision || '%' as "MG",
            round(round(k::numeric,1) / (ca + mg + k + na)::numeric * 100,1)::double precision || '%' as "K",
            round(round(na::numeric,1) / (ca + mg + k + na)::numeric * 100,1)::double precision || '%' as "NA",
            st_asText(st_union(geom)) as geom 
            from segm_analitica
            group by idlote,nombre,codigo,segmento,cic,ca,mg,k,na;'''),
            'Hierro': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select distinct idlote,nombre as lote,codigo as codigo_muestra,fe,st_asText(geom) as geom from segm_analitica;'''),
            'Manganeso': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select distinct idlote,nombre as lote,codigo as codigo_muestra,mn as valor,st_asText(geom) as geom from segm_analitica;'''),
            'Aluminio': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select distinct idlote,nombre as lote,codigo as codigo_muestra,al,st_asText(geom) as geom from segm_analitica;'''),
            'Boro': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select distinct idlote,nombre as lote,codigo as codigo_muestra,b,st_asText(geom) as geom from segm_analitica;'''),
            'Cinq': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select distinct idlote,nombre as lote,codigo as codigo_muestra,zn ,st_asText(geom) as geom from segm_analitica;'''),
            'Cobre': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select distinct idlote,nombre as lote,codigo as codigo_muestra,cu,st_asText(geom) as geom from segm_analitica;'''),
            # 'Materia Organica': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select distinct idlote,nombre as lote,codigo as codigo_muestra,organi ,st_asText(geom) as geom from segm_analitica;'''),
            # 'Relacion CN': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select distinct idlote,nombre as lote,codigo as codigo_muestra,rel_cn,st_asText(geom) as geom from segm_analitica;'''),
            'Fert Variable Intraparcelaria': aGraeSQLTools().getSql('uf_aportes_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),sql_intra),
            'Fert Variable Parcelaria': aGraeSQLTools().getSql('uf_aportes_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select * from fert_parcelaria'''),
            'Ceap36 Textura': aGraeSQLTools().getSql('ceap36_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData()),
            'Ceap36 Infiltracion': aGraeSQLTools().getSql('ceap36_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData()),
            'Ceap90 Textura': aGraeSQLTools().getSql('ceap90_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData()),
            'Ceap90 Infiltracion': aGraeSQLTools().getSql('ceap90_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData()),
            # 'Rendimiento' : aGraeSQLTools().getSql('rindes_layer_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData())
        }

        

        for q in reversed(queries):
            name = '{}-{}-{}'.format(name_camp,name_exp,q)

            if 'Textura' in q:
                layer = self.tools.getDataBaseLayer(queries[q],name,'ceap_textura')
            elif 'Infiltracion' in q:
                layer = self.tools.getDataBaseLayer(queries[q],name,'ceap_infiltracion')
            
            elif 'Intraparcelaria' in q:
                layer = self.tools.getDataBaseLayer(queries[q],name,q,debug=False)

            else:
                layer = self.tools.getDataBaseLayer(queries[q],name,q)
                
            if layer.isValid():
                self.atlasLayers[q] = layer
                QgsProject.instance().addMapLayer(layer)

        ambientes = self.tools.getDataBaseLayerUri(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'{}-{}'.format(name_camp,name_exp))
        self.atlasLayers['Ambientes'] = ambientes
        QgsProject.instance().addMapLayer(ambientes)

        
    def exportarUFS(self):
        idcampania = self.combo_campania.currentData()
        idexplotacion = self.combo_explotacion.currentData()
        nameExp = str(self.combo_explotacion.currentText()).replace(' ','_')
        name_folder = '{}{}_{}'.format(idcampania,idexplotacion,nameExp)

        # self.tools.exportarUFS(idcampania,idexplotacion,nameExp)
        s = QSettings('agrae','dbConnection')
        path = s.value('ufs_path')
        path = os.path.join(path,name_folder)

        if not os.path.exists(path):
            os.makedirs(path)

        if len(self.layer.selectedFeatures()) > 0:
            lotes = [f for f in self.layer.selectedFeatures()]
        else:
            lotes = [f for f in self.layer.getFeatures()]
        
        for lote in lotes:
            name = lote['lote']
            self.tools.exportarUFS(path,lote['iddata'],lote['lote'])


    def exportarResumen(self):
        idcampania = self.combo_campania.currentData()
        idexplotacion = self.combo_explotacion.currentData()
        nameExp = str(self.combo_explotacion.currentText()).replace(' ','_')
        self.tools.exportarResumenFertilizacion(idcampania,idexplotacion,nameExp)

    #* DESACTIVADA
    def populateContextMenu(self,menu: QtWidgets.QMenu, event: QgsMapMouseEvent):
        self.subMenu = menu.addMenu('aGrae')
        analizeAction = QtWidgets.QAction(
            agraeGUI().getIcon('main'),
            self.tr('Analizar la seleccion'),
            iface.mainWindow()
        )

        # analizeAction.triggered.connect(self.analyzeParcels)
        self.subMenu.addAction(analizeAction)
        # self.subMenu.addAction(self.simpleSelection)
        # self.subMenu.addAction(self.polygonSelection)





class selectTool(QgsMapToolIdentify):

    featureSelected = pyqtSignal(QgsFeature)
    def __init__(self, layer):
        self.iface = iface
        self.canvas = self.iface.mapCanvas()
        self.layer = layer
        iface.setActiveLayer(self.layer)

        QgsMapToolIdentify.__init__(self, self.canvas)
        
        # self.iface.currentLayerChanged.connect(self.active_changed)
        
    def active_changed(self, layer):
        if isinstance(layer, QgsVectorLayer) and layer.isSpatial():
            self.layer = layer
            
    def canvasPressEvent(self, event):
        results = self.identify(event.x(), event.y(), [self.layer], QgsMapToolIdentify.TopDownAll)
        # context = QgsRenderContext()
        

    #    print(results)
        if len(results) == 1:
            feature = results[0].mFeature
            # print(feature)
            self.featureSelected.emit(feature)
            # print(results[i].mFeature)
        
        
    def deactivate(self):
        # self.iface.currentLayerChanged.disconnect(self.active_changed)

        pass





    

        
