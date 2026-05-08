from numpy import dot
import psycopg2
import os
from qgis.PyQt.QtCore import QSettings

from ..core.config import aGraeConfig


class agraeDataBaseDriver():
    def __init__(self) -> None:

        self.config = aGraeConfig()
        self.local = self.config.local

        BASEDIR = os.path.abspath(os.path.dirname(__file__))
        os.environ['PGSERVICEFILE'] = os.path.join(BASEDIR, 'pg_service.conf')

        self.conn = None
        self.s = QSettings('agrae', 'dbConnection')

        if self.local:
            self.dsn = {
                'dbname': os.getenv('DBNAME'),
                'user': os.getenv('DBUSER'),
                'password': os.getenv('DBPASSWORD'),
                'host': os.getenv('HOST'),
                'port': os.getenv('DBPORT')
            }
        else:
            self.dsn = {
                'dbname': self.s.value('dbname'),
                'user': self.s.value('dbuser'),
                'password': self.s.value('dbpass'),
                'host': self.s.value('dbhost'),
                'port': self.s.value('dbport')
            }

    def getServiceName(self):
        return 'agrae_local' if self.local else 'agrae_prod'

    def connection(self):
        # if self.local:
        #     return psycopg2.connect(service='local' , user=self.dsn['user'] ,password=self.dsn['password'])
        # else :
        #     return psycopg2.connect(service='production' , user=self.dsn['user'] ,password=self.dsn['password'])
        return psycopg2.connect(service=self.getServiceName() )
    
    def getDSN(self):
        return self.dsn
    
    def read(self,query) : 
        conn = self.connection() 

        with conn.cursor() as cursor: 
            cursor.execute(query)
            data =  cursor.fetchall()
            return data
        
    def cursor(self,connection,factory=None):
        try:
            conn = connection
            if factory:
                cursor = conn.cursor(cursor_factory=factory)
            else: 
                cursor = conn.cursor()

        except psycopg2.InterfaceError as ie:
            cursor.close()
            connection.close()

            if factory:
                cursor = conn.cursor(cursor_factory=factory)
            else: 
                cursor = conn.cursor()
            pass

        return cursor