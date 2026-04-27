from ast import main
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QCheckBox, QButtonGroup, QPushButton, QGridLayout, QGroupBox, QWidget, QHBoxLayout, QLabel, QComboBox, QProgressBar
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QRunnable, QThreadPool, QObject
from qgis.core import QgsProject, QgsMessageLog, Qgis,QgsVectorLayer
from ..tools.composerTools import aGraeComposerTools
from ..tools import aGraeTools, aGraeSQLTools
from ..gui import agraeGUI
from ..gui.components import CustomComboBox, CultivosComboBox



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
        self.check_preescripcion_materia_organica = QCheckBox("Incluir Materia Organica y Relacion C/N")
         # Set default checked state
        self.check_preescripcion.setChecked(True)
        

        #Create a button group
        self.button_group = QButtonGroup()

        # Add the checkboxes to the button group
        self.button_group.addButton(self.check_basicos)
        self.button_group.addButton(self.check_preescripcion)
        self.button_group.addButton(self.check_preescripcion_materia_organica)
        # Set exclusive mode (only one can be checked at a time)
        self.button_group.setExclusive(True)

        # Create a horizontal layout for the checkboxes
        checkbox_layout = QHBoxLayout()
        checkbox_layout = QHBoxLayout()
        for i, checkbox in enumerate(
                (self.check_basicos,
                self.check_preescripcion,
                self.check_preescripcion_materia_organica),
                start=1):
            self.button_group.addButton(checkbox, i)  # el grupo solo controla el estado
            checkbox_layout.addWidget(checkbox)       # aquí agregas el widget real a la UI
      


        # Create a widget to hold the checkbox layout
        checkbox_widget = QWidget()
        checkbox_widget.setLayout(checkbox_layout)
        # Create  GROUPBOX 
        groupbox_checks_tipos = QGroupBox("Selecciona el tipo de Reporte a Generar")
        groupbox_checks_tipos.setLayout(QHBoxLayout())
        groupbox_checks_tipos.layout().addWidget(checkbox_widget)



        group_parametros = QGroupBox("Parámetros de Generación")
        group_parametros.setLayout(QGridLayout())
        self.check_seleccionados = QCheckBox("Solo Lotes Seleccionados")
        self.combo_cultivos = CultivosComboBox(
            endpoint=f'/gis/cultivos/data_combo/?idcampania={self.idcampania}&idexplotacion={self.idexplotacion}',
            auto_enable_on_load=True, 
            allow_all=True,
            multi_select=True)
        # self.combo_cultivos.all_text = 'Todos los Cultivos'
        # group_parametros.layout().addWidget(QLabel("Cultivo:"))
        group_parametros.layout().addWidget(self.check_seleccionados,0,0,1,2)
        group_parametros.layout().addWidget(QLabel("Cultivo:"),0,1)
        group_parametros.layout().addWidget(self.combo_cultivos,1,1)


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
        main_layout.addWidget(groupbox_checks_tipos)
        main_layout.addWidget(group_parametros)
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
        """
        Genera el diccionario de queries para crear las capas,
        aplicando filtros opcionales por cultivos seleccionados
        e iddata de los lotes seleccionados.
        """

        # --- 1) Resolver lista de idcultivo desde el combo (multi o single) ---
        # En el CultivosComboBox multi:
        #   - get_selected_ids() -> [] si solo está "Todos los cultivos..." o nada
        #   - [3,5,7] si hay cultivos seleccionados
        try:
            cultivo_ids = self.combo_cultivos.get_selected_ids()
        except Exception:
            cultivo_ids = []

        if cultivo_ids:
            # p.ej. [3, 5, 7] => ARRAY[3,5,7]
            cultivo_literal = "ARRAY[{}]".format(
                ",".join(str(int(cid)) for cid in cultivo_ids)
            )

            self.layers['Atlas'].setSubsetString('idcultivo in ({})'.format(
                        ','.join(str(int(i)) for i in cultivo_ids)
                    ))
        else:
            # sin selección real de cultivos (o solo "Todos...") -> sin filtro por cultivo
            cultivo_literal = "NULL"

        # --- 2) Resolver lista de iddata a partir de los lotes seleccionados ---
        # Esto ya te estaba funcionando para "Solo Lotes Seleccionados"
        
        if self.check_seleccionados.isChecked():
            atlas_layer = self.layers.get('Atlas')
            if atlas_layer is not None:
                iddatas = [
                    f['id']
                    for f in atlas_layer.getSelectedFeatures()
                    if 'id' in f.fields().names()
                ]
                if iddatas:
                    # Coincide con: {}::int[] AS iddata_list en los .sql
                    # Ejemplo resultante: ARRAY[10,11,25]
                    iddata_literal = 'ARRAY[{}]'.format(
                        ','.join(str(int(i)) for i in iddatas)
                    )


                    self.layers['Atlas'].setSubsetString('iddata in ({})'.format(
                        ','.join(str(int(i)) for i in iddatas)
                    ))


        else:
            iddata_literal = 'NULL'
        # --- 3) Armar queries usando la firma actual de los .sql ---
        # IMPORTANTE: asumo que tus .sql tienen:
        #   WITH params AS (
        #       SELECT
        #           {}::int   AS idcampania,
        #           {}::int   AS idexplotacion,
        #           {}::int[] AS idcultivo,
        #           {}::int[] AS iddata_list
        #   ),
        # y que en uf_aportes/segmentos hay un último {} para inyectar el SELECT final.

        queries = {
            # AMBIENTES (sin SELECT final extra)
            'Ambientes': aGraeSQLTools().getSql('ambientes_layers_query.sql').format(
                self.idcampania,
                self.idexplotacion,
                cultivo_literal,
                iddata_literal
            ),

            # SEGMENTOS + ANALÍTICA
            'Segmentos': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(
                self.idcampania,
                self.idexplotacion,
                cultivo_literal,
                iddata_literal,
                '''select distinct idlote,nombre as lote,codigo as codigo_muestra,
                          segmento,ceap,st_asText(geom) as geom
                   from segm_analitica;'''
            ),
            'Nitrogeno': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(
                self.idcampania,
                self.idexplotacion,
                cultivo_literal,
                iddata_literal,
                '''select distinct idlote,nombre as lote,codigo as codigo_muestra,
                          n as valor,no3,nh4,lower(n_tipo) as tipo,
                          n_inc as incremento, densidad, st_asText(geom) as geom
                   from segm_analitica;'''
            ),
            'Fosforo': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(
                self.idcampania,
                self.idexplotacion,
                cultivo_literal,
                iddata_literal,
                '''select distinct idlote,nombre as lote,codigo as codigo_muestra,
                          p as valor,lower(p_tipo) as tipo,
                          p_inc as incremento,st_asText(geom) as geom
                   from segm_analitica;'''
            ),
            'Potasio': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(
                self.idcampania,
                self.idexplotacion,
                cultivo_literal,
                iddata_literal,
                '''select distinct idlote,nombre as lote,codigo as codigo_muestra,
                          k as valor,lower(k_tipo) as tipo,
                          k_inc as incremento,st_asText(geom) as geom
                   from segm_analitica;'''
            ),
            'PH': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(
                self.idcampania,
                self.idexplotacion,
                cultivo_literal,
                iddata_literal,
                '''select distinct idlote,nombre as lote,codigo as codigo_muestra,
                          ph as valor,lower(ph_tipo) as tipo,
                          st_asText(geom) as geom
                   from segm_analitica;'''
            ),
            'Conductividad Electrica': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(
                self.idcampania,
                self.idexplotacion,
                cultivo_literal,
                iddata_literal,
                '''select distinct idlote,nombre as lote,codigo as codigo_muestra,
                          ce/100 as ce ,st_asText(geom) as geom
                   from segm_analitica;'''
            ),
            'Calcio': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(
                self.idcampania,
                self.idexplotacion,
                cultivo_literal,
                iddata_literal,
                '''select distinct idlote,nombre as lote,codigo as codigo_muestra,
                          ca as valor,lower(ca_tipo) as tipo,
                          st_asText(geom) as geom
                   from segm_analitica;'''
            ),
            'Magnesio': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(
                self.idcampania,
                self.idexplotacion,
                cultivo_literal,
                iddata_literal,
                '''select distinct idlote,nombre as lote,codigo as codigo_muestra,
                          mg as valor,lower(mg_tipo) as tipo,
                          st_asText(geom) as geom
                   from segm_analitica;'''
            ),
            'Sodio': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(
                self.idcampania,
                self.idexplotacion,
                cultivo_literal,
                iddata_literal,
                '''select distinct idlote,nombre as lote,codigo as codigo_muestra,
                          na as valor,lower(na_tipo) as tipo,
                          st_asText(geom) as geom
                   from segm_analitica;'''
            ),
            'Azufre': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(
                self.idcampania,
                self.idexplotacion,
                cultivo_literal,
                iddata_literal,
                '''select distinct idlote,nombre as lote,codigo as codigo_muestra,
                          s as valor,st_asText(geom) as geom
                   from segm_analitica;'''
            ),
            'CIC': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(
                self.idcampania,
                self.idexplotacion,
                cultivo_literal,
                iddata_literal,
                '''
                select distinct idlote,nombre as lote,codigo as codigo_muestra,
                       (case when segmento = 1 then 'Rojo'
                             when segmento = 2 then 'Verde'
                             when segmento = 3 then 'Azul' end) as "SEGMENTO",
                       round(cic::numeric,1)::double precision as "CIC", 
                       round(round(ca::numeric,1) / (ca + mg + k + na)::numeric * 100,1)::double precision || '%' as "CA",
                       round(round(mg::numeric,1) / (ca + mg + k + na)::numeric * 100,1)::double precision || '%' as "MG",
                       round(round(k::numeric,1) / (ca + mg + k + na)::numeric * 100,1)::double precision || '%' as "K",
                       round(round(na::numeric,1) / (ca + mg + k + na)::numeric * 100,1)::double precision || '%' as "NA",
                       st_asText(st_union(geom)) as geom 
                from segm_analitica
                group by idlote,nombre,codigo,segmento,cic,ca,mg,k,na;'''
            ),
            'Hierro': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(
                self.idcampania,
                self.idexplotacion,
                cultivo_literal,
                iddata_literal,
                '''select distinct idlote,nombre as lote,codigo as codigo_muestra,
                          fe,st_asText(geom) as geom
                   from segm_analitica;'''
            ),
            'Manganeso': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(
                self.idcampania,
                self.idexplotacion,
                cultivo_literal,
                iddata_literal,
                '''select distinct idlote,nombre as lote,codigo as codigo_muestra,
                          mn as valor,st_asText(geom) as geom
                   from segm_analitica;'''
            ),
            'Aluminio': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(
                self.idcampania,
                self.idexplotacion,
                cultivo_literal,
                iddata_literal,
                '''select distinct idlote,nombre as lote,codigo as codigo_muestra,
                          al,st_asText(geom) as geom
                   from segm_analitica;'''
            ),
            'Boro': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(
                self.idcampania,
                self.idexplotacion,
                cultivo_literal,
                iddata_literal,
                '''select distinct idlote,nombre as lote,codigo as codigo_muestra,
                          b,st_asText(geom) as geom
                   from segm_analitica;'''
            ),
            'Cinq': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(
                self.idcampania,
                self.idexplotacion,
                cultivo_literal,
                iddata_literal,
                '''select distinct idlote,nombre as lote,codigo as codigo_muestra,
                          zn ,st_asText(geom) as geom
                   from segm_analitica;'''
            ),
            'Cobre': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(
                self.idcampania,
                self.idexplotacion,
                cultivo_literal,
                iddata_literal,
                '''select distinct idlote,nombre as lote,codigo as codigo_muestra,
                          cu,st_asText(geom) as geom
                   from segm_analitica;'''
            ),
            'Materia Organica': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(
                self.idcampania,
                self.idexplotacion,
                cultivo_literal,
                iddata_literal,
                '''select distinct idlote,nombre as lote,codigo as codigo_muestra,
                          round((organi/100)::numeric,2)::double precision as organi,st_asText(geom) as geom
                   from segm_analitica;'''
            ),
            'Relacion CN': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(
                self.idcampania,
                self.idexplotacion,
                cultivo_literal,
                iddata_literal,
                '''select distinct idlote,nombre as lote,codigo as codigo_muestra,
                          rel_cn,st_asText(geom) as geom
                   from segm_analitica;'''
            ),

            # UF / APORTES
            'Fert Variable Intraparcelaria': aGraeSQLTools().getSql('uf_aportes_query.sql').format(
                self.idcampania,
                self.idexplotacion,
                cultivo_literal,
                iddata_literal,
                'select * from mapa_sig'
            ),
            'Fert Variable Parcelaria': aGraeSQLTools().getSql('uf_aportes_query.sql').format(
                self.idcampania,
                self.idexplotacion,
                cultivo_literal,
                iddata_literal,
                'select * from fert_parcelaria'
            ),

            # CEAP 36 / 90
            'Ceap36 Textura': aGraeSQLTools().getSql('ceap36_layers_query.sql').format(
                self.idcampania,
                self.idexplotacion,
                cultivo_literal,
                iddata_literal
            ),
            'Ceap36 Infiltracion': aGraeSQLTools().getSql('ceap36_layers_query.sql').format(
                self.idcampania,
                self.idexplotacion,
                cultivo_literal,
                iddata_literal
            ),
            'Ceap90 Textura': aGraeSQLTools().getSql('ceap90_layers_query.sql').format(
                self.idcampania,
                self.idexplotacion,
                cultivo_literal,
                iddata_literal
            ),
            'Ceap90 Infiltracion': aGraeSQLTools().getSql('ceap90_layers_query.sql').format(
                self.idcampania,
                self.idexplotacion,
                cultivo_literal,
                iddata_literal
            ),
        }

        # --- 4) Iniciar el worker en un hilo separado ---
        worker = LayerGeneratorWorker(queries, self.layers, self.check_basicos.isChecked())
        worker.signals.progress.connect(self.update_progress)
        worker.signals.finished.connect(self.on_layers_generated)
        worker.signals.error.connect(self.on_error)
        worker.signals.current_layer.connect(self.update_current_layer_label)

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
            aGraeComposerTools(self.layers,self.idcampania,self.idexplotacion).generateComposer(self.combo_basemap.currentText(),materia_organica=self.check_preescripcion_materia_organica.isChecked())
        # print(self.layers)

        # self.btn_generar.setEnabled(True)
        # self.accept()

    def on_error(self, error):
        self.tools.messages('aGrae GIS',f'Error: {error}',2,alert=True)
        QgsMessageLog.logMessage(f'Error: {error}', 'aGrae GIS', Qgis.Critical)
        self.btn_generar.setEnabled(True)
        self.progress_bar.setValue(0)
