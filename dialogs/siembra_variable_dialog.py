from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel, QGroupBox, QGridLayout, QSpinBox,QMessageBox
from PyQt5.QtCore import Qt, QVariant
from qgis.core import *
from qgis.gui import *
import numpy as np
import processing

from ..sql import aGraeSQLTools
from ..tools import aGraeTools
from ..gui import agraeGUI
from ..gui.components import CultivosComboBox

class SiembraVariableDialog(QDialog):
    def __init__(self, idcampania:int,idexplotacion:int, parent=None):
        super().__init__(parent)

        self.tools = aGraeTools()

        self.setWindowTitle("Siembra Variable")
        self.setMinimumSize(300, 150)
        self.setWindowModality(Qt.ApplicationModal)

        self.idcampania = idcampania
        self.idexplotacion = idexplotacion

        layout = QVBoxLayout()
        self.setLayout(layout)
        self.UIComponents()


        self.setWindowTitle("aGrae | Siembra Variable")

    def UIComponents(self):

        cultivo_group_box = QGroupBox("Procesamiento por Cultivos")
        cultivo_layout = QGridLayout()
        self.combo_cultivo = CultivosComboBox(endpoint='/gis/cultivos/data_combo/?idcampania={}&idexplotacion={}'.format(self.idcampania, self.idexplotacion), auto_enable_on_load=True)

        cultivo_layout.addWidget(QLabel("Seleccione Cultivo:"), 0, 0)
        cultivo_layout.addWidget(self.combo_cultivo, 1, 0)
        
        cultivo_group_box.setLayout(cultivo_layout)
        self.layout().addWidget(cultivo_group_box)
        
        

        parametros_group_box = QGroupBox("Configuración de Parámetros")
        parametros_layout = QGridLayout()

        self.y_min_value = QSpinBox()
        self.y_min_value.setMinimum(0)
        self.y_min_value.setMaximum(10000)
        self.y_min_value.setValue(210)
        
        self.combo_cultivo.setMinimumHeight(24)
        

        self.y_max_value = QSpinBox()
        self.y_max_value.setMinimum(0)
        self.y_max_value.setMaximum(10000)
        self.y_max_value.setValue(250)
        

        self.index_value = QSpinBox()
        self.index_value.setMinimum(0)
        self.index_value.setMaximum(10000)
        self.index_value.setValue(1)

        # Limitar altura mínima de los componentes
        self.y_min_value.setMinimumHeight(24)
        self.y_max_value.setMinimumHeight(24)
        self.index_value.setMinimumHeight(24)
        
        # Añadir widgets al layout    
        parametros_layout.addWidget(QLabel("Valor Mínimo (kg/ha):"), 0, 0)
        parametros_layout.addWidget(self.y_min_value, 1, 0)
        parametros_layout.addWidget(QLabel("Valor Máximo (kg/ha):"), 0, 1)
        parametros_layout.addWidget(self.y_max_value, 1, 1)
        parametros_layout.addWidget(QLabel("Índice de Variabilidad:"), 0, 2)
        parametros_layout.addWidget(self.index_value, 1, 2)
        
        # Grupo colapsable para parámetros avanzados

        advanced_group_box = QgsCollapsibleGroupBox("Parámetros Avanzados")
        advanced_group_box.setCollapsed(True)
        advanced_group_box.collapsedStateChanged.connect(self.showWarning)
        advanced_layout = QGridLayout()

        self.percentil_min_spin = QSpinBox()
        self.percentil_min_spin.setMinimum(0)
        self.percentil_min_spin.setMaximum(100)
        self.percentil_min_spin.setValue(1)
        self.percentil_min_spin.setMinimumHeight(24)

        self.percentil_max_spin = QSpinBox()
        self.percentil_max_spin.setMinimum(0)
        self.percentil_max_spin.setMaximum(100)
        self.percentil_max_spin.setValue(99)
        self.percentil_max_spin.setMinimumHeight(24)

        advanced_layout.addWidget(QLabel("Percentil Mínimo:"), 0, 0)
        advanced_layout.addWidget(self.percentil_min_spin, 1, 0)
        advanced_layout.addWidget(QLabel("Percentil Máximo:"), 0, 1)
        advanced_layout.addWidget(self.percentil_max_spin, 1, 1)

        advanced_group_box.setLayout(advanced_layout)
        parametros_layout.addWidget(advanced_group_box, 2, 0, 1, 3)


        generate_button = QPushButton("Generar Mapa de Siembra")
        generate_button.setEnabled(False)
        self.combo_cultivo.currentIndexChanged.connect(
            lambda _: generate_button.setEnabled(self.combo_cultivo.currentData() is not None)
        )
        generate_button.clicked.connect(self.generar_mapa_siembra)

        parametros_group_box.setLayout(parametros_layout)
        self.layout().setAlignment(parametros_group_box, Qt.AlignTop)
        self.layout().addWidget(parametros_group_box)
        self.layout().addWidget(generate_button)

        # Limitar el tamaño mínimo del diálogo a la altura y ancho actuales
        # self.setMinimumSize(300,150)
        # self.setSizeGripEnabled(True)
        self.setMinimumSize(300, 150)
        self.setMaximumSize(16777215, 16777215)  # Permite aumentar sin límite, pero no reducir por debajo del mínimo


    def importar_datos(self):
        # Lógica para importar datos de siembra variable
        print("Importando datos de siembra variable...")
        self.accept()

    def exportar_datos(self):
        # Lógica para exportar datos de siembra variable
        print("Exportando datos de siembra variable...")
        self.accept()

    def generar_capa_ce(self) -> QgsVectorLayer:

        sql = aGraeSQLTools().getSql('siembra_query.sql').format(self.idcampania, self.idexplotacion, int(self.combo_cultivo.currentData()))

        # print(sql)
        layer = self.tools.getDataBaseLayer(sql=sql,layername='C.E. - {}'.format(self.combo_cultivo.currentText()))

        if layer.isValid():
            return layer
        
    
    def generar_mapa_siembra(self):
        layer = self.generar_capa_ce()
        if not layer or not layer.isValid():
            return

        layer.startEditing()

        if 'dosis_sem' not in [field.name() for field in layer.fields()]:
            layer.dataProvider().addAttributes([QgsField('dosis_sem', QVariant.Int)])
            layer.updateFields()

        dosis_idx = layer.fields().indexOf('dosis_sem')


        # Agrupar por idlote
        features_by_lote = {}
        for f in layer.getFeatures():
            idlote = f['idlote']
            if idlote not in features_by_lote:
                features_by_lote[idlote] = []
            features_by_lote[idlote].append(f)

        # Ejemplo: iterar sobre cada grupo de polígonos con el mismo idlote
        for idlote, features in features_by_lote.items():
            # Aquí puedes procesar cada grupo de features (polígonos) con el mismo idlote
            # Ejemplo: acceder a los valores ce36 de cada polígono
            ce_values = [feat['ce36'] for feat in features if isinstance(feat['ce36'], (int, float))]

            ce_min = np.percentile(ce_values, self.percentil_min_spin.value())
            ce_max = np.percentile(ce_values, self.percentil_max_spin.value())

            _slope = (self.y_max_value.value() - self.y_min_value.value()) / (ce_max - ce_min)
            _intercept = self.y_min_value.value() - _slope * ce_min

            for feat in features:
                ce36 = feat['ce36']
                if isinstance(ce36, (int, float)):
                    val_clipped = min(max(ce36, ce_min), ce_max)
                    dosis_value = int(round(val_clipped * _slope + _intercept))
                    layer.changeAttributeValue(feat.id(), dosis_idx, dosis_value)

        
        layer.commitChanges()

        fix_geometry = processing.run("native:fixgeometries", {'INPUT': layer, 'METHOD': 1, 'OUTPUT': 'TEMPORARY_OUTPUT'})

        dissolved_layer_result = processing.run("native:dissolve", {
            'INPUT': fix_geometry['OUTPUT'] ,
            'FIELD': ['dosis_sem', 'idlote'],
            'OUTPUT': 'memory:'
        })

        dissolved_layer = dissolved_layer_result['OUTPUT']
        dissolved_layer.setName('Siembra - {}'.format(self.combo_cultivo.currentText()))

        QgsProject.instance().addMapLayer(dissolved_layer)

    def showWarning(self, collapsed):
        if not collapsed:  # Only show warning when expanding
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Warning)
            msgBox.setWindowTitle("Advertencia")
            msgBox.setText("Los parámetros están ajustados de forma predeterminada.")
            msgBox.setInformativeText(
                "Cualquier cambio puede alterar la calidad de los resultados. ¿Desea continuar?"
            )
            msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            msgBox.setDefaultButton(QMessageBox.Ok)
            ret = msgBox.exec_()

            if ret == QMessageBox.Cancel:
                self.advanceParametersGroup.setCollapsed(True) # Collapse if cancelled