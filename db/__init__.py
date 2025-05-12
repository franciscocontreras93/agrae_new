import psycopg2
import os
from qgis.PyQt.QtCore import QSettings
from dotenv import load_dotenv # Importar load_dotenv aquí


class agraeDataBaseDriver():
    def __init__(self) -> None:
        BASEDIR = os.path.abspath(os.path.dirname(__file__))
        os.environ['PGSERVICEFILE'] = os.path.join(BASEDIR,'pg_service.conf')
    
        self.conn = None
        self.s = QSettings('agrae','dbConnection')

        # --- Cargar .env y permitir la sobreescritura de variables de entorno existentes ---
        dotenv_path = os.path.join(BASEDIR, '.env')
        load_dotenv(dotenv_path, override=True) # Clave: override=True
        # ------------------------------------------------------------------------------------

        # Leer la variable LOCAL del entorno. Por defecto 'False' si no está.
        # Convertir a booleano: self.local será True si LOCAL en .env es 'true' (insensible a mayúsculas).
        local_env_value = os.getenv('LOCAL', 'False').strip().lower()
        self.local = local_env_value == 'true'
        
        # Obtener COMPUTERNAME de forma segura y normalizar a mayúsculas
        computer_name = os.getenv('COMPUTERNAME', '').strip().upper()

        if self.local:
            self.dsn = {
                'dbname': os.getenv('DBNAME'),
                'user': self.s.value('DBUSER'),
                'password': self.s.value('DBPASS'),
                'host': os.getenv('DBHOST'),
                'port': self.s.value('DBPORT')
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
    
        # La decisión de usar 'local' o 'production' service dependerá
        # del valor de self.local (que ahora se lee del .env)
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
        # print(connection.close)
       
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
