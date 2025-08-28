import os
import csv
import traceback # Para el manejo de excepciones
import time
from datetime import datetime, timedelta # <--- Añadir timedelta


# from datetime import date
from psycopg2 import InterfaceError, errors, extras


from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtWidgets import (
    QAction,
    QDialog,
    QGridLayout,
    QVBoxLayout,
    QGroupBox,
    QLabel,
    QToolButton,
    QComboBox,
    QMessageBox,
    QFileDialog,
    QTreeWidget, QTreeWidgetItem, # Para el dashboard
    QSplitter, # Para dividir el espacio
    QPushButton, # Para el botón de actualizar
    QWidget,
    QMenu
    )
from qgis.PyQt.QtGui import QColor # <--- Añadimos esta línea
from qgis.PyQt.QtCore import pyqtSignal, QSettings, QVariant, Qt, QSize, QRegExp
from qgis.core import *
from qgis.gui import *
from qgis.utils import iface
from qgis.PyQt.QtXml import QDomDocument
from qgis.PyQt import uic

import psycopg2
# Para el gráfico
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import numpy as np

from ..gui import agraeGUI
from ..db import agraeDataBaseDriver
from ..sql import aGraeSQLTools
from ..tools import aGraeTools
from ..tools.analisis_tools import aGraeResamplearMuestras

from ..gui.CustomLineEdit import CustomLineEdit
from ..gui.CustomLineSearch import CustomLineSearch
from ..gui.CustomTable import CustomTable
from ..gui.CustomTableView import (CustomTableView,CustomTableModel)
from ..gui.CustomPushButton import CustomPushButton

from .analitica_dialogs import agraeAnaliticaDialog

def formatear_tiempo_transcurrido(fecha_creacion_dt):
    """
    Formatea el tiempo transcurrido desde una fecha dada.
    fecha_creacion_dt: objeto datetime de la fecha de creación.
    """
    if not fecha_creacion_dt:
        return "-"
    
    ahora = datetime.now()
    # Asegurarse de que fecha_creacion_dt sea un objeto datetime
    if isinstance(fecha_creacion_dt, datetime):
        fecha_creacion_dt_completa = fecha_creacion_dt
    else: # Asumimos que es un objeto date
        fecha_creacion_dt_completa = datetime.combine(fecha_creacion_dt, datetime.min.time())
    diferencia = ahora - fecha_creacion_dt_completa

    dias = diferencia.days
    segundos = diferencia.seconds

    if dias >= 365:
        anios = dias // 365
        return f"Hace {anios} año{'s' if anios > 1 else ''}"
    elif dias >= 30:
        meses = dias // 30
        return f"Hace {meses} mes{'es' if meses > 1 else ''}"
    elif dias >= 7:
        semanas = dias // 7
        return f"Hace {semanas} semana{'s' if semanas > 1 else ''}"
    elif dias > 1:
        return f"Hace {dias} días"
    elif dias == 1:
        return "Ayer"
    else: # Si son 0 días, mostrar "Hoy" o un detalle más fino si se desea
        return "Hoy"


# Canvas para Matplotlib
class MplCanvasLab(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super(MplCanvasLab, self).__init__(self.fig)
        self.setParent(parent)
        try: # Intentar hacer el fondo transparente
            self.fig.patch.set_facecolor('None')
            self.fig.patch.set_alpha(0)
            self.axes.patch.set_facecolor('None')
            self.axes.patch.set_alpha(0)
        except Exception:
            pass # No es crítico si falla
    
    def plot_muestras_pendientes_donut(self, sumas_muestras):
        """
        Genera un gráfico de donut para las sumas de muestras.
        sumas_muestras: tupla/lista con (total_general, total_muestreadas, total_procesadas)
        """
        self.axes.cla()
        if not sumas_muestras or sum(sumas_muestras) == 0: # También verifica si la suma es 0
            self.axes.text(0.5, 0.5, 'No hay datos para graficar',
                           horizontalalignment='center', verticalalignment='center',
                           transform=self.axes.transAxes)
            self.draw()
            return

        total_general, total_muestreadas, total_procesadas = sumas_muestras

        # Calculamos las categorías para el donut
        pendientes_muestrear = total_muestreadas
        muestreadas_no_procesadas = total_procesadas
        # procesadas ya es total_procesadas

        labels_segmento = [] # Para las etiquetas dentro de los segmentos (solo números)
        sizes = []
        colors = []
        legend_labels = [] # Para la leyenda

        if pendientes_muestrear > 0:
            labels_segmento.append(f'{pendientes_muestrear}')
            legend_labels.append(f'Pend. Muestrear: {pendientes_muestrear}')
            sizes.append(pendientes_muestrear)
            colors.append('#ff9999') # Rojo claro
        if muestreadas_no_procesadas > 0:
            labels_segmento.append(f'{muestreadas_no_procesadas}')
            legend_labels.append(f'Muestr. No Proc.: {muestreadas_no_procesadas}')
            sizes.append(muestreadas_no_procesadas)
            colors.append('#ffcc66') # Naranja claro
        if total_procesadas > 0:
            labels_segmento.append(f'{total_general-(total_procesadas+total_muestreadas)}')
            legend_labels.append(f'Procesadas: {total_general-(total_procesadas+total_muestreadas)}')
            sizes.append(total_general-(total_procesadas+total_muestreadas))
            colors.append('#b2df8a') # Verde claro

        if not sizes: # Si todas las categorías son 0 (ej. total_general es 0)
            self.axes.text(0.5, 0.5, 'No hay muestras pendientes o procesadas', horizontalalignment='center', verticalalignment='center', transform=self.axes.transAxes)
            self.draw()
            return
        
        wedges, texts = self.axes.pie(sizes, colors=colors, startangle=90, wedgeprops=dict(width=0.4, edgecolor='w'), labels=labels_segmento, labeldistance=0.7)

        for text_obj in texts:
            text_obj.set_color('black') 
            text_obj.set_fontsize(9)

        self.axes.set_title('Estado General de Muestras')
        self.axes.axis('equal')  
        
        self.axes.legend(wedges, legend_labels, title="Categorías", loc="best")

        self.fig.tight_layout() 
        self.draw()

class GestionLaboratorioDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.tools = aGraeTools()
        self.UIComponents()
        
    
    def UIComponents(self):
        self.setWindowTitle('aGrae Tools | Gestion de Muestras y Analiticas')
        self.resize(1200,700) 

        main_dialog_layout = QVBoxLayout(self)
        
        # Crear y añadir combo_campania fuera y encima del QTabWidget
        group_campania_principal = QGroupBox("Selección de Campaña Principal")
        layout_campania_principal = QHBoxLayout(group_campania_principal)
        self.combo_campania = QComboBox() # Se instancia aquí
        layout_campania_principal.addWidget(QLabel("Campaña:"))
        layout_campania_principal.addWidget(self.combo_campania)
        main_dialog_layout.addWidget(group_campania_principal) # Añadir al layout principal

        self.tab_widget = QTabWidget()
        main_dialog_layout.addWidget(self.tab_widget)

        self.getCampaniasData() # Llamar después de instanciar combo_campania principal

        # --- Tab 1: Muestras Pendientes (Nueva) ---
        self.tab_muestras_pendientes = QWidget()
        layout_muestras_pendientes = QVBoxLayout(self.tab_muestras_pendientes)
        
        splitter_pendientes = QSplitter(Qt.Vertical) 

        self.tree_muestras_pendientes = QTreeWidget()
        self.tree_muestras_pendientes.setHeaderLabels(["Explotación", "Fecha Creación", "M. Totales", "Pend. Muestrear", "Pend. Procesar", "Estado"])
        self.tree_muestras_pendientes.setColumnWidth(0, 200) 
        self.tree_muestras_pendientes.setColumnWidth(1, 150)
        self.tree_muestras_pendientes.setColumnWidth(2, 100) 
        self.tree_muestras_pendientes.setColumnWidth(3, 120) 
        self.tree_muestras_pendientes.setColumnWidth(4, 120) 
        self.tree_muestras_pendientes.setColumnWidth(5, 250) 
        self.tree_muestras_pendientes.itemDoubleClicked.connect(self.on_dashboard_tree_item_double_clicked)
        splitter_pendientes.addWidget(self.tree_muestras_pendientes)

        self.canvas_muestras_pendientes = MplCanvasLab(self)
        splitter_pendientes.addWidget(self.canvas_muestras_pendientes)
        
        splitter_pendientes.setSizes([int(self.height() * 0.5), int(self.height() * 0.5)]) 

        layout_muestras_pendientes.addWidget(splitter_pendientes)
        
        
        
        self.tab_widget.addTab(self.tab_muestras_pendientes, "Dashboard Muestras Pendientes")

        # --- Tab 2: Gestión General de Muestras (Interfaz Actual) ---
        self.tab_gestion_general = QWidget()
        layout_gestion_general = QVBoxLayout(self.tab_gestion_general)

        # self.combo_campania = QComboBox() # Movido fuera
        self.combo_explotacion = QComboBox()
        self.combo_explotacion.setEditable(True)
        self.combo_explotacion.setInsertPolicy(QComboBox.NoInsert)
        # self.getCampaniasData() # Se llama arriba
        
        self.table = CustomTable(
            columns=['iddata','Campaña','Explotacion','Lote','Codigo','Prioridad','Tipo Muestra','Estado Analitica','Estado de Muestreo','Observaciones'],
            data = [] 
        )
        # self.updateTable() # Se llamará cuando cambie la campaña
        
        # La conexión de combo_campania se hace una vez que se crea el combo principal
        self.combo_explotacion.currentIndexChanged.connect(self.updateTable)
        
        self.toolButton = QToolButton()
        self.toolButton.setMenu(QMenu())
        self.toolButton.setPopupMode(QToolButton.MenuButtonPopup)
        self.toolButton.setIconSize(QSize(15,15))
        self.toolMenu = self.toolButton.menu()
        self.toolMenu.addSeparator().setText('Gestion de Muestras')

        self.ExportarDataCSV = QAction(agraeGUI().getIcon('csv'),'Exportar informacion de Explotacion a CSV',self)
        self.ExportarDataCSV.triggered.connect(self.exportarDataCSV)
        self.CargarCapaMuestras = QAction(agraeGUI().getIcon('pois'),'Cargar Capa de Muestras',self)
        self.CargarCapaMuestras.triggered.connect(self.loadLayerMuestreo)
        self.GenerarArchivoLaboratorio = QAction(agraeGUI().getIcon('csv'),'Generar Archivo de Laboratorio',self)
        self.GenerarArchivoLaboratorio.triggered.connect(self.crearFormatoAnalitica)
        self.ImportarArchivoAnalisis = QAction(agraeGUI().getIcon('import'),'Cargar Archivo de Laboratorio',self)
        self.ImportarArchivoAnalisis.triggered.connect(self.cargarAnalitica)
        self.DerivarDatosAnalisis = QAction(agraeGUI().getIcon('csv'),'Derivar datos de Analitica',self)
        self.DerivarDatosAnalisis.triggered.connect(self.DerivarAnalitica)
        self.GenerarReporteAnalitica = QAction(agraeGUI().getIcon('chart-bar-2'),'Generar reporte de Laboratorio (Campaña)',self)
        self.GenerarReporteAnalitica.triggered.connect(self.generarReporteAnalitica)
        self.DerivarMuestrasPendientes = QAction(agraeGUI().getIcon('pois'),'Derivar Parcelas cercanas',self)
        self.DerivarMuestrasPendientes.triggered.connect(self.derivar_muestras_cercanas)

        self.toolMenu.addAction(self.GenerarArchivoLaboratorio)
        self.toolMenu.addAction(self.ImportarArchivoAnalisis)
        self.toolMenu.addAction(self.DerivarDatosAnalisis)
        self.toolMenu.addAction(self.DerivarMuestrasPendientes)
        self.toolMenu.addSeparator().setText('Gestion de Laboratorio')
        self.toolMenu.addAction(self.CargarCapaMuestras)
        self.toolMenu.addAction(self.ExportarDataCSV)
        self.toolMenu.addAction(self.GenerarReporteAnalitica)
        self.toolButton.setIcon(agraeGUI().getIcon('tools'))
        
        group_combos = QGroupBox()
        layout_group_combos = QGridLayout()
        # layout_group_combos.addWidget(QLabel('Seleccionar Campaña'),0,0) # Movido
        layout_group_combos.addWidget(QLabel('Seleccionar Explotacion'),0,0) # Ajustar columna
        # layout_group_combos.addWidget(self.combo_campania,1,0) # Movido
        layout_group_combos.addWidget(self.combo_explotacion,1,0) # Ajustar columna
        layout_group_combos.addWidget(self.toolButton,1,1) # Ajustar columna
        group_combos.setLayout(layout_group_combos)

        layout_gestion_general.addWidget(group_combos)
        layout_gestion_general.addWidget(self.table)
        self.tab_gestion_general.setLayout(layout_gestion_general)
        self.tab_widget.addTab(self.tab_gestion_general, "Gestión General")

        # Conectar la señal del combo_campania principal a las actualizaciones
        self.combo_campania.currentIndexChanged.connect(self.on_campania_principal_changed)

        self.tab_widget.setCurrentIndex(0) 

        self.toolMenu.setStyleSheet('''
        QMenu {
            padding:5px;               }
''')
        # Cargas iniciales
        if self.combo_campania.count() > 0:
            self.on_campania_principal_changed() # Esto llamará a las 3 actualizaciones
        else: # Si no hay campañas, al menos intenta limpiar/inicializar
            self.actualizar_dashboard_muestras_pendientes()
            self.updateTable()


    def on_campania_principal_changed(self):
        self.getExplotacionData(self.combo_campania.currentData()) 
        self.updateTable() 
        self.actualizar_dashboard_muestras_pendientes() 


    def getCampaniasData(self):
        self.combo_campania.clear()
        try:
            with self.tools.conn.cursor() as cursor:
                cursor.execute('''SELECT DISTINCT concat(upper(prefix),'-',UPPER(nombre)) as nombre , id  FROM campaign.campanias ORDER BY id desc''')
                data_camp = cursor.fetchall()
                for e in data_camp:
                    self.combo_campania.addItem(e[0],e[1])
            # No llamar a getExplotacionData aquí directamente, se hará en on_campania_principal_changed o al final de UIComponents
        except Exception as e:
            QgsMessageLog.logMessage(f"Error en getCampaniasData: {e}\n{traceback.format_exc()}", "aGrae Lab", Qgis.Critical)
            self.combo_explotacion.clear()


    def getExplotacionData(self,idcampania):
        self.combo_explotacion.clear()
        if idcampania is None: 
            return

        sql = '''select distinct e.nombre , d.idexplotacion from campaign.data d
        join campaign.campanias c on c.id = d.idcampania 
        join agrae.explotacion e on e.idexplotacion = d.idexplotacion 
        where c.id = %s
        order by e.nombre'''
        
        try:
            with self.tools.conn.cursor() as cursor:
                cursor.execute(sql, (idcampania,))
                data = cursor.fetchall()
                explotaciones_para_completer = []
                if data:
                    for e in data:
                        nombre_exp = f"{e[1]}-{e[0]}" 
                        self.combo_explotacion.addItem(nombre_exp, e[1])
                        explotaciones_para_completer.append(nombre_exp)
                
                exp_completer = self.tools.dataCompleter(data_combo=explotaciones_para_completer)
                self.combo_explotacion.setCompleter(exp_completer)
        except Exception as e:
            QgsMessageLog.logMessage(f"Error en getExplotacionData: {e}\n{traceback.format_exc()}", "aGrae Lab", Qgis.Critical) # type: ignore


    def updateTable(self):
        idcampania = self.combo_campania.currentData() # Usa el combo principal
        idexplotacion = self.combo_explotacion.currentData()

        if idcampania is None or idexplotacion is None:
            self.table.populate([]) 
            return

        try:
            query_muestreo = aGraeSQLTools().getSql('muestreo_data_query.sql').format(
                idcampania,
                idexplotacion,
                'select iddata,campania,explotacion,lote,codigo,prioridad,tipo_muestra,status_lab, status,observaciones from muestras'
            )
            data_muestreo = agraeDataBaseDriver().read(query_muestreo)
            self.table.populate(data_muestreo)
        except Exception as e:
            QgsMessageLog.logMessage(f"Error al actualizar tabla de muestras: {e}\n{traceback.format_exc()}", "aGrae Lab", Qgis.Critical) # type: ignore
            self.table.populate([])


    def exportarDataCSV(self):
        idcampania = self.combo_campania.currentData() # Usa el combo principal
        idexplotacion = self.combo_explotacion.currentData()
        if idcampania is None or idexplotacion is None:
            self.tools.messages('aGrae Tools','Por favor, seleccione una campaña y explotación.', Qgis.Warning)
            return

        outputh_path, _ = QFileDialog.getSaveFileName(self, "Guardar CSV", f"REPORTE_MUESTREO_{self.combo_explotacion.currentText()}.csv", "CSV Files (*.csv)")
        if not outputh_path:
            return

        output_query = '''copy ({}) to stdout  with csv header delimiter ';' ; '''.format(aGraeSQLTools().getSql('muestreo_data_query.sql').format(idcampania,idexplotacion,'select iddata,campania,explotacion,lote,codigo,prioridad,status_mues,status_lab from muestras'))
        try:
            with open(outputh_path,'w', newline='', encoding='utf-8') as file: 
                with self.tools.conn.cursor() as cur:
                    cur.copy_expert(output_query,file)
            self.tools.messages('aGrae Tools','Archivo exportado Correctamente', Qgis.Success) # type: ignore
        except Exception as e:
            QgsMessageLog.logMessage(f"Error al exportar CSV: {e}\n{traceback.format_exc()}", "aGrae Lab", Qgis.Critical) # type: ignore
            self.tools.messages('aGrae Tools',f'Error al exportar: {e}', Qgis.Critical) # type: ignore


    def loadLayerMuestreo(self):
        idcampania = self.combo_campania.currentData() # Usa el combo principal
        idexplotacion = self.combo_explotacion.currentData()
        if idcampania is None or idexplotacion is None:
            self.tools.messages('aGrae Tools','Por favor, seleccione una campaña y explotación.', Qgis.Warning) # type: ignore
            return

        query = aGraeSQLTools().getSql('muestreo_data_query.sql').format(idcampania,idexplotacion,'select row_number() over () as id, * from muestras')
        try:
            muestras = self.tools.getDataBaseLayer(query,'{}-{}'.format(self.combo_campania.currentText(),self.combo_explotacion.currentText()),'muestreo_status',geometry='MultiPoint')
            if muestras.isValid():
                QgsProject.instance().addMapLayer(muestras)
                iface.mapCanvas().setExtent(muestras.extent())
            else:
                self.tools.messages('aGrae Tools','No se pudo cargar la capa de muestras.', Qgis.Warning) # type: ignore
        except Exception as e:
            QgsMessageLog.logMessage(f"Error al cargar capa de muestreo: {e}\n{traceback.format_exc()}", "aGrae Lab", Qgis.Critical) # type: ignore
            self.tools.messages('aGrae Tools',f'Error al cargar capa: {e}', Qgis.Critical)


    def crearFormatoAnalitica(self):
        idcampania = self.combo_campania.currentData() # Usa el combo principal
        idexplotacion = self.combo_explotacion.currentData()
        if idcampania is None or idexplotacion is None:
            self.tools.messages('aGrae Tools','Por favor, seleccione una campaña y explotación.', Qgis.Warning) # type: ignore
            return

        exp_text = self.combo_explotacion.currentText().split('-')
        exp_nombre_limpio = exp_text[1] if len(exp_text) > 1 else exp_text[0]
        exp_nombre_limpio = exp_nombre_limpio.replace(' ','_')
        camp_nombre_limpio  = self.combo_campania.currentText()[2:].replace(' ','_')
        name = '{}_{}'.format(camp_nombre_limpio,exp_nombre_limpio)

        reply = QMessageBox.question(self,'aGrae Toolbox','Quieres generar el archivo de Analitica para la explotacion:\n{}?'.format(name),QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                self.tools.crearFormatoAnalitica(idcampania,idexplotacion,name)
            except Exception as e:
                QgsMessageLog.logMessage(f"Error al crear formato analítica: {e}\n{traceback.format_exc()}", "aGrae Lab", Qgis.Critical) # type: ignore
                self.tools.messages('aGrae Tools',f'Error: {e}', Qgis.Critical)

    
    def cargarAnalitica(self):
        try:
            data = self.tools.cargarReporteAnalitica()
            if data is not None and not data.empty:
                dlg = agraeAnaliticaDialog(data)
                dlg.exec()
        except Exception as e:
            QgsMessageLog.logMessage(f"Error al cargar analítica: {e}\n{traceback.format_exc()}", "aGrae Lab", Qgis.Critical) # type: ignore
            self.tools.messages('aGrae Tools',f'Error: {e}', Qgis.Critical) # type: ignore

    
    def DerivarAnalitica(self):
        try:
            file = self.tools.cargarReporteAnalitica(dataframe=False)
            if file:
                modulo = aGraeResamplearMuestras(file)
                modulo.processing()
                self.tools.messages('aGrae GIS','Archivo procesado Correctamente', Qgis.Success, True) # type: ignore
        except Exception as e:
            QgsMessageLog.logMessage(f"Error al derivar analítica: {e}\n{traceback.format_exc()}", "aGrae Lab", Qgis.Critical) # type: ignore
            self.tools.messages('aGrae GIS',f'Error: {e}', Qgis.Critical) # type: ignore

    
    def generarReporteAnalitica(self):
        idcampania = self.combo_campania.currentData() # Usa el combo principal
        if idcampania is None: 
            self.tools.messages('aGrae Tools','Por favor, seleccione una campaña.', Qgis.Warning) # type: ignore
            return

        outputh_path, _ = QFileDialog.getSaveFileName(self, "Guardar CSV", f"REPORTE_GENERAL_{self.combo_campania.currentText()}.csv", "CSV Files (*.csv)")
        if not outputh_path:
            return

        output_query = '''copy ({}) to stdout  with csv header delimiter ';' ; '''.format(aGraeSQLTools().getSql('reporte_muestras_general.sql').format(idcampania))
        try:
            with open(outputh_path,'w', newline='', encoding='utf-8') as file:
                with self.tools.conn.cursor() as cur:
                    cur.copy_expert(output_query,file)
            self.tools.messages('aGrae Tools','Archivo exportado Correctamente', Qgis.Success) # type: ignore
        except Exception as e:
            QgsMessageLog.logMessage(f"Error al generar reporte analítica: {e}\n{traceback.format_exc()}", "aGrae Lab", Qgis.Critical) # type: ignore
            self.tools.messages('aGrae Tools',f'Error: {e}', Qgis.Critical) # type: ignore


    def derivar_muestras_cercanas(self):
        idcampania = self.combo_campania.currentData() # Usa el combo principal
        idexplotacion = self.combo_explotacion.currentData()
        if idcampania is None or idexplotacion is None:
            self.tools.messages('aGrae Tools','Por favor, seleccione una campaña y explotación.', Qgis.Warning) # type: ignore
            return

        numero_de_muestras = 2 
        query = '''with muestras as (select * from field.muestras where idcampania = %s and idexplotacion = %s),
        muestreadas as (select * from muestras where muestreado = true),
        derivadas as (select * from muestras where tipo = 2),
        procesadas as (select a.*,m.geom from muestras m join analytic.analitica a on a.cod = m.codigo ),
        pendientes as (select * from derivadas d  where d.codigo not in (select cod from procesadas)  and codigo ilike '%_D1%'),
        segmentos as (select p.codigo,s.ceap from agrae.segmentos s join pendientes p on st_intersects(s.geometria, p.geom)),
        cercanas as (select p.codigo ,c.cod,s.ceap, st_makeLine(st_centroid(p.geom),st_centroid(c.geom)) matriz_distancia, c.dist,p.geom from pendientes p
        cross join lateral (select pr.codigo as cod,round(st_transform(pr.geom,3857) <-> st_transform(p.geom,3857)) as dist, pr.geom  from muestreadas pr order by dist limit %s) as c
        join segmentos  s using(codigo)),
        data_unida as (select c.codigo,c.ceap,avg(ph) ph,avg(ce) ce,avg(carbon) carbon,avg(caliza) caliza,avg(ca) ca,avg(mg) mg,avg(k) k,avg(na) na,avg(n) n,avg(p) p,avg(organi) organi,
        avg(cox) cox,avg(al) al,avg(b) b,avg(fe) fe,avg(mn) mn,avg(cu) cu,avg(zn) zn,avg(s) s,avg(mo) mo,avg(ni) ni,avg(co) co,avg(ti) ti,avg("as") "as",avg(pb) pb,avg(cr) cr,avg(metodo) metodo
        from cercanas c 
        join analytic.analitica a on c.cod = a.cod
        group by c.codigo,c.ceap)
        insert into analytic.analitica (cod,ceap,ph,ce,carbon,caliza,ca,mg,k,na,n,p,organi,cox,al,b,fe,mn,cu,zn,s,mo,ni,co,ti,"as",pb,cr,metodo)
        select * from data_unida '''

        try:
            with self.tools.conn.cursor(cursor_factory= psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(query, (idcampania, idexplotacion, numero_de_muestras))
                self.tools.conn.commit()
            self.tools.messages('aGrae Tools','Muestras cercanas derivadas y actualizadas.', Qgis.Success) # type: ignore
        except Exception as e:
            self.tools.conn.rollback()
            QgsMessageLog.logMessage(f"Error al derivar muestras cercanas: {e}\n{traceback.format_exc()}", "aGrae Lab", Qgis.Critical) # type: ignore
            self.tools.messages('aGrae Tools',f'Error: {e}', Qgis.Critical)

    def actualizar_dashboard_muestras_pendientes(self):
        """
        Obtiene los datos de muestras pendientes y actualiza el QTreeWidget y el gráfico.
        """
        self.tree_muestras_pendientes.clear()
        
        # La consulta SQL que proporcionaste
        sql_dashboard = """
        WITH data AS (
            SELECT *
            FROM campaign."data"
            WHERE idcampania = %s -- Usar el id de la campaña seleccionada en el combo de la otra pestaña
        ),
        muestras AS (
            SELECT DISTINCT m.idexplotacion, m.codigo, m.muestreado, m.created::date as created_date -- Convertir a solo fecha
            FROM data d
            JOIN field.muestras m USING (idcampania, idexplotacion, idlote)
            WHERE m.tipo IN (1, 3)
        ),
        muestras_procesado AS (
            SELECT
                m.idexplotacion,
                m.codigo,
                m.muestreado,
                m.created_date, -- Usar la fecha convertida
                CASE
                    WHEN a.cod IS NOT NULL THEN TRUE
                    ELSE FALSE
                END AS procesado
            FROM
                muestras m
            LEFT JOIN
                analytic.analitica a ON m.codigo = a.cod
        ),
        conteo_muestras AS (
            SELECT
                idexplotacion,
                MIN(created_date) AS fecha_min_creacion, -- Usar la fecha convertida y renombrar
                COUNT(*) AS num_muestras,
                COUNT(CASE WHEN muestreado IS TRUE THEN 1 END) AS total_muestreadas,
                COUNT(CASE WHEN procesado IS TRUE THEN 1 END) AS total_procesadas
            FROM
                muestras_procesado
            GROUP BY
                idexplotacion
        )
        SELECT
            cm.idexplotacion,
            e.nombre as nombre_explotacion, -- Añadir nombre de explotación
            cm.fecha_min_creacion as created, -- Usar el nuevo nombre de columna
            cm.num_muestras,
            cm.total_muestreadas,
            cm.total_procesadas
        FROM
            conteo_muestras cm
        JOIN agrae.explotacion e ON cm.idexplotacion = e.idexplotacion -- Unir con tabla de explotaciones
        --WHERE
            --(cm.num_muestras - cm.total_muestreadas) > 0 OR (cm.total_muestreadas - cm.total_procesadas) > 0 -- Condición más amplia para pendientes
        ORDER BY
            cm.fecha_min_creacion ASC; -- Ordenar por la nueva columna
        """
        
        id_campania_seleccionada = self.combo_campania.currentData() # Obtener la campaña del combo principal
        if id_campania_seleccionada is None:
            self.canvas_muestras_pendientes.plot_muestras_pendientes_donut((0,0,0)) # Limpiar gráfico
            QgsMessageLog.logMessage("Dashboard: No hay campaña seleccionada.", "aGrae Lab", Qgis.Info) # type: ignore
            return

        try:
            conn = agraeDataBaseDriver().connection()
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute(sql_dashboard, (id_campania_seleccionada,)) # Pasar el id de campaña como parámetro
                resultados = cursor.fetchall()
            conn.close()
            
            # Variables para las sumas totales para el gráfico donut
            suma_total_general_muestras = 0
            suma_total_muestreadas = 0
            suma_total_procesadas = 0
            
            if not resultados:
                item_no_data = QTreeWidgetItem(self.tree_muestras_pendientes, ["No hay explotaciones con muestras pendientes para la campaña seleccionada."])
                self.tree_muestras_pendientes.addTopLevelItem(item_no_data)
            else:
                for row in resultados:
                    id_exp = str(row['idexplotacion'])
                    nombre_exp = str(row['nombre_explotacion'])
                    
                    fecha_dt = row['created'] 
                    if fecha_dt:
                        fecha_creacion_formateada = formatear_tiempo_transcurrido(fecha_dt) 
                    else:
                        fecha_creacion_formateada = '-'

                    num_totales = row['num_muestras']
                    num_muestreadas = row['total_muestreadas']
                    num_procesadas = row['total_procesadas']

                    pend_muestrear_calc = num_totales - num_muestreadas
                    pend_procesar_calc = num_totales - num_procesadas # Se calcula sobre el total
                    
                    # Para mostrar en la tabla
                    totales_str = str(num_totales)
                    pend_muestrear_str = str(pend_muestrear_calc)
                    pend_procesar_str = str(pend_procesar_calc)

                    # Acumular para el gráfico donut
                    suma_total_general_muestras += num_totales
                    suma_total_muestreadas += pend_muestrear_calc
                    suma_total_procesadas += pend_procesar_calc

                    

                    # Determinar estado y color de fondo para la celda de estado
                    estado_partes = []
                    color_fondo_estado = QColor("lightgreen") # Verde por defecto (completo)

                    if pend_muestrear_calc > 0:
                        estado_partes.append(f"Pend. Muestrear: {pend_muestrear_str}")
                        color_fondo_estado = QColor("red") # Rojo si hay pendientes de muestrear
                    
                    if pend_procesar_calc > 0:
                        estado_partes.append(f"Pend. Procesar: {pend_procesar_str}")
                        # Si ya es rojo (por pendientes de muestrear), no cambiar a naranja.
                        # Solo cambiar a naranja si el estado actual es verde (completo hasta ahora).
                        if color_fondo_estado == QColor("lightgreen"): 
                            color_fondo_estado = QColor("orange") # Naranja si hay pendientes de procesar
                    
                    estado_texto = " | ".join(estado_partes) if estado_partes else "Completo"
                    
                    # Crear el QTreeWidgetItem con los datos
                    # Guardar el id_exp como data en la primera columna para fácil recuperación
                    item_exp = QTreeWidgetItem(self.tree_muestras_pendientes)
                    item_exp.setText(0, f"{id_exp} - {nombre_exp}")
                    item_exp.setData(0, Qt.UserRole, int(id_exp)) # Guardar id_exp como UserRole
                    item_exp.setText(1, fecha_creacion_formateada)
                    item_exp.setText(2, totales_str)
                    item_exp.setText(3, pend_muestrear_str)
                    item_exp.setText(4, pend_procesar_str)
                    item_exp.setText(5, estado_texto)
                    
                    # Colorear el fondo de las celdas de "Pend. Muestrear" y "Pend. Procesar"
                    if pend_muestrear_calc > 0:
                        item_exp.setBackground(3, QColor("lightcoral")) # Rojo claro para Pend. Muestrear
                    else:
                        item_exp.setBackground(3, QColor("lightgreen")) # Verde si es 0

                    if pend_procesar_calc > 0:
                        item_exp.setBackground(4, QColor("lightcoral")) # Rojo claro para Pend. Procesar
                    else:
                        item_exp.setBackground(4, QColor("lightgreen")) # Verde si es 0
                    
                    item_exp.setBackground(5, color_fondo_estado) # Color general del estado
            
            self.tree_muestras_pendientes.resizeColumnToContents(0)
            self.tree_muestras_pendientes.resizeColumnToContents(1)
            self.tree_muestras_pendientes.resizeColumnToContents(5)
            # print(suma_total_general_muestras, suma_total_muestreadas, suma_total_procesadas) # Debug
            self.canvas_muestras_pendientes.plot_muestras_pendientes_donut((suma_total_general_muestras, suma_total_muestreadas, suma_total_procesadas))

        except Exception as e:
            QgsMessageLog.logMessage(f"Error al actualizar dashboard de muestras: {e}\n{traceback.format_exc()}", "aGrae Lab", Qgis.Critical) # type: ignore
            self.canvas_muestras_pendientes.plot_muestras_pendientes_donut((0,0,0)) # Limpiar gráfico en caso de error

    def on_dashboard_tree_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """
        Maneja el doble clic en un ítem del QTreeWidget del dashboard.
        """
        id_explotacion_seleccionada = item.data(0, Qt.UserRole) # Obtener el id_exp guardado

        if id_explotacion_seleccionada is not None:
            # Buscar el ítem en combo_explotacion que coincida con id_explotacion_seleccionada
            for i in range(self.combo_explotacion.count()):
                if self.combo_explotacion.itemData(i) == id_explotacion_seleccionada:
                    self.combo_explotacion.setCurrentIndex(i)
                    # Al cambiar el currentIndex de combo_explotacion, se debería disparar
                    # self.updateTable() si la conexión está hecha.
                    # Y también se actualiza el combo_campania si es necesario (aunque ya debería estarlo)
                    
                    # Cambiar a la pestaña de Gestión General (asumiendo que es el índice 1)
                    self.tab_widget.setCurrentIndex(1) 
                    break
        else:
            QgsMessageLog.logMessage("No se pudo obtener el ID de la explotación del ítem del árbol.", "aGrae Lab", Qgis.Warning)
