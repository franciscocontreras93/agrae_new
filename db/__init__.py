import os
import psycopg2

from qgis.PyQt.QtCore import QSettings
from qgis.core import QgsExpressionContextUtils

from ..core.config import aGraeConfig


class agraeDataBaseDriver:
    def __init__(self) -> None:
        self.config = aGraeConfig()
        self.local = self.config.local

        self.conn = None
        self.s = QSettings("agrae", "dbConnection")

        self.pg_service_file = self._setup_pgservicefile()
        self.service_name = self.getServiceName()

        self.dsn = {
            "service": self.service_name,
            "pgservicefile": self.pg_service_file,
        }

    def _setup_pgservicefile(self) -> str:
        """
        Configura la ruta del pg_service.conf para psycopg2 y QGIS.
        El archivo debe estar en la misma carpeta que este driver:
        agrae/db/pg_service.conf
        """
        basedir = os.path.abspath(os.path.dirname(__file__))
        pg_service_file = os.path.join(basedir, "pg_service.conf")

        os.environ["PGSERVICEFILE"] = pg_service_file

        QgsExpressionContextUtils.setGlobalVariable(
            "PGSERVICEFILE",
            pg_service_file
        )

        return pg_service_file

    def getServiceName(self) -> str:
        """
        Devuelve el servicio PostgreSQL según el modo configurado.
        """
        return "agrae_local" if self.local else "agrae_prod"

    def connection(self):
        """
        Crea una conexión usando pg_service.conf.
        """
        try:
            return psycopg2.connect(service=self.getServiceName())
        except Exception as e:
            raise ConnectionError(
                f"No se pudo conectar usando service='{self.getServiceName()}'. "
                f"PGSERVICEFILE='{self.pg_service_file}'. "
                f"Error original: {e}"
            )

    def getDSN(self) -> dict:
        """
        Mantiene compatibilidad con código antiguo.
        Ahora devuelve service y pgservicefile, no credenciales.
        """
        return self.dsn

    def read(self, query):
        """
        Ejecuta una consulta SELECT y devuelve todos los resultados.
        """
        conn = self.connection()

        try:
            with conn.cursor() as cursor:
                cursor.execute(query)
                return cursor.fetchall()
        finally:
            conn.close()

    def cursor(self, connection, factory=None):
        """
        Devuelve un cursor. Si la conexión está cerrada, crea una nueva.
        """
        try:
            if connection is None or connection.closed:
                connection = self.connection()

            if factory:
                return connection.cursor(cursor_factory=factory)

            return connection.cursor()

        except psycopg2.InterfaceError:
            connection = self.connection()

            if factory:
                return connection.cursor(cursor_factory=factory)

            return connection.cursor()