import base64
from io import BytesIO
from PIL import Image
import os
import sys

from qgis.PyQt.QtXml import QDomDocument

from qgis.core import *
from qgis.gui import QgsFieldComboBox
from qgis.utils import iface

from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSignal, QSettings, QDateTime, QThreadPool
from PyQt5.QtGui import QColor,QFont

from ..tools import aGraeTools
from ..db import agraeDataBaseDriver


class aGraeComposerTools():
    def __init__(self,layers,idcampania,idexplotacion) -> None:
        self.layers = layers
        self.idcampania = idcampania
        self.idexplotacion = idexplotacion
        self.plugin_dir = os.path.dirname(__file__)
        self.settings = QSettings('agrae','dbConnection')

        self.tools = aGraeTools()
        self.conn = agraeDataBaseDriver().connection()
        self.nombre_explotacion = str
        self.direccion_explotacion = str
        self.basemaps = {
          
            'Esri Satelite' : {
                'url': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/%7Bz%7D/%7By%7D/%7Bx%7D',
                'options': 'crs=EPSG:3857&format&type=xyz&url=https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/%7Bz%7D/%7By%7D/%7Bx%7D&zmax=20&zmin=0'
            },
            'Google Satelite' : {
                'url': 'https://mt1.google.com/vt/lyrs=s&x=%7Bx%7D&y=%7By%7D&z=%7Bz%7D',
                'options': 'type=xyz&zmin=0&zmax=20&url=https://mt1.google.com/vt/lyrs%3Ds%26x%3D{x}%26y%3D{y}%26z%3D{z}'
            },
            'PNOA Ortofoto' : {
                'url': 'contextualWMSLegend=0&crs=EPSG:4326&dpiMode=7&featureCount=10&format=image/png&layers=OI.OrthoimageCoverage&styles' ,
                'options': 'url=https://www.ign.es/wms-inspire/pnoa-ma'
            },
            'Parcelas Catastro' : {
                'url': 'contextualWMSLegend=1&crs=EPSG:4326&dpiMode=7&featureCount=10&format=image/png&layers=CP.CadastralParcel&styles' ,
                'options': 'url=http://ovc.catastro.meh.es/cartografia/INSPIRE/spadgcwms.aspx'
            }

        }
        self.panels_path = self.settings.value('paneles_path')
        self.reportes_path = self.settings.value('reporte_path')
        pass

    def setLayersToMap(self,mapItems,layers,basemap):
        
        map_1 = mapItems[0]
        map_1_settings = QgsMapSettings()
        map_1_settings.setLayers([layers[1],layers[0],basemap])
        map_1.setLayers([layers[1],layers[0],basemap])
        clippingSettings = QgsLayoutItemMapAtlasClippingSettings(map_1)
        clippingSettings.setEnabled(True)
        clippingSettings.setLayersToClip([layers[1]])
        clippingSettings.setRestrictToLayers(True)
        if len(mapItems) >= 2:
            map_2 = mapItems[1]
            map_2_settings = QgsMapSettings()
            map_2_settings.setLayers([layers[2],layers[0],basemap])
            map_2.setLayers([layers[2],layers[0],basemap])
            clippingSettings = QgsLayoutItemMapAtlasClippingSettings(map_2)
            clippingSettings.setEnabled(True)
            clippingSettings.setLayersToClip([layers[2]])
            clippingSettings.setRestrictToLayers(True)

        pass 
    def setLegendsToLayout(self,legendItem,layers,labels):
        titleFont = QFont('Arial',12,1,False)
        titleFont.setBold(True)
        subGroupFont = QFont('Arial',10,1,False)
        subGroupFont.setBold(True)
        font = QFont('Arial',10,1,False)


        legend =  legendItem
        legend.rstyle(QgsLegendStyle.Title).setFont(titleFont)
        legend.rstyle(QgsLegendStyle.Title).setMargin(QgsLegendStyle.Bottom,3)
        legend.rstyle(QgsLegendStyle.Subgroup).setFont(subGroupFont)
        legend.rstyle(QgsLegendStyle.Subgroup).setMargin(QgsLegendStyle.Bottom,3)
        legend.rstyle(QgsLegendStyle.SymbolLabel).setFont(font)
        legend.rstyle(QgsLegendStyle.SymbolLabel).setMargin(QgsLegendStyle.Left,3)
        # txt_legend.setStyle(QgsLegendStyle.Title,legend_style_title)
        # txt_legend.setStyle(QgsLegendStyle.Subgroup,legend_style_subGroup)
        # txt_legend.setStyle(QgsLegendStyle.SymbolLabel,legend_style)

        legend_model = legend.model() 
        legend_root = legend_model.rootGroup()
        legend_root.clear()

        for l in layers:
            legend_root.addLayer(l)

        # legend_root.addLayer(layers[_CEAP90_TXT])

        for tr,layer,label in zip(legend_root.children(),layers,labels):
            if tr.name() == layer.name():
                tr.setCustomProperty('legend/title-label',label)
                # tr.setCustomProperty('legend/')
        
        # pc.insertPage(QgsLayoutItemPage(),0)
        
        
        
        pass
    def getDistData(self,idcampania,idexplotacion) -> None:
        with self.conn.cursor() as cursor: 
            try:
                sql = '''with campania as (select distinct idcampania,idexplotacion from campaign.data where idcampania = {} and idexplotacion = {}),
                data as (select ex.nombre as explotacion, ex.direccion,  d.imagen as logo from campania c 
                join agrae.agricultor ag on ag.idexplotacion = c.idexplotacion
                join agrae.distribuidor d on d.iddistribuidor = ag.iddistribuidor
                join agrae.explotacion ex on ex.idexplotacion = c.idexplotacion
                )
                select * from data'''.format(idcampania,idexplotacion)
                
                cursor.execute(sql)
                data = cursor.fetchone()
                out = open(os.path.join(os.path.dirname(__file__),'img/dist_logo.png'),'wb')
                out.write(data[2])
                self.nombre_explotacion = data[0].upper()
                self.direccion_explotacion = data[1].upper()
                
                # image = Image.open(BytesIO(data))
                # print(image)
                # return image

            except TypeError as te:
                QgsMessageLog.logMessage('{}'.format(te), 'aGrae GIS', level=Qgis.Critical)      
            except Exception as ex:
                QgsMessageLog.logMessage('{}'.format(ex), 'aGrae GIS', level=Qgis.Critical)
            finally:
                out.close()
                pass
    def setTextOverElements(self,elements,text):
        try:
            for e in elements:
                e.setText(text.upper())
        except:
            pass
    def layoutGenerator(self,
            basemap,
            preview=False,
            printer=False):
        
        titleFont = QFont('Arial',12,1,False)
        titleFont.setBold(True)
        subGroupFont = QFont('Arial',10,1,False)
        subGroupFont.setBold(True)
        font = QFont('Arial',10,1,False)

        

        legend_style = QgsLegendStyle()
        legend_style.setFont(font)
        legend_style.setMargin(QgsLegendStyle.Left,3)
        legend_style_title = QgsLegendStyle()
        legend_style_title.setFont(titleFont)
        legend_style.setMargin(QgsLegendStyle.Bottom,10)
        legend_style_subGroup = QgsLegendStyle()
        legend_style_subGroup.setFont(subGroupFont)



        # _LOTES_ = self.layers['atlas']
        # _NITROGENO_ = self.layers['Nitrogeno']
        # _FOSFORO_ = self.layers['Fosforo']
        # _POTASIO_ = self.layers['potasio`']
        # _AMBIENTES_ = self.layers['Ambientes']
        # _PH_ = self.layers['PH']
        # _CONDUCTIVIDAD_ = self.layers['Conductividad Electrica']
        # _UNIDADES_I_ = self.layers['Fert Variable Intraparcelaria']
        # _UNIDADES_II_ = self.layers['Fert Variable Intraparcelaria']
        # _CALCIO_ = self.layers['Calcio']
        # _MAGNESIO_ = self.layers['Magnesio']
        # _SODIO_ = self.layers['Sodio']
        # _AZUFRE_ = self.layers['Azufre']
        # _CIC_ = self.layers['CIC']
        # _HIERRO_ = self.layers['Hierro']
        # _MANGANESO_ = self.layers['Manganeso']
        # _ALUMINIO_ = self.layers['Aluminio']
        # _BORO_ = self.layers['Boro']
        # _CINQ_ = self.layers['Cinq']
        # _COBRE_ = self.layers['Cobre']
        # _MATERIA_ORGANICA_ = self.layers['Materia Organica']
        # _REL_CN_ = self.layers['Relacion CN']
        # _SEGMENTOS_ = self.layers['Segmentos']

        # _CEAP36_TXT = 'CEAP36 TEXTURA'
        # _CEAP90_TXT = 'CEAP90 TEXTURA'
        # _CEAP36_INF = 'CEAP36 INFILTRACION'
        # _CEAP90_INF = 'CEAP90 INFILTRACION'


        basemap = self.tools.getBaseMap(basemap,self.basemaps)
        QgsProject.instance().addMapLayer(basemap,False)
        self.getDistData(idcampania=self.idcampania,idexplotacion=self.idexplotacion)

        
        # print(self.layers)




        project = QgsProject.instance()
        manager = project.layoutManager()
        layout = QgsPrintLayout(project)
        layoutName = "Preescripcion"
        layouts_list = manager.printLayouts()
        for layout in layouts_list:
            if layout.name() == layoutName:
                manager.removeLayout(layout)
        
        layout = QgsPrintLayout(project)
        layout.initializeDefaults()                 #create default map canvas
        layout.setName(layoutName)
        manager.addLayout(layout)

        self.atlas = layout.atlas()
        self.atlas.setCoverageLayer(self.layers['Atlas'])
        self.atlas.setPageNameExpression('lote')
        self.atlas.setFilenameExpression('lote')

        self.atlas.refreshCurrentFeature()
        self.atlas.updateFeatures()
        self.atlas.setEnabled(True)
        self.atlas.seekTo(0)

        feature = self.atlas.coverageLayer().getFeature(self.atlas.currentFeatureNumber()+1)

        pc = layout.pageCollection()
        # pc.page(0).setPageSize('A4', QgsLayoutItemPage.Orientation.Portrait)
        for l in range(0,14):
            pc.addPage(QgsLayoutItemPage(layout=layout))
            pc.page(l).setPageSize('A4', QgsLayoutItemPage.Orientation.Portrait)


        tmpfile = self.plugin_dir + '/templates/prescripcion_dev.qpt'
        with open(tmpfile) as f:
            template_content = f.read()
            
        doc = QDomDocument()
        doc.setContent(template_content)
        items, _ = layout.loadFromTemplate(doc, QgsReadWriteContext(), False)


        logos = [i for i in items if isinstance(i,QgsLayoutItemPicture) and i.id() == 'exp_logo']
        direcciones = [i for i in items if isinstance(i,QgsLayoutItemLabel) and i.id() == 'exp_dir']
        nombres_exp = [i for i in items if isinstance(i,QgsLayoutItemLabel) and i.id() == 'exp_name']
        nombres_lotes = [i for i in items if isinstance(i,QgsLayoutItemLabel) and i.id() == 'lote_nom']
        
        for l in logos:
            l.setPicturePath(os.path.join(os.path.dirname(__file__),'img/dist_logo.png'))


        self.setTextOverElements(nombres_exp,self.nombre_explotacion.upper())
        self.setTextOverElements(direcciones,self.direccion_explotacion.upper())
        


        # # dist_logo_item.setPicturePath(os.path.join(os.path.dirname(__file__),'ui/img/dist_logo.png'))

        # #* MAPAS
       



        lotes = self.layers['Atlas']

        
        self.setLayersToMap([layout.itemById('ceap36_txt'),layout.itemById('ceap90_txt')],[lotes,self.layers['Ceap36 Textura'],self.layers['Ceap36 Infiltracion']],basemap) #*  PAG 01
        self.setLayersToMap([layout.itemById('ceap36_inf'),layout.itemById('ceap90_inf')],[lotes,self.layers['Ceap90 Textura'],self.layers['Ceap90 Infiltracion']],basemap) #* PAG 02
        self.setLayersToMap([layout.itemById('map_nitrogeno'),layout.itemById('map_fosforo')],[lotes,self.layers['Nitrogeno'],self.layers['Fosforo']],basemap) #* PAG 03
        self.setLayersToMap([layout.itemById('map_potasio'),layout.itemById('map_ambientes')],[lotes,self.layers['Potasio'],self.layers['Ambientes']],basemap) #* PAG 04
        self.setLayersToMap([layout.itemById('map_ph'),layout.itemById('map_conductividad')],[lotes,self.layers['PH'],self.layers['Conductividad Electrica']],basemap) #* PAG 05
        self.setLayersToMap([layout.itemById('map_06')],[lotes,self.layers['Fert Variable Intraparcelaria']],basemap) #* PAG 06
        self.setLayersToMap([layout.itemById('map_07_01')],[lotes,self.layers['Fert Variable Intraparcelaria']],basemap) #* PAG 07_01
        self.setLayersToMap([layout.itemById('map_07_02')],[lotes,self.layers['Fert Variable Parcelaria']],basemap) #* PAG 07_02
        self.setLayersToMap([layout.itemById('map_calcio'),layout.itemById('map_magnesio')],[lotes,self.layers['Calcio'],self.layers['Magnesio']],basemap) #* PAG 08
        self.setLayersToMap([layout.itemById('map_sodio'),layout.itemById('map_azufre')],[lotes,self.layers['Sodio'],self.layers['Azufre']],basemap) #* PAG 09
        self.setLayersToMap([layout.itemById('map_cic'),layout.itemById('map_segmentos')],[lotes,self.layers['CIC'],self.layers['Segmentos']],basemap) #* PAG 10
        self.setLayersToMap([layout.itemById('map_hierro'),layout.itemById('map_manganeso')],[lotes,self.layers['Hierro'],self.layers['Manganeso']],basemap) #* PAG 14
        self.setLayersToMap([layout.itemById('map_aluminio'),layout.itemById('map_boro')],[lotes,self.layers['Aluminio'],self.layers['Boro']],basemap) #* PAG 15
        self.setLayersToMap([layout.itemById('map_cinq'),layout.itemById('map_cobre')],[lotes,self.layers['Cinq'],self.layers['Cobre']],basemap) #* PAG 16
        # self.setLayersToMap([layout.itemById('map_materia_organica'),layout.itemById('map_rel_cn')],[lotes,self.layers['Materia Organica'],self.layers['Relacion CN']],basemap) #* PAG 17
        # # self.setLayersToMap([layout.itemById('map_cic')],[layers[_LOTES_],layers[_CIC_]],basemap) #* PAG 10
        
        # # print(layers[_UNIDADES_I_])

        
        
        # #* LEYENDAS 
        self.setLegendsToLayout(layout.itemById('legend_txt'),[self.layers['Ceap36 Textura']],['Texturas'])
        self.setLegendsToLayout(layout.itemById('legend_inf'),[self.layers['Ceap36 Infiltracion']],['Infiltración [mm/h]'])
        self.setLegendsToLayout(layout.itemById('legend_03'),[self.layers['Nitrogeno'],self.layers['Fosforo']],['Nitrogeno','Fosforo'])
        self.setLegendsToLayout(layout.itemById('legend_04'),[self.layers['Potasio'],self.layers['Ambientes']],['Potasio','Ambientes Productivos'])
        self.setLegendsToLayout(layout.itemById('legend_05'),[self.layers['PH'],self.layers['Conductividad Electrica']],['pH','Conductividad Eléctrica'])
        self.setLegendsToLayout(layout.itemById('legend_06'),[self.layers['Fert Variable Intraparcelaria']],['Unidades Fertilizantes'])
        self.setLegendsToLayout(layout.itemById('legend_07_01'),[self.layers['Fert Variable Intraparcelaria']],['Unidades Fertilizantes'])
        self.setLegendsToLayout(layout.itemById('legend_07_02'),[self.layers['Fert Variable Parcelaria']],['UF Unica'])
        self.setLegendsToLayout(layout.itemById('legend_08'),[self.layers['Calcio'],self.layers['Magnesio']],['Calcio','Magnesio'])
        self.setLegendsToLayout(layout.itemById('legend_09'),[self.layers['Sodio'],self.layers['Azufre']],['Sodio','Azufre'])
        self.setLegendsToLayout(layout.itemById('legend_10'),[self.layers['CIC']],['CIC'])
        self.setLegendsToLayout(layout.itemById('legend_14'),[self.layers['Hierro'],self.layers['Manganeso']],['Hierro','Manganeso'])
        self.setLegendsToLayout(layout.itemById('legend_15'),[self.layers['Aluminio'],self.layers['Boro']],['Aluminio','Boro'])
        self.setLegendsToLayout(layout.itemById('legend_16'),[self.layers['Cinq'],self.layers['Cobre']],['Cinq','Cobre'])
        # self.setLegendsToLayout(layout.itemById('legend_17'),[self.layers['Materia Organica'],self.layers['Relacion CN']],['Materia Organica','Relacion Carbono/Nitrogeno'])


        cic_table = layout.itemById('cic_table')
        table_item = cic_table.multiFrame()
        

       

        self.atlas.featureChanged.connect(lambda: self.moveCanvas(
            layout,
            layout.itemById('ceap36_inf'),
            self.atlas,
            nombres_lotes,
            self.layers,
            [layout.itemById('panel_00'),layout.itemById('panel_02'),layout.itemById('panel_01'),layout.itemById('panel_03')],
            table_item
            ))

        # if preview:
        iface.openLayoutDesigner(layout)
        
        # if printer:
        #     self.exportAtlasReport()

        

       






        

        # pass
    def moveCanvas(self,
                   layout,
                   map:QgsLayoutItemMap,
                   atlas:QgsLayoutAtlas,
                   nombresLotes,
                   layers,
                   panels,
                   table
                   ):
            

            feature = atlas.coverageLayer().getFeature(atlas.currentFeatureNumber()+1)
            nombre_lote = feature.attribute('lote')
            for l in layers:
                if l != 'Atlas':
                    layers[l].setSubsetString('''  "lote"= '{}' '''.format(nombre_lote))
                    if l == 'CIC':
                        cic_layer = layers[l]
            

            table.setVectorLayer(cic_layer)
            table.setDisplayedFields(['segmento'.upper(),'cic','ca','mg','k','na'])
            c_0 = table.columns()[0]
            c_0.setHeading('Segmento')

            table.refreshAttributes()

         
            self.setTextOverElements(nombresLotes,nombre_lote)

            # print(self.panels_path)
            
            panels[0].setPicturePath(self.panels_path+'/Panel00'+nombre_lote+'.png')
            panels[1].setPicturePath(self.panels_path+'/Panel02'+nombre_lote+'.png')
            panels[2].setPicturePath(self.panels_path+'/Panel01'+nombre_lote+'.png')
            panels[3].setPicturePath(self.panels_path+'/Panel03'+nombre_lote+'.png')
            
            extent = map.extent()
            atlas.coverageLayer().getFeature(atlas.currentFeatureNumber()+1)
            iface.mapCanvas().setExtent(extent)  

    def ComposerPrintWorker(self):
        self.tools.UserMessages('Generando archivos de Preescripcion, este proceso puede tardar varios minutos.\nPorfavor espere un momento.')
        # print('worker')
        worker = Worker(lambda: self.layoutGenerator(printer=True))
        # worker.signals.finished.connect(lambda: self.tools.UserMessages('Archivos generados correctamente',level=Qgis.Success))
        worker.signals.finished.connect(lambda: iface.messageBar().pushMessage("aGrae GIS", 'Archivos generados correctamente', level=Qgis.Success))
        self.threadpool.start(worker)
    def exportAtlasReport(self):
        """exportAtlasReport Print layout aGrae
        """        
        directory = list(set([f['explotacion'] for f in self.atlas.coverageLayer().getFeatures()]))[0]
        directory = directory.replace(' ','_')
        path = os.path.join(self.reportes_path,directory+'_' + QDateTime.currentDateTime().toString('yyyyMMddHHmmss'))
        zipper = AgraeZipper()
        try:
            os.makedirs(path)
            self.atlas.beginRender()
            settings = QgsLayoutExporter.PdfExportSettings()
            settings.appendGeoreference = False
            settings.simplifyGeometries = True
            
            exporter = QgsLayoutExporter(self.atlas.layout())
            
            for i in range(0,self.atlas.count()):
                self.atlas.seekTo(i)
                name = self.atlas.currentFilename().replace(' ','_')
                name = name + '_' + QDateTime.currentDateTime().toString('yyyyMMddHHmmss')+".pdf"
                exporter.exportToPdf(path+r'\\'+name,settings)
                # self.tools.UserMessages('Reporte del Lote <b>{}</b> generado correctamente'.format(name), 5, Qgis.Success)
            self.atlas.endRender()
            zipper.zipFiles(path,True)
        except Exception as ex:
            print(ex)

    def generateComposer(self,basemap):
        self.layoutGenerator(basemap=basemap)
