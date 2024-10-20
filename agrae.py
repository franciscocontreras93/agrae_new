from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QCoreApplication, Qt,QSize


from .gui import agraeGUI
from .dialogs.main import agraeMainWidget
from .dialogs.lotes_dialog import LotesMainWindow
from .dialogs.tools_dockwidget import *
from .dialogs.config_dialog import agraeConfigDialog
from .dialogs.gee_dialog import aGraeGEEDialog
from .dialogs.lab_dialog import GestionLaboratorioDialog


from .db import agraeDataBaseDriver
from .tools import aGraeTools

from .dialogs import aGraeDialogs



class aGraeToolbox:
    def __init__(self, iface):
        self.iface = iface
        self.menu = self.tr(u'&aGrae GIS')
        self.toolbar = self.iface.addToolBar(u'aGrae GIS')
        self.toolbar.setObjectName(u'aGrae GIS')
        

        self.actions = []

        self.tools = aGraeTools()

        
    
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('agrae', message)
    
    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action


    def initGui(self):
        # self.action = QAction('Go!', self.iface.mainWindow())
        # self.action.triggered.connect(self.run)
        # self.iface.addToolBarIcon(self.action)
        # self.CargarLotesDialogAction = self.tools.getAction(None,agraeGUI().getIcon('add'),'Cargar Nuevos Lotes',callback=aGraeDialogs.cargarLotesDialog)
        # self.CrearCEDialogAction = self.tools.getAction(None,agraeGUI().getIcon('map-base'),'Cargar Datos Base',callback=aGraeDialogs.cargarCEDialog)
        
        # tools_agrae_actions = [self.CargarLotesDialogAction,self.CrearCEDialogAction]

        # self.tools_agrae = self.tools.getToolButton(tools_agrae_actions,agraeGUI().getIcon('tools'),setMainIcon=True)
        # self.toolbar.addWidget(self.tools_agrae)

        self.add_action(agraeGUI().getIcon('lotes'),'Cargar Lotes',self.agraeGestionLotes,add_to_menu=False,add_to_toolbar=True)
        self.add_action(agraeGUI().getIcon('main'),'aGrae GIS',self.agraeDock,add_to_toolbar=True)
        self.add_action(agraeGUI().getIcon('laboratorio-icon'),'Gestion Laboratorio',self.GestionarLaboratorio,add_to_toolbar=True)
        # self.add_action(agraeGUI().getIcon('main'),'aGrae GIS',self.testGee,add_to_toolbar=True)
        self.add_action(agraeGUI().getIcon('settings'),'Ajustes aGrae GIS',self.agraeConfig,add_to_menu=True,add_to_toolbar=False)



    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&aGrae GIS'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar
        # print(self.actions)
    def onClosePlugin(self,widget):

        # disconnects
        widget.closingPlugin.disconnect(
            self.onClosePlugin)
        self.pluginIsActive = False
        # self.mainWindowDialog.tableWidget_3.setRowCount(0)
        # self.mainWindowDialog.an_lbl_file.setText('')

    def agraeMainWindow(self):
        # QMessageBox.information(None, 'Minimal plugin', 'ALGO ALGO')
        self.mainWindowDialog = agraeMainWidget() 
        self.mainWindowDialog.closingPlugin.connect(lambda: self.onClosePluginMain(self.mainWindowDialog))
        self.mainWindowDialog.show()

    def agraeGestionLotes(self):
        # self.lotesDialog = LotesMainWindow()
        # self.lotesDialog.closingPlugin.connect(lambda: self.onClosePluginMain(self.lotesDialog))
        # self.lotesDialog.show()
        self.tools.getLotesLayer()

    def agraeDock(self):
        try:
            self.lotesLayer = QgsProject.instance().mapLayersByName('aGrae Lotes')[0]
        except IndexError:
            dsn = agraeDataBaseDriver().getDSN()
            uri = QgsDataSourceUri()
            uri.setConnection(dsn['host'],dsn['port'],dsn['dbname'],dsn['user'],dsn['password'])
            uri.setDataSource('public','lotes','geom','','id')
            self.lotesLayer = QgsVectorLayer(uri.uri(),'aGrae Lotes','postgres')
            QgsProject.instance().addMapLayer(self.lotesLayer)
            pass
        self.dock = agraeToolsDockwidget(self.lotesLayer)

        # self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dock)

    def agraeConfig(self):
        dialog = agraeConfigDialog()
        dialog.exec()


    def testGee(self):
        dialog = aGraeGEEDialog()
        dialog.exec()

    def GestionarLaboratorio(self):
        dialog = GestionLaboratorioDialog()
        dialog.exec()

    