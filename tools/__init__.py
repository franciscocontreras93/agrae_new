import os, csv
import pandas as pd
import numpy as np
import processing
from io import BytesIO
from PIL import Image

from psycopg2 import extras, Binary
from qgis.PyQt import QtWidgets
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtGui import QIcon
from qgis.utils import iface 
from qgis.core import *
from qgis.PyQt.QtCore import  QVariant, QSettings, QSize,QDateTime


from ..db import agraeDataBaseDriver
from ..sql import aGraeSQLTools


class aGraeTools():
    def __init__(self):
        self.instance = QgsProject.instance()
        try:
            self.conn = agraeDataBaseDriver().connection()
        except Exception as ex:
            print(ex)
            self.conn = None
        self.plugin_name = 'aGrae Toolbox'

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

    def messages(self,title:str,text:str,level,duration:int=2,alert=False):
        """Levels:\n
        0.  Info\n
        1.  Warning\n
        2.  Critical\n
        3.  Success\n
        """        
        iface.messageBar().pushMessage(title,text,level,duration)
        if alert:
            if level== 0:
                QtWidgets.QMessageBox.information(None, title, text)
            elif level == 1: 
                QtWidgets.QMessageBox.warning(None, title, text)
            elif level == 2:
                QtWidgets.QMessageBox.critical(None, title, text)
            elif level == 3:
                QtWidgets.QMessageBox.about(None, title, text)
            
        QgsMessageLog.logMessage(text, title, level)
    
    def deleteAction(self,question:str,sql:str,widget=None,actions:list=None,):
        reply = QtWidgets.QMessageBox.question(None,'aGrae Toolbox',question,QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            with self.conn.cursor() as cursor:
                try:
                    cursor.execute(sql)
                    self.conn.commit()
                except Exception as ex:
                    self.conn.rollback()
                    print('{}'.format(ex))
        
        if widget and actions:
            widget.setChecked(False)
            self.enableElements(widget,actions)

    def question(self,question,action):
        reply = QtWidgets.QMessageBox.question(None,'aGrae Toolbox',question,QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            return action



        pass
    
    def dataCompleter(self,sql:str) -> list:
        with self.conn.cursor() as cursor:
            cursor.execute(sql)
            data = []
            for t in cursor.fetchall():
                for i in t:
                    data.append(i)

            data = set(data)
            completer = QCompleter(data)
            completer.setCaseSensitivity(False)
            return completer
    
    def searchGetData(self,lineWidget:QLineEdit,tableWidget:QTableWidget,param:str,query_empty:str,query_param:str):
        if param == '':
            sql =  query_empty
            try:
                self.populateTable(sql, tableWidget)
            except IndexError as ie:
                self.conn.rollback()
                pass
            except Exception as ex:
                self.conn.rollback()
                print(ex)
        else:
            sql = query_param
            try:
                # print(sql)
                self.populateTable(sql, tableWidget)
            except IndexError as ie:
                print(ie)
                self.conn.rollback()
                pass
            except Exception as ex:
                print(ex)
                self.conn.rollback()

    def populateTable(self,sql:str,tableWidget:QtWidgets.QTableWidget, action=False):
        with self.conn.cursor() as cursor:
                try:
                    cursor.execute(sql)
                    data = cursor.fetchall()
                    # print(data)
                    tableWidget.setRowCount(0)
                    if len(data) > 0:
                        # print(data)
                        a = len(data)
                        b = len(data[0])
                        i = 1
                        j = 1
                        tableWidget.setRowCount(a)
                        tableWidget.setColumnCount(b)
                        for j in range(a):
                            for i in range(b):
                                if str(data[j][i]) != 'None':
                                    item = QtWidgets.QTableWidgetItem(str(data[j][i]))
                                else:
                                    item  = QtWidgets.QTableWidgetItem(str('N/D'))  
                                tableWidget.setItem(j, i, item)
                                # tableWidget.resizeRowToContext()
                except IndexError as ie:
                    pass
    
    def enableElements(self,widget,elements:list):
        if widget.isChecked():
            for e in elements:
                if isinstance(e,QCheckBox):
                    # print('is checkBox')
                    e.setChecked(True)
                e.setEnabled(True)
        else:
            for e in elements:
                if isinstance(e,QCheckBox):
                    # print('is checkBox')
                    e.setChecked(False)
                e.setEnabled(False)

        pass
    
    def clearWidget(self,widgets:list):
        for w in widgets:
            w.clear()

    def openFileDialog(self): 
        options = QFileDialog.Options()
        # options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(
            None, "aGrae GIS", "", "Todos los archivos (*);;Archivos separados por coma (*.csv)", options=options)
        if fileName:
            # print('test',fileName)
            return fileName
        else: 
            return None
        
    def getDirectory(self):
        # options = QFileDialog.options()

        dirname = QFileDialog.getExistingDirectory(None, "Selecciona una Carpeta")
        return dirname
     
    def processImageToBytea(self,path):
        try:
            QgsMessageLog.logMessage("Procesando Imagen".format(), 'aGrae GIS', Qgis.Info)
            ima = Image.open(path)
            with BytesIO() as f: 
                ima.save(f,format='PNG')
                return Binary(f.getvalue())
        
        except IOError:
            # sys.exit(1)
            return ''
        except:
            return ''
    
    def crearSegmento(self,layer,field_segmento):
        lyr = layer
        srid = lyr.crs().authid()[5:]
        sql = """ insert into agrae.segmentos(segmento,geometria) values """
        if len(lyr.selectedFeatures()) > 0: features = lyr.selectedFeatures() 
        else: features = lyr.getFeatures()
        try:
            with self.conn.cursor() as cursor:
                try: 
                    for f in features :
                        segm = f[field_segmento] 
                        geometria = f.geometry() .asWkt()
                        sql = sql + f""" ({segm},st_multi(st_force2d(st_transform(st_geomfromtext('{geometria}',{srid}),4326)))),\n"""                   
                    # print(sql)
                    cursor.execute(sql[:-2])   
                    self.conn.commit() 
                    QMessageBox.about(None, 'aGrae GIS', 'Segmentos Cargados Correctamente \na la base de datos')

                except Exception as ex:

                    QgsMessageLog.logMessage(f'{ex}', 'aGrae GIS', level=1)
                    self.conn.rollback()
    
        except Exception as ex: 
            QgsMessageLog.logMessage(f'{ex}', 'aGrae GIS', level=1)
            self.conn.rollback()

    def crearAmbiente(self,layer,field_ambiente,field_ndvi):
        lyr = layer
        srid = lyr.crs().authid()[5:]
        sql = """ insert into agrae.ambiente(ambiente,ndvimax,geometria) values """
        if len(lyr.selectedFeatures()) > 0: features = lyr.selectedFeatures() 
        else: features = lyr.getFeatures()
        try:
            with self.conn.cursor() as cursor:
                try: 
                    for f in features :
                        amb = int(f[field_ambiente])
                        ndvimax = float(f[field_ndvi])

                        geometria = f.geometry() .asWkt()
                        sql = sql + f'''({amb},{ndvimax}, st_multi(st_force2d(st_transform(st_geomfromtext('{geometria}',{srid}),4326)))),\n'''                  
                    
                    # print(sql)
                    cursor.execute(sql[:-2])   
                    self.conn.commit() 
                    QMessageBox.about(None, 'aGrae GIS', 'Ambientes Cargados Correctamente \na la base de datos')

                except Exception as ex:

                    QgsMessageLog.logMessage(f'{ex}', 'aGrae GIS', level=1)
                    self.conn.rollback()
    
        except Exception as ex: 
            QgsMessageLog.logMessage(f'{ex}', 'aGrae GIS', level=1)
            self.conn.rollback()

        pass

    def crearCE(self,layer,field_ce36, field_ce90):
        def kf(value):
            if value > 0: return round( 2.0014 * value ** -1.514, 4)
            else :  return 0
        
    
        lyr = layer
        srid = lyr.crs().authid()[5:]
        sql = """ insert into agrae.ce(ce36, kf36, ce90, kf90 ,geometria) values """
        if len(lyr.selectedFeatures()) > 0: features = lyr.selectedFeatures() 
        else: features = lyr.getFeatures()
        try:
            reply = QtWidgets.QMessageBox.question(None,'aGrae Toolbox','Se cargaran {} poligonos a la base de datos,\n este proceso puede tardar. Quiere Continuar?'.format(len(features)),QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
            if reply == QtWidgets.QMessageBox.Yes:
            
                with self.conn.cursor() as cursor:
                    try: 
                        for f in features :
                            ce36 = f[field_ce36]
                            kf36 = kf(f[field_ce36])
                            ce90 = f[field_ce90]
                            kf90 = kf(f[field_ce90])

                            geometria = f.geometry() .asWkt()
                            sql = sql + f'''({ce36},{kf36},{ce90},{kf90}, st_multi(st_force2d(st_transform(st_geomfromtext('{geometria}',{srid}),4326)))),\n'''                  
                        
                        # print(sql)
                        cursor.execute(sql[:-2])   
                        self.conn.commit() 
                        QMessageBox.about(None, 'aGrae GIS', 'CE Cargados Correctamente \na la base de datos')

                    except Exception as ex:

                        QgsMessageLog.logMessage(f'{ex}', 'aGrae GIS', level=1)
                        self.conn.rollback()
    
        except Exception as ex: 
            QgsMessageLog.logMessage(f'{ex}', 'aGrae GIS', level=1)
            self.conn.rollback()

        pass
        
    def crearRindes(self,
                     layer:QgsVectorLayer,
                     field_volumen:QgsField,
                     field_humedad:QgsField,
                     fecha:str,
                     idcampania:int,
                     idexplotacion:int,
                     target_crs: QgsCoordinateReferenceSystem  = QgsCoordinateReferenceSystem("EPSG:4326")):
        layer = layer
        if layer.crs() != target_crs:
            layer = self.reprojectLayer(layer,target_crs)
        
        srid = target_crs.authid()[5:]

        # srid = lyr.crs().authid()[5:]
        sql = """ INSERT INTO field.data_rindes(volumen, humedad, fecha_muestreo, geom,idcampania,idexplotacion) VALUES"""
        if len(layer.selectedFeatures()) > 0: features = layer.selectedFeatures() 
        else: features = layer.getFeatures()
        for f in features:
            volumen = f[field_volumen] 
            humedad = f[field_humedad] 
            geometria = f.geometry() .asWkt()
            sql = sql + """ ({},{},'{}',st_geomfromtext('{}',{}),{},{}),\n""".format(volumen,humedad,fecha,geometria,srid,idcampania,idexplotacion)                 
        
        with self.conn.cursor() as cursor:
            try: 
                
                cursor.execute(sql[:-2])   
                self.conn.commit() 
                self.messages('Monitor de Rendimiento', 'Datos de Rendimiento cargados a la base de datos',3)

            except Exception as ex:
                self.messages('Monitor de Rendimiento', ex,2,alert=True)
                self.conn.rollback()
    
    def reprojectLayer(self,layer,target_crs):
        parameter = {
            'INPUT': layer,
            'TARGET_CRS': target_crs,
            'OUTPUT': 'memory:Reprojected'
        }
        return processing.run('native', parameter)['OUTPUT']

    def getLotesLayer(self):
        sql = aGraeSQLTools().getSql('lotes_layer.sql')
        layer = self.getDataBaseLayer(sql,layername='aGrae Lotes',styleName='lotes_asignados',memory=False)
        QgsProject.instance().addMapLayer(layer)
        iface.actionSelect().trigger()
        iface.setActiveLayer(layer)

    def getDataBaseLayerUri(self,idcampania,idexplotacion,name):
        dns = agraeDataBaseDriver().getDSN()
        styleUri = os.path.join(os.path.dirname(__file__), 'styles/{}.qml'.format('ambientes'))
        sql = ''' with data as (select distinct 
            d.iddata,
            d.idcampania,
            d.idexplotacion,
            d.idlote,
            d.idcultivo, 
            d.idregimen,
            d.fertilizantefondoformula,
            d.fertilizantefondoajustado,
            d.fertilizantecob1formula,
            d.fertilizantecob1ajustado,
            d.fertilizantecob2formula,
            d.fertilizantecob2ajustado,
            d.fertilizantecob3formula,
            d.fertilizantecob3ajustado,
            c.ms_cosecha,
            c.extraccioncosechan,
            c.extraccioncosechap,
            c.extraccioncosechak, 
            c.ms_residuo,
            c.extraccionresiduon,
            c.extraccionresiduop,
            c.extraccionresiduok, 
            d.prod_esperada 
            from campaign.data d 
            join agrae.cultivo c on c.idcultivo = d.idcultivo
            where d.idcampania = {} and d.idexplotacion = {} ),
        lotes as (select l.*, 
            d.iddata,
            d.idcampania,
            d.idexplotacion,
            d.idcultivo,
            d.idregimen as regimen,
            d.ms_cosecha,
            d.extraccioncosechan,
            d.extraccioncosechap,
            d.extraccioncosechak, 
            d.ms_residuo,
            d.extraccionresiduon,
            d.extraccionresiduop,
            d.extraccionresiduok, 
            d.prod_esperada from data d join agrae.lotes l on d.idlote = l.idlote ),
        ambientes as (select distinct l.nombre as lote,a.idambiente,a.ambiente,a.ndvimax,st_collectionextract(st_multi(st_intersection(l.geom,a.geometria)),3) as geom, l.prod_esperada, l.idlote, l.iddata from agrae.ambiente a join lotes l on st_intersects(l.geom,a.geometria))
        select row_number() over () as id , lote,idambiente,ambiente,ndvimax::numeric,(geom) as geom from ambientes
        '''.format(idcampania,idexplotacion)

        uri = QgsDataSourceUri() 
        uri.setConnection(dns['host'], dns['port'], dns['dbname'], dns['user'], dns['password'])
        uri.setDataSource('', f'({sql})', 'geom', '', 'id')
            # uriUnidades.setDataSource('public', 'unidades', 'geometria', f'"idlotecampania" = {idlotecampania}', 'id')
        lyrAmbientes = QgsVectorLayer(uri.uri(), '{}-Ambientes'.format(name), 'postgres')
        lyrAmbientes.loadNamedStyle(styleUri)
        return lyrAmbientes
    
    def getDataBaseLayer(self, sql:str, layername:str ='Resultados' ,styleName:str ='',memory=True,save=False,debug=False) -> QgsVectorLayer:
        col_types = {
            20 : QVariant.Int,
            21: QVariant.Int,
            23: QVariant.Int,
            25: QVariant.String,
            701: QVariant.Double,
            1700: QVariant.Double,
            1043: QVariant.String,
            1082: QVariant.String,
        }
        if styleName.lower() in ['fosforo','potasio','calcio','magnesio','sodio']: estilo = 'analisis_ppm' 
        else: estilo = styleName

        styleUri = os.path.join(os.path.dirname(__file__), 'styles/{}.qml'.format(estilo))

        with self.conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
            if memory:
                lyr = QgsVectorLayer('MultiPolygon?crs=epsg:4326&index=yes'.format(type),layername,'memory')
                provider = lyr.dataProvider()
                try:
                    lyr.startEditing()
                    cursor.execute(sql)
                    coldesc = tuple(c for c in cursor.description if c[0] != 'geom')

                    
                    data = cursor.fetchall()
                    if debug:
                        # print(data)
                        print(coldesc)
                    # QgsMessageLog.logMessage('{}'.format(sql), '{} Debug'.format(self.plugin_name), level=Qgis.Warning) #! DEBUG
                    # QgsMessageLog.logMessage('{}'.format(coldesc), '{} Debug'.format(self.plugin_name), level=Qgis.Warning) #! DEBUG
                    fields = [QgsField(c[0],col_types[c[1]]) for c in coldesc]
                    provider.addAttributes(fields)
                    lyr.updateFields()
                    geom = QgsGeometry()
                    features = []
                    for r in data:
                        # if debug:
                        #     print(r['geom'])
                        feat = QgsFeature()
                        feat.setFields(lyr.fields())
                        for c in fields:
                            feat.setAttribute(c.name(),r[c.name()])
                        feat.setGeometry(geom.fromWkt(r['geom']))
                        features.append(feat)
                        if debug:
                            print(feat)
                        # QgsMessageLog.logMessage('{}'.format(feat.geometry().asWkt()), '{} Debug'.format(self.plugin_name), level=Qgis.Warning) #! DEBUG
                        provider.addFeatures([feat])
                    
                    lyr.commitChanges()
                    lyr.loadNamedStyle(styleUri)
                    
                    if lyr.isValid():
                        # print(lyr.isValid())
                        QgsMessageLog.logMessage('Capa: <b>{}</b> CORRECTA'.format(lyr.name()), self.plugin_name, level=Qgis.Info)
                        # if save:
                        #     s = QSettings('agrae','dbConnection')
                        #     path = s.value('ufs_path')
                        #     fn = os.path.join(path,'UFS_{}.shp'.format(layername))
                        #     self.saveLayer(lyr,fn,layername)

                        return lyr
                    else:
                        # print(lyr.isValid())
                        QgsMessageLog.logMessage('Capa: <b>{}</b> INCORRECTA'.format(lyr.name()), self.plugin_name, level=Qgis.Warning)
                        # return lyr
                
                except Exception as ex:
                    iface.messageBar().pushMessage("Error:", "Ocurrio un Error, revisa el panel de mensajes del Registro", level=Qgis.Critical)
                    # print(ex)
                    QgsMessageLog.logMessage('{}'.format(ex), self.plugin_name, level=Qgis.Critical)
                    self.conn.rollback()

            else:
                dns = agraeDataBaseDriver().getDSN()
                uri = QgsDataSourceUri() 
                uri.setConnection(dns['host'], dns['port'], dns['dbname'], dns['user'], dns['password'])
                uri.setDataSource('', f'({sql})', 'geom', '', 'id')
                    # uriUnidades.setDataSource('public', 'unidades', 'geometria', f'"idlotecampania" = {idlotecampania}', 'id')
                lyrAmbientes = QgsVectorLayer(uri.uri(), '{}'.format(layername), 'postgres')
                lyrAmbientes.loadNamedStyle(styleUri)
                return lyrAmbientes

    def crearFormatoAnalitica(self,idcampania:int,idexplotacion:int,name:str):
        s = QSettings('agrae','dbConnection')
        path = s.value('analisis_path')
        sql = aGraeSQLTools().getSql('csv_report_data.sql').format(idcampania,idexplotacion)
        # sql_verify = aGraeSQLTools().getSql('csv_report_verify.sql').format(idcampania,idexplotacion)
        try:
            with open(os.path.join(os.path.dirname(__file__), 'extras/reporte.csv'),'r',newline='') as base: 
                csv_reader = csv.reader(base,delimiter=';')
                header = next(csv_reader)
            with open(os.path.join(path,'{}.csv'.format(name)),'w',newline='') as file: 
                csv_writer = csv.writer(file,delimiter=';')          
                csv_writer.writerow(header)
                with self.conn.cursor() as cursor:
                    cursor.execute(sql)
                    data = cursor.fetchall()
                    csv_writer.writerows([r for r in list(data)])

                    # cursor.execute(sql_verify)
                    # data_2 = cursor.fetchall()
                    # print(data_2)

            self.messages('aGrae GIS','Archivo Creado Correctamente <a href="{}">{}</a>'.format(os.path.join(path,'{}.csv'.format(name)),os.path.join(path,'{}.csv'.format(name))),3,5)

        except Exception as ex:
            print(ex)
            self.messages('aGrae GIS','Ocurrio un error: {}'.format(ex),2,3)
            pass
        
    def cargarReporteAnalitica(self):
        file = self.openFileDialog()
        # print(file)
        if file != None:
            df = pd.read_csv(file,delimiter=';')
            df = df.astype(object).replace(np.nan, 'NULL')
            # print(df)
            
            # print(data)
            return df
        else: 
            return pd.DataFrame()
        
    def guardarReporteAnalitica(self,df):
        df1 = df
        columns = [c for c in df1.columns]
        _VALUES = list()
        print(columns)   
        with self.conn.cursor() as cursor:
            try:   
                for index, r in df1.iterrows():
                    sql = aGraeSQLTools().getSql('csv_report_create.sql').format(r['COD'],r['ceap'],r['PH'],r['CE'],r['CARBON'],r['CALIZA'],r['CA'],r['MG'],r['K'],r['NA'],r['N'],r['P'],r['ORGANI'],r['AL'],r['B'],r['FE'],r['MN'],r['CU'],r['ZN'],r['S'],r['MO'],r['ARCILLA'],r['LIMO'],r['ARENA'],r['NI'],r['CO'],r['TI'],r['AS'],r['PB'],r['CR'],r['METODO_P'])
                    
                    try:
                        cursor.execute(sql)
                        self.messages('aGrae GIS','Analitica ({}) Cargada Correctamente'.format(r['COD']),3,alert=True)
                        self.conn.commit()
                    except Exception as ex:
                        self.conn.rollback()
                        raise Exception('Ocurrio un Error: {}'.format(ex))
                    
            except Exception as ex:
                QMessageBox.about(None, self.plugin_name, 'Ocurrio un error, revisa el panel de registros para más información')
                QgsMessageLog.logMessage(f'{ex}', self.plugin_name, level=1)
                self.conn.rollback()
            # try:     
            #     cursor.execute(_SQL_INSERT + ' ,\n'.join(_VALUES))
            #     self.conn.commit()
            #     # self.tools.actualizarNecesidades()
            #     iface.messageBar().pushMessage(self.plugin_name, 'Analitica Cargada Correctamente', level=Qgis.Success)
            #     QgsMessageLog.logMessage('Analitica Cargada Correctamente', self.plugin_name, level=Qgis.Success)
                    

            # except errors.lookup('23505'):
            #     # QMessageBox.about(None, self.plugin_name,'El analisis con codigo: {} ya existe en la base de datos.\nComprueba la informacion'.format(row['COD']))
            #     # QgsMessageLog.logMessage('El analisis con codigo: {} ya existe en la base de datos.\nComprueba la informacion'.format(row['COD']), self.plugin_name, level=Qgis.Warning)
            #     # self.conn.rollback()
            #     _SQL_UPDATE = '''UPDATE analytic.analitica
            #     SET             idanalitica=nextval('analytic.analitica_idanalitica_seq'::regclass), ceap=0, ph=0, ce=0, carbon=0, caliza=0, ca=0, mg=0, k=0, na=0, n=0, p=0, organi=0, cox=0, rel_cn=0, ca_eq=0, mg_eq=0, k_eq=0, na_eq=0, cic=0, ca_f=0, mg_f=0, k_f=0, na_f=0, al=0, b=0, fe=0, mn=0, cu=0, zn=0, s=0, mo=0, arcilla=0, limo=0, arena=0, ni=0, co=0, ti=0, "as"=0, pb=0, cr=0, metodo=0
            #     WHERE cod='';'''
            
            # except Exception as ex:
            #     QMessageBox.about(None, self.plugin_name, 'Ocurrio un error, revisa el panel de registros para más información')
            #     QgsMessageLog.logMessage(f'{ex}', self.plugin_name, level=1)
            #     self.conn.rollback()

            # self.an_save_bd.setEnabled(False)
            # QMessageBox.about(self, f"aGrae GIS:",f"Analitica almacenada correctamente")
        
    def crearReporteTest(self):
        #! CREAR BASE DEL ANALISIS DE LABORATORIO
        s = QSettings('agrae','dbConnection')
        path = s.value('analisis_path')
        # print('Crear Reporte')
        idx = self.tableWidget_2.selectionModel().selectedRows()
        header = []
        # print(len(idx))
        if len(idx) >0: 
            reporte_path = self.saveFileDialog()
            if reporte_path != False: 
                with open(os.path.join(os.path.dirname(__file__), 'extras/reporte.csv'),'r',newline='') as base: 
                    csv_reader = csv.reader(base,delimiter=';')
                    header = next(csv_reader)
                with open(reporte_path,'w',newline='') as file: 
                    csv_writer = csv.writer(file,delimiter=';')          
                    csv_writer.writerow(header)
                    for i in sorted(idx):
                        idsegmento = self.tableWidget_2.item(i.row(), 0).text()
                        idlotecampania = self.tableWidget_2.item(i.row(), 1).text()
                        with self.conn:
                            query = "select idsegmentoanalisis, cod_muestra , regimen, ceap from segmentos where idsegmento = {} and idlotecampania = {}".format(
                                idsegmento, idlotecampania)
                            # cursor = self.conn.cursor(cursor_factory=extras.DictCursor)
                            cursor = self.conn.cursor() 
                            cursor.execute(query)
                            data = cursor.fetchall()
                            if data[0][3] != None:                            
                                iter_data = [r for r in list(data)]
                                csv_writer.writerows(iter_data)
                            else:
                                iter_data = []
                                # print(data['ceap'])
                                sql = f''' update public.segmento
                                set ceap = q.ceap
                                from (select s.idsegmento, percentile_cont(0.5) within group( order by c.ceap) ceap from ceap36 c 
                                join segmento s on st_intersects(c.geom,s.geometria)
                                where s.idsegmento in ({idsegmento})
                                group by s.idsegmento ) as q
                                where  segmento.idsegmento = q.idsegmento'''

                                try:
                                    # cursor = self.conn.cursor(cursor_factory=extras.DictCursor)
                                    cursor.execute(sql)
                                    self.conn.commit()
                                    iface.messageBar().pushMessage("aGrae GIS", "Se Calculo el CEAP para el segmento {}".format(idsegmento), level=Qgis.Success)

                                    cursor = self.conn.cursor() 
                                    cursor.execute("select idsegmentoanalisis, cod_muestra , regimen, ceap from segmentos where idsegmento = {} and idlotecampania = {}".format(
                                    idsegmento, idlotecampania))
                                    data = cursor.fetchall()
                                    csv_writer.writerows([r for r in list(data)])

                                except Exception as ex:
                                    self.conn.rollback()
                                    QgsMessageLog.logMessage("{}".format(ex), 'aGrae GIS', level=Qgis.Critical)

                    self.utils.msgBar('Archivo Creado Correctamente <a href="{}">{}</a>'.format(reporte_path,reporte_path),3,10)
            else:            
                QMessageBox.about(self, 'aGrae GIS', 'La ruta ingresada no es valida')

        else: 
            # print('Debe Seleccionar al menos un segmento')
            pass

    def exportarUFS(self,idcampania:int,idexplotacion:int,nameExp:str):
        s = QSettings('agrae','dbConnection')
        path = s.value('ufs_path')
        fn = os.path.join(path,'UFS_{}.shp'.format(nameExp))
        print(fn)
        q = '''select distinct 
        row_number() OVER (ORDER BY (st_dump(geom)).geom) as id,
        uf,
        uf_etiqueta,
        lote, prod_esperada, prod_ponderada, 
        fertilizantefondoformula for_1, 
        fertilizantefondocalculado dos_1,
        fertilizantecob1formula for_2, 
        fertilizantecob1calculado dos_2,
        fertilizantecob2formula for_3, 
        fertilizantecob2calculado dos_3,
        fertilizantecob3formula for_4, 
        fertilizantecob3calculado dos_4,
        round((st_area(st_transform(((st_dump(geom)).geom),8857))/10000)::numeric,2)::double precision area_ha,
        st_asText(st_multi((st_dump(geom)).geom)) as geom
        from uf_final;'''
        query  = aGraeSQLTools().getSql('uf_aportes_query.sql').format(idcampania,idexplotacion,q)
        layer = self.getDataBaseLayer(query,'UFS_{}'.format(nameExp),styleName='Fert Variable Intraparcelaria',memory=True)
        try:
            self.saveLayer(layer,fn,nameExp)
            self.messages('aGrae GIS','Se ha generado el archivo UFS correctamente.',3,alert=True)
        except Exception as ex:

            print(ex)

    def exportarResumenFertilizacion(self,idcampania:int,idexplotacion:int,nameExp:str):
        s = QSettings('agrae','dbConnection')
        path = s.value('reporte_path')
        q = '''select 
        lote,
        cultivo,
        agricultor,
        area_lote,
        prod_esperada,
        fertilizantefondoformula, 
        sum(round((fertilizantefondocalculado * area_ha))) as fertilizantefondoaplicado,
        round(sum((fertilizantefondocalculado * area_ha) / area_lote)) as fertilizantefondomedia,
        fertilizantecob1formula, 
        sum(round((fertilizantecob1calculado * area_ha))) as fertilizantecob1aplicado,
        round(sum((fertilizantecob1calculado * area_ha) / area_lote)) as fertilizantecob1media,
        fertilizantecob2formula, 
        sum(round((fertilizantecob2calculado * area_ha))) as fertilizantecob2aplicado,
        round(sum((fertilizantecob2calculado * area_ha) / area_lote)) as fertilizantecob2media,
        fertilizantecob3formula, 
        sum(round((fertilizantecob3calculado * area_ha))) as fertilizantecob3aplicado,
        round(sum((fertilizantecob3calculado * area_ha) / area_lote)) as fertilizantecob3media
        from uf_final
        group by
        lote,
        cultivo,
        agricultor,
        area_lote,
        prod_esperada,
        fertilizantefondoformula, 
        fertilizantecob1formula,
        fertilizantecob2formula, 
        fertilizantecob3formula;'''
        query  = aGraeSQLTools().getSql('uf_aportes_query.sql').format(idcampania,idexplotacion,q)
        try: 
            with self.conn.cursor() as cursor:  
                cursor.execute(query) 
                data = [r for r in list(cursor.fetchall())]
                # expName = list(set([r[0] for r in data]))
                # print(expName[0])
                try: 
                    with open(os.path.join(os.path.dirname(__file__), 'extras/resumen.csv'),'r',newline='') as base:
                        csv_reader = csv.reader(base,delimiter=';')
                        header = next(csv_reader)
                    with open(os.path.join(path, 'resumen_{}_{}.csv'.format(nameExp,QDateTime.currentDateTime().toString('yyyyMMddHHmmss'))),'w',newline='') as file:
                            csv_writer = csv.writer(file,delimiter=';')          
                            csv_writer.writerow(header)
                            csv_writer.writerows(data)
                    
                    self.messages('aGrae GIS','Se ha generado el archivo de Resumen correctamente.',3,alert=True)
                except Exception as ex: print(ex)
        except Exception as ex: print(ex)

        



        pass
    
    def styleSheetPlotDialog(self) -> str:
        style = '''QTabBar::tab:selected {background : green ; color : white ; border-color : white }
                   QTabBar::tab {padding : 4px ; margin : 2px ;  border-radius : 2px  ; border: 1px solid #000 ; heigth: 15px }
                   '''
        return style
    
    def getCultivosData(self,sql:str,widget_combo,firts_element:str = 'Seleccionar...'):
        widget_combo.clear()
        widget_combo.addItem(firts_element,0)
        with self.conn.cursor() as cursor:
            try:
                cursor.execute(sql)
                data_exp = cursor.fetchall() 
                self.conn.commit()
                for e in data_exp: 
                    widget_combo.addItem(e[0],e[1])
            except Exception as ex:
                self.conn.rollback()
                print(ex)

    def checkData(self,data):
        """checkData  function to check the UF values in sql query, if not exist, add to an array with valid data

        :param str data: fetch data with sql
        :param list uf: uf value array
        :return list: array with data structured
        """
        ufs = ['UF1', 'UF2', 'UF3','UF4','UF5','UF6','UF7','UF8','UF9']


        validate = [e[0] for e in data]
        # print(validate)

        for uf in ufs:
           if uf not in validate:
                data.append((uf, 0, '0 / 0 / 0', '0 / 0 / 0', '0 / 0 / 0', 0,''))


        return data
    
    def sumaPonderada(self,v,a):
        """
        v = Value a = Area

        """
        try:
            zipedd = zip(v, a)
            # print('zipped',zipedd)
            p1 = [v * a for (v, a) in zipedd]
            p2 = round(sum(p1)/sum(a))
        except ZeroDivisionError:
            p2=0 

        # print('suma_ponderada',p2)
        return p2  
    
    def ajustesFertilizantes(self,n:list,x:float,p:list,y:float,k:list,z:float):
        
        """
        n: List of uf values for N
        x: value for N dosification
        p: List of uf values for P
        y: Value dosification for P, 
        k: List of K values
        z: Value dosification for K 

        return data: Structured analized values, Totals


        """
        uf = ['UF1','UF2','UF3','UF4','UF5','UF6','UF7','UF8','UF9']

        n1 = [round(e/x) if x != 0 else 0 for e in n]
        zn = zip(uf, n1)
        tn = sum(n1)
        dataN = {k:v for k,v in zn}
        # print('N: ', dataN)

        p1 = [round(e/y) if y != 0 else 0 for e in p]
        zp = zip(uf,p1)
        dataP = {k:v for k,v in zp}
        tp = sum(p1)
        # print('P: ',dataP)  

        k1 = [round(e/z) if z != 0 else 0 for e in k]
        zk = zip(uf,k1)
        tk = sum(k1)
        dataK = {k:v for k,v in zk}
        # print('K :',dataK)

        pk1 = [round((e+i)/2) for e,i in zip(p1,k1)]
        zpk = zip(uf,pk1)
        tpk = sum(pk1)
        dataPK = {k:v for k,v in zpk}

        totales = [tn,tp,tk,tpk]

        # print('PK :',dataPK)

        data = zip(uf,n1,p1,k1,pk1)
        return data
    
    def groupLayers(self,group_name:str,name_layer:str):
        layers  = [l for l in self.instance.mapLayers().values() if group_name in l.name()]
        for l in layers:
            if name_layer in l.name():
                return l
            
    def getBaseMap(self,name:str,basemaps:dict) -> QgsRasterLayer:
        basemap = basemaps[name]
        url = basemap['url']
        options = basemap['options']
        urlWithParams = 'url={}&{}'.format(url,options)
        return QgsRasterLayer(urlWithParams,name,'wms')
    
    def saveLayer(self,layer,dir:str,fileName:str,driver:str='ESRI Shapefile'):
        # print('saving')
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = driver
        options.layerName = fileName
        options.fileEncoding = 'utf-8'
        fileName = fileName.lower()
        fileName = fileName.replace(' ','_')
        if driver == 'ESRI Shapefile':
            fileName = '{}.shp'.format(fileName)
        elif driver == 'CSV':
            fileName = '{}.csv'.format(fileName)

        fn = os.path.join(dir)
        try:
            QgsVectorFileWriter.writeAsVectorFormatV3(layer,fn,QgsCoordinateTransformContext(),options)
            
        except Exception as ex:
            print(ex)

    def asignarMultiplesCultivos(self,idcultivo:int,data:list):
        sql = '''UPDATE campaign.data
        SET idcultivo={}
        WHERE iddata in ({})'''.format(idcultivo,','.join(data))
        with self.conn.cursor() as cursor:
            try:
                cursor.execute(sql)
                self.conn.commit()

                self.messages('aGrae Tools','Se Asignaron los cultivos Correctamente.',3)
            
            except Exception as ex:
                self.messages('aGrae Tools','No se pudieron asignar los cultivos.\n {}'.format(ex),2,alert=True)
                raise Exception(ex)


    




            

