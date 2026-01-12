import pandas as pd 
import numpy as np
import os
import random


class aGraeResamplearMuestras():
    def __init__(self,file_path:str):
       
        self.file_path = file_path
        self.df = self.readFile(self.file_path)
        self.df = self.df.replace(np.nan,0).replace('#¡VALOR!',0).replace('#N/D',0)
        
        pass

    def readFile(self,file_path):
        encodings = ['utf-8','iso-8859-1','windows-1252','iso-8859-2','ascii']
        encoded = False
        while encoded == False:
            for enc in encodings:
                try:
                    df = pd.read_csv(r'{}'.format(file_path),delimiter=';',encoding=enc)
                    encoded = True
                    return df
                except UnicodeEncodeError:
                    encoded = False
                    print('Cambiando esquema de codificacion')

    def processing(self):
        df = self.df
        df_procesado = pd.DataFrame(columns=df.columns)
        adjust_index = {
            'PH' : -476.00,
            'CE' : 10.00,
            'N' : 198047,
            'P'  : -8.21,
            'K' : 2.66,
            'CA' : -0.44,
            'MG' : 11.55,
            'NA': -9.25,
            'S' : -6.88,
            'ZN': 5.27,
            'B' : 102.00,
            'FE' : -82.36,
            'MN' : -7.24,
            'CU' : 36.60,
            'AL'  : 3.03,
            'NO3' : 198047 / 10000,
            'NH4' : 198047 / 10000
        }


        for id in df['idlote'].unique():
            try:
                new_df = df[df['idlote'] == id]
                
                scope = list(new_df[new_df['COD'].str.contains(r'_D\d{1}',regex=True) == False]['ceap'])
                # print(scope)
                scope = min(scope)
                derivates = list(new_df[new_df['COD'].str.contains(r'_D\d{1}',regex=True) == True]['ceap'])


                if len(derivates) > 0:
                    adjust_coefficient = {row['COD'] : 
                                        {'ceap' : (((row['ceap']-scope) / scope + 1) * 100) if (((row['ceap']-scope) / scope + 1) * 100) < 200 else 200, 
                                        'min':  ((((row['ceap']-scope) / scope + 1) * 100) if (((row['ceap']-scope) / scope + 1) * 100) < 200 else 200) * 0.75 if ((((row['ceap']-scope) / scope + 1) * 100) if (((row['ceap']-scope) / scope + 1) * 100) < 200 else 200) != 100  else 100,
                                        'max': (((((row['ceap']-scope) / scope + 1) * 100) if (((row['ceap']-scope) / scope + 1) * 100) < 200 else 200) * 0.75) * 1.25 if ((((row['ceap']-scope) / scope + 1) * 100) if (((row['ceap']-scope) / scope + 1) * 100) < 200 else 200) != 100  else 100 
                                        } 
                                for index,row in new_df.iterrows() }
                    scope_row = None
                    for index,row in new_df.iterrows():

                        min_v = adjust_coefficient[row['COD']]['min']
                        max_v = adjust_coefficient[row['COD']]['max']
                        
                        rand = random.uniform(min_v,max_v)
                        
                        if rand == 100:
                            scope_row = row
                            # END LOPP
                    
                    for index,row in new_df.iterrows():   
                        if '_D' in row['COD'] and row['N'] == float(0):
                            
                            try:
                                ph = rand / adjust_index['PH'] + scope_row['PH']
                                row['PH'] = ph if ph > 0 else ph * -1
                                ce = rand / adjust_index['CE'] + scope_row['CE']
                                row['CE'] = ce if ce > 0 else ce * -1
                                
                                nit = rand / adjust_index['N'] + scope_row['N']
                                if nit > 2 * scope_row['N']:
                                    nit = rand / 100 * scope_row['N']
                                row['N'] = nit if nit > 0 else nit * -1
                                
                                p = rand / adjust_index['P'] + scope_row['P']
                                if p < 0 :
                                    p = p * -1

                                row['P'] = p if p >= 0 else p * -1
                                k = rand / adjust_index['K'] + scope_row['K']
                                row['K'] = k if k >= 0 else k * -1   
                                carb = scope_row['CARBON']
                                row['CARBON'] = carb if carb >= 0 else carb * -1
                                ca = rand / adjust_index['CA'] + scope_row['CA']
                                row['CA'] = ca if ca >= 0 else ca * -1
                                mg = rand / adjust_index['MG'] + scope_row['MG']
                                row['MG'] = mg if mg >= 0 else mg * -1
                                na = rand / adjust_index['NA'] + scope_row['NA']
                                row['NA'] = na if na >= 0 else na * -1   
                                if row['S'] != 0 : 
                                    row['S'] = rand / adjust_index['S'] + scope_row['S'] 
                                else: 
                                    row['S'] = 0 
                                zn = rand / adjust_index['ZN'] + scope_row['ZN']
                                row['ZN'] = zn if zn >= 0 else zn * -1
                                
                                b = rand / adjust_index['B'] + scope_row['B']
                                row['B'] = b if b >= 0 else b * -1

                                fe = rand / adjust_index['FE'] + scope_row['FE']
                                row['FE'] = fe if fe >= 0 else fe * -1
                                mn = rand / adjust_index['MN'] + scope_row['MN']
                                row['MN'] = mn if mn >= 0 else mn * -1
                                cu = rand / adjust_index['CU'] + scope_row['CU']
                                row['CU'] = cu if cu >= 0 else cu * -1
                                al = rand / adjust_index['AL'] + scope_row['AL']
                                row['AL'] = al if al >= 0 else al * -1
                                no3 = round(rand / (adjust_index['N'] / 10000) + scope_row['NO3'])
                                row['NO3'] = round(no3, 2) if no3 >= 0 else round(no3 * -1, 2)
                                nh4 = round(rand / (adjust_index['N'] / 10000) + scope_row['NH4'])
                                row['NH4'] = round(nh4, 2) if nh4 >= 0 else round(nh4 * -1, 2)
                                row['METODO_P'] = scope_row['METODO_P']

                            except Exception as ex:
                                print(ex)
                        rand = random.uniform(min_v,max_v)
                        df_procesado.loc[index] = row
            except Exception as ex:
                print(id,ex)
                pass 
            
        file_name = '{}_procesado.csv'.format(os.path.splitext(os.path.basename(self.file_path))[0])
        out = os.path.join(os.path.dirname(self.file_path),file_name)
        df_procesado.to_csv(out,sep=';',index=False)


#* REEPLAZAR EL PATH POR LA RUTA DND ESTA EL ARCHIVO

# file_path = r"C:\Users\Francisco\Downloads\Telegram Desktop\PRUEBA_2_procesado.csv"

# modulo = aGraeResamplearMuestras(file_path)
# modulo.processing()

        


        
    