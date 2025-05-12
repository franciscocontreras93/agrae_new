"""
Model exported as python.
Name : 1_Post-procesado
Group : aGrae GEE
With QGIS : 33411
"""

from qgis.core import QgsCoordinateReferenceSystem
from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsProcessingParameterFeatureSource
from qgis.core import QgsProcessingParameterFile
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterVectorLayer
import processing


class GEE_postprocesado(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer('capa_ambientes_gee', 'Capa Ambientes GEE', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterLayer('capa_ndvi_gee', 'Capa NDVI GEE', defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSource('lote', 'Lote', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterFile('estilo', 'Estilo', behavior=QgsProcessingParameterFile.File, fileFilter='Todos los archivos (*.*)', defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('mapa_de_ambientes', 'Mapa de Ambientes', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(16, model_feedback)
        results = {}
        outputs = {}

        # Reproyectar capa
        alg_params = {
            'INPUT': parameters['capa_ambientes_gee'],
            'OPERATION': '',
            'TARGET_CRS': parameters['capa_ndvi_gee'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ReproyectarCapa'] = processing.run('native:reprojectlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Corregir geometrías 1
        alg_params = {
            'INPUT': outputs['ReproyectarCapa']['OUTPUT'],
            'METHOD': 1,  # Estructura
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CorregirGeometras1'] = processing.run('native:fixgeometries', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Reproyectar capa Lote
        alg_params = {
            'INPUT': parameters['lote'],
            'OPERATION': '',
            'TARGET_CRS': parameters['capa_ndvi_gee'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ReproyectarCapaLote'] = processing.run('native:reprojectlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Corregir geometrías 3
        alg_params = {
            'INPUT': outputs['ReproyectarCapaLote']['OUTPUT'],
            'METHOD': 1,  # Estructura
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CorregirGeometras3'] = processing.run('native:fixgeometries', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # Seleccionar por expresión
        alg_params = {
            'EXPRESSION': '$area < 400',
            'INPUT': outputs['CorregirGeometras1']['OUTPUT'],
            'METHOD': 0,  # creando una nueva selección
        }
        outputs['SeleccionarPorExpresin'] = processing.run('qgis:selectbyexpression', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Eliminar los polígonos seleccionados
        alg_params = {
            'INPUT': outputs['SeleccionarPorExpresin']['OUTPUT'],
            'MODE': 1,  # Área más pequeña
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['EliminarLosPolgonosSeleccionados'] = processing.run('qgis:eliminateselectedpolygons', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # Corregir geometrías 2 
        alg_params = {
            'INPUT': outputs['EliminarLosPolgonosSeleccionados']['OUTPUT'],
            'METHOD': 1,  # Estructura
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CorregirGeometras2'] = processing.run('native:fixgeometries', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # Disolver 
        alg_params = {
            'FIELD': ['ambiente'],
            'INPUT': outputs['CorregirGeometras2']['OUTPUT'],
            'SEPARATE_DISJOINT': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Disolver'] = processing.run('native:dissolve', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # Corregir geometrías 4
        alg_params = {
            'INPUT': outputs['Disolver']['OUTPUT'],
            'METHOD': 1,  # Estructura
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CorregirGeometras4'] = processing.run('native:fixgeometries', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}

        # Estadísticas de zona
        alg_params = {
            'COLUMN_PREFIX': 'NDVI',
            'INPUT': outputs['CorregirGeometras4']['OUTPUT'],
            'INPUT_RASTER': parameters['capa_ndvi_gee'],
            'RASTER_BAND': 1,
            'STATISTICS': [3],  # Mediana
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['EstadsticasDeZona'] = processing.run('native:zonalstatisticsfb', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(10)
        if feedback.isCanceled():
            return {}

        # Corregir geometrías 5
        alg_params = {
            'INPUT': outputs['EstadsticasDeZona']['OUTPUT'],
            'METHOD': 1,  # Estructura
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CorregirGeometras5'] = processing.run('native:fixgeometries', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(11)
        if feedback.isCanceled():
            return {}

        # Cortar 
        alg_params = {
            'INPUT': outputs['CorregirGeometras5']['OUTPUT'],
            'OVERLAY': outputs['CorregirGeometras3']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Cortar'] = processing.run('native:clip', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(12)
        if feedback.isCanceled():
            return {}

        # Quitar campo(s)
        alg_params = {
            'COLUMN': ['count'],
            'INPUT': outputs['Cortar']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['QuitarCampos'] = processing.run('native:deletecolumn', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(13)
        if feedback.isCanceled():
            return {}

        # Cambiar nombre de campo
        alg_params = {
            'FIELD': 'NDVImedian',
            'INPUT': outputs['QuitarCampos']['OUTPUT'],
            'NEW_NAME': 'NDVImax',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CambiarNombreDeCampo'] = processing.run('native:renametablefield', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(14)
        if feedback.isCanceled():
            return {}

        # Reproyectar capa Final
        alg_params = {
            'INPUT': outputs['CambiarNombreDeCampo']['OUTPUT'],
            'OPERATION': '',
            'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:4326'),
            'OUTPUT': parameters['MapaDeAmbientes']
        }
        outputs['ReproyectarCapaFinal'] = processing.run('native:reprojectlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['MapaDeAmbientes'] = outputs['ReproyectarCapaFinal']['OUTPUT']

        feedback.setCurrentStep(15)
        if feedback.isCanceled():
            return {}

        # Establecer el estilo de capa
        alg_params = {
            'INPUT': outputs['ReproyectarCapaFinal']['OUTPUT'],
            'STYLE': 'C:\\Users\\Ing_G\\AppData\\Roaming\\QGIS\\QGIS3\\profiles\\default\\python\\plugins\\agrae\\tools\\styles\\ambientes.qml'
        }
        outputs['EstablecerElEstiloDeCapa'] = processing.run('native:setlayerstyle', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        return results

    def name(self):
        return '1_Post-procesado'

    def displayName(self):
        return '1_Post-procesado'

    def group(self):
        return 'aGrae GEE'

    def groupId(self):
        return 'aGrae GEE'

    def createInstance(self):
        return _postprocesado()
