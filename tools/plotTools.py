import os, re
import shutil
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtCore import  Qt

from qgis.PyQt.QtCore import QSettings, QVariant
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

from qgis.utils import iface
from qgis.core import *




class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, data):
        super(TableModel, self).__init__()
        self._data = None
        self._data = data
        self.colors = {'UF1': '#0be825',
                       'UF2': '#dd3f20',
                       'UF3': '#f5f227',
                       'UF4': '#0e13a9',
                       'UF5': '#f618d5',
                       'UF6': '#d5d5d5',
                       'UF7': '#18d9f6',
                       'UF8': '#8800e2',
                       'UF9': '#fab505'}

    def data(self, index, role):

        if role == Qt.DisplayRole:
            value = self._data.iloc[index.row(), index.column()]
            if value != NULL and value != 0:
                # print(value)
                return str(value)
            else:
                return int(0)
        if role == Qt.BackgroundRole and index.column() == 0:
            value = self._data.iloc[index.row()][0]
            try:
                if value in self.colors.keys():
                    return QtGui.QColor(self.colors[value])
            except:
                pass
        

        if role == Qt.FontRole:                     
            return QtGui.QFont("Segoe UI", 9, QtGui.QFont.Bold)
       
       
        if role == Qt.TextAlignmentRole: 
            return Qt.AlignCenter
        
            

    def rowCount(self, index):
        return self._data.shape[0]

    def columnCount(self, index):
        return self._data.shape[1]

    def headerData(self, section, orientation, role):
        # section is the index of the column/row.
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._data.columns[section])

            if orientation == Qt.Vertical:
                return str(self._data.index[section])
            
    def styleSheet(self) -> str:
        style = '''QTabBar::tab:selected {background : green ; color : white ; border-color : white }
                   QTabBar::tab {padding : 4px ; margin : 2px ;  border-radius : 2px  ; border: 1px solid #000 ; heigth: 15px }
                   '''
        return style


class PanelRender():
    """
    Class PanelRender:  Renderiza el panel agropecuario con los siguientes parametros. 
    lote(string) = Nombre del Lote.
    parcela(string) = Nombre Parcelario.
    cultivo = Nombre Cultivo
    produccion(int) = Produccion Ponderada
    n,p,k (int) = Valores Resultantes de NPK 

    """

    path = {'base': os.path.join(os.path.dirname(__file__), r'img\base00.png'),
            'base2': os.path.join(os.path.dirname(__file__), r'img\base02.png'),
            'base3': os.path.join(os.path.dirname(__file__), r'img\base03.png'),
            'base4': os.path.join(os.path.dirname(__file__), r'img\base04.png'),
            'plot': os.path.join(os.path.dirname(__file__), r'img\chart.png'),
            'table': os.path.join(os.path.dirname(__file__), r'img\tabla.png'),
            'tf1': os.path.join(os.path.dirname(__file__), r'img\tf1.png'),
            'tf2': os.path.join(os.path.dirname(__file__), r'img\tf2.png'),
            'tf3': os.path.join(os.path.dirname(__file__), r'img\tf3.png'),
            'tf4': os.path.join(os.path.dirname(__file__), r'img\tf4.png'),
            'trigo_esquema': os.path.join(os.path.dirname(__file__), r'img\assets\trigo_esquema.png')}

    _cultivos_path = {
        'TRIGO B': os.path.join(os.path.dirname(__file__), r'img\assets\cereal_esquema.png'),
        'MAIZ G': os.path.join(os.path.dirname(__file__), r'img\assets\maiz_esquema.png'),
                }

    def __init__(self, lote, cultivo, produccion, area, npk: list, i: int, pesos:list, precios:list,aplicados:list,formulas:list,dataHuellaCarbono,preciosTon:list,moneda):
        
        
        
        self.iface = iface
        self.now = datetime.now()
        self.date = self.now.strftime("%H%M%S%d%m%y")
        self.lote = lote
        # self.parcela = parcela
        self.cultivo = cultivo
        self.prod_ponderado = produccion
        self.area = area
        self.n_ponderado = npk[0]
        self.p_ponderado = npk[1]
        self.k_ponderado = npk[2]

        self.i = i
        self._pesos = pesos
        self._pesos_aplicados = aplicados
        self._precios = precios
        self._precios_ton = preciosTon
        self.formulas = formulas
        self.dataHuellaCarbono = dataHuellaCarbono
        self.moneda = moneda
       

        

        self.p1 = None
        self.p2 = None
        self.p3 = None
        self.phc = None

        self.font = ImageFont.truetype("arialbi.ttf", 13)
        self.font2 = ImageFont.truetype("arialbi.ttf", 10)
        self.font3 = ImageFont.truetype("arialbi.ttf", 12)
        self.color = (0, 0, 0)

        pass

    def panelUno(self):
        
        img = Image.open(self.path['base'])
        font = ImageFont.truetype("arialbi.ttf", 13)
        font2 = ImageFont.truetype("arialbi.ttf", 10)
        color = (0, 0, 0)
        d1 = ImageDraw.Draw(img)
        d1.text((328, 434), "{} Kg cosecha/Ha".format(self.prod_ponderado),
                font=font, fill=color)
        d2 = ImageDraw.Draw(img)
        d2.text((630, 434), "{} Ha".format(self.area), font=font, fill=color)
        d3 = ImageDraw.Draw(img)
        d3.text((576, 456), "{} / {} / {}".format(self.n_ponderado, self.p_ponderado, self.k_ponderado),
                font=font, fill=color)
        img2 = Image.open(self.path['plot'])
        img2 = img2.resize((281, 211))
        img.paste(img2, (25, 184), mask=img2)
        img3 = Image.open(self.path['table'])
        img3 = img3.resize((386, 225))
        img.paste(img3, (314, 187), mask=img3)
        
        self.setEsquema(self.cultivo, img)


        d4 = ImageDraw.Draw(img)
        d4.text((44, 225), "N", font=font2, fill=color)
        d4.text((44, 262), "P", font=font2, fill=color)
        d4.text((44, 303), "K", font=font2, fill=color)
        d4.text((28, 340), "Carb.", font=font2, fill=color)
        self.p1 = img

    def setEsquema(self, cultivo, img):
        try:
            if cultivo in self._cultivos_path:
                path = self._cultivos_path[cultivo]
                esquema = Image.open(path)
                esquema = esquema.resize((290, 141))
                img.paste(esquema, (25, 50), mask=esquema)
        except UnboundLocalError:
            print('No existe Grafico')
            pass
    
    def panelHuellaCarbono(self,
                           datos: dict = {
                               'percent': 0,
                               'chc': 0,
                               'biomasa': 0,
                               'cosecha': 0,
                               'residuo': 0,
                               'fertilizacion': 0
                           }):
        font = ImageFont.truetype("arialbi.ttf", 18)
        font2 = ImageFont.truetype("arialbi.ttf", 12)
        img = Image.open(self.path['base4'])
        draw = ImageDraw.Draw(img)
        txt = 'Si hacemos las coseas BIEN, además de\nahorrar Fertilizante, conseguimos un\n{}% de HUELLA DE CARBONO\nrepecto a seguir haciendolas como siempre'.format(
            datos['percent'])
        draw.text((240, 140), txt, font=font, fill=self.color,
                  anchor='mm', align='center', spacing=12)  # ! TEXTO PANEL
        draw.text((620, 100), '{:,} KgCO2eq/ha'.format(datos['chc']), font=font, fill=(110, 178, 83),
                  anchor='mm', align='center', spacing=12)  # ! CAPTURA HUELLA DE CARBONO
        draw.text((680, 135), '{:,} KgCO2eq/ha'.format(datos['biomasa']), font=font2, fill=(0, 0, 0),
                  anchor='mm', align='center', spacing=12)  # ! CAPTURA BIOMASA
        draw.text((680, 160), '{:,} KgCO2eq/ha'.format(datos['cosecha']), font=font2, fill=(0, 0, 0),
                  anchor='mm', align='center', spacing=12)  # ! CAPTURA COSECHA
        draw.text((680, 185), '{:,} KgCO2eq/ha'.format(datos['residuo']), font=font2, fill=(0, 0, 0),
                  anchor='mm', align='center', spacing=12)  # ! CAPTURA RESIDUO
        draw.text((680, 205), '{:,} KgCO2eq/ha'.format(datos['fertilizacion']*(-1)), font=font2, fill=(0, 0, 0),
                  anchor='mm', align='center', spacing=12)  # ! CAPTURA FERTILZIACION VARIABLE
        self.phc = img
        pass


    def panelDos(self, i, pesos,precios):
        def modify(formula):
            # print(formula)
            pa = re.compile('^[0]')
            f = ''

            # formula = list(formula.split('-'))
            for e in formula:

                if re.match(pa, e):
                    e = e[1:]

                f = f + ' {}% -'.format(e)

            return f[:-1]
        font = ImageFont.truetype("arialbi.ttf", 15)
        font2 = ImageFont.truetype("arialbi.ttf", 13)
        font3 = ImageFont.truetype("arialbi.ttf", 22)
        font4 = ImageFont.truetype("arialbi.ttf", 16)
        color = self.color
        formulas = ''

        total_peso = sum(pesos)
        # print(pesos)
        # print(total_peso)
        coste_unitario = sum(precios)

        coste_total = round((coste_unitario * self.area),2)

        w = 117
        h = 307

        datos = self.dataHuellaCarbono
        # print(datos)


        img = Image.open(self.path['base2'])
        draw = ImageDraw.Draw(img)
        if i >= 1:
            tf1 = Image.open(self.path['tf1'])
            tf1 = tf1.resize((w, h))
            img.paste(tf1, (67, 155), mask=tf1)
            f1 = modify(self.formulas[0])
            formulas = formulas + f1 + ' --- '
            draw.text((120,140), '{}'.format(f1), font=font,fill=(0,0,0),anchor='mm') #! FORMULA 1
            draw.text((75, 450), '{} Kg/Ha\n{:,} {}/Ha'.format(pesos[0], precios[0],self.moneda), font=font, fill=color, align='center', spacing=8)
        if i >= 2:
            tf2 = Image.open(self.path['tf2'])
            tf2 = tf2.resize((w, h))
            img.paste(tf2, (232, 155), mask=tf2)
            f2 = modify(self.formulas[1])
            formulas = formulas + f2 + ' --- '
            draw.text((285,140), f2, font=font,fill=color,anchor='mm') #! FORMULA 2
            draw.text((245, 450), '{} Kg/Ha\n{:,} {}/Ha'.format(pesos[1], precios[1], self.moneda), font=font, fill=color, align='center', spacing=8)
        if i >= 3:
            tf3 = Image.open(self.path['tf3'])
            tf3 = tf3.resize((w, h))
            img.paste(tf3, (400, 155), mask=tf3)
            f3 = modify(self.formulas[2])
            formulas = formulas + f3 + ' --- '
            draw.text((455,140), f3, font=font,fill=color,anchor='mm') #! FORMULA 3
            draw.text((410, 450), '{} Kg/Ha\n{:,} {}/Ha'.format(
                pesos[2], precios[2],self.moneda), font=font, fill=color, align='center', spacing=8)
        if i >= 4:
            tf4 = Image.open(self.path['tf4'])
            tf4 = tf4.resize((w, h))
            img.paste(tf4, (566, 155), mask=tf4)
            f4 = modify(self.formulas[3])
            formulas = formulas + f4 + ' --- '
            draw.text((620,140), f4, font=font,fill=color,anchor='mm') #! FORMULA 4
            draw.text((580, 450), '{} Kg/Ha\n{:,}{}/Ha'.format(
                pesos[3], precios[3], self.moneda), font=font, fill=color, align='center', spacing=8)
        
        draw.text((270, 532), '{:,} {}/Ha'.format(coste_unitario,self.moneda), font=font3, fill=color)
        draw.text((270, 584), '{:,} Ha'.format(self.area), font=font3, fill=color)
        draw.text((500, 545), '{} {:,}'.format(self.moneda,coste_total), font=font3, fill=color)


        txt = 'Si hacemos las coseas BIEN, además\nde ahorrar Fertilizante, conseguimos un\n{}% de HUELLA DE CARBONO\nrepecto a seguir haciendolas como\nsiempre'.format(
            datos['percent'])
        draw = ImageDraw.Draw(img)
        draw.text((210, 735), txt,
                  font=font,
                  fill=self.color,
                  anchor='mm',
                  align='center',
                  spacing=10)  # ! TEXTO PANEL
        draw.text((520, 652), '{:,} KgCO2eq/ha'.format(datos['chc']), font=ImageFont.truetype("arialbi.ttf", 22), fill=(110, 178, 83),
                  anchor='mm', align='center', spacing=12)  # ! CAPTURA HUELLA DE CARBONO
        draw.text((590, 687), '{:,} KgCO2eq/ha'.format(datos['biomasa']), font=ImageFont.truetype("arialbi.ttf", 15), fill=(110, 178, 83),
                  anchor='mm', align='center', spacing=12)  # ! CAPTURA BIOMASA
        draw.text((605, 722), '{:,} KgCO2eq/ha'.format(datos['cosecha']), font=ImageFont.truetype("arialbi.ttf", 15), fill=(110, 178, 83),
                  anchor='mm', align='center', spacing=12)  # ! CAPTURA COSECHA
        draw.text((605, 760), '{:,} KgCO2eq/ha'.format(datos['residuo']), font=ImageFont.truetype("arialbi.ttf", 15), fill=(110, 178, 83),
                  anchor='mm', align='center', spacing=12)  # ! CAPTURA RESIDUO
        draw.text((580, 797), '{:,} KgCO2eq/ha'.format(datos['fertilizacion']*(-1)), font=ImageFont.truetype("arialbi.ttf", 15), fill=(226, 59, 59),
                  anchor='mm', align='center', spacing=12)  # ! CAPTURA FERTILZIACION VARIABLE

        nota = 'Se han calculado {} combinaciones de Fertilizantes para ajustar las necesidades del Cultivo.\nDe ellas se ha seleccionado la combinacion mas economica. Los fertilizantes con los que\nse ha analizado han sido: {}\n***Precios Fertilizantes a dia {}. Pueden sufrir Variacion***'.format(
            len(precios), formulas[:-4], datetime.today().strftime("%d/%m/%Y"))

        draw.text((50, 850),
                  nota, font=ImageFont.truetype("arial.ttf", 12), fill=color)

        

        
        self.p2 = img
    
    def panelTres(self):
        def modify(formula):
            # print(formula)
            pa = re.compile('^[0]')
            f = ''
            
            # formula = list(formula.split('-'))
            for e in formula:

                if re.match(pa, e):
                    e = e[1:]

                f = f + ' {}% -'.format(e)

            return f[:-1]

        pesos = self._pesos_aplicados
        # print(pesos)
        precios = self._precios_ton
        x = 150
        y = 105
        font = self.font3
        font2 = ImageFont.truetype("arialbi.ttf", 14)
        color = self.color
        img = Image.open(self.path['base3'])
        draw = ImageDraw.Draw(img)
        total_unitario = 0
        formulas = ''
        datos = self.dataHuellaCarbono

        # print(pesos,precios)
        # for e,x in pesos,precios:
        #     print(e,x)


        if len(pesos) >= 1:
            f1 = self.formulas[0]
            f1 = modify(f1)
            formulas = formulas + f1 + ' --- '
            t1 = round(pesos[0]/self.area)*(precios[0]/1000)
            # print(t1)
            #! ERROR EN LA MEDIA OJO
            #! BUG
            draw.text((140, y), '{}\n\n{:,} Kg/ha\n{:,} {}/ha\n\n{:,} Kg'.format(f1, round(pesos[0]/self.area), round(
                t1),self.moneda, round(pesos[0])), font=font2, fill=color, align='center', spacing=8)
            total_unitario = total_unitario + round(
                t1)
            print(total_unitario)
            

        if len(pesos) >= 2:
            f2 = self.formulas[1]
            f2 = modify(f2)
            formulas = formulas + f2 + ' --- '
            t2 = round(pesos[1]/self.area)*(precios[1]/1000)
            # print(t2)
            draw.text(((148*2)+10, y), '{}\n\n{:,}Kg/ha\n{:,}{}/ha\n\n{:,} Kg'.format(f2, round(pesos[1]/self.area), round(
                t2), self.moneda, round(pesos[1])), font=font2, fill=color, align='center', spacing=8)
            total_unitario = total_unitario + round(
                t2)
            print(total_unitario)
            
           

        if len(pesos) >= 3:
            f3 = self.formulas[2]
            f3 = modify(f3)
            formulas = formulas + f3 + ' --- '
            t3 = round(pesos[2]/self.area)*(precios[2]/1000)
            # print(t3)
            draw.text(((148*3)+20, y), '{}\n\n{:,}Kg/ha\n{:,}{}/ha\n\n{:,}Kg'.format(f3, round(pesos[2]/self.area), round(
                t3), self.moneda, round(pesos[2])), font=font2, fill=color, align='center', spacing=8)
            total_unitario = total_unitario + round(
                t3)
            print(total_unitario)
            

        if len(pesos) > 3:
            f4 = self.formulas[3]
            f4 = modify(f4)
            formulas = formulas + f4 + ' --- '
            t4= round(pesos[3]/self.area)*(precios[3]/1000)
            # print(t4)
            draw.text(((148*4)+30, y), '{}\n\n{:,}Kg/ha\n{:,}{}/ha\n\n{:,}Kg'.format(3, round(pesos[3]/self.area), round(
                t4), self.moneda, round(pesos[3])), font=font2, fill=color, align='center', spacing=8)
            total_unitario = total_unitario + round(
                t4)
            print(total_unitario)
            

        draw.text((340, 295),
                  '{:,} {}/ha'.format(total_unitario,self.moneda),
                  font=ImageFont.truetype("arialbi.ttf", 16),
                  fill=color,
                  align='center')
        draw.text((340, 345),
                  '{} Ha'.format(self.area),
                  font=ImageFont.truetype("arialbi.ttf", 16),
                  fill=color,
                  align='center')

        draw.text((600, 335),
                  '{} {:,}'.format(self.moneda,round((total_unitario*self.area),2)),
                  font=ImageFont.truetype("arialbi.ttf", 24),
                  fill=color)
        


        nota = 'Se han calculado {} combinaciones de Fertilizantes para ajustar las necesidades del Cultivo.\nDe ellas se ha seleccionado la combinacion mas economica. Los fertilizantes con los que\nse ha analizado han sido: {}\n***Precios Fertilizantes a dia {}. Pueden sufrir Variacion***'.format(
            len(precios), formulas[:-4], datetime.today().strftime("%d/%m/%Y"))

        draw.text((50, 630),
                  nota, font=ImageFont.truetype("arial.ttf", 12), fill=color)
        txt = 'Si hacemos las coseas BIEN, además\nde ahorrar Fertilizante, conseguimos un\n{}% de HUELLA DE CARBONO\nrepecto a seguir haciendolas como\nsiempre'.format(
            datos['percent'])
        draw = ImageDraw.Draw(img)
        draw.text((230, 525), txt,
                  font=ImageFont.truetype("arialbi.ttf", 16),
                  fill=self.color,
                  anchor='mm',
                  align='center',
                  spacing=10)  # ! TEXTO PANEL
        draw.text((560, 445), '{:,} KgCO2eq/ha'.format(datos['chc']), font=ImageFont.truetype("arialbi.ttf", 22), fill=(110, 178, 83),
                  anchor='mm', align='center', spacing=12)  # ! CAPTURA HUELLA DE CARBONO
        draw.text((650, 482), '{:,} KgCO2eq/ha'.format(datos['biomasa']), font=ImageFont.truetype("arialbi.ttf", 15), fill=(110, 178, 83),
                  anchor='mm', align='center', spacing=12)  # ! CAPTURA BIOMASA
        draw.text((670, 518), '{:,} KgCO2eq/ha'.format(datos['cosecha']), font=ImageFont.truetype("arialbi.ttf", 15), fill=(110, 178, 83),
                  anchor='mm', align='center', spacing=12)  # ! CAPTURA COSECHA
        draw.text((670, 555), '{:,} KgCO2eq/ha'.format(datos['residuo']), font=ImageFont.truetype("arialbi.ttf", 15), fill=(110, 178, 83),
                  anchor='mm', align='center', spacing=12)  # ! CAPTURA RESIDUO
        draw.text((650, 595), '{:,} KgCO2eq/ha'.format(datos['fertilizacion']*(-1)), font=ImageFont.truetype("arialbi.ttf", 15), fill=(226, 59, 59),
                  anchor='mm', align='center', spacing=12)  # ! CAPTURA FERTILZIACION VARIABLE

        self.p3 = img
        pass


    
    def showPanel(self):
        self.panelUno()
        self.img.show()

    def savePanel(self):
        s = QSettings('agrae','dbConnection')
        self.panelUno()
        self.panelHuellaCarbono(self.dataHuellaCarbono)
        # print(self.i,self._pesos,self._precios)
        self.panelDos(self.i,self._pesos,self._precios)
        filename = s.value('paneles_path')
        self.panelTres()
        self.p1.save(f'{filename}\\Panel00{self.lote}.png')
        self.p2.save(f'{filename}\\Panel02{self.lote}.png')
        self.p3.save(f'{filename}\\Panel01{self.lote}.png')
        self.phc.save((f'{filename}\\Panel03{self.lote}.png'))
        # self.p2.show()

        self.iface.messageBar().pushMessage(f'Paneles Exportado Correctamente <a href="{filename}">{filename}</a>', 3, 10)
        