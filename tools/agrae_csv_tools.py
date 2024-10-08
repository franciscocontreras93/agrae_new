import pandas as pd
import numpy as np 
from  ..sql import aGraeSQLTools
from . import aGraeTools


class aGraeCSVTools():
    def __init__(self,file):
        self._df = pd.read_csv(file,delimiter=';')
        self._df = self._df.replace('#N/D', None).replace(np.NaN,None)
        self.tools = aGraeTools()



    def replace_none_data(self,value):
        if value == None: return 0 
        else: return value

    def remove_last_line_from_string(self,s:str):
        return s[:s.rfind('\n')] 
    
    def updateCultivoDataFromCSV(self):
        values = ''
        for index,row in self._df.iterrows():
            
            idcultivo = self.replace_none_data(row['idcultivo'])
            idregimen = self.replace_none_data(row['idregimen'])
            prod_esperada = self.replace_none_data(row['prod_esperada'])

            values = values + ''' select {},nullif({},0),nullif({},0),nullif({},0) \nunion'''.format(row['iddata'],idcultivo,idregimen,prod_esperada)
        
        values = self.remove_last_line_from_string(values)
        sql = aGraeSQLTools().getSql('update_data_from_csv_query.sql').format(values)
        # print(sql)
        
        with self.tools.conn.cursor() as cursor:
            try:    
                cursor.execute(sql)
                self.tools.conn.commit()
                self.tools.messages('aGrae Tools','Datos actualizados correctamente',3)
            except Exception as ex:
                self.tools.messages('aGrae Tools | error: ','Ocurrio un Error revisa el panel para mas informacion',2)
                print(ex)
                self.tools.conn.rollback()
        



# df = pd.read_csv(r"C:\Users\Francisco\OneDrive - AGRAE SOLUTIONS\General - AGRAE SOLUTIONS\10002_ARCHIVOS_DESARROLLO\99_Cesto\TEST_CSV_Cooperativa_Santabarbara\LOTES.csv",delimiter=';')
# df = df.replace('#N/D', None).replace(np.NaN,None)

# data = dict
# query = '''with values(iddata,idcultivo,idregimen,prod_esperada) as ({})'''
# values = ''
# for index,row in df.iterrows():
#     if row['idcultivo'] == None:
#         idcultivo = 0
#     else:
#         idcultivo = row['idcultivo']
    
#     if row['idregimen']== None:
#         idregimen = 0
        
#     else:
#         idregimen = row['idregimen']
#     if row['prod_esperada'] == None:
#         prod_esperada = 0
#     else:
#         prod_esperada = row['prod_esperada']

#     values = values + ''' select {},nullif({},0),nullif({},0),nullif({},0) \nunion'''.format(row['iddata'],idcultivo,idregimen,prod_esperada)

# def remove_last_line_from_string(s:str):
#     return s[:s.rfind('\n')]

# values = remove_last_line_from_string(values)
# query = query.format(values)