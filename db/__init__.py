import psycopg2
import os
from qgis.PyQt.QtCore import QSettings



class agraeDataBaseDriver():
    def __init__(self) -> None:
        BASEDIR = os.path.abspath(os.path.dirname(__file__))
        os.environ['PGSERVICEFILE'] = os.path.join(BASEDIR,'pg_service.conf')
        # print(os.environ['PGSERVICEFILE'] )
    
        self.conn = None
        self.s = QSettings('agrae','dbConnection')
        self.local  = False

        if self.local and os.environ['COMPUTERNAME'] == 'FRANCISCO':
            from dotenv import load_dotenv
            load_dotenv(os.path.join(BASEDIR, '.env'))
            self.dsn = {
                'dbname': os.getenv('DBNAME'),
                'user': self.s.value('dbuser'),
                'password': self.s.value('dbpass'),
                'host': os.getenv('HOST'),
                'port': self.s.value('dbport')
            }
        else:
            self.dsn = {
                'dbname': self.s.value('dbname'),
                'user': self.s.value('dbuser'),
                'password': self.s.value('dbpass'),
                'host': self.s.value('dbhost'),
                'port': self.s.value('dbport')
            }        
        pass

    def connection(self):
        if self.local:
            return psycopg2.connect(service='local' , user=self.dsn['user'] ,password=self.dsn['password'])
        else :
            return psycopg2.connect(service='production' , user=self.dsn['user'] ,password=self.dsn['password'])
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