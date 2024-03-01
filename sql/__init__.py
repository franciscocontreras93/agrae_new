import os

class aGraeSQLTools():
    def __init__(self):
        self.path = os.path.dirname(__file__)
        pass

    def getSql(self,file:str):
        filePath = os.path.join(self.path,file)
        with open(filePath,'r') as fd:
            sql = fd.read()
            fd.close()
            return sql
        
    

