import tempfile

__author__ = 'purma'

import unittest
import sys
from kataja.saved.KatajaMain import KatajaMain
from PyQt5 import QtWidgets, QtGui, QtCore, QtTest
from kataja.singletons import running_environment

running_environment.switch_to_test_mode()

def prepare_app():
    app = QtWidgets.QApplication(sys.argv)
    app.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps)
    app.setApplicationName('Kataja')
    app.setOrganizationName('Purma')
    app.setOrganizationDomain('purma.fi')
    app.setStyle('fusion')
    return app

class TestMainWindowStructure(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._app = prepare_app()
        cls._main = KatajaMain(cls._app, sys.argv)
        cls._app.setActiveWindow(cls._main)
        cls._app.processEvents()
        QtTest.QTest.qWaitForWindowActive(cls._main)

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
        self.assertTrue(m.ui_manager, "No ui_support manager")
        #self.ui_manager.populate_ui_elements()
        self.assertTrue(m.forest_keeper, "No forest keeper")
        self.assertTrue(m.visualizations, "No visualizations")
        self.assertTrue(m.status_bar, "No status bar")
        #self.load_initial_treeset()
        #self.action_finished()

    def test_action(self):
        self._main.trigger_action('next_forest')

    def test_save_and_load(self):
        filename = tempfile.gettempdir() + '/savetest.kataja'
        self._main.trigger_action('save', filename=filename)
        size_in_save = len(self._main.forest.nodes)
        self._main.trigger_action('next_forest')
        self._main.trigger_action('next_forest')
        size_now = len(self._main.forest.nodes)
        self._main.trigger_action('open', filename=filename)
        size_after_load = len(self._main.forest.nodes)
        self.assertNotEqual(size_in_save, size_now, "Fix this test: same nodecount in initial "
                                                    "forest and comparison forest. They need to "
                                                    "be different.")
        self.assertNotEqual(size_after_load, size_now, "Nodecount didn't change after load")
        self.assertEqual(size_in_save, size_after_load, "Nodecount in saved forest "
                                                        "different to loaded forest")




if __name__ == '__main__':
    unittest.main()