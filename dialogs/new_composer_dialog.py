from PyQt5.QtWidgets import QDialog, QVBoxLayout, QCheckBox, QButtonGroup, QPushButton, QGridLayout, QWidget, QHBoxLayout, QLabel, QComboBox, QProgressBar
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QRunnable, QThreadPool, QObject
from qgis.core import QgsProject, QgsMessageLog, Qgis,QgsVectorLayer
from ..tools.composerTools import aGraeComposerTools
from ..tools import aGraeTools, aGraeSQLTools
from ..gui import agraeGUI


class WorkerSignals(QObject):
    """
    Defines the signals available from a running worker thread.
    """
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)
    current_layer = pyqtSignal(str)  # Signal to emit the current layer name


class LayerGeneratorWorker(QRunnable):
    """
    Worker thread for generating layers.
    """

    def __init__(self, queries, layers_dict, basic_mode):
        super().__init__()
        self.queries = queries
        self.tools = aGraeTools()
        self.layers_dict = layers_dict
        self.signals = WorkerSignals()
        self.basic_mode = basic_mode

    def run(self):
        """
        Your code goes in this function.
        """
        try:
            if self.basic_mode:
                selected_queries = {k: self.queries[k] for k in ['Ambientes', 'Segmentos','Fert Variable Intraparcelaria', 'Fert Variable Parcelaria', 'Ceap36 Textura', 'Ceap36 Infiltracion', 'Ceap90 Textura', 'Ceap90 Infiltracion']}
            else:
                selected_queries = self.queries

            total_queries = len(selected_queries)
            current_query = 0

            for q in reversed(selected_queries):
                current_query += 1
                self.signals.progress.emit(int((current_query / total_queries) * 100))
                self.signals.current_layer.emit('{}/{} {} '.format(current_query, total_queries,q))  # Emit the current layer name

                if 'Textura' in q:
                    layer = self.tools.getDataBaseLayer(selected_queries[q], q, 'ceap_textura')
                elif 'Infiltracion' in q:
                    layer = self.tools.getDataBaseLayer(selected_queries[q], q, 'ceap_infiltracion')
                elif 'Intraparcelaria' in q:
                    layer = self.tools.getDataBaseLayer(selected_queries[q], q, q, debug=False)
                else:
                    layer = self.tools.getDataBaseLayer(selected_queries[q], q, q)

                if layer.isValid():
                    self.layers_dict[q] = layer
                    # QgsProject.instance().addMapLayer(layer)

            self.signals.finished.emit()

        except Exception as e:
            self.signals.error.emit((type(e), e, None))

class new_Composer(QDialog):
    def __init__(self, idcampania: int, idexplotacion: int, lotesLayer:QgsVectorLayer, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Generar Informe")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWindowIcon(agraeGUI().getIcon('printer'))
        self.idcampania = idcampania
        self.idexplotacion = idexplotacion

        self.layers = {}
        self.layers['Atlas'] = lotesLayer
        self.threadpool = QThreadPool()
        self.tools = aGraeTools()

        # Create the checkboxes
        self.check_basicos = QCheckBox("Mapas Basicos (Ambientes-Segmentos-Texturas)")
        self.check_preescripcion = QCheckBox("Preescripcion")
        self.check_preescripcion.setChecked(True)

        # Create a button group
        self.button_group = QButtonGroup()

        # Add the checkboxes to the button group
        self.button_group.addButton(self.check_basicos)
        self.button_group.addButton(self.check_preescripcion)

        # Set exclusive mode (only one can be checked at a time)
        self.button_group.setExclusive(True)

        # Create a horizontal layout for the checkboxes
        checkbox_layout = QHBoxLayout()
        checkbox_layout.addWidget(self.check_basicos)
        checkbox_layout.addWidget(self.check_preescripcion)

        # Create a widget to hold the checkbox layout
        checkbox_widget = QWidget()
        checkbox_widget.setLayout(checkbox_layout)

        # create Basemap selector
        label_basemap = QLabel('Seleccionar un Basemap')
        self.combo_basemap = QComboBox()
        self.combo_basemap.addItems([k for k in self.tools.getBasemapsDict()])

        combo_layout = QHBoxLayout()
        combo_layout.addWidget(label_basemap)
        combo_layout.addWidget(self.combo_basemap)

        # Create progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
         # Add a label to show the current layer
        self.current_layer_label = QLabel("Generando Capa: ")

        # Create buttons
        self.btn_generar = QPushButton("Generar Reporte")
        self.btn_imprimir = QPushButton("Imprimir Reporte")
        self.btn_imprimir.setEnabled(False)
        self.cancel_button = QPushButton("Cancel")
        self.btn_generar.clicked.connect(self.on_generate_clicked)
        self.cancel_button.clicked.connect(self.reject)

        # Create a layout for buttons
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.btn_generar)
        button_layout.addWidget(self.btn_imprimir)
        button_layout.addWidget(self.cancel_button)

        # Create a main layout and add the checkboxes and buttons
        main_layout = QVBoxLayout()
        main_layout.addWidget(checkbox_widget)
        main_layout.addLayout(combo_layout)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.current_layer_label)  # Add the label to the layout
        main_layout.addLayout(button_layout)
        main_layout.setSpacing(30)
        self.setLayout(main_layout)

    def on_generate_clicked(self):
        self.btn_generar.setEnabled(False)
        self.progress_bar.setValue(0)
        self.generateLayers()

    def get_checked_button_text(self):
        """Returns the text of the currently checked button, or None if none are checked."""
        checked_button = self.button_group.checkedButton()
        if checked_button:
            return checked_button.text()
        return None

    def generateLayers(self):
        queries = {
            'Ambientes': aGraeSQLTools().getSql('ambientes_layers_query.sql').format(self.idcampania, self.idexplotacion),
            'Segmentos': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.idcampania, self.idexplotacion, '''select distinct idlote,nombre as lote,codigo as codigo_muestra,segmento,ceap,st_asText(geom) as geom from segm_analitica;'''),
            'Nitrogeno': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.idcampania, self.idexplotacion, '''select distinct idlote,nombre as lote,codigo as codigo_muestra,n as valor,lower(n_tipo) as tipo, n_inc as incremento, st_asText(geom) as geom from segm_analitica;'''),
            'Fosforo': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.idcampania, self.idexplotacion, '''select distinct idlote,nombre as lote,codigo as codigo_muestra,p as valor,lower(p_tipo) as tipo, p_inc as incremento,st_asText(geom) as geom from segm_analitica;'''),
            'Potasio': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.idcampania, self.idexplotacion, '''select distinct idlote,nombre as lote,codigo as codigo_muestra,k as valor,lower(k_tipo) as tipo, k_inc as incremento,st_asText(geom) as geom from segm_analitica;'''),
            'PH': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.idcampania, self.idexplotacion, '''select distinct idlote,nombre as lote,codigo as codigo_muestra,ph as valor,lower(ph_tipo) as tipo,st_asText(geom) as geom from segm_analitica;'''),
            'Conductividad Electrica': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.idcampania, self.idexplotacion, '''select distinct idlote,nombre as lote,codigo as codigo_muestra,ce/100 as ce ,st_asText(geom) as geom from segm_analitica;'''),
            'Calcio': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.idcampania, self.idexplotacion, '''select distinct idlote,nombre as lote,codigo as codigo_muestra,ca as valor,lower(ca_tipo) as tipo,st_asText(geom) as geom from segm_analitica;'''),
            'Magnesio': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.idcampania, self.idexplotacion, '''select distinct idlote,nombre as lote,codigo as codigo_muestra,mg as valor,lower(mg_tipo) as tipo,st_asText(geom) as geom from segm_analitica;'''),
            'Sodio': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.idcampania, self.idexplotacion, '''select distinct idlote,nombre as lote,codigo as codigo_muestra,na as valor,lower(na_tipo) as tipo,st_asText(geom) as geom from segm_analitica;'''),
            'Azufre': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.idcampania, self.idexplotacion, '''select distinct idlote,nombre as lote,codigo as codigo_muestra,s as valor,st_asText(geom) as geom from segm_analitica;'''),
            'CIC': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.idcampania, self.idexplotacion, '''
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
            'Hierro': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.idcampania, self.idexplotacion, '''select distinct idlote,nombre as lote,codigo as codigo_muestra,fe,st_asText(geom) as geom from segm_analitica;'''),
            'Manganeso': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.idcampania, self.idexplotacion, '''select distinct idlote,nombre as lote,codigo as codigo_muestra,mn as valor,st_asText(geom) as geom from segm_analitica;'''),
            'Aluminio': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.idcampania, self.idexplotacion, '''select distinct idlote,nombre as lote,codigo as codigo_muestra,al,st_asText(geom) as geom from segm_analitica;'''),
            'Boro': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.idcampania, self.idexplotacion, '''select distinct idlote,nombre as lote,codigo as codigo_muestra,b,st_asText(geom) as geom from segm_analitica;'''),
            'Cinq': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.idcampania, self.idexplotacion, '''select distinct idlote,nombre as lote,codigo as codigo_muestra,zn ,st_asText(geom) as geom from segm_analitica;'''),
            'Cobre': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.idcampania, self.idexplotacion, '''select distinct idlote,nombre as lote,codigo as codigo_muestra,cu,st_asText(geom) as geom from segm_analitica;'''),
            # 'Materia Organica': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.idcampania, self.idexplotacion, '''select distinct idlote,nombre as lote,codigo as codigo_muestra,organi ,st_asText(geom) as geom from segm_analitica;'''),
            # 'Relacion CN': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.idcampania, self.idexplotacion, '''select distinct idlote,nombre as lote,codigo as codigo_muestra,rel_cn,st_asText(geom) as geom from segm_analitica;'''),
            'Fert Variable Intraparcelaria': aGraeSQLTools().getSql('uf_aportes_query.sql').format(self.idcampania, self.idexplotacion, 'select * from mapa_sig'),
            # 'Fert Variable Intraparcelaria': aGraeSQLTools().getSql('uf_aportes_query.sql').format(self.idcampania, self.idexplotacion, 'select iddata,uf,uf_etiqueta,st_asText(geom) as geom  from fert_intraparcelaria'),
            
            'Fert Variable Parcelaria': aGraeSQLTools().getSql('uf_aportes_query.sql').format(self.idcampania, self.idexplotacion, '''select * from fert_parcelaria'''),
            'Ceap36 Textura': aGraeSQLTools().getSql('ceap36_layers_query.sql').format(self.idcampania, self.idexplotacion),
            'Ceap36 Infiltracion': aGraeSQLTools().getSql('ceap36_layers_query.sql').format(self.idcampania, self.idexplotacion),
            'Ceap90 Textura': aGraeSQLTools().getSql('ceap90_layers_query.sql').format(self.idcampania, self.idexplotacion),
            'Ceap90 Infiltracion': aGraeSQLTools().getSql('ceap90_layers_query.sql').format(self.idcampania, self.idexplotacion),
            # 'Rendimiento' : aGraeSQLTools().getSql('rindes_layer_query.sql').format(self.idcampania, self.idexplotacion)
            # 'Mapa_SIG' : aGraeSQLTools().getSql('uf_aportes_query.sql').format(self.idcampania, self.idexplotacion,'select * from mapa_sig')
        }

        basic_mode = self.check_basicos.isChecked()

        worker = LayerGeneratorWorker(queries, self.layers, basic_mode)
        worker.signals.progress.connect(self.update_progress)
        worker.signals.finished.connect(self.on_layers_generated)
        worker.signals.error.connect(self.on_error)
        worker.signals.current_layer.connect(self.update_current_layer_label)  # Connect the new signal

        self.threadpool.start(worker)

    def update_progress(self, progress):
        self.progress_bar.setValue(progress)

    def update_current_layer_label(self, layer_name):
        self.current_layer_label.setText(f"Generando Capa: {layer_name}")

    def on_layers_generated(self):
        # self.tools.messages('aGrae GIS','Capas Generadas Correctamente',3,alert=True)
        self.current_layer_label.setText('Capas Generadas Correctamente')
        for layer in self.layers:
            QgsProject.instance().addMapLayer(self.layers[layer])

        if self.check_basicos.isChecked():
            aGraeComposerTools(self.layers,self.idcampania,self.idexplotacion).generateComposer(self.combo_basemap.currentText(),basic=True)
        else:
            aGraeComposerTools(self.layers,self.idcampania,self.idexplotacion).generateComposer(self.combo_basemap.currentText())
        # print(self.layers)

        # self.btn_generar.setEnabled(True)
        # self.accept()

    def on_error(self, error):
        self.tools.messages('aGrae GIS',f'Error: {error}',2,alert=True)
        QgsMessageLog.logMessage(f'Error: {error}', 'aGrae GIS', Qgis.Critical)
        self.btn_generar.setEnabled(True)
        self.progress_bar.setValue(0)
