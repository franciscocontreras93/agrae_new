import pandas as pd 
import numpy as np
import os
import random


class aGraeResamplearMuestras():
    def __init__(self,file_path:str):
       
        self.file_path = file_path
        self.df = self.readFile(self.file_path)
        # try:
        #     df = pd.read_csv(r'{}'.format(file_path),delimiter=';',encoding='utf-8')
        # except UnicodeEncodeError:
        #     df = pd.read_csv(r'{}'.format(file_path),delimiter=';',encoding='utf-8')
        # df = df.replace(np.nan,0).replace('#¡VALOR!',0).replace('#N/D',0)
        
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
            'AL'  : 3.03    
        }


        for id in df['idlote'].unique(): 
            new_df = df[df['idlote'] == id]
            
            scope = list(new_df[new_df['COD'].str.contains(r'_D\d{1}',regex=True) == False]['ceap'])
            scope = scope[-1]
            derivates = list(new_df[new_df['COD'].str.contains(r'_D\d{1}',regex=True) == True]['ceap'])
            # # new_df['COD'].str.contains(r'_D\d{1}',regex=True)
            # print(scope[-1],derivates)

            if len(derivates) > 0:
                adjust_coefficient = {row['COD'] : 
                                    {'ceap' : (((row['ceap']-scope) / scope + 1) * 100) if (((row['ceap']-scope) / scope + 1) * 100) < 200 else 200, 
                                     'min':  (((row['ceap']-scope) / scope + 1) * 100) * 0.75 if (((row['ceap']-scope) / scope + 1) * 100) != 100  else 100,
                                     'max': ((((row['ceap']-scope) / scope + 1) * 100) * 0.75) * 1.25 if (((row['ceap']-scope) / scope + 1) * 100) != 100  else 100 } 
                            for index,row in new_df.iterrows() }
                # print(adjust_coefficient)
                scope_row = None
                for index,row in new_df.iterrows():

                    min = adjust_coefficient[row['COD']]['min']
                    max = adjust_coefficient[row['COD']]['max']
                    
                    rand = random.uniform(min,max)

                    
                    if rand == 100:
                        scope_row = row
                    
                    if '_D' in row['COD']:
                        try:
                            row['PH'] = rand / adjust_index['PH'] + scope_row['PH']
                            row['CE'] = rand / adjust_index['CE'] + scope_row['CE']
                            row['N'] = rand / adjust_index['N'] + scope_row['N']
                            row['P'] = rand / adjust_index['P'] + scope_row['P']
                            row['K'] = rand / adjust_index['K'] + scope_row['K']
                            row['CARBON'] = scope_row['CARBON']
                            row['CA'] = rand / adjust_index['CA'] + scope_row['CA']
                            row['MG'] = rand / adjust_index['MG'] + scope_row['MG']
                            row['NA'] = rand / adjust_index['NA'] + scope_row['NA']
                            if row['S'] != 0 : 
                                row['S'] = rand / adjust_index['S'] + scope_row['S'] 
                            else: 
                                row['S'] = 0 
                            row['ZN'] = rand / adjust_index['ZN'] + scope_row['ZN']
                            if row['B'] != 0 : 
                                row['B'] = rand / adjust_index['B'] + scope_row['B']
                            else:
                                row['B'] = 0
                            row['FE'] = rand / adjust_index['FE'] + scope_row['FE']
                            row['MN'] = rand / adjust_index['MN'] + scope_row['MN']
                            row['CU'] = rand / adjust_index['CU'] + scope_row['CU']
                            row['AL'] = rand / adjust_index['AL'] + scope_row['AL']
                            row['METODO_P'] = scope_row['METODO_P']
                        except Exception as ex:
                            print(ex)
                    
                    df_procesado.loc[index] = row
            

        # df_procesado = df_procesado.drop(columns=['idlote'])
        # print(df_procesado)
        file_name = '{}_procesado.csv'.format(os.path.splitext(os.path.basename(self.file_path))[0])
        out = os.path.join(os.path.dirname(self.file_path),file_name)
        # print(out)
        df_procesado.to_csv(out,sep=';',index=False)


#* REEPLAZAR EL PATH POR LA RUTA DND ESTA EL ARCHIVO

# file_path = r"C:\Users\Francisco\Downloads\Telegram Desktop\CAMPAÑA_25_JONATHAN_GARCIA.csv" 

# modulo = aGraeResamplearMuestras(file_path)
# modulo.processing()

        


        
    