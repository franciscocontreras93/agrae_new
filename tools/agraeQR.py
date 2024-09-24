import io
import segno
from PIL import Image, ImageDraw, ImageFont
from matplotlib import font_manager
import os
from qgis.PyQt.QtCore import QSettings


class aGraeLabelGenerator():
    def __init__(self):

        self.s = QSettings('agrae','dbConnection')
        self.outpath = self.s.value('paneles_path')
        pass

    def generateQR(self,code):
        out = io.BytesIO()
        qr = segno.make_qr(code,error='H')
        qr.save(out,
            scale=10,
            kind='png',
            border=1
        )
        out.seek(0)
        return  Image.open(out)
    
    def generateLabel(self, qr : Image ,code):
        
        font = font_manager.FontProperties(family='sans-serif', weight='bold')
        font = font_manager.findfont(font)

        w_cm = 2.5
        h_cm = 3.5
        res_x,res_y = (300,300)
        f = 2.54
        w = int(w_cm / f * res_x)
        h = int(h_cm / f * res_y)

        logo = Image.open(os.path.join(os.path.dirname(__file__), r'img\logo.png'))

        label = Image.new('RGB',(w,h),color='white')

        # Get dimensions of each image
        width1, height1 = label.size
        width2, height2 = qr.size
        width3, height3 = logo.size

        center_x, center_y = (width1/2), (height1/2)

        # Offset inner image to align its center
        im2_x = round(center_x - (width2/2))
        im2_y = round(center_y - (height2/2))

        im3_x = round(center_x - (width3/2))
        im3_y = round(center_y - (height3/2)-120)

        label.paste(logo,(im3_x,30),mask=logo)

        draw = ImageDraw.Draw(label)
        font = ImageFont.truetype(font, 36)
        draw.text((w/2 ,90),code,align='center',font=font,fill=(0,0,0), anchor='mm')
        label.paste(qr,(im2_x,im2_y+40))

    
        label.save(f'{self.outpath}\\label_{code}.png',format='png')

        # label.show()
        return f'{self.outpath}\\label_{code}.png'

    
   
    


