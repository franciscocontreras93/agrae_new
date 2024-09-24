from PIL import Image
import os
from qgis.PyQt import uic
from qgis.PyQt.QtXml import QDomDocument

from qgis.core import *
from qgis.utils import iface

from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSignal, QSettings, QDateTime, QThreadPool
from PyQt5.QtGui import QFont

from ..tools import aGraeTools
from ..tools.composerTools import aGraeComposerTools
from ..sql import aGraeSQLTools
agraeComposerDialog, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'ui/composer_dialog.ui'))
class agraeComposer(QDialog,agraeComposerDialog):
    closingPlugin = pyqtSignal()
    def __init__(self,layers,idcampania,idexplotacion,parent=None) -> None:
        super(agraeComposer,self).__init__(parent)
        self.setupUi(self)
        self.layers = layers
        self.tools = aGraeTools()
        self.composerTools = aGraeComposerTools(self.layers,idcampania,idexplotacion)
        self.setWindowTitle('Generar Reporte de Preescripcion')
        self.setModal(False)
        

        # self.threadpool = QThreadPool()
        # self.atlas = None
        # self.settings = QSettings('agrae','dbConnection')
        # self.panels_path = self.settings.value('paneles_path')
        # self.reportes_path = self.settings.value('reporte_path')
        # self.tools = aGraeTools()
        # self.conn = self.tools.conn()
        # # self.tools = AgraeToolset()
        # self.excludedProviders = ['DB2', 'EE', 'OAPIF', 'WFS', 'arcgisfeatureserver', 'arcgismapserver', 'ept', 'gdal', 'grass', 'grassraster', 'hana', 'mdal', 'mesh_memory', 'mssql','oracle', 'postgresraster',  'virtualraster', 'wcs', 'wms']
        # self.clasificationMethods = [
        #     'Cuantil',
        #     'Escala Logaritmica',
        #     'Desviacion Standard',
        #     'Intervalo Igual',
        #     'Pretty Breaks',
        #     'Jenks']
        self.plugin_dir = os.path.dirname(__file__)
        # self.root = QgsProject.instance().layerTreeRoot()
        # self.groups = [ g for g in self.root.children() if isinstance(g, QgsLayerTreeGroup) ] 

        # # self.comboBox.addItems(lambda name: for x.name() in self.groups)

        

        # self.render = None
       

        
        self.UIComponents()
        # print(self.excludedLayers)
    def closeEvent(self,event):
        self.closingPlugin.emit()

        event.accept()
    def populateCombos(self):
    
        self.combo_basemap.clear()
        self.combo_basemap.addItems([k for k in self.composerTools.basemaps])

    def UIComponents(self):
        self.populateCombos()
        self.pushButton.clicked.connect(self.generateComposer)
        # self.pushButton.clicked.connect(lambda: self.layoutGenerator(preview=True))
        # self.pushButton_2.clicked.connect(self.ComposerPrintWorker)
    
    
    def generateComposer(self):
        self.composerTools.generateComposer(self.combo_basemap.currentText())
        self.close()
    
        
        pass

    def generateLayers(self):
        
        queries = {
            'Segmentos': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select idlote,nombre as lote,codigo as codigo_muestra,segmento,ceap,st_asText(geom) as geom from segm_analitica;'''),
            'Nitrogeno': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select idlote,nombre as lote,codigo as codigo_muestra,n,lower(n_tipo) as tipo, n_inc as incremento, st_asText(geom) as geom from segm_analitica;'''),
            'Fosforo': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select idlote,nombre as lote,codigo as codigo_muestra,p,lower(p_tipo) as tipo, p_inc as incremento,st_asText(geom) as geom from segm_analitica;'''),
            'Potasio': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select idlote,nombre as lote,codigo as codigo_muestra,k,lower(k_tipo) as tipo, k_inc as incremento,st_asText(geom) as geom from segm_analitica;'''),
            'PH': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select idlote,nombre as lote,codigo as codigo_muestra,ph as valor,lower(ph_tipo) as tipo,st_asText(geom) as geom from segm_analitica;'''),
            'Conductividad Electrica': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select idlote,nombre as lote,codigo as codigo_muestra,ce ,st_asText(geom) as geom from segm_analitica;'''),
            'Calcio': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select idlote,nombre as lote,codigo as codigo_muestra,ca,lower(ca_tipo) as tipo,st_asText(geom) as geom from segm_analitica;'''),
            'Magnesio': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select idlote,nombre as lote,codigo as codigo_muestra,mg,lower(mg_tipo) as tipo,st_asText(geom) as geom from segm_analitica;'''),
            'Sodio': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select idlote,nombre as lote,codigo as codigo_muestra,na,lower(na_tipo) as tipo,st_asText(geom) as geom from segm_analitica;'''),
            'Azufre': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select idlote,nombre as lote,codigo as codigo_muestra,s as valor,st_asText(geom) as geom from segm_analitica;'''),
            'CIC': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select idlote,nombre as lote,codigo as codigo_muestra,
            (case when segmento = 1 then 'Rojo' when segmento = 2 then 'Verde' when segmento = 3 then 'Azul' end) as segmento,
            round(cic::numeric,2)::double precision as cic, 
            round(ca::numeric,2)::double precision as ca,
            round(mg::numeric,2)::double precision as mg, 
            round(k::numeric,2)::double precision as k, 
            round(na::numeric,2)::double precision as na,
            st_asText(geom) as geom from segm_analitica;'''),
            'Hierro': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select idlote,nombre as lote,codigo as codigo_muestra,fe,st_asText(geom) as geom from segm_analitica;'''),
            'Manganeso': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select idlote,nombre as lote,codigo as codigo_muestra,mn as valor,st_asText(geom) as geom from segm_analitica;'''),
            'Aluminio': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select idlote,nombre as lote,codigo as codigo_muestra,al as valor,st_asText(geom) as geom from segm_analitica;'''),
            'Boro': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select idlote,nombre as lote,codigo as codigo_muestra,b,st_asText(geom) as geom from segm_analitica;'''),
            'Cinq': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select idlote,nombre as lote,codigo as codigo_muestra,zn,st_asText(geom) as geom from segm_analitica;'''),
            'Cobre': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select idlote,nombre as lote,codigo as codigo_muestra,cu,st_asText(geom) as geom from segm_analitica;'''),
            'Materia Organica': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select idlote,nombre as lote,codigo as codigo_muestra,organi,st_asText(geom) as geom from segm_analitica;'''),
            'Relacion CN': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select idlote,nombre as lote,codigo as codigo_muestra,rel_cn,st_asText(geom) as geom from segm_analitica;'''),
            'Fert Variable Intraparcelaria': aGraeSQLTools().getSql('uf_aportes_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select lote,uf, uf_etiqueta, necesidades_iniciales, fertilizantefondoformula, fertilizantefondocalculado,fertilizantecob1formula, fertilizantecob1calculado,fertilizantecob2formula, fertilizantecob2calculado,fertilizantecob3formula, fertilizantecob3calculado,area_ha,st_asText(geom) as geom from uf_final uf'''),
            'Fert Variable Parcelaria': aGraeSQLTools().getSql('uf_aportes_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select distinct lote,fertilizantefondoformula,round(sum(fertilizantefondocalculado * area_ha))::integer dosisfondo,fertilizantecob1formula,round(sum(fertilizantecob1calculado * area_ha))::integer dosiscob1,fertilizantecob2formula,round(sum(fertilizantecob2calculado * area_ha))::integer dosiscob2,fertilizantecob3formula,round(sum(fertilizantecob3calculado * area_ha))::integer dosiscob3,sum(area_ha) area_ha,st_asText(st_union(geom)) geom from uf_final group by lote,fertilizantefondoformula,fertilizantecob1formula,fertilizantecob2formula,fertilizantecob3formula'''),
            'Ceap36 Textura': aGraeSQLTools().getSql('ceap36_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData()),
            'Ceap36 Infiltracion': aGraeSQLTools().getSql('ceap36_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData()),
            'Ceap90 Textura': aGraeSQLTools().getSql('ceap90_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData()),
            'Ceap90 Infiltracion': aGraeSQLTools().getSql('ceap90_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData()),
            'Rendimiento' : aGraeSQLTools().getSql('rindes_layer_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData())
        }
        

        pass
    






    
