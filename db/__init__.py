import psycopg2
from qgis.PyQt.QtCore import QSettings


class agraeDataBaseDriver():
    def __init__(self) -> None:

        self.conn = None
        self.s = QSettings('agrae','dbConnection')

        # self.dsn = {
        #     'dbname': self.s.value('dbname'),
        #     'user': self.s.value('dbuser'),
        #     'password': self.s.value('dbpass'),
        #     'host': self.s.value('dbhost'),
        #     'port': self.s.value('dbport')
        # }
        self.dsn = {
            'dbname': 'agrae_migrate',
            'user': self.s.value('dbuser'),
            'password': self.s.value('dbpass'),
            'host': self.s.value('dbhost'),
            'port': self.s.value('dbport')
        }
        
        pass

    def connection(self):
        self.conn = psycopg2.connect(
            database=self.dsn['dbname'], 
            user = self.dsn['user'], 
            password = self.dsn['password'], 
            host = self.dsn['host'], 
            port = self.dsn['port'])
        if self.conn != None: 
            return self.conn
        
    def getDSN(self):
        return self.dsn
        



