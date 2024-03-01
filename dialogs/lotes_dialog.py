import datetime
import os
import csv
import requests
import json
import time


# from datetime import date
from psycopg2 import InterfaceError, errors, extras
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtCore import pyqtSignal, QSettings, QVariant, Qt,QSize
from qgis.PyQt.QtGui import QColor, QIcon, QPixmap
from qgis.core import *
from qgis.utils import iface
from qgis.PyQt.QtXml import QDomDocument
from ..db import agraeDataBaseDriver
from ..sql import aGraeSQLTools

lotesDialogUI, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'ui/lotes_dialog.ui'))

class LotesMainWindow(QDialog,lotesDialogUI):
    closingPlugin = pyqtSignal()
    _WIDTH = 600
    _HEIGHT = 400
    _FILTER_PROXY = QgsMapLayerProxyModel.VectorLayer

    def __init__(self,parent=None):
        super(LotesMainWindow, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle('Gestion de Lotes')
        self.conn = agraeDataBaseDriver().connection()
        self.updateDataBaseCombos()
        self.resize(self._WIDTH,self._HEIGHT)
        self.UIComponents()
        self.agraeSql = aGraeSQLTools()

    def UIComponents(self):
        self.comboLayers.setFilters(QgsMapLayerProxyModel.PolygonLayer)
        self.comboLayers.setExcludedProviders([])
        self.comboLayers.layerChanged.connect(self.updateLayerCombos)
        for c in [self.comboCamp,self.comboExp,self.comboCamp_2,self.comboExp_2]:

            c.setEditable(True)
            c.setInsertPolicy(QComboBox.NoInsert)
            c.completer().setCompletionMode(QCompleter.PopupCompletion)

        self.comboNombre.setFilters(QgsFieldProxyModel.String)
        self.comboCultivo.setFilters(QgsFieldProxyModel.String)
        self.comboProduccion.setFilters(QgsFieldProxyModel.Numeric)


        self.btn_create.clicked.connect(self.create)
        
    def updateDataBaseCombos(self):
        with self.conn.cursor(cursor_factory=extras.DictCursor) as cursor:
            try:
                cursor.execute('SELECT DISTINCT UPPER(nombre), idexplotacion  FROM agrae.explotacion ORDER BY UPPER(nombre)')
                # print(cursor.fetchall())
                data_exp = cursor.fetchall() 
                # print(data)
                # self.comboExplotaciones.addItems([ [e[1],e[0]] for e in data])
                cursor.execute('SELECT DISTINCT UPPER(nombre), id  FROM campaign.campanias ORDER BY id DESC')
                data_camp = cursor.fetchall()

                for e in data_exp: 
                    self.comboExp.addItem(e[0],e[1])
                    self.comboExp_2.addItem(e[0],e[1])

                for e in data_camp:
                    self.comboCamp.addItem(e[0],e[1])
                    self.comboCamp_2.addItem(e[0],e[1])
            except Exception as ex:
                raise ex

    def updateLayerCombos(self,layer:QgsVectorLayer):
        try:
            for c in [self.comboNombre,self.comboCultivo,self.comboProduccion,self.comboRegimen]:
                c.setLayer(layer)
                fields = layer.fields()
                self.setFieldsByName(self.comboNombre,fields,['lote','nombre'])
                self.setFieldsByName(self.comboCultivo,fields,['cultivo','nombre_cultivo'])
                self.setFieldsByName(self.comboProduccion,fields,['prod_esperada','produccion'])
                self.setFieldsByName(self.comboRegimen,fields,['regimen'])
        except:
            print('An exception occurred')
            


    def setFieldsByName(self,widget,fields:QgsFields,parameters:[str]):
        for field in fields:
            if field.name() in parameters:
                    widget.setField(field.name())
        pass
    

    def create(self):
        layer = self.comboLayers.currentLayer()
        campania = self.comboCamp.currentData() 
        exp = self.comboExp.currentData()
        # sql = '''INSERT INTO agrae.lotes(nombre, geom)  VALUES\n'''

        for f in layer.getFeatures():
            try:
                nombre = f[self.comboNombre.currentField()]
            except KeyError:
                nombre = ''

            try:
                cultivo = f[self.comboCultivo.currentField()]
            except KeyError:
                cultivo = ''

            try:
                produccion = f[self.comboProduccion.currentField()]
            except KeyError:
                produccion = 0

            try:
                regimen = f[ self.comboRegimen.currentField()]
            except KeyError:
                regimen = ''


            sql = self.agraeSql.getSql('new_lote.sql') 
            geom = f.geometry().asWkt()
            sql = sql.format(campania,exp,nombre,cultivo,regimen,produccion,geom)
            with self.conn.cursor() as cursor:
                try:
                    cursor.execute(sql)
                    print('Lote : {} creado exitosamente.'.format(nombre))
                    self.conn.commit()
                except Exception as ex:
                    print(ex)
                    self.conn.rollback()


        # print(layer)


class LoteWeatherDialog(QDialog):
    closingPlugin = pyqtSignal()
    def __init__(self,feat):
        super().__init__()
        self.setWindowTitle('Informacion Climatica')
        self.feat = feat

        self.UIComponents()
        self.getWeatherInfo()

        self.setFixedSize(QSize(250,400))

    def messages(self,title:str,text:str,level):
        iface.messageBar().pushMessage(title,text,level)
        QgsMessageLog.logMessage(text, title, level)

    def UIComponents(self):
        stylesheet = 'QLabel { font-weight : bold }'
        
        self.layout = QGridLayout()
        self.groupBoxLayout = QGridLayout()
        self.groupBox = QGroupBox()
        self.groupBox.setTitle('Informacion climatica')
        self.label_weather_icon = QLabel('ICONO')
        self.label_weather_icon.setMaximumSize(QSize(300,80))
        self.label_weather_icon.setAlignment(Qt.AlignCenter)
        self.groupBoxLayout.addWidget(self.label_weather_icon,0,0,1,0)

        self.label_1 = QLabel('Lote {}'.format(self.feat['lote']))
        self.label_1.setAlignment(Qt.AlignCenter)
        self.groupBoxLayout.addWidget(self.label_1,1,0,1,0)

        self.label_2 = QLabel('Estado Actual:')
        self.groupBoxLayout.addWidget(self.label_2,2,0)

        self.label_weather_status = QLabel()
        self.label_weather_status.setStyleSheet(stylesheet)
        self.groupBoxLayout.addWidget(self.label_weather_status,2,1)

        self.label_3 = QLabel('Temperatura:')
        self.groupBoxLayout.addWidget(self.label_3,3,0)

        self.label_weather_temp = QLabel()
        self.label_weather_temp.setStyleSheet(stylesheet)
        self.groupBoxLayout.addWidget(self.label_weather_temp,3,1)

        self.label_4 = QLabel('Humedad:')
        self.groupBoxLayout.addWidget(self.label_4,4,0)

        self.label_weather_humidity  = QLabel()
        self.label_weather_humidity.setStyleSheet(stylesheet)
        self.groupBoxLayout.addWidget(self.label_weather_humidity,4,1)

        self.label_5 = QLabel('Presion:')
        self.groupBoxLayout.addWidget(self.label_5,5,0)

        self.label_weather_pressure  = QLabel()
        self.label_weather_pressure.setStyleSheet(stylesheet)
        self.groupBoxLayout.addWidget(self.label_weather_pressure,5,1)
       
        self.label_6 = QLabel('Nubes:')
        self.groupBoxLayout.addWidget(self.label_6,6,0)

        self.label_weather_clouds  = QLabel()
        self.label_weather_clouds.setStyleSheet(stylesheet)
        self.groupBoxLayout.addWidget(self.label_weather_clouds,6,1)

        self.label_7 = QLabel('Viento:')
        self.groupBoxLayout.addWidget(self.label_7,7,0)

        self.label_weather_wind  = QLabel()
        self.label_weather_wind.setStyleSheet(stylesheet)
        self.groupBoxLayout.addWidget(self.label_weather_wind,7,1)






       
        self.groupBox.setLayout(self.groupBoxLayout)
        self.layout.addWidget(self.groupBox)
        self.setLayout(self.layout)

        pass
    
    def getWeatherInfo(self):
        self.label_weather_icon.clear()
        lat = self.feat.geometry().centroid().asPoint().y()
        long = self.feat.geometry().centroid().asPoint().x()
        # print(lat,long)
        params  = {
            'lat' : str(lat),
            'lon' : str(long),
            'lang' : 'es',
            'units' : 'metric',
            'appid' : '658e4107fe614c29cc28ec36ff712f6b'
        }

        url = u'https://api.openweathermap.org/data/2.5/weather'

        r = requests.get(url,params=params)
       
        response = json.loads(r.text)
        weather = response['weather'][0]
        main = response['main']
        clouds = response['clouds']
        wind = response['wind']
        dt = response['dt']
        
        dt = datetime.datetime.fromtimestamp(dt)
        

        pix = WeatherIcon(weather['icon']).getPixmap()
        self.label_weather_icon.setPixmap(pix)
        self.label_weather_status.setText(str(weather['description']).capitalize())
        self.label_weather_temp.setText('{} °C'.format(str(round(main['temp'],1)).capitalize()))
        self.label_weather_humidity.setText('{} %'.format(str(round(main['humidity'],1)).capitalize()))
        self.label_weather_pressure.setText('{} hpa'.format(str(round(main['pressure'])).capitalize()))
        self.label_weather_clouds.setText('{} %'.format(str(round(clouds['all'])).capitalize()))
        self.label_weather_wind.setText('{} km/h'.format(str(round(wind['speed'],2)).capitalize()))



class WeatherIcon():
    def __init__(self,code) -> None:
        self.link = 'https://openweathermap.org/img/wn/{}@2x.png'.format(code)
        self.icon = QIcon()
    
    def getIcon(self):
        try:
            response = requests.get(self.link)
            pixmap = QPixmap()
            pixmap.loadFromData(response.content)
            self.icon = QIcon(pixmap)
            return self.icon
        except:
            pass

    def getPixmap(self):
        try:
            response = requests.get(self.link)
            pixmap = QPixmap()
            pixmap.loadFromData(response.content)
            return pixmap
        except:
            pass
    


      