import pandas as pd 
import numpy as np
import os


file_path = r'D:\GeoSIG\aGrae\ANALITICA\CAMPAÑA_25_JORGE_ESTEBANEZ_REMUESTREO.csv'
df = pd.read_csv(file_path,delimiter=';')
df = df.replace(np.nan,0)
data = {}

for i,r in df.iterrows():
    data[r['idlote']] = {}

for i,r in df.iterrows():
    if r['idlote'] in data:
        data[r['idlote']] = {
            r['COD'] : r['ceap']
        }
    
    

print(data)


        


        
    