import psycopg2
from qgis.PyQt.QtCore import QSettings


class agraeDataBaseDriver():
    def __init__(self) -> None:

        self.conn = None
        self.s = QSettings('agrae','dbConnection')

        self.dsn = {
            'dbname': self.s.value('dbname'),
            'user': self.s.value('dbuser'),
            'password': self.s.value('dbpass'),
            'host': self.s.value('dbhost'),
            'port': self.s.value('dbport')
        }
        
        pass

    def connection(self):
        try:
            self.conn = psycopg2.connect(
                database=self.dsn['dbname'], 
                user = self.dsn['user'], 
                password = self.dsn['password'], 
                host = self.dsn['host'], 
                port = self.dsn['port'])
            if self.conn != None: 
                return self.conn
        except psycopg2.OperationalError:
            raise Exception('Error de conexion a la Base de datos')
        except psycopg2.InterfaceError : 
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


