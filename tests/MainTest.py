__author__ = 'purma'

import unittest
import sys
from kataja.KatajaMain import KatajaMain
from PyQt5 import QtWidgets, QtPrintSupport, QtGui, QtCore, QtTest
from kataja.singletons import ctrl, prefs, qt_prefs

class TestMainWindowStructure(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._app = QtWidgets.QApplication(sys.argv)
        cls._app.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps)
        splash = QtWidgets.QSplashScreen(QtGui.QPixmap('../resources/katajalogo.png'))
        cls._main = KatajaMain(cls._app, splash, sys.argv)
        splash.finish(cls._main)
        cls._app.setActiveWindow(cls._main)
        cls._app.processEvents()
        QtTest.QTest.qWaitForWindowActive(cls._main)
        #.qWaitForWindowShown(window)
        #QtTest.QTest.qWaitForWindowExposed(window) #.qWaitForWindowShown(window)
        #app.exec_()

    @classmethod
    def tearDownClass(cls):
        cls._main.close()
        cls._app.exit()

    def test_parts_exist(self):
        m = self._main
        self.assertTrue(m.app, "No main app")
        self.assertTrue(m.forest, "No forest")
        self.assertTrue(m.fontdb, "No fontdb")
        self.assertTrue(m.fontdb, "No fontdb")
        self.assertTrue(m.color_manager, "No color manager")
        #ctrl.late_init(self)
        #prefs.import_node_classes(ctrl)
        #prefs.load_preferences()
        #qt_prefs.late_init(prefs, self.fontdb)
        #import_plugins(prefs, plugins_path)
        self.assertTrue(m.graph_scene, "No graph scene")
        self.assertTrue(m.graph_view, "No graph view")
        self.assertTrue(m.graph_scene.graph_view, "No graph view in graph scene")
        self.assertTrue(m.ui_manager, "No ui manager")
        #self.ui_manager.populate_ui_elements()
        self.assertTrue(m.key_manager, "No key manager")
        self.assertTrue(m.object_factory, "No object factory")
        self.assertTrue(m.forest_keeper, "No forest keeper")
        self.assertTrue(m.visualizations, "No visualizations")
        self.assertTrue(m.status_bar, "No status bar")
        #self.load_treeset()
        #self.action_finished()


if __name__ == '__main__':
    unittest.main()