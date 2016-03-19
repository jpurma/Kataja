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

from kataja.singletons import ctrl, prefs
from kataja.ui.PreferencesDialog import PreferencesDialog



# ### File ######

a = {}

file_extensions = {'pickle': '.kataja', 'pickle.zipped': '.zkataja',
                   'dict': '.dict', 'dict.zipped': '.zdict', 'json': '.json',
                   'json.zipped': '.zjson', }
# Not sure if we need a separate set for
# windows, if they still use three-letter extensions


def new_structure():
    """ Create new Forest, insert it after the current one and select it.
    :return: None
    """
    i, forest = ctrl.main.forest_keeper.new_forest()
    ctrl.main.change_forest()
    ctrl.main.add_message('(Cmd-n) New forest, n.%s' % (i + 1))

a['new_forest'] = {'command': '&New forest', 'method': new_structure, 'undoable': False,
                   'shortcut': 'Ctrl+n', 'tooltip': 'Create a new forest after the current one'}


def new_project():
    """ Create new project, replaces the current project at the moment.
    :return: None
    """
    project = ctrl.main.create_new_project()
    ctrl.main.add_message("Starting a new project '%s'" % project.name)

a['new_project'] = {'command': 'New project', 'method': new_project, 'undoable': False,
                    'tooltip': 'Create a new empty project.'}


def switch_project(index):
    """ Switch to another project. The action description is generated dynamically,
    not in code below.
    :param index:
    :return:
    """
    project = ctrl.main.switch_project(index)
    ctrl.main.add_message("Switched to project '%s'" % project.name)


def open_kataja_file(filename=''):
    """ Open file browser to load a kataja data file
    :param filename: optional filename, if given, no file dialog is displayed
    :return: None
    """
    m = ctrl.main
    # fileName  = QtGui.QFileDialog.getOpenFileName(self,
    # self.tr("Open File"),
    # QtCore.QDir.currentPath())
    file_help = """All (*.kataja *.zkataja *.dict *.zdict *.json *.zjson);;
Kataja files (*.kataja);; Packed Kataja files (*.zkataja);;
Python dict dumps (*.dict);; Packed python dicts (*.zdict);;
JSON dumps (*.json);; Packed JSON (*.zjson);;
Text files containing bracket trees (*.txt, *.tex)"""

    # inspection doesn't recognize that getOpenFileName is static, switch it
    # off:
    # noinspection PyTypeChecker,PyCallByClass
    if not filename:
        filename, filetypes = QtWidgets.QFileDialog.getOpenFileName(ctrl.main,
                                                                    "Open "
                                                                    "KatajaMain "
                                                                    "trees", "",
                                                                    file_help)
    if not filename:
        return
    save_format = 'dict'
    zipped = False
    for key, value, in file_extensions.items():
        if filename.endswith(value):
            i = key.split('.')
            zipped = len(i) == 2
            save_format = i[0]
            break

    m.clear_all()
    if zipped:
        if save_format == 'json' or save_format == 'dict':
            f = gzip.open(filename, 'rt')
        elif save_format == 'pickle':
            f = gzip.open(filename, 'rb')
        else:
            ctrl.add_message("Failed to load '%s'. Unknown format." % filename)
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
        f.close()
        ctrl.add_message("Failed to load '%s'. Unknown format." % filename)
        return

    f.close()
    # prefs.update(data['preferences'].__dict__)
    # qt_prefs.update(prefs)
    ctrl.disable_undo()
    m.load_objects(data, m)
    ctrl.resume_undo()
    m.change_forest()
    ctrl.add_message("Loaded '%s'." % filename)


a['open'] = {'command': '&Open', 'method': open_kataja_file, 'undoable': False,
             'shortcut': 'Ctrl+o'}


def save_kataja_file(filename=''):
    """ Save kataja data with an existing file name.
    :param filename: filename received from dialog.
    Format is deduced from the extension of filename.
    :return: None
    """
    filename = filename or ctrl.main.forest_keeper.filename
    if not filename:
        save_as()
        return

    save_format = 'pickle'
    zipped = False
    for key, value, in file_extensions.items():
        if filename.endswith(value):
            i = key.split('.')
            zipped = len(i) == 2
            save_format = i[0]
            break

    all_data = ctrl.main.create_save_data()
    t = time.time()
    pickle_format = 4
    print(filename)

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
        ctrl.main.add_message(
            "Failed to save '%s', no proper format given." % filename)
        return

    f.close()
    ctrl.main.add_message(
        "Saved to '%s'. Took %s seconds." % (filename, time.time() - t))

    # fileFormat  = action.data().toByteArray()
    # self.saveFile(fileFormat)


a['save'] = {'command': '&Save', 'method': save_kataja_file, 'undoable': False,
             'shortcut': 'Ctrl+s'}


def save_as():
    """ Save kataja data to file set by file dialog """
    ctrl.main.action_finished()
    file_help = """"All (*.kataja *.zkataja *.dict *.zdict *.json *.zjson);;
Kataja files (*.kataja);; Packed Kataja files (*.zkataja);;
Python dict dumps (*.dict);; Packed python dicts (*.zdict);;
JSON dumps (*.json);; Packed JSON (*.zjson)
"""
    filename, file_type = QtWidgets.QFileDialog.getSaveFileName(ctrl.main,
                                                                "Save Kataja "
                                                                "trees", "",
                                                                file_help)
    if filename:
        ctrl.main.forest_keeper.filename = filename
        save_kataja_file()


a['save_as'] = {'command': '&Save as', 'undoable': False, 'method': save_as}


def print_to_file():
    """ Starts the printing process.
     1st step is to clean the scene for a printing and display the printed
     area -frame.
     2nd step: after 50ms remove printed area -frame and prints to pdf,
     and write the file.

     2nd step is triggered by a timer in main window.
     :return: None
    """
    if prefs.print_file_path is None:
        dialog = QtWidgets.QFileDialog(ctrl.main)
        dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptOpen)
        dialog.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
        dialog.setLabelText(QtWidgets.QFileDialog.Accept, "Select")
        dialog.setWindowTitle('Select folder where to save your tree graphs (this needs to be done '
                              'only once)'
)
        if dialog.exec_():
            files = dialog.selectedFiles()
            if files:
                prefs.print_file_path = files[0]
        else:
            return

    sc = ctrl.graph_scene
    # hide unwanted components
    no_brush = QtGui.QBrush(Qt.NoBrush)
    sc.setBackgroundBrush(no_brush)
    sc.photo_frame = sc.addRect(sc.visible_rect().adjusted(-1, -1, 2, 2),
                                ctrl.cm.selection())
    sc.update()
    ctrl.graph_view.repaint()
    ctrl.main.print_started = True  # to avoid a bug where other timers end up triggering main's
    ctrl.main.startTimer(50)


a['print_pdf'] = {'command': '&Print', 'method': print_to_file,
                  'undoable': False, 'shortcut': 'Ctrl+p'}


def render_in_blender():
    """ (not working recently) Try to export as a blender file and run
    blender render.
    :return: None
    """
    ctrl.graph_scene.export_3d(prefs.blender_env_path + '/temptree.json',
                               ctrl.forest)
    ctrl.main.add_message('Command-r  - render in blender')
    command = '%s -b %s/puutausta.blend -P %s/treeloader.py -o ' \
              '//blenderkataja -F JPEG -x 1 -f 1' % (
                  prefs.blender_app_path, prefs.blender_env_path,
                  prefs.blender_env_path)
    args = shlex.split(command)
    subprocess.Popen(args)  # , cwd =prefs.blender_env_path)


a['blender_render'] = {'command': '&Render in Blender',
                       'method': render_in_blender, 'shortcut': 'Ctrl+r'}


def open_preferences():
    """ Opens the large preferences dialog
    :return: None
    """
    if not ctrl.ui.preferences_dialog:
        ctrl.ui.preferences_dialog = PreferencesDialog(ctrl.main)
    ctrl.ui.preferences_dialog.open()


a['preferences'] = {'command': '&Preferences', 'method': open_preferences}


def close_all_windows():
    """ Implements Quit command
    :return: None
    """
    ctrl.main.app.closeAllWindows()


a['quit'] = {'command': '&Quit', 'method': close_all_windows,
             'shortcut': 'Ctrl+q'}

