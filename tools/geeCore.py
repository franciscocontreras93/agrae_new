from math import sin
import os
import signal
import ee
import datetime
import tempfile
import processing

from typing import Union, Annotated

from urllib import request

from qgis.utils import iface
from qgis.core import *

from ..tools import aGraeTools

#from qgis.PyQt.QtCore import QSettings

class GEETools:
    def __init__(self):
        pass

    def getGeometry(self,buffer:int,feature:QgsFeature):

        coords = []
        geom = feature.geometry()
        
        poly = geom.asMultiPolygon()
        features = [poly[f][0] for f in range(len(poly))]
        for f in features:
            for point in f:
                coords.append([point.x(),point.y()])  

        geometry = ee.Geometry.MultiPolygon(coords)
        geometry = geometry.buffer(buffer)
        
        return geometry
    
    def addIndexComposite(self,image,bands:Annotated[list[str],2],name:str='nd'): return image.addBands(image.normalizedDifference(bands).rename(name))
    
    def clipScene(self,image,geometry): return image.clip(geometry)

    def getScene (self,geometry:ee.Geometry.MultiPolygon,since:ee.Date,until:ee.Date,bands:Annotated[list[str],2]=['B8','B4'],max_clouds:int=5):
        
        imageCollection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterBounds(geometry).filterMetadata('CLOUDY_PIXEL_PERCENTAGE', 'less_than', max_clouds).filter(ee.Filter.calendarRange(until,since,'year'))
        # imageCollection = ee.ImageCollection('COPERNICUS/S2_SR').filterBounds(self.geometry).filterMetadata('CLOUDY_PIXEL_PERCENTAGE', 'less_than', self._max_clouds).filter(ee.Filter.calendarRange(self._years.get(0),self._years.get(-1),'year'))
        scene = imageCollection.map(lambda image: self.addIndexComposite(image,bands,'nd'))
        scene = scene.select(['nd'])
        scene = scene.map(lambda image: self.clipScene(image,geometry))
        return  scene
    
    def getProcessedScene(self,years:ee.List,scene:ee.ImageCollection):
        processed = years.map(lambda y: self.processingScene(y,scene))
        return processed
    
    def processingScene(self,y,scene: ee.ImageCollection):
        return scene.filter(ee.Filter.calendarRange(y, y, 'year')).reduce(ee.Reducer.max()) 
    
    def getConvolve(self,image:ee.Image,units:int,magnitude:int,radius:int):
        units = {
            1 : 'pixels',
            2 : 'meters'
        }
        filter = ee.Kernel.square(
          radius= radius,
          units= units[units],
          magnitude = magnitude,
          normalize = True
        )
        return image.convolve(filter)

    def getReclassifiedImage(self,image,radius:int,magnitude:int,units:int,ndre:bool):
        NDVIConvolve = self.getConvolve(
            image = image,
            radius= radius,
            magnitude= magnitude,
            units= units
        )
        
        percentile = self.getPercentiles(NDVIConvolve)
        if ndre:
            expression = ee.String('(b(0) <= ').cat(ee.Number(percentile.get('nd_max_p14').getInfo()).format()).cat(') ? 14 : (b(0) <= ').cat(ee.Number(percentile.get('nd_max_p28').getInfo()).format()).cat(') ? 28 : (b(0) <= ').cat(ee.Number(percentile.get('nd_max_p42').getInfo()).format()).cat(') ? 42 : (b(0) <= ').cat(ee.Number(percentile.get('nd_max_p56').getInfo()).format()).cat(') ? 56 : (b(0) <= ').cat(ee.Number(percentile.get('nd_max_p70').getInfo()).format()).cat(') ? 70 : (b(0) <= ').cat(ee.Number(percentile.get('nd_max_p84').getInfo()).format()).cat(') ? 84 : 100');reclass = NDVIConvolve.expression(expression) 
        else: 
            expression = ee.String('(b(0) <= ').cat(ee.Number(percentile.get('nd_max_p25').getInfo()).format()).cat(') ? 20 : (b(0) < ').cat(ee.Number(percentile.get('nd_max_p50').getInfo()).format()).cat(') ? 40 : 60')

        reclass = NDVIConvolve.expression(expression)
        return reclass
    

    def maskClouds(self,image,feature): 
        scl = image.select('SCL')
        clouds =  scl.eq(3).Or(scl.eq(8)).Or(scl.eq(9)).Not()

        cloud_area = clouds.reduceRegion(reducer=ee.Reducer.sum(),geometry=feature, scale=10,maxPixels=1e8).get('SCL')

        roiArea = feature.area().divide(10000)
        cloudPercentage = ee.Number(cloud_area).divide(roiArea).multiply(100)

        return image.set('cloud_percentage', cloudPercentage)
    
    def maskS2Clouds(self,image): 
        qa = image.select('QA60')
        cloudBitMask = 1 << 10;
        cirrusBitMask = 1 << 11;
        mask = qa.bitesiseAnd(cloudBitMask).eq(0).And(qa.bitesiseAnd(cirrusBitMask).eq(0))



        return image.updateMask(mask).divide(10000)

    def imageDownloadURL(self,image,feature):
        return image.getDownloadURL({
            'format':'GeoTIFF',
            'crs': 'EPSG:3857',
            'region': feature,
            'scale':10
            })
    
    def downloadImage(self,image,feature,name='temp'):
        temp = tempfile.gettempdir()
        url = image.getDownloadURL({
            'format':'GeoTIFF',
            'crs': 'EPSG:3857',
            'region': feature,
            'scale':10
            })
        downloadPath = os.path.join(tempfile.gettempdir(),f"{name}.tiff")
        request.urlretrieve(url,downloadPath)
        fileName = os.path.basename(downloadPath)
        r = QgsRasterLayer(downloadPath,'NDVI_GEE_Layer')
        QgsProject.instance().addMapLayer(r)
        return r
    
    def getLayerClip(self,feature) -> QgsVectorLayer:

        layer_clip = QgsVectorLayer('Multipolygon?crs=EPSG:4326','lote','memory')
        lote_feat = QgsFeature()
        lote_feat.setGeometry(feature.geometry())
        layer_clip.startEditing()
        layer_clip.addFeature(lote_feat)
        layer_clip.commitChanges()

        return layer_clip

    def postProcessing(self,ambientes_gee,ndvi_gee,layer_clip:QgsVectorLayer):

        QgsMessageLog.logMessage('**** Ejecutando algoritmo de Post-Procesamiento. ****' , 'aGrae GEE', level=Qgis.Info) 
        processing.runAndLoadResults("model:1_Post-procesado", {
        'capa_ambientes_gee':self.ambientesLayer,
        'capa_ndvi_gee':self.ndviLayer,
        # 'lote':QgsProcessingFeatureSourceDefinition(self._layer.source() , selectedFeaturesOnly=True, featureLimit=-1, geometryCheck=QgsFeatureRequest.GeometryAbortOnInvalid),
        'lote': layer_clip,
        'mapa_de_ambientes':'TEMPORARY_OUTPUT'})
        QgsMessageLog.logMessage('**** Mapa de Ambientes generado Correctamente ****' , 'aGrae GEE', level=Qgis.Info) 

class aGraeNDVI:
    def __init__(
        self,
        layer :QgsVectorLayer = iface.activeLayer(),
        year : int =datetime.datetime.today().year , 
        period: int = 5, 
        min_cloud : int = 20,
        kernel_radius : int = 20,
        kernel_magnitude : int = 1,
        kernel_units : int = 1,
        scale : int  = 1
        ): 

        """
        layer QgsVectorLayer default iface.activeLayer() := Capa que contiene el Lote SELECCIONADO a evaluar,
        year int default  20 := Anio desde el cual se realizara la Evaluacion, 
        period int default 5 := Numero de Anios a Evaluar desde el anio seleccionado ejemplo: year - 5 = 2019,
        min_cloud int default 20 := indice de nubosidad maxima aceptable en la escena,
        kernel_radius default  20 := Radio de busqueda del Kernel para la convolucion de la imagen,
        kernel_magnitude  int default 1 := Magnitud del Kernel para la convolucion de la imagen,
        scale int default 1 := Escala utilizada para la transformacion del raster a Poligonos.



        """     
        print('**** Inicializando Google-Earth-Engine ****')
        self.authenticated = False
        self.initialized = False

        if not self.authenticated or not self.initialized:
            self.authenticate()
        

        print('**** Google-Earth-Engine Inicializado Correctamente ****')
        
        self._layer = layer
        self._crs = self._layer.crs()
        self._destCrs = QgsCoordinateReferenceSystem(4326)
        transformation_crs = QgsCoordinateTransform(self._crs, self._destCrs, QgsProject.instance())
        
        self._year = year
        self._initial_date = self._year  - period
        
        self._years =  ee.List.sequence(self._initial_date, self._year)

        self._min_clouds = min_cloud
        
        self._kernel_radius = kernel_radius 
        self._kernel_magnitude = kernel_magnitude
        self._kernel_units = kernel_units
        
        self._scale = scale
        
        
    def authenticate(self):
        # if not self.authenticated:
        #     try: 
        #         ee.Authenticate(auth_mode='localhost')
        #         self.authenticated = True
        #     except:
        #         pass
        if not self.initialized:
            try:
                ee.Initialize(project='ee-agraeproyectos')
                self.initialized = True
            except:
                pass


       

    def getGeometry(self):
        
        feature = list(self._layer.selectedFeatures())[0]
        geom = feature.geometry()
        geom.transform(self._tr)
        
        if geom.isMultipart():
            poly = geom.asMultiPolygon() 
            n = len(poly[0][0])
            coords = [[poly[0][0][i][0],poly[0][0][i][1]] for i in range(n)]
        else:
            poly = geom.asPolygon() 
            coords = []
            for pol in poly:
                for c in pol:
                    coords.append([c[0],c[1]])
            
        geometry = ee.Geometry.Polygon(coords) 
        geometry = geometry.buffer(1)
        return geometry
    def addNDVI(self,image): return image.addBands(image.normalizedDifference(['B8','B4']))
    
    def processingScene(self,y):
        return self.sceneNDVI.filter(ee.Filter.calendarRange(y, y, 'year')).reduce(ee.Reducer.max()) 
        
    def getSceneNDVI (self):
        
        imageCollection = ee.ImageCollection('COPERNICUS/S2_SR').filterBounds(self.geometry).filterMetadata('CLOUDY_PIXEL_PERCENTAGE', 'less_than', self._min_clouds).filter(ee.Filter.calendarRange(self._years.get(0),self._years.get(-1),'year'))
        scene = imageCollection.map(self.addNDVI)
        scene = scene.select(['nd'])
        scene = scene.map(self.clipScene)
        return  scene
    
    def getProcessedScene(self):
        processed = self._years.map(lambda y: self.processingScene(y))
        return processed
    def clipScene(self,image):
        return image.clip(self.geometry)
        
    def getConvolve(self,image):
        units = {
            1 : 'pixels',
            2 : 'meters'
        }
        filter = ee.Kernel.square(
          radius= self._kernel_radius,
          units= units[self._kernel_units],
          magnitude = self._kernel_magnitude,
          normalize = True
        )
        return image.convolve(filter)
    
    def getPercentiles(self,image : ee.Image , percentiles : list = [25,50,75]):
        return image.reduceRegion(ee.Reducer.percentile(percentiles), self.geometry, 1)
    
#   
    def getReclassifiedImage(self,image):
        NDVIConvolve = self.getConvolve(
            image = image
        )
        
        percentile = self.getPercentiles(NDVIConvolve)
        expression = ee.String('(b(0) <= ').cat(ee.Number(percentile.get('nd_max_p25').getInfo()).format()).cat(') ? 20 : (b(0) <= ').cat(ee.Number(percentile.get('nd_max_p50').getInfo()).format()).cat(') ? 40 : 60')
        reclass = NDVIConvolve.expression(expression)
        return reclass
        
    def getAmbientes(self,image):
        ambientes = image.reduceToVectors(
          scale = self._scale,
          labelProperty = 'ambiente',
          bestEffort = False,
          geometry = self.geometry
          )
        
        return ambientes
          
    def imageDownloadURL(self,image):
        return image.getDownloadURL({
            'format':'GeoTIFF',
            'crs': 'EPSG:3857',
            'region': self.geometry,
            'scale':10
            })
    def vectorDownloadURL(self,vector):
        return vector.getDownloadURL('geojson')
        
        
    def downloadImage(self,image,name='temp'):
        temp = tempfile.gettempdir()
        url = self.imageDownloadURL(image)
        downloadPath = os.path.join(tempfile.gettempdir(),f"{name}.tiff")
        request.urlretrieve(url,downloadPath)
        fileName = os.path.basename(downloadPath)
        r = QgsRasterLayer(downloadPath,'NDVI_GEE_Layer')
#        QgsProject.instance().addMapLayer(r)
        return r
        
    def downloadVector(self,vector,name='vector_temp'):
        downloadPath = os.path.join(tempfile.gettempdir(),f"{name}.geojson")
        url=self.vectorDownloadURL(vector)
        request.urlretrieve(url,downloadPath)
        v = QgsVectorLayer(downloadPath,'Ambientes_GEE_Layer')
#        QgsProject.instance().addMapLayer(v)
        return v
    
        
    def executePostProcessing(self):

        print('**** Ejecutando algoritmo de Post-Procesamiento. ****')
        processing.runAndLoadResults("model:1_Post-procesado", {
        'capa_ambientes_gee':self.ambientesLayer,
        'capa_ndvi_gee':self.ndviLayer,
        'lote':QgsProcessingFeatureSourceDefinition(self._layer.source() , selectedFeaturesOnly=True, featureLimit=-1, geometryCheck=QgsFeatureRequest.GeometryAbortOnInvalid),
        'mapa_de_ambientes':'TEMPORARY_OUTPUT'})
        print('**** Mapa de Ambientes generado Correctamente ****')


    def run(self):
        print('**** Ejecutando algoritmo de Pre-Procesamiento en GEE. ****\n**** Este proceso puede tardar algunos minutos. ****')
        self.geometry = self.getGeometry()
        self.sceneNDVI = self.getSceneNDVI()
        self.processed = ee.ImageCollection.fromImages(self.getProcessedScene())
        self.NDVImax = self.processed.median()
        self.reclassified = self.getReclassifiedImage(self.NDVImax)
        self.ambientes = self.getAmbientes(self.reclassified)
        
        self.ndviLayer = self.downloadImage(self.NDVImax)
        self.ambientesLayer = self.downloadVector(self.ambientes)
        
        print('**** Pre-Procesamiento Exitoso ****')
        
        self.executePostProcessing()



class aGraeNDVIMulti:
    def __init__(
        self,
        layer : QgsVectorLayer,
        feature : QgsFeature,
        crs = QgsCoordinateReferenceSystem,
        year : int =datetime.datetime.today().year ,
        period: int = 5, 
        max_clouds : int = 20,
        buffer_radius : int = 5,
        kernel_radius : int = 20,
        kernel_units : int = 1,
        kernel_magnitude : int = 1,
        scale : int  = 1
        ): 
#        print('**** Inicializando Google-Earth-Engine ****')
#        ee.Authenticate(auth_mode='localhost')

        self.tools = GEETools()
       
        self._feature = feature
        # self._layer = layer
        # self._crs = self._layer.crs()
        self._crs = QgsCoordinateReferenceSystem(4326)
        self._destCrs = QgsCoordinateReferenceSystem(4326)
        self._tr = QgsCoordinateTransform(QgsCoordinateReferenceSystem(4326), self._destCrs, QgsProject.instance())
        
        self._year = year
        self._initial_date = self._year  - period

        self._years =  ee.List.sequence(self._initial_date, self._year)
        self._buffer_radius = buffer_radius 
        self._kernel_radius = kernel_radius 
        self._kernel_magnitude = kernel_magnitude
        self._kernel_units = kernel_units
        
        self._scale = scale
        self._max_clouds = max_clouds

        ee.Initialize(project='ee-agraeproyectos')
        QgsMessageLog.logMessage('*** Google Earth Engine Iniciado Correctamente ***' , 'aGrae GEE', level=Qgis.Info) 
        QgsMessageLog.logMessage(f'*** {self._feature}***' , 'aGrae GEE', level=Qgis.Info) 
        QgsMessageLog.logMessage(f'*** {self._crs}***' , 'aGrae GEE', level=Qgis.Info) 
                
    def getGeometry(self,feature):
        
        coords = []
        geom = feature.geometry()
        geom.transform(self._tr)
        
        poly = geom.asMultiPolygon()
        features = [poly[f][0] for f in range(len(poly))]
        for f in features:
            for point in f:
                coords.append([point.x(),point.y()])  

        geometry = ee.Geometry.MultiPolygon(coords)
        geometry = geometry.buffer(self._buffer_radius)
        
        return geometry
    
    def addNDVI(self,image): return image.addBands(image.normalizedDifference(['B8','B4']))
    
    def processingScene(self,y):
        return self.sceneNDVI.filter(ee.Filter.calendarRange(y, y, 'year')).reduce(ee.Reducer.max()) 
        
    def getSceneNDVI (self):
        
        imageCollection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterBounds(self.geometry).filterMetadata('CLOUDY_PIXEL_PERCENTAGE', 'less_than', self._max_clouds).filter(ee.Filter.calendarRange(self._years.get(0),self._years.get(-1),'year'))
        # imageCollection = ee.ImageCollection('COPERNICUS/S2_SR').filterBounds(self.geometry).filterMetadata('CLOUDY_PIXEL_PERCENTAGE', 'less_than', self._max_clouds).filter(ee.Filter.calendarRange(self._years.get(0),self._years.get(-1),'year'))
        scene = imageCollection.map(lambda image: self.tools.addIndexComposite(image,['B8','B4'],'nd'))
        scene = scene.select(['nd'])
        scene = scene.map(lambda image: self.tools.clipScene(image,self.geometry))
        return  scene
    
    def getProcessedScene(self):
        processed = self._years.map(lambda y: self.processingScene(y))
        return processed
    def clipScene(self,image):
        return image.clip(self.geometry)
        
    def getConvolve(self,image):
        units = {
            1 : 'pixels',
            2 : 'meters'
        }
        filter = ee.Kernel.square(
          radius= self._kernel_radius,
          units= units[self._kernel_units],
          magnitude = self._kernel_magnitude,
          normalize = True
        )
        return image.convolve(filter)
    
    def getPercentiles(self,image : ee.Image , percentiles : list = [25,50,75]):
        return image.reduceRegion(ee.Reducer.percentile(percentiles), self.geometry, 1)
    
#   
    def getReclassifiedImage(self,image):
        NDVIConvolve = self.getConvolve(
            image = image
        )
        
        percentile = self.getPercentiles(NDVIConvolve)
        expression = ee.String('(b(0) <= ').cat(ee.Number(percentile.get('nd_max_p25').getInfo()).format()).cat(') ? 20 : (b(0) < ').cat(ee.Number(percentile.get('nd_max_p50').getInfo()).format()).cat(') ? 40 : 60')
        reclass = NDVIConvolve.expression(expression)
        return reclass
        
    def getAmbientes(self,image):
        ambientes = image.reduceToVectors(
          scale = self._scale,
          labelProperty = 'ambiente',
          bestEffort = False,
          geometry = self.geometry
          )
        
        return ambientes
          
    def imageDownloadURL(self,image):
        return image.getDownloadURL({
            'format':'GeoTIFF',
            'crs': 'EPSG:3857',
            'region': self.geometry,
            'scale':10
            })
    def vectorDownloadURL(self,vector):
        return vector.getDownloadURL('geojson')
        
        
    def downloadImage(self,image,name='temp'):
        temp = tempfile.gettempdir()
        url = self.imageDownloadURL(image)
        downloadPath = os.path.join(tempfile.gettempdir(),f"{name}.tiff")
        request.urlretrieve(url,downloadPath)
        fileName = os.path.basename(downloadPath)
        r = QgsRasterLayer(downloadPath,'NDVI_GEE_Layer')
        # QgsProject.instance().addMapLayer(r)
        return r
        
    def downloadVector(self,vector,name='vector_temp'):
        downloadPath = os.path.join(tempfile.gettempdir(),f"{name}.geojson")
        url=self.vectorDownloadURL(vector)
        request.urlretrieve(url,downloadPath)
        v = QgsVectorLayer(downloadPath,'Ambientes_GEE_Layer')
        # QgsProject.instance().addMapLayer(v)
        return v
    
        
    def execute(self,layer_clip:QgsVectorLayer):

        QgsMessageLog.logMessage('**** Ejecutando algoritmo de Post-Procesamiento. ****' , 'aGrae GEE', level=Qgis.Info) 
        processing.runAndLoadResults("model:1_Post-procesado", {
        'capa_ambientes_gee':self.ambientesLayer,
        'capa_ndvi_gee':self.ndviLayer,
        # 'lote':QgsProcessingFeatureSourceDefinition(self._layer.source() , selectedFeaturesOnly=True, featureLimit=-1, geometryCheck=QgsFeatureRequest.GeometryAbortOnInvalid),
        'lote': layer_clip,
        'mapa_de_ambientes':'TEMPORARY_OUTPUT'})
        QgsMessageLog.logMessage('**** Mapa de Ambientes generado Correctamente ****' , 'aGrae GEE', level=Qgis.Info) 


    def run(self):
        QgsMessageLog.logMessage('**** Ejecutando algoritmo de Pre-Procesamiento en GEE. ****\n**** Este proceso puede tardar algunos minutos. ****' , 'aGrae GEE', level=Qgis.Info) 
        
        # exp = QgsExpression('idexplotacion = {}'.format(self.idexplotacion))
        for feature in [f for f in self._layer.getFeatures()]:

            layer_clip = QgsVectorLayer('Multipolygon?crs=EPSG:4326','lote','memory')
            lote_feat = QgsFeature()
            lote_feat.setGeometry(feature.geometry())
            layer_clip.startEditing()
            layer_clip.addFeature(lote_feat)
            layer_clip.commitChanges()

            # self.geometry = self.getGeometry(feature)
            self.geometry = self.tools.getGeometry(self._buffer_radius,feature,self._tr)
            self.sceneNDVI = self.getSceneNDVI()
            self.processed = ee.ImageCollection.fromImages(self.getProcessedScene())
            self.NDVImax = self.processed.median()
            self.reclassified = self.getReclassifiedImage(self.NDVImax)
            self.ambientes = self.getAmbientes(self.reclassified)
            
            self.ndviLayer = self.downloadImage(self.NDVImax)
            self.ambientesLayer = self.downloadVector(self.ambientes)
            print('**** Pre-Procesamiento Exitoso ****')

            QgsMessageLog.logMessage('**** Pre-Procesamiento Exitoso ****' , 'aGrae GEE', level=Qgis.Info) 
            
            self.execute(layer_clip)
        

class aGraeNDRE:
    def __init__(self,
                layer :QgsVectorLayer = iface.activeLayer(),
                max_clouds : int = 20,
                buffer_radius : int = 5,
                kernel_radius : int = 20,
                kernel_units : int = 1,
                kernel_magnitude : int = 1,
                scale : int  = 1) -> None:
        
        self._layer = layer
        self._crs = self._layer.crs()
        self._destCrs = QgsCoordinateReferenceSystem(4326)
        self._tr = QgsCoordinateTransform(self._crs, self._destCrs, QgsProject.instance())
        self._buffer_radius = buffer_radius

        self.tools = GEETools()
        self.geometry = None

        self.today = ee.Date(datetime.datetime.today())
        self.startDate = ee.Date(datetime.datetime.now().date().replace(month=1, day=1).strftime('%Y-%m-%d'))
        pass

    def getGeometry(self,feature):
        
        coords = []
        geom = feature.geometry()
        geom.transform(self._tr)
        
        poly = geom.asMultiPolygon()
        features = [poly[f][0] for f in range(len(poly))]
        for f in features:
            for point in f:
                coords.append([point.x(),point.y()])  

        geometry = ee.Geometry.MultiPolygon(coords)
        geometry = geometry.buffer(self._buffer_radius)
        
        return geometry
    

    def getScene (self,):
        
        # imageCollection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterBounds(self.geometry).filterMetadata('CLOUDY_PIXEL_PERCENTAGE', 'less_than', self._max_clouds).filterDate(self.startDate,self.today)
        imageCollection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterBounds(self.geometry).filterDate(self.startDate,self.today)
        # scene = scene.select(['NDRE'])
        # scene = imageCollection.map(lambda image: self.tools.clipScene(image,self.geometry))
        # scene = scene.map(lambda image: self.tools.maskClouds(image,self.geometry))
        # scene = scene.map(lambda image: self.tools.addIndexComposite(image,['B8','B5'],'NDRE'))
        return  imageCollection 
    
    def run(self):
        QgsMessageLog.logMessage('**** Ejecutando algoritmo de Pre-Procesamiento en GEE. ****\n**** Este proceso puede tardar algunos minutos. ****' , 'aGrae GEE', level=Qgis.Info) 
        
        # exp = QgsExpression('idexplotacion = {}'.format(self.idexplotacion))
        for feature in [f for f in self._layer.getFeatures()]:

            layer_clip = QgsVectorLayer('Multipolygon?crs=EPSG:4326','lote','memory')
            lote_feat = QgsFeature()
            lote_feat.setGeometry(feature.geometry())
            layer_clip.startEditing()
            layer_clip.addFeature(lote_feat)
            layer_clip.commitChanges()

            # self.geometry = self.getGeometry(feature)
            self.geometry = self.tools.getGeometry(self._buffer_radius,feature,self._tr)
            self.scene_with_cloud_percentage = self.getScene()
            self.filteredCollection = self.scene_with_cloud_percentage.filter(ee.Filter.lte('cloud_percentage', 10))
            self.hasValidImages = self.filteredCollection.size().gt(0)

            self.latestImage =  ee.Image(ee.Algorithms.If(self.hasValidImages,self.filteredCollection.first(),ee.Image(0)))
            imageDate = ee.Date(self.latestImage.get('system:time_start')).format('YYYY-MM-dd')
            self.tools.downloadImage(self.latestImage,self.geometry)
            # print('Fecha de la imagen más reciente:', imageDate)


            # self.processed = ee.ImageCollection.fromImages(self.getProcessedScene())
            # self.NDVImax = self.processed.median()
            # self.reclassified = self.getReclassifiedImage(self.NDVImax)
            # self.ambientes = self.getAmbientes(self.reclassified)
            
            # self.ndviLayer = self.downloadImage(self.NDVImax)
            # self.ambientesLayer = self.downloadVector(self.ambientes)
            # print('**** Pre-Procesamiento Exitoso ****')

            # QgsMessageLog.logMessage('**** Pre-Procesamiento Exitoso ****' , 'aGrae GEE', level=Qgis.Info) 
            
            # self.execute(layer_clip)



class aGraeGEECore:
    
    def __init__(self):
        ee.Initialize(project='ee-agraeproyectos')
        self.tools = GEETools()

        pass

    def runAmbiente(self,feature: QgsFeature,bands:list, buffer: int,since:str,until:str,kernel_radius:int=5,kernel_magnitude:int=1,kernel_units:int=1,max_clouds:int=5):
        layer_clip = self.tools.getLayerClip(feature)
        since = ee.Date(since).get('year')
        until = ee.Date(until).get('year')
        self._years =  ee.List.sequence(until, since)
        self.geometry = self.tools.getGeometry(buffer,feature)
        self.scene = self.tools.getScene(
            geometry=self.geometry,
            since=since,
            until=until,
            bands=bands,
            max_clouds=max_clouds
        )
        self.processed = self.tools.getProcessedScene(self._years,self.scene)
        print(self.processed.getInfo())
        # self.NDVImax = self.processed.median()

        # self.reclassified = self.tools.getReclassifiedImage(self.NDVImax,kernel_radius,kernel_magnitude,kernel_units)
        # self.ambientes = self.getAmbientes(self.reclassified)
            
        # self.ndviLayer = self.downloadImage(self.NDVImax)
        # self.ambientesLayer = self.downloadVector(self.ambientes)
        # # print('**** Pre-Procesamiento Exitoso ****')

        # # QgsMessageLog.logMessage('**** Pre-Procesamiento Exitoso ****' , 'aGrae GEE', level=Qgis.Info) 
        
        # self.tools.postProcessing(self.ambientesLayer,self.ndviLayer,layer_clip)
        # QgsProject.instance().addMapLayer(layer_clip)
        

