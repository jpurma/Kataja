import ast
import gzip
import json
import pickle
import pprint
import shlex
import subprocess
import time

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence

from kataja.KatajaAction import KatajaAction

from kataja.singletons import ctrl, prefs, log
from kataja.ui_support.PreferencesDialog import PreferencesDialog

# ==== Class variables for KatajaActions:
#
# k_action_uid : unique id for calling this action. required, other are optional
# k_command : text used for menu command and log feedback, unless the method returns a fdback string
# k_tooltip : tooltip text for ui element. If not given, uses k_command as tooltip.
# k_undoable : is the action undoable, default is True
# k_shortcut : keyboard shortcut given as string, e.g. 'Ctrl+x'
# k_shortcut_context : can be nothing or 'parent_and_children' if shortcut is active only when the
#                      parent widget is visible and active
# k_checkable : should the action be checkable, default False
#
# ==== Methods:
#
# method : gets called when action is triggered. If it returns a string, this is used as a command
#          feedback string, otherwise k_command is printed to log.
# getter : if there is an UI element that can show state or display value, this method returns the
#          value. These are called quite often, but with values that have to change e.g. when item
#          is dragged, you'll have to update manually.
# enabler : if enabler is defined, the action is active (also reflected into its UI elements) only
#           when enabler returns True
#


# ### File ######

file_extensions = {
    'pickle': '.kataja',
    'pickle.zipped': '.zkataja',
    'dict': '.dict',
    'dict.zipped': '.zdict',
    'json': '.json',
    'json.zipped': '.zjson',
}


def deduce_format(filename):
    save_format = 'dict'
    zipped = False
    for key, value, in file_extensions.items():
        if filename.endswith(value):
            i = key.split('.')
            zipped = len(i) == 2
            save_format = i[0]
            break
    return save_format, zipped


# Not sure if we need a separate set for
# windows, if they still use three-letter extensions


class NewProject(KatajaAction):
    k_action_uid = 'new_project'
    k_command = 'New project'
    k_tooltip = 'Create a new empty project'
    k_undoable = False

    def method(self):
        """ Create new project, replaces the current project at the moment.
        :return: None
        """
        project = ctrl.main.start_new_document()
        log.info("Starting a new project '%s'" % project.name)


class Open(KatajaAction):
    k_action_uid = 'open'
    k_command = 'Open'
    k_shortcut = QKeySequence(QKeySequence.Open)
    k_undoable = False

    @staticmethod
    def get_filename_from_dialog():
        file_help = """All (*.kataja *.zkataja *.dict *.zdict *.json *.zjson);;
        Kataja files (*.kataja);; Packed Kataja files (*.zkataja);;
        Python dict dumps (*.dict);; Packed python dicts (*.zdict);;
        JSON dumps (*.json);; Packed JSON (*.zjson);;
        Text files containing bracket trees (*.txt, *.tex)"""
        # inspection doesn't recognize that getOpenFileName is static, switch it
        # off:
        # noinspection PyTypeChecker,PyCallByClass
        filename, filetypes = QtWidgets.QFileDialog.getOpenFileName(
            ctrl.main,
            "Open Kataja trees",
            prefs.userspace_path,
            file_help
        )
        return filename

    def load_data_from_file(self, filename):
        save_format, zipped = deduce_format(filename)

        if zipped:
            if save_format == 'json' or save_format == 'dict':
                f = gzip.open(filename, 'rt')
            elif save_format == 'pickle':
                f = gzip.open(filename, 'rb')
            else:
                log.info("Failed to load '%s'. Unknown format." % filename)
                return
        else:
            if save_format == 'pickle':
                f = open(filename, 'rb')
            else:
                f = open(filename, 'r')
                # import codecs
                # f = codecs.open(filename, 'rb', encoding = 'utf-8')

        if save_format == 'pickle':
            pickle_worker = pickle.Unpickler(f)
            data = pickle_worker.load()
        elif save_format == 'dict':
            data = ast.literal_eval(f.read())
            # data = eval(f.read())
        elif save_format == 'json':
            data = json.load(f)
        else:
            log.info("Failed to load '%s'. Unknown format." % filename)
        f.close()
        return data

    def method(self, filename=''):
        """ Open file browser to load a kataja data file
        :param filename: optional filename, if given, no file dialog is displayed
        :return: None
        """
        if not filename:
            filename = self.get_filename_from_dialog()
        if not filename:
            return

        data = self.load_data_from_file(filename)
        if not data:
            return

        # prefs.update(data['preferences'].__dict__)
        # qt_prefs.update(prefs)
        m = ctrl.main
        m.disable_signaling()
        required_plugin = data.get('kataja_plugin_name', '')
        if required_plugin != prefs.active_plugin_name:
            if required_plugin:
                print('having to switch plugins')
                ctrl.main.enable_plugin(required_plugin, reload=False)
            else:
                print('has to disable plugin')
                ctrl.main.disable_current_plugin()
        root_uid = data.get('kataja_root_document_uid', '')
        doc = m.start_new_document(filename, uid=root_uid)
        print('loading data: ', data)
        print('created empty document')
        doc.load_objects(data, m)
        doc.has_filename = True
        print('done load it with saved data')
        print(f'received {len(doc.forests)} forests, with: ')
        for i, forest in enumerate(doc.forests):
            print(f'Forest {i}: {len(forest.nodes)} nodes and {len(forest.edges)} edges.)')
        m.enable_signaling()
        m.set_document(doc)
        print('done setting it as active document')

        ctrl.main.document_changed.emit()
        print('document changed, emit')
        doc.update_forest()
        print('forest changed')
        log.info("Loaded '%s'." % filename)


class Save(KatajaAction):
    k_action_uid = 'save'
    k_command = 'Save'
    k_shortcut = QKeySequence(QKeySequence.Save)
    k_undoable = False

    @staticmethod
    def get_filename_from_dialog():
        file_help = """"All (*.kataja *.zkataja *.dict *.zdict *.json *.zjson);;
        Kataja files (*.kataja);; Packed Kataja files (*.zkataja);;
        Python dict dumps (*.dict);; Packed python dicts (*.zdict);;
        JSON dumps (*.json);; Packed JSON (*.zjson)
        """
        # inspection doesn't recognize that getOpenFileName is static, switch it
        # off:
        # noinspection PyTypeChecker,PyCallByClass
        filename, filetypes = QtWidgets.QFileDialog.getSaveFileName(
            ctrl.main,
            "Save Kataja trees",
            prefs.userspace_path,
            file_help
        )
        print('received filename from dialog: ', filename)
        return filename

    @staticmethod
    def save_file(filename):
        save_format, zipped = deduce_format(filename)

        all_data = ctrl.document.create_save_data()
        t = time.time()
        pickle_format = 4

        if save_format == 'pickle':
            if zipped:
                f = gzip.open(filename, 'wb')
            else:
                f = open(filename, 'wb')
            pickle_worker = pickle.Pickler(f, protocol=pickle_format)
            pickle_worker.dump(all_data)
        elif save_format == 'dict':
            if zipped:
                f = gzip.open(filename, 'wt')
            else:
                f = open(filename, 'w')
            pp = pprint.PrettyPrinter(indent=1, stream=f)
            pp.pprint(all_data)
        elif save_format == 'json':
            if zipped:
                f = gzip.open(filename, 'wt')
            else:
                f = open(filename, 'w')
            json.dump(all_data, f, indent="\t", sort_keys=False)
        else:
            log.info("Failed to save '%s', no proper format given." % filename)
            return

        f.close()
        log.info("Saved to '%s'. Took %s seconds." % (filename, time.time() - t))

    def method(self):
        filename = ctrl.document.filename
        if not (filename and ctrl.document.has_filename):
            filename = self.get_filename_from_dialog()
        if filename:
            ctrl.document.has_filename = True
        self.save_file(filename)


class SaveAs(Save):
    k_action_uid = 'save_as'
    k_command = 'Save as'
    k_shortcut = QKeySequence(QKeySequence.SaveAs)
    k_undoable = False

    def method(self, filename='', save_as=False):
        filename = self.get_filename_from_dialog()
        if filename:
            ctrl.document.filename = filename
            ctrl.document.has_filename = True
            self.save_file(filename)


class PrintToFile(KatajaAction):
    k_action_uid = 'print_pdf'
    k_command = 'Print'
    k_shortcut = QKeySequence(QKeySequence.Print)
    k_undoable = False
    k_tooltip = 'Capture as image'

    def method(self):
        """ Starts the printing process.
         1st step is to clean the scene for a printing and display the printed
         area -frame.
         2nd step: after 50ms remove printed area -frame and prints to pdf,
         and write the file.

         2nd step is triggered by a timer in main window.
         :return: None
        """
        sc = ctrl.graph_scene
        # hide unwanted components
        no_brush = QtGui.QBrush(Qt.NoBrush)
        sc.setBackgroundBrush(no_brush)
        sc.photo_frame = sc.addRect(ctrl.view_manager.print_rect().adjusted(-1, -1, 2, 2), ctrl.cm.selection())
        sc.update()
        for node in ctrl.forest.nodes.values():
            node.setCacheMode(QtWidgets.QGraphicsItem.NoCache)
        ctrl.graph_view.repaint()
        ctrl.main.print_started = True  # to avoid a bug where other timers end up triggering main's
        ctrl.main.startTimer(50)


#
# class RenderInBlender(KatajaAction):
#     k_action_uid = 'blender_render'
#     k_command = '&Render in Blender'
#     k_shortcut = 'Ctrl+r'
#     k_undoable = False
#
#     def method(self):
#         """ (not working recently) Try to export as a blender file and run
#         blender render.
#         :return: None
#         """
#         ctrl.graph_scene.export_3d(prefs.blender_env_path + '/temptree.json',
#                                    ctrl.forest)
#         log.info('Command-r  - render in blender')
#         command = '%s -b %s/puutausta.blend -P %s/treeloader.py -o ' \
#                   '//blenderkataja -F JPEG -x 1 -f 1' % (
#                       prefs.blender_app_path, prefs.blender_env_path,
#                       prefs.blender_env_path)
#         args = shlex.split(command)
#         subprocess.Popen(args)  # , cwd =prefs.blender_env_path)



class OpenPreferences(KatajaAction):
    k_action_uid = 'preferences'
    k_command = 'Preferences'
    k_shortcut = QKeySequence(QKeySequence.Preferences)
    k_undoable = False

    def method(self):
        """ Opens the large preferences dialog
        :return: None
        """
        if not ctrl.ui.preferences_dialog:
            ctrl.ui.preferences_dialog = PreferencesDialog(ctrl.main)
        ctrl.ui.preferences_dialog.open()


class Quit(KatajaAction):
    k_action_uid = 'quit'
    k_command = 'Quit'
    k_shortcut = QKeySequence(QKeySequence.Quit)
    k_undoable = False

    def method(self):
        """ Implements Quit command
        :return: None
        """
        ctrl.main.app.closeAllWindows()
