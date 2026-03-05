import os

import psycopg2

from qgis.PyQt import QtWidgets #type: ignore
from qgis.PyQt.QtCore import pyqtSignal, Qt,QDate,QSize,QSettings #type: ignore
from qgis.PyQt.QtGui import QIcon,QColor #type: ignore

from qgis.core import * #type: ignore
from qgis.utils import iface #type: ignore
from qgis.gui import QgsMapToolIdentify,QgsMapMouseEvent, QgsHighlight, QgsCollapsibleGroupBox # type: ignore
from ..tools import aGraeTools
from ..tools.analisis_tools import aGraeResamplearMuestras
from ..tools.agrae_csv_tools import aGraeCSVTools
from ..tools.gee import NDVIProcessor, NDVIListDownloadWorker
from ..tools.agraeIdentifyTool import aGraeSelectTool
from ..tools.agraeCopiarAnaliticaSelectTool import aGraeCopyAnaliticaSelectTool
from ..tools.styling_tools import _apply_index_style, _index_presets

from ..db import agraeDataBaseDriver
from ..sql import aGraeSQLTools
from ..gui import agraeGUI
from ..gui.components import CampaniasComboBox, ExplotacionesComboBox, CultivosComboBox, RegimenComboBox, InfoCardNumLotes

from ..dialogs import aGraeDialogs, AgricultorSelectDialog

from .explotacion_dialogs import CopyExplotacionDialog, CreateExplotacionDialog, UpdateExplotacionDialog, GestionExplotacionDialog,GestionarExplotacionesDialog
from .campania_dialogs import CloneCampaniaDialog, CreateCampaniaDialog, UpdateCampaniaDialog
from .lotes_dialog import LoteWeatherDialog
from .analitica_dialogs import agraeAnaliticaDialog
from .gestion_personas import GestionPersonasDialog
from .gestion_distribuidor import GestionDistribuidorDialog
from .gestion_agricultor import GestionAgricultorDialog
from .datos_base_dialog import GestionDatosBaseDialog, CrearLotesDialog
from .composer_dialog import agraeComposer
from .new_composer_dialog import new_Composer 
from .cultivos_dialog import GestionarCultivosDialog
from .parametros_dialog import GestionarParametrosDialog
from .plots_dialog import agraePlotsDialog
from .monitor_dialogs import MonitorRendimientosDialog
from .gee_dialog import aGraeGEEDialog
from .reportes_dialog import ReportesDialog
from .asignar_cultivos_dialog import AsignarCultivosDialog
from .siembra_variable_dialog import SiembraVariableDialog
from .copiar_analitica_dialog import CopyAnaliticaWizardDialog
from .contratos_dialog import ContratosDialog


class agraeToolsDockwidget(QtWidgets.QDockWidget):
    def __init__(self,
                 layer:QgsVectorLayer, # type: ignore
                 parent=None):
        super(agraeToolsDockwidget,self).__init__(parent)
        self.instance = QgsProject.instance()
        
        # UI elements will be created in UIComponents
        self._create_ui_elements() # Helper to declare elements

        # self.setupUi(self) # This will be replaced by programmatic UI creation
        self.setWindowTitle('aGrae Tools')
        self.layer = layer
        self.conn = agraeDataBaseDriver().connection()
        self.tools = aGraeTools()
        self.UIComponents()
        # --- Wire backend-driven combo signals ---
        try:
            self.combo_campania.items_loaded.connect(self._on_campaigns_ready)
            self.combo_campania.current_value_changed.connect(self._on_campaign_changed)
        except Exception:
            pass
        try:
            self.combo_explotacion.items_loaded.connect(self._maybe_load_lotes)
            self.combo_explotacion.current_value_changed.connect(self._maybe_load_lotes)
        except Exception:
            pass

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
        

        # self.combo_campania.refresh()  # backend-driven combo loads itself
        # self.getCultivosData()
        self.getRegimenData()

        
        iface.addDockWidget(Qt.RightDockWidgetArea,self)
        self.atlasLayers = dict()
        # iface.mapCanvas().contextMenuAboutToShow.connect(self.populateContextMenu)
        pass

    def _create_ui_elements(self):
        """Helper method to declare UI elements."""
        self.toolBox = QtWidgets.QToolBox()

        # Page 1: Información de Lote
        self.page_info_lote = QtWidgets.QWidget()
        self.combo_campania = CampaniasComboBox()

        self.tool_camp = QtWidgets.QToolButton()

        self.combo_explotacion = ExplotacionesComboBox()
        self.combo_explotacion.bind_to_campaigns(self.combo_campania)
        self.combo_explotacion.currentIndexChanged.connect(self.getLotesExplotacionLayer)

        self.tool_exp = QtWidgets.QToolButton()

        # self.card_num_lotes = InfoCardNumLotes()
        # self.card_num_lotes.bind_to_explotacion(self.combo_campania, self.combo_explotacion)

        self.label_info = QtWidgets.QLabel("")
        self.label_info_muestreo = QtWidgets.QLabel("")
        self.label_num_lotes = QtWidgets.QLabel("-")  # Nuevo QLabel para número de lotes
        self.label_area_lotes = QtWidgets.QLabel("- ha")  # Nuevo QLabel para área de lotes
        self.area_lote = QtWidgets.QDoubleSpinBox()
        self.area_lote.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.area_lote.setAlignment(Qt.AlignRight)  # Nuevo QDoubleSpinBox para área del lote seleccionado
        self.area_lote.setDecimals(2)
        self.area_lote.setSuffix(" ha")
        self.area_lote.setMaximum(10000)  # Máximo 10,000 ha
        self.area_lote.setReadOnly(True)  # Deshabilitado para que sea solo de lectura
        self.area_lote.setMinimum(0)
        self.line_nombre = QtWidgets.QLineEdit()
        self.line_nombre.setEnabled(False)
        self.label_2 = QtWidgets.QLabel("Cultivo:")
        self.combo_cultivo = CultivosComboBox()
        self.combo_cultivo.setPlaceholderText('Seleccionar cultivo')
        self.label_4 = QtWidgets.QLabel("Régimen:")
        self.combo_regimen = RegimenComboBox()
        self.combo_regimen.setPlaceholderText('Seleccionar régimen')
        self.label_7 = QtWidgets.QLabel("Producción Esperada (Kg/Ha):")
        self.line_produccion = QtWidgets.QSpinBox()
        self.line_produccion.setEnabled(False)
        self.line_produccion.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.line_produccion.setSuffix(" Kg/Ha")
        self.line_produccion.setMaximum(500000) # Max 200 Ton/Ha
        # self.check_siembra = QtWidgets.QCheckBox("Fecha Siembra")
        # self.check_siembra.setEnabled(False)
        # self.date_siembra = QtWidgets.QDateEdit()
        # self.date_siembra.setEnabled(False)
        # self.date_siembra.setCalendarPopup(True)
        # self.check_cosecha = QtWidgets.QCheckBox("Fecha Cosecha")
        # self.check_cosecha.setEnabled(False)
        # self.date_cosecha = QtWidgets.QDateEdit()
        # self.date_cosecha.setEnabled(False)
        # self.date_cosecha.setCalendarPopup(True)
        self.label_status = QtWidgets.QLabel("Estado: Desconocido")
        self.tool_lote = QtWidgets.QToolButton()

        self.line_price_lote = QtWidgets.QSpinBox()
        self.line_price_lote.setEnabled(False)
        self.line_price_lote.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.line_price_lote.setSuffix(" €")
        self.line_price_lote.setMaximum(100000) # Max 100000 €

        # Page 2: Fertilización y Cultivos
        self.page_fertilizacion_cultivos = QtWidgets.QWidget() # For the second tab
        self.tab_widget_fertilizacion = QtWidgets.QTabWidget() # TabWidget for page 2
        self.combo_aplicacion = QtWidgets.QComboBox()
        self.combo_aplicacion.addItem("1ra Aplicación")
        self.combo_aplicacion.addItem("2da Aplicación")
        self.combo_aplicacion.addItem("3ra Aplicación")
        self.combo_aplicacion.addItem("4ta Aplicación")
        self.date_aplicacion = QtWidgets.QDateEdit()
        self.date_aplicacion.setEnabled(False)
        self.line_formula = QtWidgets.QLineEdit()
        self.line_formula.setEnabled(False)
        self.line_precio = QtWidgets.QSpinBox()
        self.line_precio.setEnabled(False)
        self.line_precio.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.line_precio.setSuffix(" €")
        self.line_precio.setMaximum(1000) # Max 10000 €
        self.combo_ajuste = QtWidgets.QComboBox()
        self.combo_ajuste.setEnabled(False)
        self.combo_ajuste.addItem("Seleccionar...")
        self.combo_ajuste.addItem("N")
        self.combo_ajuste.addItem("P")
        self.combo_ajuste.addItem("K")
        self.combo_ajuste.addItem("PK")
        self.label_status_fertilizacion = QtWidgets.QLabel("Estado Fertilización: -")
        self.tool_fert = QtWidgets.QToolButton()

        self.combo_cultivo_2 = CultivosComboBox(editable=False, filter_enabled=True, auto_enable_on_load=True)
        self.combo_regimen_2 = RegimenComboBox(editable=False, filter_enabled=True, auto_enable_on_load=True)

        self.combo_cultivo_2.bind_filters(self.combo_campania, self.combo_explotacion, enabled=True)
        self.combo_regimen_2.bind_filters(self.combo_campania, self.combo_explotacion, self.combo_cultivo_2, enabled=True)

        self.line_produccion_2 = QtWidgets.QSpinBox()
        self.line_produccion_2.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.line_produccion_2.setSuffix(" Kg/Ha")
        self.line_produccion_2.setMaximum(500000) # Max 200 Ton/Ha
        self.date_siembra_2 = QtWidgets.QDateEdit()
        self.date_siembra_2.setDate(QDate.currentDate())

        # self.date_siembra_2.setMinimumDate(self.combo_campania.get_current_campaign_qdates()[0])
        # self.date_siembra_2.setMaximumDate(self.combo_campania.get_current_campaign_qdates()[1])

        self.date_siembra_2.setCalendarPopup(True)
        self.date_siembra_2.setEnabled(True) # TODO ACTIVAR CUANDO SE INTEGRE LA DATA COMPLETA A LA API DE AGRAE.

        self.date_cosecha_2 = QtWidgets.QDateEdit()
        self.date_cosecha_2.setCalendarPopup(True)
        self.date_cosecha_2.setEnabled(False) # TODO ACTIVAR CUANDO SE INTEGRE LA DATA COMPLETA A LA API DE AGRAE.


        self.btn_save_cultivo_prod_exp = QtWidgets.QPushButton("Guardar")
        self.btn_save_cultivo_prod_exp.setEnabled(True)

        self.btn_save_cultivo_date_exp = QtWidgets.QPushButton("Guardar")


        # Page 3: Google Earth Engine
        self.page_gee_module = QtWidgets.QWidget() # For the third tab
        self.page_gee_layout = QtWidgets.QVBoxLayout(self.page_gee_module)



        self.combo_cultivo_3 = QtWidgets.QComboBox()
        self.combo_cultivo_3.setEditable(True)
        self.combo_cultivo_3.setInsertPolicy(QtWidgets.QComboBox.NoInsert)



        self.analisis_gee_group = QtWidgets.QGroupBox("Tipo de Analisis:")
        self.analisis_gee_layout = QtWidgets.QHBoxLayout(self.analisis_gee_group)
        self.page_gee_layout.setContentsMargins(10, 10, 10, 10)  # Add margins to the layout
        self.ndvi_radio = QtWidgets.QRadioButton("NDVI")
        self.ndre_radio = QtWidgets.QRadioButton("NDRE")
        self.savi_radio = QtWidgets.QRadioButton("SAVI")
        # self.natural_color_radio = QtWidgets.QRadioButton("Color Natural") #TODO

        # self.savi_radio.setEnabled(False) 
        # self.natural_color_radio.setEnabled(False)


        self.analisis_gee_layout.addWidget(self.ndvi_radio)
        self.analisis_gee_layout.addWidget(self.ndre_radio)
        self.analisis_gee_layout.addWidget(self.savi_radio)
        # self.analisis_gee_layout.addWidget(self.natural_color_radio)
        self.ndvi_radio.setChecked(True)
        # self.analisis_gee_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins for a cleaner look
        self.analisis_gee_layout.setSpacing(10)  # Add spacing between buttons


        

        self.analisis_gee_date_range_group = QtWidgets.QGroupBox("Rango de Fechas:")
        self.analisis_gee_date_range_group.setToolTip('Rango de fechas para el análisis, si se desactiva, se usara la ultima imagen disponible según parametros.')
        # self.analisis_gee_date_range_group.setCheckable(True)
        # self.analisis_gee_date_range_group.setChecked(True)
        self.analisis_gee_date_range_layout = QtWidgets.QGridLayout(self.analisis_gee_date_range_group)

        self.date_edit_desde = QtWidgets.QDateEdit()
        self.date_edit_hasta = QtWidgets.QDateEdit()
        self.date_edit_desde.setCalendarPopup(True)
        self.date_edit_hasta.setCalendarPopup(True)
        self.date_edit_desde.setDate(QDate.currentDate().addMonths(-2))
        self.date_edit_hasta.setDate(QDate.currentDate())
        self.date_edit_desde.setMaximumDate(QDate.currentDate())
        self.date_edit_hasta.setMaximumDate(QDate.currentDate())

        self.date_edit_desde.dateChanged.connect(self._validate_date_range)
        self.date_edit_hasta.dateChanged.connect(self._validate_date_range)


        self.analisis_gee_date_range_layout.addWidget(QtWidgets.QLabel("Desde:"), 0, 0)
        self.analisis_gee_date_range_layout.addWidget(self.date_edit_desde, 1, 0)
        self.analisis_gee_date_range_layout.addWidget(QtWidgets.QLabel("Hasta:"), 0, 1)
        self.analisis_gee_date_range_layout.addWidget(self.date_edit_hasta, 1, 1)


        self.status_gee_label = QtWidgets.QLabel("")
        self.status_gee_label.setVisible(False)

        self.analisis_gee_progressbar = QtWidgets.QProgressBar()
        self.analisis_gee_progressbar.setRange(0, 100)
        self.analisis_gee_progressbar.setValue(0)
        self.analisis_gee_progressbar.setTextVisible(True)

        self.analisis_gee_ejecutar_button = QtWidgets.QPushButton("Ejecutar")
        self.analisis_gee_ejecutar_button.clicked.connect(self.run_ndvi_processor)

        # self.page_gee_layout.addWidget(self.filtrar_cultivo_group)
        self.page_gee_layout.addWidget(self.analisis_gee_group)
        self.page_gee_layout.addWidget(self.analisis_gee_date_range_group)
        self.page_gee_layout.addWidget(self.status_gee_label)
        self.page_gee_layout.addWidget(self.analisis_gee_progressbar)
        self.page_gee_layout.addWidget(self.analisis_gee_ejecutar_button)
        self.page_gee_layout.addStretch()  # Add stretch to push content to the top

        # Herramientas Generales (fuera del ToolBox)
        self.tool_agrae = QtWidgets.QToolButton()
        self.tool_exp_2 = QtWidgets.QToolButton() # Este es el de herramientas de explotación, no el que está al lado del combo
        self.tool_lab = QtWidgets.QToolButton()
        self.tool_data = QtWidgets.QToolButton()


    def UIComponents(self):
        self.setWindowIcon(agraeGUI().getIcon('main'))

        # Main widget for the DockWidget
        main_widget = QtWidgets.QWidget()
        self.setWidget(main_widget)
        dock_layout = QtWidgets.QVBoxLayout(main_widget)

        # Group: Selección de Campaña y Explotación (Fuera del ToolBox)
        group_camp_exp = QgsCollapsibleGroupBox("Selección de Campaña y Explotación")
        group_camp_exp.setCollapsed(False)
        layout_camp_exp = QtWidgets.QGridLayout(group_camp_exp)
        layout_camp_exp.addWidget(QtWidgets.QLabel("Campaña:"), 0, 0)
        layout_camp_exp.addWidget(self.combo_campania, 0, 1)
        layout_camp_exp.addWidget(self.tool_camp, 0, 2)
        layout_camp_exp.addWidget(QtWidgets.QLabel("Explotación:"), 1, 0)
        layout_camp_exp.addWidget(self.combo_explotacion, 1, 1)
        layout_camp_exp.addWidget(self.tool_exp, 1, 2)
      
        # Añadir nuevos labels para información de lotes
        dock_layout.addWidget(group_camp_exp)

        info_group_box = QgsCollapsibleGroupBox("Datos de la Explotación.")
        info_group_box.setCollapsed(True)
        layout_info_group = QtWidgets.QGridLayout(info_group_box)
        layout_info_group.addWidget(self.label_info,0,0)
        layout_info_group.addWidget(self.label_info_muestreo,1,0)
        # layout_info_group.addWidget(self.card_num_lotes,0,0)

        # Group: Herramientas Generales (Fuera del ToolBox)
        tools_group_box = QgsCollapsibleGroupBox("Herramientas")
        tools_group_box.setCollapsed(True)
        layout_tools_group = QtWidgets.QGridLayout(tools_group_box) # Usar QHBoxLayout para que estén en línea

        self.tool_agrae.setText("aGrae General")
        self.tool_exp_2.setText("Explotación") 
        self.tool_lab.setText("Laboratorio")
        self.tool_data.setText("Gestión de Datos")

        layout_tools_group.addWidget(QtWidgets.QLabel("aGrae"),0,0)
        layout_tools_group.addWidget(QtWidgets.QLabel("Explotación"),0,1)
        layout_tools_group.addWidget(QtWidgets.QLabel("Laboratorio"),0,2)
        layout_tools_group.addWidget(QtWidgets.QLabel("Gestión de Datos"),0,3)
        layout_tools_group.addWidget(self.tool_agrae,1,0)
        layout_tools_group.addWidget(self.tool_exp_2,1,1) 
        layout_tools_group.addWidget(self.tool_lab,1,2)
        layout_tools_group.addWidget(self.tool_data,1,3)
        dock_layout.addWidget(tools_group_box)
        dock_layout.addWidget(info_group_box)


        # Create ToolBox and add it to the main dock layout
        self.toolBox = QtWidgets.QToolBox()
        dock_layout.addWidget(self.toolBox)

        # # --- Page 0: Informacion de Explotacion
        # self.page_info_explotacion = QtWidgets.QWidget()
        # page_info_explotacion_layout = QtWidgets.QVBoxLayout(self.page_info_explotacion)
        # page_info_explotacion_layout.addWidget(info_group_box)

        # self.toolBox.addItem(self.page_info_explotacion, "Información de Explotación")



        # --- Page 1: Información de Lote ---
        self.page_info_lote = QtWidgets.QWidget()
        page_info_lote_layout = QtWidgets.QVBoxLayout(self.page_info_lote)

        # Group: Información del Lote
        group_info_lote_details = QtWidgets.QGroupBox("Información del Lote")
        layout_info_lote_details = QtWidgets.QFormLayout(group_info_lote_details) 

        # Nombre Lote and tool_lote side-by-side
        h_layout_nombre_lote = QtWidgets.QHBoxLayout()
        h_layout_nombre_lote.addWidget(self.line_nombre)
        h_layout_nombre_lote.addWidget(self.tool_lote)
        layout_info_lote_details.addRow(QtWidgets.QLabel("Nombre Lote:"), h_layout_nombre_lote)
        layout_info_lote_details.addRow(QtWidgets.QLabel("Área Lote Seleccionado:"), self.area_lote)
        layout_info_lote_details.addRow(self.label_2, self.combo_cultivo)
        layout_info_lote_details.addRow(self.label_4, self.combo_regimen)
        layout_info_lote_details.addRow(self.label_7, self.line_produccion)
        
        # h_layout_siembra = QtWidgets.QHBoxLayout()
        # h_layout_siembra.addWidget(self.check_siembra)
        # h_layout_siembra.addWidget(self.date_siembra)
        # layout_info_lote_details.addRow(h_layout_siembra)

        # h_layout_cosecha = QtWidgets.QHBoxLayout()
        # h_layout_cosecha.addWidget(self.check_cosecha)
        # h_layout_cosecha.addWidget(self.date_cosecha)
        # layout_info_lote_details.addRow(h_layout_cosecha)

        layout_info_lote_details.addRow(self.label_status)
        page_info_lote_layout.addWidget(group_info_lote_details)

        group_info_lote_billing = QtWidgets.QGroupBox("Información de Facturación y Económicos del Lote")
        layout_info_lote_billing = QtWidgets.QFormLayout(group_info_lote_billing)

        layout_info_lote_billing.addRow(QtWidgets.QLabel("Precio de Facturación:"), self.line_price_lote)
        page_info_lote_layout.addWidget(group_info_lote_billing)




        page_info_lote_layout.addStretch() 
        self.toolBox.addItem(self.page_info_lote, "Información de Lote")
        self.toolBox.setCurrentIndex(0)
        self.toolBox.setItemIcon(0,agraeGUI().getIcon('info'))

        # --- Page 2: Fertilización y Cultivos Explotación ---
        self.page_fertilizacion_cultivos = QtWidgets.QWidget()
        page_fertilizacion_layout = QtWidgets.QVBoxLayout(self.page_fertilizacion_cultivos)
         #Group: Control de Cultivo
        group_control_cultivo = QtWidgets.QGroupBox("Cultivos asociados a la Exp. y Camp. Seleccionados.")
        layout_control_cultivo = QtWidgets.QFormLayout(group_control_cultivo) # Layout for the tab content
        layout_control_cultivo.addRow(QtWidgets.QLabel("Seleccionar cultivo: "),self.combo_cultivo_2)

        page_fertilizacion_layout.addWidget(group_control_cultivo) # Add the groupbox to the tab's layout

        # Create TabWidget for Fertilización and Actualizar Cultivos
        self.tab_widget_fertilizacion = QtWidgets.QTabWidget()
        page_fertilizacion_layout.addWidget(self.tab_widget_fertilizacion)

       


        # Group: Fertilización de Campaña
        widget_fert_camp = QtWidgets.QWidget() # Widget to hold the groupbox for the tab
        group_fert_camp = QtWidgets.QGroupBox("Fertilización de Campaña (Datos Generales)")
        layout_fert_camp = QtWidgets.QFormLayout(widget_fert_camp) # Layout for the tab content
        layout_fert_camp.addWidget(group_fert_camp) # Add the groupbox to the tab's layout
        # Populate the groupbox (original QFormLayout for group_fert_camp)
        form_layout_in_group_fert = QtWidgets.QFormLayout(group_fert_camp)

        # Aplicación and tool_fert side-by-side
        h_layout_aplicacion_fert = QtWidgets.QHBoxLayout()
        h_layout_aplicacion_fert.addWidget(self.combo_aplicacion)
        h_layout_aplicacion_fert.addWidget(self.tool_fert)
        form_layout_in_group_fert.addRow(QtWidgets.QLabel("Aplicación:"), h_layout_aplicacion_fert)

        form_layout_in_group_fert.addRow(QtWidgets.QLabel("Fecha Aplicación:"), self.date_aplicacion)
        form_layout_in_group_fert.addRow(QtWidgets.QLabel("Fórmula (NPK):"), self.line_formula)
        form_layout_in_group_fert.addRow(QtWidgets.QLabel("Precio (€/Tn):"), self.line_precio)
        form_layout_in_group_fert.addRow(QtWidgets.QLabel("Ajuste:"), self.combo_ajuste)
        form_layout_in_group_fert.addRow(self.label_status_fertilizacion)
        self.tab_widget_fertilizacion.addTab(widget_fert_camp, "Fertilización Campaña")

        # Group: Actualizar Cultivos de la Explotación
        widget_act_cult_exp = QtWidgets.QWidget() # Widget to hold the groupbox for the tab
        group_act_cult_exp = QtWidgets.QGroupBox("Actualizar Cultivos de la Explotación")
        layout_act_cult_exp = QtWidgets.QFormLayout(widget_act_cult_exp) # Layout for the tab content
        layout_act_cult_exp.addWidget(group_act_cult_exp) # Add the groupbox to the tab's layout
        # Populate the groupbox (original QFormLayout for group_act_cult_exp)
        form_layout_in_group_act_cult = QtWidgets.QFormLayout(group_act_cult_exp)
        # form_layout_in_group_act_cult.addRow(QtWidgets.QLabel("Cultivo:"), self.combo_cultivo_2)
        form_layout_in_group_act_cult.addRow(QtWidgets.QLabel("Régimen:"), self.combo_regimen_2)
        form_layout_in_group_act_cult.addRow(QtWidgets.QLabel("Producción Esperada (Kg/Ha):"), self.line_produccion_2)
        # form_layout_in_group_act_cult.addRow(QtWidgets.QLabel("Fecha Siembra:"), self.date_siembra_2)
        form_layout_in_group_act_cult.addRow(self.btn_save_cultivo_prod_exp)
        self.tab_widget_fertilizacion.addTab(widget_act_cult_exp, "Actualizar Produccion")


        # Gruop: Actualziar Fecha Siembra y Cosecha de Lotes
        widget_act_cult_dates_exp = QtWidgets.QWidget() # Widget to hold the groupbox for the tab
        group_act_cult_dates_exp = QtWidgets.QGroupBox("Actualizar Fechas de Siembra")
        layout_act_cult_dates_exp = QtWidgets.QFormLayout(widget_act_cult_dates_exp) # Layout for the tab content
        layout_act_cult_dates_exp.addWidget(group_act_cult_dates_exp) # Add the groupbox to the tab's layout
        # Populate the groupbox (original QFormLayout for group_act_cult_exp)
        form_layout_in_group_act_cult_dates = QtWidgets.QFormLayout(group_act_cult_dates_exp)
        # form_layout_in_group_act_cult.addRow(QtWidgets.QLabel("Cultivo:"), self.combo_cultivo_2)
        form_layout_in_group_act_cult_dates.addRow(QtWidgets.QLabel("Fecha Siembra:"), self.date_siembra_2)
        # form_layout_in_group_act_cult_dates.addRow(QtWidgets.QLabel("Fecha Cosecha:"), self.date_cosecha_2)
        form_layout_in_group_act_cult_dates.addRow(self.btn_save_cultivo_date_exp)
        self.tab_widget_fertilizacion.addTab(widget_act_cult_dates_exp, "Actualizar Fechas Siembra | Cosecha")
        page_fertilizacion_layout.addStretch() 
        self.toolBox.addItem(self.page_fertilizacion_cultivos, "Datos de Fertilización y Cultivo")
        self.toolBox.setItemIcon(1,agraeGUI().getIcon('tractor')) # Icono para la segunda pestaña


        # FACTURACION
        self.page_facturacion = QtWidgets.QWidget()
        page_facturacion_layout = QtWidgets.QVBoxLayout()
        self.page_facturacion.setLayout(page_facturacion_layout)

        # Gestion de Contratos
        gb_contratos = QtWidgets.QGroupBox("Gestión de Contratos")
        gb_contratos_layout = QtWidgets.QFormLayout(gb_contratos)
        gb_contratos_layout.setLabelAlignment(Qt.AlignLeft)
        gb_contratos_layout.setFormAlignment(Qt.AlignTop)
        gb_contratos_layout.setHorizontalSpacing(12)
        gb_contratos_layout.setVerticalSpacing(8)
        gb_contratos_layout.setContentsMargins(10, 12, 10, 10)
        btn_create_contrato = QtWidgets.QPushButton("Gestionar Contrato")
        btn_create_contrato.setMinimumHeight(28)
        btn_create_contrato.clicked.connect(self.gestionarContratosDialog)

        row = QtWidgets.QWidget()
        row_lay = QtWidgets.QHBoxLayout(row)
        row_lay.setContentsMargins(0, 0, 0, 0)
        row_lay.setSpacing(6)
        row_lay.addWidget(btn_create_contrato)
        row_lay.addStretch(1)

        gb_contratos_layout.addRow(QtWidgets.QLabel('Contratos:'), row)

        page_facturacion_layout.addWidget(gb_contratos)
        page_facturacion_layout.addStretch(1)

        



        # if True:
        #     self.toolBox.addItem(self.page_facturacion, "Datos de Facturación y Económicos Generales")
        #     self.toolBox.setItemIcon(2,agraeGUI().getIcon('explotacion'))


        self.toolBox.addItem(self.page_gee_module, "Modulo de Google Earth Engine")


        # Set initial properties and connections
        # self.date_siembra.dateChanged.connect(self.dateSiembraChanged)
        # self.date_cosecha.dateChanged.connect(self.dateCosechaChanged)

        
        
        self.toolBox.setItemIcon(2,agraeGUI().getIcon('satelite')) # Icono para la segunda pestaña
        self.toolBox.currentChanged.connect(self.infoLote)
        
        # for c in [self.combo_cultivo]:
        #     c.setEditable(True)
        #     c.setInsertPolicy(QtWidgets.QComboBox.NoInsert)
        #     c.completer().setCompletionMode(QtWidgets.QCompleter.PopupCompletion)

        # self.combo_campania.currentIndexChanged.connect(lambda: self.combo_explotacion.refresh()))
        
        self.combo_cultivo_2.currentIndexChanged.connect(self.clearAplicacion)
        
        self.initTools()
        
        # self.check_siembra.stateChanged.connect(lambda e: self.check_status(e,self.fechaSiembra,self.date_siembra))
        # self.check_cosecha.stateChanged.connect(lambda e: self.check_status(e,self.fechaCosecha,self.date_cosecha))

        self.combo_aplicacion.currentIndexChanged.connect(self.getCultivosCampaniaData)
        self.btn_save_cultivo_prod_exp.clicked.connect(self.actualizarProduccionCultivo)
        self.btn_save_cultivo_date_exp.clicked.connect(self.actualizarDataCultivoFechas)

        # Set object names for stylesheets or direct access if needed (optional but good practice)
        self.toolBox.setObjectName("toolBox")
        self.combo_campania.setObjectName("combo_campania")
        # ... and so on for other widgets if you need to style them via objectName

    def initTools(self):

        # TOOLBUTTONS 
        # TOOL_AGRAE
        self.AsignarLotesExplotacion = QtWidgets.QAction(agraeGUI().getIcon('selection'),'Asignar Lotes Seleccionados a Explotacion',self)
        self.AsignarLotesExplotacion.triggered.connect(self.asignarLotesExp)
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
        self.ActualizarDatosFromCSV = QtWidgets.QAction(agraeGUI().getIcon('csv'),'Actualizar Informacion de Cultivos desde CSV',self)
        self.ActualizarDatosFromCSV.triggered.connect(self.actualizarDatosCultivosCSV)
        
        actions_agrae = [self.IndentifyLoteAction,self.CargarLotes,self.CrearCE,self.CrearSegmentos,self.CrearAmbientes,self.ActualizarDatosFromCSV,self.AsignarLotesExplotacion]
        self.tools.settingsToolsButtons(self.tool_agrae,actions_agrae,icon=agraeGUI().getIcon('tools'),setMainIcon=True)

        
        # TOOL_EXP_2
       
        self.AsignarAgricultorLotes = QtWidgets.QAction(agraeGUI().getIcon('select-farmer'),'Asignar Agricultor a Lotes Seleccionados',self)
        self.AsignarAgricultorLotes.triggered.connect(self.asignarAgricultorLotesDialog) 

        self.AsignarCultivosLotes = QtWidgets.QAction(agraeGUI().getIcon('select-cultivo'),'Asignar Cultivo a Lotes Seleccionados',self)
        self.AsignarCultivosLotes.triggered.connect(self.asignarCultivosLotesDialog)
        self.CargarCapasExplotacion = QtWidgets.QAction(agraeGUI().getIcon('add-layer'),'Generar capas de Explotacion',self)
        self.CargarCapasExplotacion.triggered.connect(self.generarCapasExplotacion)
        self.GenerarReporteFertilizacion = QtWidgets.QAction(agraeGUI().getIcon('printer'),'Generar Reporte de Preescripcion',self)
        self.GenerarReporteFertilizacion.triggered.connect(self.generateComposerDialog)
        self.GenerarMapaSig = QtWidgets.QAction(agraeGUI().getIcon('add-layer'),'Generar Mapa SIG',self)
        self.GenerarMapaSig.triggered.connect(self.getMapaSig)
        self.GenerarMapaRindes = QtWidgets.QAction(agraeGUI().getIcon('add-layer'),'Generar Mapa de Rendimiento',self)
        self.GenerarMapaRindes.triggered.connect(self.getMapaRindes)
        self.GenerarIntegralTermica = QtWidgets.QAction(agraeGUI().getIcon('weather'),'Generar Mapa de Integral Termica',self)
        self.GenerarIntegralTermica.triggered.connect(self.getIntegralTermicaLayer)

        self.GenerarUnidadesFertilizacion = QtWidgets.QAction(agraeGUI().getIcon('tractor'),'Exportar SHP de Preescripcion',self)
        self.GenerarUnidadesFertilizacion.triggered.connect(self.exportarUFS)
        self.GenerarResumenFertilizacion = QtWidgets.QAction(agraeGUI().getIcon('csv'),'Generar Resumen de Preescripcion',self)
        self.GenerarResumenFertilizacion.setToolTip('Exportar resumen de prescripción de fertilización a archivo CSV.\nPermite generar reporte de todos los lotes, o solo los lotes seleccionados.')
        self.GenerarResumenFertilizacion.triggered.connect(self.exportarResumen)
        self.GenerarAmbientes = QtWidgets.QAction(agraeGUI().getIcon('satelite'),'Generar Mapas de Ambientes',self)
        self.GenerarAmbientes.triggered.connect(self.geeDialog)
        # SIEMBRA VARIABLE
        self.GenerarMapaSiembra = QtWidgets.QAction(agraeGUI().getIcon('seed-icon'),'Generar Mapa de Siembra',self)
        self.GenerarMapaSiembra.triggered.connect(self.MapaSiembraDialog)

        self.MonitorDeRendimiento = QtWidgets.QAction(agraeGUI().getIcon('rindes'),'Monitor de Rendimiento',self)
        self.MonitorDeRendimiento.triggered.connect(self.monitorRendimientoDialog)
        actions_exp = [
            self.AsignarCultivosLotes,
            self.AsignarAgricultorLotes,
            self.CargarCapasExplotacion,
            self.GenerarReporteFertilizacion,
            self.GenerarMapaSig,
            self.GenerarIntegralTermica,
            self.GenerarUnidadesFertilizacion,
            self.GenerarResumenFertilizacion,
            self.GenerarAmbientes,
            self.MonitorDeRendimiento,
            self.GenerarMapaSiembra]
        # actions_exp = [self.AsignarLotesExplotacion,self.CargarCapasExplotacion,self.GenerarReporteFertilizacion,self.GenerarUnidadesFertilizacion,self.GenerarResumenFertilizacion]
        self.tools.settingsToolsButtons(self.tool_exp_2,actions_exp,icon=agraeGUI().getIcon('explotacion'),setMainIcon=True)

        # TOOL_LAB
        self.GestionarMuestras = QtWidgets.QAction(agraeGUI().getIcon('list-check'),'Gestionar Muestras y Analiticas',self)
        self.GestionarMuestras.triggered.connect(aGraeDialogs.gestionarMuestrasDialog)
        self.GenerarPuntosMuestreo = QtWidgets.QAction(agraeGUI().getIcon('pois'),'Generar Puntos de Muestreo.',self)
        self.GenerarPuntosMuestreo.triggered.connect(aGraeDialogs.muestreoDialog)
        self.CrearArchivoAnalisis = QtWidgets.QAction(agraeGUI().getIcon('csv'),'Generar Archivo de Laboratorio',self)
        self.CrearArchivoAnalisis.triggered.connect(self.crearFormatoAnalitica)
        self.ImportarArchivoAnalisis = QtWidgets.QAction(agraeGUI().getIcon('import'),'Cargar Archivo de Laboratorio',self)
        self.ImportarArchivoAnalisis.triggered.connect(self.cargarAnalitica)
        self.DerivarDatosAnalisis = QtWidgets.QAction(agraeGUI().getIcon('csv'),'Derivar datos de Analitica',self)
        self.DerivarDatosAnalisis.triggered.connect(self.DerivarAnalitica)
        self.CopiarDatosAnaliticos = QtWidgets.QAction(agraeGUI().getIcon('clone'),'Copiar Datos de Analiticas',self)
        self.CopiarDatosAnaliticos.triggered.connect(self.copiarDatosAnaliticos)

        actions_lab = [self.GestionarMuestras,self.GenerarPuntosMuestreo,self.CrearArchivoAnalisis,self.ImportarArchivoAnalisis,self.DerivarDatosAnalisis,self.CopiarDatosAnaliticos]
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

        actions_data = [self.GestionarPersonas,self.GestionarExplotaciones,self.GestionarAgricultores,self.GestionarDistribuidores,self.GestionarCultivos] # DELETE FROM MASTER
        # actions_data = [self.GestionarExplotaciones,self.GestionarPersonas,self.GestionarAgricultores,self.GestionarDistribuidores,self.GestionarCultivos,self.GestionarParametros]
        
        self.tools.settingsToolsButtons(self.tool_data,actions_data,icon=agraeGUI().getIcon('list-check'),setMainIcon=True)


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
        self.ReloadCampaniaAction.triggered.connect(self.combo_campania.refresh)

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
        self.EditarLoteAction.triggered.connect(lambda: self.tools.enableElements(self.EditarLoteAction,[self.line_nombre,self.line_produccion,self.combo_cultivo,self.combo_regimen,self.ActualizarLoteAction,self.EliminarLoteAction]))
        actions_lote = [self.EditarLoteAction,self.ActualizarLoteAction,self.ClimaLoteAction,self.GenerarPanelesDialogAction,self.EliminarLoteAction,]
        self.tools.settingsToolsButtons(self.tool_lote, actions_lote)

        # TOOL_FERT
        self.EditarFertilizacionAction = QtWidgets.QAction(agraeGUI().getIcon('edit'),'Editar Datos',self)
        self.EditarFertilizacionAction.setCheckable(True)
        self.EditarFertilizacionAction.setToolTip('Editar Datos de Fertilizacion')
        self.ActualizarFertilizacionAction = QtWidgets.QAction(agraeGUI().getIcon('save'),'Guardar Datos',self)
        self.ActualizarFertilizacionAction.setEnabled(False)
        self.ActualizarFertilizacionAction.setToolTip('Guardar Datos de Fertilización')
        self.EditarFertilizacionAction.triggered.connect(lambda: self.tools.enableElements(self.EditarFertilizacionAction,[self.line_formula,self.line_precio,self.combo_ajuste,self.date_aplicacion,self.ActualizarFertilizacionAction]))
        self.ActualizarFertilizacionAction.triggered.connect(self.saveDataCampania)
        self.settingsToolsButtons(self.tool_fert,[self.EditarFertilizacionAction,self.ActualizarFertilizacionAction])
        # self.settingsToolsButtons(self.tool_fert)
        self.tool_fert_menu = self.tool_fert.menu()

    # DIALOGS
    def campaniaCreateDialog(self):
        dlg = CreateCampaniaDialog()
        dlg.campCreated.connect(self.combo_campania.refresh)
        dlg.exec()

    def campaniaUpdateDialog(self):
        dlg = UpdateCampaniaDialog(self.combo_campania.currentData())
        dlg.campUpdated.connect(self.combo_campania.refresh)
        dlg.exec()
        # print(self.combo_campania.currentData())

    def campaniaCloneDialog(self):
        dlg = CloneCampaniaDialog()
        dlg.campCloned.connect(self.combo_campania.refresh)
        dlg.exec()

    def explotacionCreateDialog(self):
        dlg = CreateExplotacionDialog(self.combo_campania.currentData())
        # dlg.expCreated.connect(lambda e: self.tools.messages('aGrae Tools','Explotacion {} creada correctamente'.format(e),3))
        dlg.loteCreated.connect(self.afterLotesCreated)
        dlg.exec()
    
    def explotacionUpdateDialog(self):
        dlg = UpdateExplotacionDialog(self.combo_explotacion.currentData(),self.combo_explotacion.currentText())
        dlg.expUpdated.connect(lambda: self.combo_explotacion.refresh())
        dlg.exec()
    
    def explotacionCopyDialog(self):
        dlg = CopyExplotacionDialog(self.combo_explotacion.currentData(),self.combo_campania.currentData(),self.combo_explotacion.currentText())
        dlg.expCopied.connect(self.combo_explotacion.refresh)
        dlg.exec()

    def loteAnliticDialog(self):
        cultivo = self.combo_cultivo.currentText()
        idcultivo = self.combo_cultivo.currentData()
        produccion = str(self.line_produccion.value())

        
        with agraeDataBaseDriver().connection().cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
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


        dlg = new_Composer(self.combo_campania.currentData(),self.combo_explotacion.currentData(),self.layer)
        dlg.exec()
    
    def copiarDatosAnaliticos(self):
        canvas = iface.mapCanvas()
        layer = self.layer
        self.copy_tool = aGraeCopyAnaliticaSelectTool(canvas, layer, self.combo_campania.currentData(), self.combo_explotacion.currentData(), id_field='idlote')
        self.copy_tool.execute_endpoint.connect(lambda x,y: self.tools.copiar_analitica(self.combo_campania.currentData(),self.combo_explotacion.currentData(),x,y))

        canvas.setMapTool(self.copy_tool)

    def run_ndvi_processor(self):

        radio_map = {
            self.ndvi_radio: 1,
            self.ndre_radio: 2,
            self.savi_radio: 3,
        }

        index = next((value for radio, value in radio_map.items() if radio.isChecked()), None)

        # idcampania = self.combo_campania.currentData()
        # idexplotacion = self.combo_explotacion.currentData()
        idlotes = [f['idlote'] for f in self.layer.selectedFeatures() ]
        if self.layer.selectedFeatureCount() == 0:
            idlotes = [f['idlote'] for f in self.layer.getFeatures() ]
        else:
            idlotes = [f['idlote'] for f in self.layer.selectedFeatures() ]
        fecha_inicio = self.date_edit_desde.date().toString("yyyy-MM-dd")
        fecha_fin = self.date_edit_hasta.date().toString("yyyy-MM-dd")

        if index is None:
            return

        self._selected_index = index
        

        payload = {
            "idlotes": idlotes,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "index": index,
            "buffer":10
        }

        processor = NDVIProcessor("/gee/index_by_idlotes")

        self._ndvi_worker = NDVIListDownloadWorker(
            processor=processor,
            payload=payload,
            max_workers=4,
            parent=self,
        )

        # progressbar: indeterminado al inicio
        self.analisis_gee_progressbar.setVisible(True)
        self.analisis_gee_progressbar.setRange(0, 0)
        self.analisis_gee_progressbar.setValue(0)

        self.status_gee_label.setVisible(True)

        # señales
        def _on_init(total: int):
            self.analisis_gee_progressbar.setRange(0, max(total, 1))
            self.analisis_gee_progressbar.setValue(0)

        self._ndvi_worker.progressInit.connect(_on_init)
        self._ndvi_worker.status.connect(self.status_gee_label.setText)
        self._ndvi_worker.progress.connect(self.analisis_gee_progressbar.setValue)
        self._ndvi_worker.orderReady.connect(self._on_ndvi_order_ready)
        self._ndvi_worker.itemReady.connect(self._on_ndvi_item_ready)
        self._ndvi_worker.error.connect(lambda m: print(m))

        self._ndvi_worker.start()

    def _add_index_layer(self, fecha: str, path: str):
        # 1) presets: como la función pide self, pásale self
        presets = _index_presets()  

        # 2) usa el índice entero como clave (1/2/3)
        idx = getattr(self, "_selected_index", 1)
        preset = presets.get(idx, presets[1])  

        layer_name = f"{preset.name}_{fecha}"
        rlayer = QgsRasterLayer(path, layer_name)

        if not rlayer.isValid():
            try:
                os.remove(path)
            except Exception:
                pass
            return

        _apply_index_style(rlayer, preset, band=1)
        QgsProject.instance().addMapLayer(rlayer)

    def _on_ndvi_order_ready(self, fechas: list):
        self._ndvi_expected_order = fechas          # lista ordenada old->new
        self._ndvi_downloaded_paths = {}            # fecha -> path
        self._ndvi_next_idx = 0


    def _on_ndvi_item_ready(self, fecha: str, path: str):
        # Guardar lo que llegó
        if not hasattr(self, "_ndvi_downloaded_paths"):
            self._ndvi_downloaded_paths = {}
        self._ndvi_downloaded_paths[fecha] = path

        # Intentar cargar en orden
        self._flush_ndvi_layers_in_order()

    def _flush_ndvi_layers_in_order(self):
        if not getattr(self, "_ndvi_expected_order", None):
            return

        while self._ndvi_next_idx < len(self._ndvi_expected_order):
            fecha = self._ndvi_expected_order[self._ndvi_next_idx]
            path = self._ndvi_downloaded_paths.get(fecha)
            if not path:
                break  # esa fecha todavía no está descargada

            # aquí sí cargas capa y aplicas estilo
            self._add_index_layer(fecha, path)
            self._ndvi_next_idx += 1

        

    def geeDialog(self):
        dlg = aGraeGEEDialog()
        dlg.exec_()

    def asignarCultivosLotesDialog(self):

        if len(self.layer.selectedFeatures()) == 0:
            self.tools.messages('Asignar Cultivos','Seleccione al menos un lote para asignar los cultivos.',2)
            return
        
        iddata = [f['iddata'] for f in self.layer.selectedFeatures()]
        dlg = AsignarCultivosDialog(iddata,self.combo_campania.get_current_campaign_qdates())
        dlg.exec()
        pass

    def asignarAgricultorLotesDialog(self):
        if len(self.layer.selectedFeatures()) == 0:
            self.tools.messages('Asignar Agricultor','Seleccione al menos un lote para asignar el agricultor.',2)
            return
        idlote = [f['idlote'] for f in self.layer.selectedFeatures()]
        dlg = AgricultorSelectDialog(idexplotacion= self.combo_explotacion.get_current_explotacion_id(), idlotes=idlote)
        dlg.exec()

    def gestionarContratosDialog(self):
        dlg = ContratosDialog(idexplotacion=self.combo_explotacion.get_current_id())
        dlg.exec()
        pass
    
    def actualizarDatosCultivosCSV(self):
        file = self.tools.openFileDialog()
        aGraeCSVTools(file).updateCultivoDataFromCSV()


    def MapaSiembraDialog(self):
        dlg = SiembraVariableDialog(
            idcampania=self.combo_campania.currentData(),
            idexplotacion= self.combo_explotacion.currentData()
        )
        dlg.exec()
        

        

    def getIdCultivo(self,data):
        """[DEPRECATED]"""
        self.idCultivo = data
        

    def monitorRendimientoDialog(self):

        dlg = MonitorRendimientosDialog(
            idcampania=self.combo_campania.currentData(),
            idexplotacion= self.combo_explotacion.currentData()
        )
        dlg.exec()

    # FUCNTIONS
    def identify(self):
        self.identifyTool = aGraeSelectTool(self.layer)
        self.identifyTool.featureSelected.connect(self.fillDataLote)
        iface.mapCanvas().setMapTool(self.identifyTool)

    def copyrDatosAnaliticos(self):
        self.copyTool = agraeCopiarAnaliticaSelectTool(self.layer)
        # self.copyTool.featureSelected.connect(self.copiarDatosAnaliticosDialog)

    def getData(self,query_name:str,check:bool=False) -> list:
        with agraeDataBaseDriver().connection().cursor() as cursor:
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
        if i == 1: # This condition will likely not be met if there's only one active tab for "Fertilización"
            if hasattr(self, 'identifyTool') and self.identifyTool: # Check if identifyTool exists
                 iface.mapCanvas().setMapTool(self.identifyTool)
            else: # If not, create it
                self.identify() 
                iface.mapCanvas().setMapTool(self.identifyTool)


    def updateComboExp(self):
        sql = '''select distinct e.nombre , d.idexplotacion from campaign.data d
        join campaign.campanias c on c.id = d.idcampania 
        join agrae.explotacion e on e.idexplotacion = d.idexplotacion 
        where c.id = {}'''.format(self.combo_campania.currentData())

        sql_date_camp = 'select fecha_desde, fecha_hasta from campaign.campanias where id = {}'.format(self.combo_campania.currentData())
        # print(sql_date_camp)
        self.combo_explotacion.clear()
        with agraeDataBaseDriver().connection().cursor() as cursor:
            try:
                cursor.execute(sql)
                data = cursor.fetchall()
                if len(data) >= 1:
                    for e in data:
                        self.combo_explotacion.addItem(e[0],e[1])
            except:
                agraeDataBaseDriver().connection().rollback()

            try:
                cursor.execute(sql_date_camp)
                data = cursor.fetchone()
                # print(data[0])
                # self.date_siembra.setDate(self.currentDate)
                self.FechaDesde = data[0]
                self.FechaHasta = data[1]

                # self.date_siembra.setMinimumDate(self.FechaDesde)
                # self.date_siembra.setMaximumDate(self.FechaHasta)
                # self.date_cosecha.setMinimumDate(self.FechaDesde)
                # self.date_cosecha.setMaximumDate(self.FechaHasta)
                self.date_aplicacion.setMinimumDate(self.FechaDesde)
                self.date_aplicacion.setMaximumDate(self.FechaHasta)
                # print(data)



            except Exception as ex:
              agraeDataBaseDriver().connection().rollback()
              
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
            with agraeDataBaseDriver().connection() as conn:
                try:
                    cursor = conn.cursor()
                    for f in features:
                        sql = sql + '({},{},{}),\n'.format(campania,explotacion,f['id'])
                    query = base  + sql 
                    # print(query[:-2])

                    
                    cursor.execute(query[:-2])
                    conn.commit()

                except Exception as ex:
                    print(ex)
                    conn.rollback()

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
                with agraeDataBaseDriver().connection().cursor() as cursor:
                    cursor.execute(query[:-2])
                    self.conn.commit()

            except Exception as ex:
                print(ex)
                self.conn.rollback()

        else: 
            print('Debe seleccionar uno o mas lotes')

    
    def getExpInfo(self):
        # DATA GENERAL
        sql_general = f'''with data as (select * from campaign."data" where idcampania  = {self.combo_campania.currentData()} and idexplotacion = {self.combo_explotacion.currentData()}),  
lotes as (select distinct l.*,st_transform(st_buffer(st_transform(l.geom,8857),-0.5),4326) buffer from data d join agrae.lotes l using(idlote)),
segmentos as (select distinct l.idlote, st_union(s.geometria) as geom
	from lotes l join agrae.segmentos s on st_intersects(l.buffer,s.geometria) 
	where not st_isempty(st_intersection(l.buffer,s.geometria))
	group by l.idlote)
select 
	count(*) as lotes_totales, 
	round((st_area(st_transform(st_union(geom),25830))/10000)::numeric,2) area_ha_total, 
	coalesce((select distinct count(idlote) from segmentos),0) as lotes_mapeados,
	coalesce((select distinct round((st_area(st_transform(st_union(geom),25830))/10000)::numeric,2) from segmentos),0.0) as area_mapeada 
	from lotes'''
        
        #DATA MUESTREO
        sql_muestreo = f'''WITH data AS (
    SELECT *
    FROM campaign."data"
    WHERE idcampania = {self.combo_campania.currentData()}  
      AND idexplotacion = {self.combo_explotacion.currentData()}    
),
muestras AS (
    SELECT DISTINCT m.codigo, m.muestreado
    FROM data d
    JOIN field.muestras m USING (idcampania, idexplotacion, idlote)
    where m.tipo in (1,3,4)
),
muestras_procesado AS (
    SELECT
        m.codigo,
        m.muestreado,
        CASE
            WHEN a.cod IS NOT NULL THEN TRUE
            ELSE FALSE
        END AS procesado
    FROM
        muestras m
    LEFT JOIN
        analytic.analitica a ON m.codigo = a.cod
)
select
	COUNT(*) num_muestras,
    COUNT(CASE WHEN muestreado IS TRUE THEN 1 END) AS total_muestreadas,
    COUNT(CASE WHEN procesado IS TRUE THEN 1 END) AS total_procesadas
FROM
    muestras_procesado;'''
        tolerancia = 0.95
        
        with agraeDataBaseDriver().connection().cursor() as cursor:
            try:
                cursor.execute(sql_general)
                data_gen = cursor.fetchone()
                if data_gen:
                    num_lotes = data_gen[0]
                    area_ha = data_gen[1]
                    num_lotes_mapeados = data_gen[2]    
                    area_mapeada = data_gen[3]

                    color_mapeadas = "green" if num_lotes_mapeados >= num_lotes else "red"
                    color_area = "green" if area_mapeada/area_ha >= tolerancia else "red"
                    

                    self.label_info.setText(f"Lotes: <font color='blue'><b>{num_lotes}</b></font> | Área Exp: <font color='blue'><b>{area_ha} ha</b></font> | Lotes Mapeados: <font color='{color_mapeadas}'><b>{num_lotes_mapeados}</b></font> | Área Mapeada: <font color='{color_area}'><b>{area_mapeada} ha</b></font>")
                else:
                    self.label_info.setText("Lotes: <b>-</b> | Área: <b>- ha</b>")

                cursor.execute(sql_muestreo)
                data = cursor.fetchone()
                if data:
                    num_muestras_totales = data[0]
                    num_muestreadas = data[1]
                    num_procesadas = data[2]

                    color_muestreadas = "green" if num_muestreadas >= num_muestras_totales else "red"
                    color_procesadas = "green" if num_procesadas >= num_muestreadas else "red"

                    texto_muestreo = f"Muestras Totales: <b>{num_muestras_totales}</b> | <font color='{color_muestreadas}'>Muestreadas: <b>{num_muestreadas}</b></font> | <font color='{color_procesadas}'>Procesadas: <b>{num_procesadas}</b></font>"
                    self.label_info_muestreo.setText(texto_muestreo)
                else:
                    self.label_info_muestreo.setText("Muestras Totales: <b>-</b> | Muestreadas: <b>-</b> | Procesadas: <b>-</b>")
            except Exception as ex:
                print(ex)
                self.conn.rollback()


    def getLotesExplotacionLayer(self):
       

        sql = aGraeSQLTools().getSql('view_lotes.sql')

        try:
            # self.label_info.setText('Campaña: {} | Explotacion: {}'.format(self.combo_campania.currentData(),self.combo_explotacion.currentData()))
            self.getExpInfo()
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
        # self.layer.setSubsetString(reset)
        if self.combo_explotacion.currentData() != None:
            # exp = QgsExpression("\"idexplotacion\"={}".format(self.combo_explotacion.currentData()))
            # it = self.layer.getFeatures(QgsFeatureRequest(exp))
            # ids = [f.id() for f in it]
            # self.layer.selectByIds(ids)
            # self.layer.setSubsetString("\"idexplotacion\"={}".format(self.combo_explotacion.currentData()))
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
        
        with agraeDataBaseDriver().connection().cursor() as cursor: 
            try:
                cursor.execute(sql)
                data = cursor.fetchall()
                for e in data:
                    self.combo_cultivo_2.addItem(e[0],e[1])
                self.getCultivosCampaniaData(self.combo_cultivo_2.currentIndex())
            except Exception as ex:
              self.conn.rollback()
            #   print('{}'.format(ex))

    
    # -------- helpers for backend-driven combos --------
    def _apply_campaign_dates_from_combo(self):
        """
        Lee 'fecha_desde' y 'fecha_hasta' del item actual del CampaniasComboBox (si vienen en el payload)
        y ajusta las restricciones de los QDateEdit relevantes. Silencioso si no existen.
        """
        try:
            it = self.combo_campania.get_current_item() if hasattr(self.combo_campania, 'get_current_item') else None
            if not isinstance(it, dict):
                return
            fecha_desde = it.get('fecha_desde') or it.get('fecha_inicio')
            fecha_hasta = it.get('fecha_hasta') or it.get('fecha_fin')
            if not (fecha_desde and fecha_hasta):
                return
            fd = QDate.fromString(str(fecha_desde), 'yyyy-MM-dd')
            fh = QDate.fromString(str(fecha_hasta), 'yyyy-MM-dd')
            if not fd.isValid() or not fh.isValid():
                return
            # Guarda para lógica existente que use estos atributos
            self.FechaDesde = fd
            self.FechaHasta = fh
            # Aplica a los date edits si existen
            for de in (getattr(self, 'date_siembra', None), getattr(self, 'date_cosecha', None), getattr(self, 'date_aplicacion', None)):
                if de:
                    de.setMinimumDate(fd)
                    de.setMaximumDate(fh)
        except Exception:
            pass

    def _on_campaigns_ready(self, _items):
        """Primera carga de campañas lista: aplica fechas (si hay)."""
        self._apply_campaign_dates_from_combo()

    def _on_campaign_changed(self, _cid):
        """Cambio de campaña por el usuario: aplica fechas (si hay)."""
        self._apply_campaign_dates_from_combo()

    def _maybe_load_lotes(self, *_):
        """Cuando hay explotación válida, dispara la carga de lotes."""
        try:
            eid = self.combo_explotacion.currentData()
            if eid is None:
                return
            self.getLotesExplotacionLayer()
        except Exception:
            pass
    def getCampaniasData(self):
        """[DEPRECATED]"""

        self.combo_campania.refresh()
        self.getLotesExplotacionLayer()
            
            # except Exception as ex:
            #     self.conn.rollback()
            #     print(ex,'Error getCampaniasData')
                
    def getExplotacionData(self,idcampania):
        """[DEPRECATED]"""
        self.combo_explotacion.refresh()
        self.getLotesExplotacionLayer()
            
    def getCultivosData(self):
        """[DEPRECATED]"""
        with agraeDataBaseDriver().connection().cursor() as cursor:
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
        """[DEPRECATED]"""
        with agraeDataBaseDriver().connection().cursor() as cursor:
            try:
                cursor.execute('SELECT DISTINCT UPPER(nombre), id  FROM analytic.regimen ORDER BY id')
                data_reg = cursor.fetchall()
                self.conn.commit()
                for e in data_reg:
                    self.combo_regimen.addItem(e[0],e[1])
                    self.combo_regimen_2.addItem(e[0],e[1])
            except Exception as ex:
                self.conn.rollback()
                print(ex)

    def fillCombos(self):
        """[DEPRECATED]"""
        self.combo_campania.refresh()
        self.combo_explotacion.refresh()
        # self.combo_regimen_2.refresh()


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

        # self.date_siembra.setDate(self.FechaDesde)
        # self.date_cosecha.setDate(self.FechaHasta)

        self.toolBox.setCurrentIndex(0)

        self.idLote = feat['idlote']
        self.idData = feat['iddata']
        self.nombreLote = feat['lote']
        self.areaLoteSeleccionado = feat['area_ha']
        self.idCultivo = feat['idcultivo']
        self.idRegimen = feat['idregimen']
        self.prodEsperada = feat['prod_esperada']
        self.prodFinal = feat['prod_final']
        self.line_nombre.setText(self.nombreLote)
        self.area_lote.setValue(feat['area_ha'])
        


        self.checkData(isinstance(self.idCultivo,int),self.label_2,self.idCultivo,self.combo_cultivo)
        self.checkData(isinstance(self.idRegimen,int),self.label_4,self.idRegimen,self.combo_regimen)
        self.checkData(isinstance(self.prodEsperada,int) and self.prodEsperada > 0  ,self.label_7,self.prodEsperada,self.line_produccion)

        if isinstance(feat['fechasiembra'],QDate):
            # self.check_siembra.setChecked(True)
            # if self.EditarLoteAction.isChecked():
            #     self.date_siembra.setEnabled(True)
            # else:
            #     self.date_siembra.setEnabled(False)

            self.label_status.setText('Cultivando')
            self.label_status.setStyleSheet("QLabel { background-color : green; color : white; }")
            # self.fechaSiembra = feat['fechasiembra'].toString('yyyy-MM-dd')
            # self.date_siembra.setDate(feat['fechasiembra'])
        else:

            # self.check_siembra.setChecked(False)
            self.fechaSiembra = ''

        if isinstance(feat['fechacosecha'],QDate):
            # self.check_cosecha.setChecked(True)
            # # if self.EditarLoteAction.isChecked():
            # #     self.date_cosecha.setEnabled(True)
            # else:
            #     self.date_cosecha.setEnabled(False)
            self.fechaCosecha = feat['fechacosecha'].toString('yyyy-MM-dd')
            # self.date_cosecha.setDate(feat['fechacosecha'])
            self.label_status.setText('Lote Cosechado')
            self.label_status.setStyleSheet("QLabel { background-color : blue; color : white; }")
        else:
            # self.check_cosecha.setChecked(False)
            self.fechaCosecha = ''
  
        
    def updateLote(self):
        
        idcultivo = self.combo_cultivo.get_current_id()
        idregimen = self.combo_regimen.get_current_id()
        nombre = self.line_nombre.text()
        prod_esperada = self.line_produccion.value()
        # # prod_final = self.line_prod_final.value()
        
        json_payload = {
        "lote": {
            "nombre": str(nombre)
        },
        "data_campania": {
            "iddata": self.idData,
            "idcultivo": idcultivo,
            "idregimen": idregimen,
            "prod_esperada": prod_esperada,
            "fechasiembra": None,
            "fechacosecha": None
        }
        }

        # if self.check_siembra.isChecked():
        #     json_payload['data_campania']['fechasiembra'] = self.date_siembra.date().toString('yyyy-MM-dd')
        # if self.check_cosecha.isChecked():
        #     json_payload['data_campania']['fechacosecha'] = self.date_cosecha.date().toString('yyyy-MM-dd')

        # print(json_payload)

        self.tools.updateLoteInfo(json_payload)
        
                
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

            with agraeDataBaseDriver().connection().cursor() as cursor: 
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
                  with agraeDataBaseDriver().connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute(sql)
                       
                        conn.commit()
                        self.tools.messages('aGrae Tools','Datos de fertilizacion guardados correctamente',3,alert=True)

                except  Exception as ex:
                    conn.rollback()
                    QgsMessageLog.logMessage('{}'.format(ex), 'aGrae Tools', 2)
                    self.tools.messages('aGrae Tools','Ocurrio un error {}'.format(ex),2)
                    print(ex)
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
        # self.combo_campania.refresh()  # backend-driven combo loads itself

    def deleteExplotacion(self):
        question = 'Quieres eliminar la Explotacion {}?, esta acción eliminará\nsolo los datos asociados a la campaña seleccionada.'.format(self.combo_explotacion.currentText())
        sql = '''delete from campaign.data where idcampania = {} and idexplotacion = {}'''.format(self.combo_campania.currentData(),self.combo_explotacion.currentData())
        self.tools.deleteAction(question,sql)
        self.combo_explotacion.refresh()
        self.reloadLayer()

    def deleteLote(self):
        question = 'Quieres eliminar el lote {}?, esta acción eliminará\nsolo los datos asociados a la campaña.'.format(self.nombreLote)
        sql = '''delete from campaign.data where iddata = {}'''.format(self.idData)
        actions = [self.line_nombre,self.line_produccion,self.combo_cultivo,self.combo_regimen,self.ActualizarLoteAction,self.EliminarLoteAction]
        # actions = [self.line_nombre,self.line_produccion,self.combo_cultivo,self.combo_regimen,self.date_siembra,self.date_cosecha,self.ActualizarLoteAction,self.EliminarLoteAction]
        try:
            self.tools.deleteAction(question,sql,self.EditarLoteAction,actions)
            self.tools.messages('aGrae Tools','Se elimino el lote {} de la explotacion actual.'.format(self.nombreLote),3,duration=5)
        except Exception as ex:
            print(ex)
            self.tools.messages('aGrae Tools','No se pudo eliminar el lote'.format(self.nombreLote),2,alert=True)


    def crearFormatoAnalitica(self):
        # METODO PARA CREAR LOS FORMATOS DE REPORTES ANALITICOS EN ARCHIVOS .CSV
        exp = self.combo_explotacion.currentText().replace(' ','_')
        exp = exp.split('-')[1]
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
        name_exp = name_exp.split('-')[1]
        # sql_intra = '''select row_number() over () as id, explotacion,cultivo,lote,uf,uf_etiqueta,f_fondo,d_fondo,f_cob1,d_cob1,f_cob2,d_cob2,f_cob3,d_cob3,area_ha,st_asText(geom) as geom from fert_intraparcelaria'''
        sql_intra = '''select * from mapa_sig'''

        queries = {
            # 'Ambientes': aGraeSQLTools().getSql('ambientes_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData()),
            # 'Segmentos': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select distinct idlote,nombre as lote,codigo as codigo_muestra,segmento,ceap,st_asText(geom) as geom from segm_analitica;'''),
            # 'Nitrogeno': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select distinct idlote,nombre as lote,codigo as codigo_muestra,n as valor,no3,nh4,lower(n_tipo) as tipo, n_inc as incremento, st_asText(geom) as geom from segm_analitica;'''),
            # 'Fosforo': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select distinct idlote,nombre as lote,codigo as codigo_muestra,p as valor,lower(p_tipo) as tipo, p_inc as incremento,st_asText(geom) as geom from segm_analitica;'''),
            # 'Potasio': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select distinct idlote,nombre as lote,codigo as codigo_muestra,k as valor,lower(k_tipo) as tipo, k_inc as incremento,st_asText(geom) as geom from segm_analitica;'''),
            # 'PH': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select distinct idlote,nombre as lote,codigo as codigo_muestra,ph as valor,lower(ph_tipo) as tipo,st_asText(geom) as geom from segm_analitica;'''),
            # 'Conductividad Electrica': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select distinct idlote,nombre as lote,codigo as codigo_muestra,ce/100 as ce ,st_asText(geom) as geom from segm_analitica;'''),
            # 'Calcio': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select distinct idlote,nombre as lote,codigo as codigo_muestra,ca as valor,lower(ca_tipo) as tipo,st_asText(geom) as geom from segm_analitica;'''),
            # 'Magnesio': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select distinct idlote,nombre as lote,codigo as codigo_muestra,mg as valor,lower(mg_tipo) as tipo,st_asText(geom) as geom from segm_analitica;'''),
            # 'Sodio': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select distinct idlote,nombre as lote,codigo as codigo_muestra,na as valor,lower(na_tipo) as tipo,st_asText(geom) as geom from segm_analitica;'''),
            # 'Azufre': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select distinct idlote,nombre as lote,codigo as codigo_muestra,s as valor,st_asText(geom) as geom from segm_analitica;'''),
            # 'CIC': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''
            # select distinct idlote,nombre as lote,codigo as codigo_muestra,
            # (case when segmento = 1 then 'Rojo' when segmento = 2 then 'Verde' when segmento = 3 then 'Azul' end) as "SEGMENTO",
            # round(cic::numeric,1)::double precision as "CIC", 
            # round(round(ca::numeric,1) / (ca + mg + k + na)::numeric * 100,1)::double precision || '%' as "CA",
            # round(round(mg::numeric,1) / (ca + mg + k + na)::numeric * 100,1)::double precision || '%' as "MG",
            # round(round(k::numeric,1) / (ca + mg + k + na)::numeric * 100,1)::double precision || '%' as "K",
            # round(round(na::numeric,1) / (ca + mg + k + na)::numeric * 100,1)::double precision || '%' as "NA",
            # st_asText(st_union(geom)) as geom 
            # from segm_analitica
            # group by idlote,nombre,codigo,segmento,cic,ca,mg,k,na;'''),
            # 'Hierro': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select distinct idlote,nombre as lote,codigo as codigo_muestra,fe,st_asText(geom) as geom from segm_analitica;'''),
            # 'Manganeso': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select distinct idlote,nombre as lote,codigo as codigo_muestra,mn as valor,st_asText(geom) as geom from segm_analitica;'''),
            # 'Aluminio': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select distinct idlote,nombre as lote,codigo as codigo_muestra,al,st_asText(geom) as geom from segm_analitica;'''),
            # 'Boro': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select distinct idlote,nombre as lote,codigo as codigo_muestra,b,st_asText(geom) as geom from segm_analitica;'''),
            # 'Cinq': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select distinct idlote,nombre as lote,codigo as codigo_muestra,zn ,st_asText(geom) as geom from segm_analitica;'''),
            # 'Cobre': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select distinct idlote,nombre as lote,codigo as codigo_muestra,cu,st_asText(geom) as geom from segm_analitica;'''),
            # 'Materia Organica': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select distinct idlote,nombre as lote,codigo as codigo_muestra,organi ,st_asText(geom) as geom from segm_analitica;'''),
            # 'Relacion CN': aGraeSQLTools().getSql('segmentos_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select distinct idlote,nombre as lote,codigo as codigo_muestra,rel_cn,st_asText(geom) as geom from segm_analitica;'''),
            # 'Fert Variable Intraparcelaria': aGraeSQLTools().getSql('uf_aportes_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),sql_intra),
            # 'Fert Variable Parcelaria': aGraeSQLTools().getSql('uf_aportes_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'''select * from fert_parcelaria'''),
            # 'Ceap36 Textura': aGraeSQLTools().getSql('ceap36_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData()),
            # 'Ceap36 Infiltracion': aGraeSQLTools().getSql('ceap36_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData()),
            # 'Ceap90 Textura': aGraeSQLTools().getSql('ceap90_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData()),
            # 'Ceap90 Infiltracion': aGraeSQLTools().getSql('ceap90_layers_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData()),
            'Rendimiento' : aGraeSQLTools().getSql('rindes_layer_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData())
            # 'Mapa_SIG' : aGraeSQLTools().getSql('uf_aportes_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'select * from mapa_sig')
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

        # ambientes = self.tools.getDataBaseLayerUri(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'{}-{}'.format(name_camp,name_exp))
        # self.atlasLayers['Ambientes'] = ambientes
        # QgsProject.instance().addMapLayer(ambientes)

    def getMapaSig(self):

        query =  aGraeSQLTools().getSql('uf_aportes_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData(),'NULL','NULL', 'select * from mapa_sig')
        name = '{}_{}_MAPA_SIG'.format(self.combo_campania.currentText(),self.combo_explotacion.currentText().split('-')[1])
        layer = self.tools.getDataBaseLayer(query,name,styleName='Fert Variable Intraparcelaria',debug=True)
        QgsProject.instance().addMapLayer(layer)

    def getMapaRindes(self):
        query = aGraeSQLTools().getSql('rindes_layer_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData())
        name = '{}_{}_Rindes'.format(self.combo_campania.currentText(),self.combo_explotacion.currentText().split('-')[1])
        layer = self.tools.getDataBaseLayer(query,name,styleName='Rendimiento',debug=True)
        QgsProject.instance().addMapLayer(layer)

    def getIntegralTermicaLayer(self):
        query = aGraeSQLTools().getSql('integral_termica_query.sql').format(self.combo_campania.currentData(),self.combo_explotacion.currentData())
        name = '{}_{}_Integral_Termica'.format(self.combo_campania.get_current_campaign_name(),self.combo_explotacion.get_current_explotacion_name())
        layer = self.tools.getDataBaseLayer(query,name,styleName='integral_termica',memory=True,debug=True)
        QgsProject.instance().addMapLayer(layer)

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
        try:
            for lote in lotes:
                name = lote['lote']
                self.tools.exportarUFS(path,lote['iddata'],lote['lote'])
            self.tools.messages('aGrae GIS','Archivos Generados Correctamente',3,alert=True)
        except Exception as ex:
            print(ex)
            self.tools.messages('aGrae GIS','Ocurrio un Error',1,alert=True)
        


    def exportarResumen(self):
        #TODO EXPORTAR RESUMEN DE FERTILIZACION DE LOS LOTES SELECCIONADOS

        idcampania = self.combo_campania.currentData()
        idexplotacion = self.combo_explotacion.currentData()
        nameExp = str(self.combo_explotacion.currentText()).replace(' ','_')
        if len(self.layer.selectedFeatures()) > 0:
            iddata = [f['iddata'] for f in self.layer.selectedFeatures()]
            self.tools.exportarResumenFertilizacion(
                nameExp=nameExp,
                iddata=iddata)
        else:
             self.tools.exportarResumenFertilizacion(
                nameExp=nameExp,
                idcampania=idcampania,
                idexplotacion=idexplotacion)


    
    def actualizarProduccionCultivo(self):
        idcampania = self.combo_campania.currentData()
        idexplotacion = self.combo_explotacion.currentData()
        idCultivo = self.combo_cultivo_2.currentData()
        idRegimen = self.combo_regimen_2.currentData()
        produccion = self.line_produccion_2.value()
        if self.combo_cultivo_2.currentData() != None and self.combo_regimen_2.currentData() != None:
            reply = QtWidgets.QMessageBox.question(self,'aGrae Toolbox','Quieres Actualizar la data para todos los cultivos: {}.\nDe la explotacion {}?'.format(self.combo_cultivo_2.currentText() , self.combo_explotacion.currentText()),QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
            if reply == QtWidgets.QMessageBox.Yes:
                self.tools.actualizarProduccionCultivo(idRegimen,produccion,idcampania,idexplotacion,idCultivo)


    def actualizarDataCultivoFechas(self):
        self.tools.updateFechaSiembraLotes(
            self.combo_campania.currentData(),
            self.combo_explotacion.currentData(),
            self.combo_cultivo_2.currentData(),
            self.date_siembra_2.date().toString('yyyy-MM-dd'))



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

    def _validate_date_range(self):
        max_months = 6

        desde = self.date_edit_desde.date()
        hasta = self.date_edit_hasta.date()

        # No permitir fechas futuras
        today = QDate.currentDate()
        if hasta > today:
            hasta = today
            self.date_edit_hasta.setDate(hasta)

        if desde > today:
            desde = today
            self.date_edit_desde.setDate(desde)

        # Si rango mayor a 6 meses, ajustar automáticamente
        max_hasta = desde.addMonths(max_months)

        if hasta > max_hasta:
            self.date_edit_hasta.blockSignals(True)
            self.date_edit_hasta.setDate(max_hasta)
            self.date_edit_hasta.blockSignals(False)

        # Si usuario mueve "hasta" hacia atrás más de 6 meses
        min_desde = hasta.addMonths(-max_months)

        if desde < min_desde:
            self.date_edit_desde.blockSignals(True)
            self.date_edit_desde.setDate(min_desde)
            self.date_edit_desde.blockSignals(False)








    

        
