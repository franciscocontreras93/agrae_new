from ast import main
import hashlib

from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QCheckBox, QButtonGroup, QPushButton, QGridLayout, QGroupBox, QWidget, QHBoxLayout, QLabel, QComboBox, QProgressBar, QSpinBox, QFileDialog
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QRunnable, QThreadPool, QObject
from qgis.core import QgsProject, QgsMessageLog, Qgis,QgsVectorLayer
from qgis.gui import QgsCollapsibleGroupBox
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
    cancelled = pyqtSignal()


class LayerGeneratorWorker(QRunnable):
    """
    Worker thread for generating layers.
    """

    def __init__(self, queries, layers_dict):
        super().__init__()
        self.queries = queries
        self.tools = aGraeTools()
        self.layers_dict = layers_dict
        self.signals = WorkerSignals()
        self.cancel_requested = False

    def cancel(self):
        self.cancel_requested = True

    def run(self):
        """
        Your code goes in this function.
        """
        try:
            total_queries = len(self.queries)
            current_query = 0

            for q in reversed(self.queries):
                if self.cancel_requested:
                    self.signals.cancelled.emit()
                    return

                current_query += 1
                self.signals.progress.emit(int((current_query / total_queries) * 100))
                self.signals.current_layer.emit('{}/{} {} '.format(current_query, total_queries,q))  # Emit the current layer name

                if 'Textura' in q:
                    layer = self.tools.getDataBaseLayer(self.queries[q], q, 'ceap_textura')
                elif 'Infiltracion' in q:
                    layer = self.tools.getDataBaseLayer(self.queries[q], q, 'ceap_infiltracion')
                elif 'Intraparcelaria' in q:
                    layer = self.tools.getDataBaseLayer(self.queries[q], q, q, debug=False)
                else:
                    layer = self.tools.getDataBaseLayer(self.queries[q], q, q)

                if layer.isValid():
                    layer.setCustomProperty(
                        'agrae/report_query_hash',
                        hashlib.sha256(
                            self.queries[q].encode('utf-8')
                        ).hexdigest()
                    )
                    self.layers_dict[q] = layer
                    # QgsProject.instance().addMapLayer(layer)

            if self.cancel_requested:
                self.signals.cancelled.emit()
            else:
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
        self.automatic_export = False
        self.output_directory = None
        self.cancel_requested = False
        self.layer_worker = None

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
        self.combo_basemap.addItems([
            name
            for name in self.tools.getBasemapsDict()
            if name != 'Parcelas Catastro'
        ])
        self.combo_basemap.addItem('Sin mapa base')
        self.check_catastro = QCheckBox("Superponer parcelas de Catastro")

        combo_layout = QHBoxLayout()
        combo_layout.addWidget(label_basemap)
        combo_layout.addWidget(self.combo_basemap)
        combo_layout.addWidget(self.check_catastro)

        # Advanced report export options
        advanced_group = QgsCollapsibleGroupBox("Opciones avanzadas")
        advanced_group.setCollapsed(True)
        advanced_group.setLayout(QGridLayout())

        self.spin_export_dpi = QSpinBox()
        self.spin_export_dpi.setRange(72, 600)
        self.spin_export_dpi.setValue(150)
        self.spin_export_dpi.setSuffix(" DPI")
        self.check_txt = QCheckBox("Generar archivo TXT")
        self.check_txt.setChecked(True)

        advanced_group.layout().addWidget(
            QLabel("Resolución de exportación:"),
            0,
            0
        )
        advanced_group.layout().addWidget(self.spin_export_dpi, 0, 1)
        advanced_group.layout().addWidget(self.check_txt, 1, 0, 1, 2)

        # Create progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
         # Add a label to show the current layer
        self.current_layer_label = QLabel("Generando Capa: ")

        # Create buttons
        self.btn_generar_manual = QPushButton(
            "Generar manualmente (abrir compositor)"
        )
        self.btn_generar_automatico = QPushButton(
            "Generar automáticamente (PDF por lote)"
        )
        self.btn_detener = QPushButton("Detener proceso")
        self.btn_detener.setEnabled(False)
        self.cancel_button = QPushButton("Cancel")
        self.btn_generar_manual.clicked.connect(
            lambda: self.on_generate_clicked(False)
        )
        self.btn_generar_automatico.clicked.connect(
            lambda: self.on_generate_clicked(True)
        )
        self.btn_detener.clicked.connect(self.stop_automatic_process)
        self.cancel_button.clicked.connect(self.reject)

        # Create a layout for buttons
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.btn_generar_manual)
        button_layout.addWidget(self.btn_generar_automatico)
        button_layout.addWidget(self.btn_detener)
        button_layout.addWidget(self.cancel_button)

        # Create a main layout and add the checkboxes and buttons
        main_layout = QVBoxLayout()
        main_layout.addWidget(groupbox_checks_tipos)
        main_layout.addWidget(group_parametros)
        main_layout.addLayout(combo_layout)
        main_layout.addWidget(advanced_group)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.current_layer_label)  # Add the label to the layout
        main_layout.addLayout(button_layout)
        main_layout.setSpacing(30)
        self.setLayout(main_layout)

    def on_generate_clicked(self, automatic_export):
        self.automatic_export = automatic_export
        self.output_directory = None
        self.cancel_requested = False

        self.btn_generar_manual.setEnabled(False)
        self.btn_generar_automatico.setEnabled(False)
        self.btn_detener.setEnabled(automatic_export)
        self.cancel_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.generateLayers()

    def stop_automatic_process(self):
        self.cancel_requested = True
        self.btn_detener.setEnabled(False)
        self.current_layer_label.setText(
            "Deteniendo el proceso al finalizar la operación actual..."
        )

        if self.layer_worker is not None:
            self.layer_worker.cancel()

        QApplication.processEvents()

    def on_generation_cancelled(self):
        self.layer_worker = None
        self.current_layer_label.setText("Proceso automático detenido")
        self.btn_generar_manual.setEnabled(True)
        self.btn_generar_automatico.setEnabled(True)
        self.btn_detener.setEnabled(False)
        self.cancel_button.setEnabled(True)

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
                          n_inc as incremento, st_asText(geom) as geom
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

        # --- 4) Reutilizar capas en memoria que correspondan a la consulta ---
        if self.check_basicos.isChecked():
            selected_names = [
                'Ambientes',
                'Segmentos',
                'Fert Variable Intraparcelaria',
                'Fert Variable Parcelaria',
                'Ceap36 Textura',
                'Ceap36 Infiltracion',
                'Ceap90 Textura',
                'Ceap90 Infiltracion'
            ]
            selected_queries = {
                name: queries[name]
                for name in selected_names
            }
        else:
            selected_queries = queries

        pending_queries = {}
        reused_count = 0

        for name, query in selected_queries.items():
            query_hash = hashlib.sha256(
                query.encode('utf-8')
            ).hexdigest()
            reusable_layer = next(
                (
                    layer
                    for layer in QgsProject.instance().mapLayersByName(name)
                    if (
                        layer.isValid()
                        and layer.providerType() == 'memory'
                        and layer.customProperty(
                            'agrae/report_query_hash',
                            ''
                        ) == query_hash
                    )
                ),
                None
            )

            if reusable_layer is not None:
                self.layers[name] = reusable_layer
                reused_count += 1
            else:
                pending_queries[name] = query

        if not pending_queries:
            self.progress_bar.setValue(100)
            self.current_layer_label.setText(
                f"Capas reutilizadas: {reused_count}/{len(selected_queries)}"
            )
            self.on_layers_generated()
            return

        if reused_count:
            self.current_layer_label.setText(
                f"Capas reutilizadas: {reused_count}. "
                f"Generando {len(pending_queries)} restantes..."
            )

        # --- 5) Generar únicamente las capas pendientes ---
        worker = LayerGeneratorWorker(
            pending_queries,
            self.layers
        )
        self.layer_worker = worker
        worker.signals.progress.connect(self.update_progress)
        worker.signals.finished.connect(self.on_layers_generated)
        worker.signals.error.connect(self.on_error)
        worker.signals.current_layer.connect(self.update_current_layer_label)
        worker.signals.cancelled.connect(self.on_generation_cancelled)

        self.threadpool.start(worker)

    def update_progress(self, progress):
        self.progress_bar.setValue(progress)

    def update_current_layer_label(self, layer_name):
        self.current_layer_label.setText(f"Generando Capa: {layer_name}")

    def update_report_progress(
        self,
        current,
        total,
        report_name,
        completed=False
    ):
        if total <= 0 or current <= 0:
            progress = 0
        elif completed:
            progress = int((current / total) * 100)
        else:
            progress = int(((current - 1) / total) * 100)

        self.progress_bar.setValue(progress)

        if current <= 0:
            self.current_layer_label.setText(
                "Preparando generación de informes..."
            )
        elif completed and current == total:
            self.current_layer_label.setText(
                f"Informes generados: {current}/{total}"
            )
        else:
            self.current_layer_label.setText(
                f"Generando informe {current}/{total}: {report_name}"
            )

        QApplication.processEvents()

    def on_layers_generated(self):
        self.layer_worker = None

        if self.cancel_requested:
            self.on_generation_cancelled()
            return

        # self.tools.messages('aGrae GIS','Capas Generadas Correctamente',3,alert=True)
        self.current_layer_label.setText('Capas Generadas Correctamente')
        for layer in self.layers:
            QgsProject.instance().addMapLayer(self.layers[layer])

        if self.automatic_export:
            self.output_directory = QFileDialog.getExistingDirectory(
                self,
                "Seleccionar carpeta para los informes"
            )
            if not self.output_directory:
                self.current_layer_label.setText(
                    'Generación automática cancelada'
                )
                self.btn_generar_manual.setEnabled(True)
                self.btn_generar_automatico.setEnabled(True)
                self.btn_detener.setEnabled(False)
                self.cancel_button.setEnabled(True)
                return

        if self.check_basicos.isChecked():
            aGraeComposerTools(
                self.layers,
                self.idcampania,
                self.idexplotacion
            ).generateComposer(
                self.combo_basemap.currentText(),
                basic=True,
                catastro=self.check_catastro.isChecked(),
                automatic_export=self.automatic_export,
                export_dpi=self.spin_export_dpi.value(),
                output_directory=self.output_directory,
                progress_callback=self.update_report_progress,
                generate_txt=self.check_txt.isChecked(),
                cancel_callback=lambda: self.cancel_requested
            )
        else:
            aGraeComposerTools(
                self.layers,
                self.idcampania,
                self.idexplotacion
            ).generateComposer(
                self.combo_basemap.currentText(),
                materia_organica=self.check_preescripcion_materia_organica.isChecked(),
                catastro=self.check_catastro.isChecked(),
                automatic_export=self.automatic_export,
                export_dpi=self.spin_export_dpi.value(),
                output_directory=self.output_directory,
                progress_callback=self.update_report_progress,
                generate_txt=self.check_txt.isChecked(),
                cancel_callback=lambda: self.cancel_requested
            )

        self.btn_generar_manual.setEnabled(True)
        self.btn_generar_automatico.setEnabled(True)
        self.btn_detener.setEnabled(False)
        self.cancel_button.setEnabled(True)

    def on_error(self, error):
        self.layer_worker = None
        self.tools.messages('aGrae GIS',f'Error: {error}',2,alert=True)
        QgsMessageLog.logMessage(f'Error: {error}', 'aGrae GIS', Qgis.Critical)
        self.btn_generar_manual.setEnabled(True)
        self.btn_generar_automatico.setEnabled(True)
        self.btn_detener.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.progress_bar.setValue(0)
