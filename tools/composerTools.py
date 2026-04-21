import os
import tempfile

from qgis.PyQt.QtXml import QDomDocument

from qgis.core import *
from qgis.gui import QgsFieldComboBox
from qgis.utils import iface

from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSignal, QSettings, QDateTime, QThreadPool
from PyQt5.QtGui import QColor, QFont

from ..tools import aGraeTools
from ..db import agraeDataBaseDriver
from ..core.api import APIRequest


class aGraeComposerTools():
    """
    Herramientas para generar layouts e informes atlas.
    """

    def __init__(self, layers, idcampania, idexplotacion) -> None:
        self.layers = layers
        self.idcampania = idcampania
        self.idexplotacion = idexplotacion
        self.plugin_dir = os.path.dirname(__file__)
        self.settings = QSettings('agrae', 'dbConnection')

        self.tools = aGraeTools()
        self.api = APIRequest()
        self.conn = agraeDataBaseDriver().connection()

        self.nombre_explotacion = ''
        self.direccion_explotacion = ''
        self.txt_export_path = None
        self.designer = None
        self.layout = None
        self.atlas = None

        self.temp_logo_path = os.path.join(
            tempfile.gettempdir(),
            f"agrae_dist_logo_{self.idexplotacion}.png"
        )

        self.basemaps = {
            'Esri Satelite': {
                'url': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/%7Bz%7D/%7By%7D/%7Bx%7D',
                'options': 'crs=EPSG:3857&format&type=xyz&url=https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/%7Bz%7D/%7By%7D/%7Bx%7D&zmax=20&zmin=0'
            },
            'Google Satelite': {
                'url': 'https://mt1.google.com/vt/lyrs=s&x=%7Bx%7D&y=%7By%7D&z=%7Bz%7D',
                'options': 'type=xyz&zmin=0&zmax=20&url=https://mt1.google.com/vt/lyrs%3Ds%26x%3D{x}%26y%3D{y}%26z%3D{z}'
            },
            'PNOA Ortofoto': {
                'url': 'contextualWMSLegend=0&crs=EPSG:4326&dpiMode=7&featureCount=10&format=image/png&layers=OI.OrthoimageCoverage&styles',
                'options': 'url=https://www.ign.es/wms-inspire/pnoa-ma'
            },
            'Parcelas Catastro': {
                'url': 'contextualWMSLegend=1&crs=EPSG:4326&dpiMode=7&featureCount=10&format=image/png&layers=CP.CadastralParcel&styles',
                'options': 'url=http://ovc.catastro.meh.es/cartografia/INSPIRE/spadgcwms.aspx'
            }
        }

        self.panels_path = self.settings.value('paneles_path')
        self.reportes_path = self.settings.value('reporte_path')

    def setLayersToMap(self, mapItems, layers, basemap):
        """
        Asigna capas a uno o dos mapas del layout.
        """
        map_1 = mapItems[0]
        map_1_settings = QgsMapSettings()
        map_1_settings.setLayers([layers[1], layers[0], basemap])
        map_1.setLayers([layers[1], layers[0], basemap])

        clippingSettings = QgsLayoutItemMapAtlasClippingSettings(map_1)
        clippingSettings.setEnabled(True)
        clippingSettings.setLayersToClip([layers[1]])
        clippingSettings.setRestrictToLayers(True)

        if len(mapItems) >= 2:
            map_2 = mapItems[1]
            map_2_settings = QgsMapSettings()
            map_2_settings.setLayers([layers[2], layers[0], basemap])
            map_2.setLayers([layers[2], layers[0], basemap])

            clippingSettings = QgsLayoutItemMapAtlasClippingSettings(map_2)
            clippingSettings.setEnabled(True)
            clippingSettings.setLayersToClip([layers[2]])
            clippingSettings.setRestrictToLayers(True)

    def setLegendsToLayout(self, legendItem, layers, labels):
        """
        Configura la leyenda del layout.
        """
        titleFont = QFont('Arial', 12, 1, False)
        titleFont.setBold(True)
        subGroupFont = QFont('Arial', 10, 1, False)
        subGroupFont.setBold(True)
        font = QFont('Arial', 10, 1, False)

        legend = legendItem
        legend.rstyle(QgsLegendStyle.Title).setFont(titleFont)
        legend.rstyle(QgsLegendStyle.Title).setMargin(QgsLegendStyle.Bottom, 3)
        legend.rstyle(QgsLegendStyle.Subgroup).setFont(subGroupFont)
        legend.rstyle(QgsLegendStyle.Subgroup).setMargin(QgsLegendStyle.Bottom, 3)
        legend.rstyle(QgsLegendStyle.SymbolLabel).setFont(font)
        legend.rstyle(QgsLegendStyle.SymbolLabel).setMargin(QgsLegendStyle.Left, 3)

        legend_model = legend.model()
        legend_root = legend_model.rootGroup()
        legend_root.clear()

        for l in layers:
            legend_root.addLayer(l)

        for tr, layer, label in zip(legend_root.children(), layers, labels):
            if tr.name() == layer.name():
                tr.setCustomProperty('legend/title-label', label)

    def getDistData(self, idcampania, idexplotacion) -> None:
        """
        Obtiene datos de explotación y descarga el logo del distribuidor a un archivo temporal.
        """
        try:
            with self.conn.cursor() as cursor:
                sql = '''
                select ex.nombre as explotacion, ex.direccion
                from agrae.explotacion ex
                where ex.idexplotacion = {}
                limit 1
                '''.format(idexplotacion)

                cursor.execute(sql)
                data = cursor.fetchone()

                if data:
                    self.nombre_explotacion = data[0].upper() if data[0] else ''
                    self.direccion_explotacion = data[1].upper() if data[1] else ''
                else:
                    self.nombre_explotacion = ''
                    self.direccion_explotacion = ''

            endpoint = f'gis/distribuidores/imagen/{idexplotacion}'
            response = self.api.get(endpoint=endpoint, raw=True)

            if response:
                with open(self.temp_logo_path, 'wb') as out:
                    out.write(response)

        except TypeError as te:
            QgsMessageLog.logMessage(f'{te}', 'aGrae GIS', level=Qgis.Critical)
        except Exception as ex:
            QgsMessageLog.logMessage(f'{ex}', 'aGrae GIS', level=Qgis.Critical)

    def applyLayoutLogos(self, logos_exp, logos_agrae):
        """
        Asigna los logos a los elementos de imagen del layout.
        """
        try:
            if os.path.exists(self.temp_logo_path):
                for item in logos_exp:
                    item.setPicturePath(self.temp_logo_path)
                    item.refresh()

            agrae_logo = os.path.join(os.path.dirname(__file__), 'img', 'agrae_logo.png')
            for item in logos_agrae:
                item.setPicturePath(agrae_logo)
                item.refresh()

        except Exception as ex:
            QgsMessageLog.logMessage(f'{ex}', 'aGrae GIS', level=Qgis.Warning)

    def setTextOverElements(self, elements, text):
        """
        Asigna texto a múltiples elementos del layout.
        """
        try:
            for e in elements:
                e.setText(text.upper())
        except Exception:
            pass

    def askTxtSavePath(self):
        """
        Pregunta al usuario si desea guardar un TXT y permite elegir la ruta.
        """
        reply = QMessageBox.question(
            None,
            "aGrae GIS",
            "¿Deseas guardar también un archivo TXT con la explotación y los lotes?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply != QMessageBox.Yes:
            return None

        project_path = QgsProject.instance().fileName()
        base_dir = os.path.dirname(project_path) if project_path else os.path.expanduser("~")

        default_name = f"informes_lotes.txt"
        # default_name = default_name.replace(" ", "_").replace("/", "_").replace("\\", "_")

        file_path, _ = QFileDialog.getSaveFileName(
            None,
            "Guardar resumen de lotes",
            os.path.join(base_dir, default_name),
            "Archivos de texto (*.txt)"
        )

        return file_path if file_path else None

    def getAtlasLotes(self):
        """
        Devuelve la lista de lotes visibles en la capa Atlas.
        """
        atlas_layer = self.layers.get('Atlas')
        if not atlas_layer:
            return []

        field_names = atlas_layer.fields().names()

        lote_field = None
        if 'lote' in field_names:
            lote_field = 'lote'
        elif 'nombre' in field_names:
            lote_field = 'nombre'

        if lote_field is None:
            return []

        lotes = []
        for f in atlas_layer.getFeatures():
            value = f[lote_field]
            if value is not None:
                lotes.append(str(value))

        return sorted(set(lotes))

    def writeLotesTxt(self, file_path):
        """
        Escribe un TXT con la explotación y los lotes.
        """
        if not file_path:
            return

        lotes = self.getAtlasLotes()
        contenido = f"Explotacion: {self.nombre_explotacion}\n"
        contenido += f"Lotes: {' ; '.join(lotes)}"

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(contenido)

        QgsMessageLog.logMessage(
            f'TXT generado correctamente: {file_path}',
            'aGrae GIS',
            level=Qgis.Success
        )

    def connectDesignerClose(self):
        """
        Abre el diseñador y conecta la limpieza al cerrar.
        """
        self.designer = iface.openLayoutDesigner(self.layout)
        if self.designer is not None:
            self.designer.destroyed.connect(self.clearFilter)

    def layoutGeneratorPreescripcion(
        self,
        basemap,
        materia_organica=False,
        preview=False,
        printer=False
    ):
        """
        Genera el layout de preescripción.
        """
        titleFont = QFont('Arial', 12, 1, False)
        titleFont.setBold(True)
        subGroupFont = QFont('Arial', 10, 1, False)
        subGroupFont.setBold(True)
        font = QFont('Arial', 10, 1, False)

        legend_style = QgsLegendStyle()
        legend_style.setFont(font)
        legend_style.setMargin(QgsLegendStyle.Left, 3)

        legend_style_title = QgsLegendStyle()
        legend_style_title.setFont(titleFont)
        legend_style.setMargin(QgsLegendStyle.Bottom, 10)

        legend_style_subGroup = QgsLegendStyle()
        legend_style_subGroup.setFont(subGroupFont)

        basemap = self.tools.getBaseMap(basemap, self.basemaps)
        QgsProject.instance().addMapLayer(basemap, False)
        self.getDistData(idcampania=self.idcampania, idexplotacion=self.idexplotacion)

        project = QgsProject.instance()
        manager = project.layoutManager()
        layoutName = "Preescripcion"

        layouts_list = manager.printLayouts()
        for layout in layouts_list:
            if layout.name() == layoutName:
                manager.removeLayout(layout)

        layout = QgsPrintLayout(project)
        layout.initializeDefaults()
        layout.setName(layoutName)
        manager.addLayout(layout)
        self.layout = layout

        self.atlas = layout.atlas()
        self.atlas.setCoverageLayer(self.layers['Atlas'])
        self.atlas.setPageNameExpression('lote')
        self.atlas.setFilenameExpression('lote')
        self.atlas.refreshCurrentFeature()
        self.atlas.updateFeatures()
        self.atlas.setEnabled(True)
        self.atlas.seekTo(0)

        pc = layout.pageCollection()
        for l in range(0, 15 if materia_organica else 14):
            pc.addPage(QgsLayoutItemPage(layout=layout))
            pc.page(l).setPageSize('A4', QgsLayoutItemPage.Orientation.Portrait)

        tmpfile = self.plugin_dir + '/templates/prescripcion_dev.qpt'
        with open(tmpfile) as f:
            template_content = f.read()

        doc = QDomDocument()
        doc.setContent(template_content)
        items, _ = layout.loadFromTemplate(doc, QgsReadWriteContext(), False)

        logos_agrae = [i for i in items if isinstance(i, QgsLayoutItemPicture) and i.id() == 'Logo Agrae']
        logos_exp = [i for i in items if isinstance(i, QgsLayoutItemPicture) and i.id() == 'exp_logo']
        direcciones = [i for i in items if isinstance(i, QgsLayoutItemLabel) and i.id() == 'exp_dir']
        nombres_exp = [i for i in items if isinstance(i, QgsLayoutItemLabel) and i.id() == 'exp_name']
        nombres_lotes = [i for i in items if isinstance(i, QgsLayoutItemLabel) and i.id() == 'lote_nom']

        self.applyLayoutLogos(logos_exp, logos_agrae)

        self.setTextOverElements(nombres_exp, self.nombre_explotacion.upper())
        self.setTextOverElements(direcciones, self.direccion_explotacion.upper())

        lotes = self.layers['Atlas']

        self.setLayersToMap([layout.itemById('ceap36_txt'), layout.itemById('ceap90_txt')], [lotes, self.layers['Ceap36 Textura'], self.layers['Ceap90 Textura']], basemap)
        self.setLayersToMap([layout.itemById('ceap36_inf'), layout.itemById('ceap90_inf')], [lotes, self.layers['Ceap36 Infiltracion'], self.layers['Ceap90 Infiltracion']], basemap)
        self.setLayersToMap([layout.itemById('map_nitrogeno'), layout.itemById('map_fosforo')], [lotes, self.layers['Nitrogeno'], self.layers['Fosforo']], basemap)
        self.setLayersToMap([layout.itemById('map_potasio'), layout.itemById('map_ambientes')], [lotes, self.layers['Potasio'], self.layers['Ambientes']], basemap)
        self.setLayersToMap([layout.itemById('map_ph'), layout.itemById('map_conductividad')], [lotes, self.layers['PH'], self.layers['Conductividad Electrica']], basemap)
        self.setLayersToMap([layout.itemById('map_06')], [lotes, self.layers['Fert Variable Intraparcelaria']], basemap)
        self.setLayersToMap([layout.itemById('map_07_01')], [lotes, self.layers['Fert Variable Intraparcelaria']], basemap)
        self.setLayersToMap([layout.itemById('map_07_02')], [lotes, self.layers['Fert Variable Parcelaria']], basemap)
        self.setLayersToMap([layout.itemById('map_calcio'), layout.itemById('map_magnesio')], [lotes, self.layers['Calcio'], self.layers['Magnesio']], basemap)
        self.setLayersToMap([layout.itemById('map_sodio'), layout.itemById('map_azufre')], [lotes, self.layers['Sodio'], self.layers['Azufre']], basemap)
        self.setLayersToMap([layout.itemById('map_cic'), layout.itemById('map_segmentos')], [lotes, self.layers['CIC'], self.layers['Segmentos']], basemap)
        self.setLayersToMap([layout.itemById('map_hierro'), layout.itemById('map_manganeso')], [lotes, self.layers['Hierro'], self.layers['Manganeso']], basemap)
        self.setLayersToMap([layout.itemById('map_aluminio'), layout.itemById('map_boro')], [lotes, self.layers['Aluminio'], self.layers['Boro']], basemap)
        self.setLayersToMap([layout.itemById('map_cinq'), layout.itemById('map_cobre')], [lotes, self.layers['Cinq'], self.layers['Cobre']], basemap)

        if materia_organica:
            self.setLayersToMap([layout.itemById('map_materia_organica'), layout.itemById('map_rel_cn')], [lotes, self.layers['Materia Organica'], self.layers['Relacion CN']], basemap)

        self.setLegendsToLayout(layout.itemById('legend_txt'), [self.layers['Ceap36 Textura']], ['Texturas'])
        self.setLegendsToLayout(layout.itemById('legend_inf'), [self.layers['Ceap36 Infiltracion']], ['Infiltración [mm/h]'])
        self.setLegendsToLayout(layout.itemById('legend_03'), [self.layers['Nitrogeno'], self.layers['Fosforo']], ['Nitrogeno', 'Fosforo'])
        self.setLegendsToLayout(layout.itemById('legend_04'), [self.layers['Potasio'], self.layers['Ambientes']], ['Potasio', 'Ambientes Productivos'])
        self.setLegendsToLayout(layout.itemById('legend_05'), [self.layers['PH'], self.layers['Conductividad Electrica']], ['pH', 'Conductividad Eléctrica'])
        self.setLegendsToLayout(layout.itemById('legend_06'), [self.layers['Fert Variable Intraparcelaria']], ['Unidades Fertilizantes'])
        self.setLegendsToLayout(layout.itemById('legend_07_01'), [self.layers['Fert Variable Intraparcelaria']], ['Unidades Fertilizantes'])
        self.setLegendsToLayout(layout.itemById('legend_07_02'), [self.layers['Fert Variable Parcelaria']], ['UF Unica'])
        self.setLegendsToLayout(layout.itemById('legend_08'), [self.layers['Calcio'], self.layers['Magnesio']], ['Calcio', 'Magnesio'])
        self.setLegendsToLayout(layout.itemById('legend_09'), [self.layers['Sodio'], self.layers['Azufre']], ['Sodio', 'Azufre'])
        self.setLegendsToLayout(layout.itemById('legend_10'), [self.layers['CIC']], ['CIC'])
        self.setLegendsToLayout(layout.itemById('legend_14'), [self.layers['Hierro'], self.layers['Manganeso']], ['Hierro', 'Manganeso'])
        self.setLegendsToLayout(layout.itemById('legend_15'), [self.layers['Aluminio'], self.layers['Boro']], ['Aluminio', 'Boro'])
        self.setLegendsToLayout(layout.itemById('legend_16'), [self.layers['Cinq'], self.layers['Cobre']], ['Cinq', 'Cobre'])

        if materia_organica:
            self.setLegendsToLayout(layout.itemById('legend_17'), [self.layers['Materia Organica'], self.layers['Relacion CN']], ['Materia Organica', 'Relacion Carbono/Nitrogeno'])

        cic_table = layout.itemById('cic_table')
        table_item = cic_table.multiFrame()

        self.atlas.featureChanged.connect(lambda e: self.moveCanvas(
            layout.itemById('ceap36_inf'),
            self.atlas,
            nombres_lotes,
            self.layers,
            table_item,
        ))

        self.txt_export_path = self.askTxtSavePath()

        if preview or not printer:
            self.connectDesignerClose()

        if printer:
            self.exportAtlasReport()

    def layoutGeneratorBasico(
        self,
        basemap,
        preview=False,
        printer=False
    ) -> None:
        """
        Genera el layout básico.
        """
        titleFont = QFont('Arial', 12, 1, False)
        titleFont.setBold(True)
        subGroupFont = QFont('Arial', 10, 1, False)
        subGroupFont.setBold(True)
        font = QFont('Arial', 10, 1, False)

        legend_style = QgsLegendStyle()
        legend_style.setFont(font)
        legend_style.setMargin(QgsLegendStyle.Left, 3)

        legend_style_title = QgsLegendStyle()
        legend_style_title.setFont(titleFont)
        legend_style.setMargin(QgsLegendStyle.Bottom, 10)

        legend_style_subGroup = QgsLegendStyle()
        legend_style_subGroup.setFont(subGroupFont)

        basemap = self.tools.getBaseMap(basemap, self.basemaps)
        QgsProject.instance().addMapLayer(basemap, False)
        self.getDistData(idcampania=self.idcampania, idexplotacion=self.idexplotacion)

        project = QgsProject.instance()
        manager = project.layoutManager()
        layoutName = "Preescripcion"

        layouts_list = manager.printLayouts()
        for layout in layouts_list:
            if layout.name() == layoutName:
                manager.removeLayout(layout)

        layout = QgsPrintLayout(project)
        layout.initializeDefaults()
        layout.setName(layoutName)
        manager.addLayout(layout)
        self.layout = layout

        self.atlas = layout.atlas()
        self.atlas.setCoverageLayer(self.layers['Atlas'])
        self.atlas.setPageNameExpression('lote')
        self.atlas.setFilenameExpression('lote')
        self.atlas.refreshCurrentFeature()
        self.atlas.updateFeatures()
        self.atlas.setEnabled(True)
        self.atlas.seekTo(0)

        pc = layout.pageCollection()
        for l in range(0, 4):
            pc.addPage(QgsLayoutItemPage(layout=layout))
            pc.page(l).setPageSize('A4', QgsLayoutItemPage.Orientation.Portrait)

        tmpfile = self.plugin_dir + '/templates/reporte_basico.qpt'
        with open(tmpfile) as f:
            template_content = f.read()

        doc = QDomDocument()
        doc.setContent(template_content)
        items, _ = layout.loadFromTemplate(doc, QgsReadWriteContext(), False)

        logos_agrae = [i for i in items if isinstance(i, QgsLayoutItemPicture) and i.id() == 'Logo Agrae']
        logos_exp = [i for i in items if isinstance(i, QgsLayoutItemPicture) and i.id() == 'exp_logo']
        direcciones = [i for i in items if isinstance(i, QgsLayoutItemLabel) and i.id() == 'exp_dir']
        nombres_exp = [i for i in items if isinstance(i, QgsLayoutItemLabel) and i.id() == 'exp_name']
        nombres_lotes = [i for i in items if isinstance(i, QgsLayoutItemLabel) and i.id() == 'lote_nom']

        self.applyLayoutLogos(logos_exp, logos_agrae)

        self.setTextOverElements(nombres_exp, self.nombre_explotacion.upper())
        self.setTextOverElements(direcciones, self.direccion_explotacion.upper())

        lotes = self.layers['Atlas']

        self.setLayersToMap([layout.itemById('ceap36_txt'), layout.itemById('ceap90_txt')], [lotes, self.layers['Ceap36 Textura'], self.layers['Ceap90 Textura']], basemap)
        self.setLayersToMap([layout.itemById('ceap36_inf'), layout.itemById('ceap90_inf')], [lotes, self.layers['Ceap36 Infiltracion'], self.layers['Ceap90 Infiltracion']], basemap)
        self.setLayersToMap([layout.itemById('map_segmentos'), layout.itemById('map_ambientes')], [lotes, self.layers['Segmentos'], self.layers['Ambientes']], basemap)
        self.setLayersToMap([layout.itemById('map_06'), layout.itemById('map_07')], [lotes, self.layers['Fert Variable Intraparcelaria'], self.layers['Fert Variable Parcelaria']], basemap)

        self.setLegendsToLayout(layout.itemById('legend_txt'), [self.layers['Ceap36 Textura']], ['Texturas'])
        self.setLegendsToLayout(layout.itemById('legend_inf'), [self.layers['Ceap36 Infiltracion']], ['Infiltración [mm/h]'])
        self.setLegendsToLayout(layout.itemById('legend_03'), [self.layers['Segmentos'], self.layers['Ambientes']], ['Segmentos de Suelo', 'Ambientes Productivos'])
        self.setLegendsToLayout(layout.itemById('legend_04'), [self.layers['Fert Variable Intraparcelaria'], self.layers['Fert Variable Parcelaria']], ['Fertilización Intraparcelaria', 'Fertilización Parcelaria'])

        self.atlas.featureChanged.connect(lambda: self.moveCanvas(
            layout.itemById('ceap36_inf'),
            self.atlas,
            nombres_lotes,
            self.layers
        ))

        self.txt_export_path = self.askTxtSavePath()

        if preview or not printer:
            self.connectDesignerClose()

        if printer:
            self.exportAtlasReport()

    def moveCanvas(
        self,
        map: QgsLayoutItemMap,
        atlas: QgsLayoutAtlas,
        nombresLotes,
        layers,
        table=None,
        basic=False,
    ):
        """
        Actualiza textos y filtros al cambiar de entidad atlas.
        """
        nombre_lote = atlas.currentFilename()
        self.setTextOverElements(nombresLotes, nombre_lote)

        cic_layer = None
        for l in layers:
            if l != 'Atlas':
                layers[l].setSubsetString(''' "lote" = '{}' '''.format(nombre_lote))
                if l == 'CIC':
                    cic_layer = layers[l]

        if not basic and table is not None and cic_layer is not None:
            table.setVectorLayer(cic_layer)
            table.setDisplayedFields(['segmento'.upper(), 'cic', 'ca', 'mg', 'k', 'na'])

            c_0 = table.columns()[0]
            c_0.setHeading('Segmento')
            table.refreshAttributes()

        extent = map.extent()
        atlas.coverageLayer().getFeature(atlas.currentFeatureNumber() + 1)
        iface.mapCanvas().setExtent(extent)

    def ComposerPrintWorker(self):
        """
        Ejecuta la generación de informes en segundo plano.
        """
        self.tools.UserMessages('Generando archivos de Preescripcion, este proceso puede tardar varios minutos.\nPorfavor espere un momento.')
        worker = Worker(lambda: self.layoutGeneratorPreescripcion(printer=True))
        worker.signals.finished.connect(lambda: iface.messageBar().pushMessage("aGrae GIS", 'Archivos generados correctamente', level=Qgis.Success))
        self.threadpool.start(worker)

    def exportAtlasReport(self):
        """
        Exporta el atlas a PDF y limpia filtros al finalizar.
        """
        directory = list(set([f['explotacion'] for f in self.atlas.coverageLayer().getFeatures()]))[0]
        directory = directory.replace(' ', '_')
        path = os.path.join(self.reportes_path, directory + '_' + QDateTime.currentDateTime().toString('yyyyMMddHHmmss'))
        zipper = AgraeZipper()

        try:
            os.makedirs(path)
            self.atlas.beginRender()

            settings = QgsLayoutExporter.PdfExportSettings()
            settings.appendGeoreference = False
            settings.simplifyGeometries = True

            exporter = QgsLayoutExporter(self.atlas.layout())

            for i in range(0, self.atlas.count()):
                self.atlas.seekTo(i)
                name = self.atlas.currentFilename().replace(' ', '_')
                name = name + '_' + QDateTime.currentDateTime().toString('yyyyMMddHHmmss') + ".pdf"
                exporter.exportToPdf(path + r'\\' + name, settings)

            self.atlas.endRender()
            zipper.zipFiles(path, True)

        except Exception as ex:
            print(ex)

        finally:
            self.clearFilter()

    def generateComposer(self, basemap, basic=False, materia_organica=False):
        """
        Lanza la generación del layout.
        """
        if basic:
            self.layoutGeneratorBasico(basemap=basemap)
        else:
            self.layoutGeneratorPreescripcion(basemap=basemap, materia_organica=materia_organica)

    def clearFilter(self):
        """
        Guarda el TXT si procede, limpia filtros y elimina el logo temporal.
        """
        try:
            if self.txt_export_path:
                self.writeLotesTxt(self.txt_export_path)

            for x in self.layers:
                layer = self.layers[x]
                layer.setSubsetString('')

            if self.temp_logo_path and os.path.exists(self.temp_logo_path):
                try:
                    os.remove(self.temp_logo_path)
                except Exception:
                    pass

        except Exception as ex:
            QgsMessageLog.logMessage('{}'.format(ex), 'aGrae GIS', level=Qgis.Critical)

    def layoutBasicogenerator(self, basemap, preview=False, printer=False):
        """
        Método legacy sin uso actual.
        """
        basemap = self.tools.getBaseMap(basemap, self.basemaps)
        QgsProject.instance().addMapLayer(basemap, False)
        self.getDistData(idcampania=self.idcampania, idexplotacion=self.idexplotacion)

        titleFont = QFont('Arial', 12, 1, False)
        titleFont.setBold(True)
        subGroupFont = QFont('Arial', 10, 1, False)
        subGroupFont.setBold(True)
        font = QFont('Arial', 10, 1, False)

        legend_style = QgsLegendStyle()
        legend_style.setFont(font)
        legend_style.setMargin(QgsLegendStyle.Left, 3)

        legend_style_title = QgsLegendStyle()
        legend_style_title.setFont(titleFont)
        legend_style.setMargin(QgsLegendStyle.Bottom, 10)

        legend_style_subGroup = QgsLegendStyle()
        legend_style_subGroup.setFont(subGroupFont)

        pass