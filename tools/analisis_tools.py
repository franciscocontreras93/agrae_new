import pandas as pd 
import numpy as np
import os
import random


file_path = r"D:\GeoSIG\aGrae\ANALITICA\CAMPAÑA_25_DUJOSAGRI_SL.csv"
df = pd.read_csv(file_path,delimiter=';',encoding='utf-8')
df = df.replace(np.nan,0).replace('#¡VALOR!',0).replace('#N/D',0)
# df = df.replace('#¡VALOR!',0)
# .replace('#N/D', 0, inplace=True)
# .replace('#¡VALOR!', 0, inplace=True)
# df = df.replace('#N/D', 0, inplace=True)
# df = df.replace('#¡VALOR!', 0, inplace=True)

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
    # new_df = df.replace('#¡VALOR!',0)
    # print(new_df)
    scope = new_df[new_df['COD'].str.contains(r'_D\d{1}',regex=True) == False]['ceap']
    scope = float(scope.iloc[0])
    # derivates = new_df[new_df['COD'].str.contains(r'_D\d{1}',regex=True) == True]['ceap']
    # # new_df['COD'].str.contains(r'_D\d{1}',regex=True)
    # print(scope)

    adjust_coefficient = {row['COD'] : 
                        {'ceap' : (((row['ceap']-scope) / scope + 1) * 100) if (((row['ceap']-scope) / scope + 1) * 100) < 200 else 200, 
                         'min':  (((row['ceap']-scope) / scope + 1) * 100) * 0.75 if (((row['ceap']-scope) / scope + 1) * 100) != 100  else 100,
                         'max': ((((row['ceap']-scope) / scope + 1) * 100) * 0.75) * 1.25 if (((row['ceap']-scope) / scope + 1) * 100) != 100  else 100 } 
                for index,row in new_df.iterrows() }
    

    for index,row in new_df.iterrows():

        min = adjust_coefficient[row['COD']]['min']
        max = adjust_coefficient[row['COD']]['max']
        rand = random.uniform(min,max)
        # print(rand)


        if rand == 100:
            scope_row = row    
        else:

            row['PH'] = rand / adjust_index['PH'] + scope_row['PH']
            row['CE'] = rand / adjust_index['CE'] + scope_row['CE']
            row['N'] = rand / adjust_index['N'] + scope_row['N']
            row['P'] = rand / adjust_index['P'] + scope_row['P']
            row['K'] = rand / adjust_index['K'] + scope_row['K']
            row['CARBON'] = scope_row['CARBON']
            row['CA'] = rand / adjust_index['CA'] + scope_row['CA']
            row['MG'] = rand / adjust_index['MG'] + scope_row['MG']
            row['NA'] = rand / adjust_index['NA'] + scope_row['NA']
            row['S'] = rand / adjust_index['S'] + scope_row['S']
            row['ZN'] = rand / adjust_index['ZN'] + scope_row['ZN']
            row['B'] = rand / adjust_index['B'] + scope_row['B']
            row['FE'] = rand / adjust_index['FE'] + scope_row['FE']
            row['MN'] = rand / adjust_index['MN'] + scope_row['MN']
            row['CU'] = rand / adjust_index['CU'] + scope_row['CU']
            row['AL'] = rand / adjust_index['AL'] + scope_row['AL']
    
# for d in data:
#     print(d)
#     new_df = pd.DataFrame(d)
#     # scope = d[1].str.contains(r'_D\d{1}',regex=True)
#     print(new_df)




        


        
    