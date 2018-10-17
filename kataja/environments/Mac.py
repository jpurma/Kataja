import os
import shutil
import sys
from pathlib import Path
from PyQt5 import QtCore

from kataja.globals import *
from kataja.environments.Base import Base


class Mac(Base):
    """ Fonts and resource paths when running in MacOS """

    def __init__(self, test_mode=False):
        super().__init__(test_mode=test_mode)
        self.cmd_or_ctrl = '⌘'
        if not test_mode and 'Kataja.app' in Path(sys.argv[0]).parts:
            self.code_mode = 'build'
            self.init_mac_app_paths()
        self.fonts = {
            MAIN_FONT: ['Asana Math', 'Normal', 12],
            CONSOLE_FONT: ['Menlo', 'Normal', 11],
            UI_FONT: ['Helvetica Neue', 'Normal', 10],
            BOLD_FONT: ['STIX', 'Bold', 12],
            ITALIC_FONT: ['Asana Math', 'Italic', 12],
            SMALL_CAPS: ['Menlo', 'Normal', 10],
            SMALL_FEATURE: ['Helvetica Neue', 'Normal', 7],
            CUSTOM_FONT1: ['Asana Math', 'Normal', 12],
            CUSTOM_FONT2: ['Asana Math', 'Normal', 12],
            CUSTOM_FONT3: ['Asana Math', 'Normal', 12]
        }

    def init_mac_app_paths(self):
        """ When runnins as a mac app, the plugins directory is put to Application
        Support/Kataja/plugins.
        Also the resources folder is inside the app package, and default save location is user's
        home path.
        :return:
        """
        my_path = Path(__file__).parts
        i = my_path.index('Kataja.app')
        app_path = str(Path(*list(my_path[:i + 1])))
        self.resources_path = os.path.join(app_path, 'Contents/Resources/resources/')
        self.default_userspace_path = os.path.expanduser('~/')
        # Make sure that 'plugins'-dir is available in Application Support
        library_kat = os.path.expanduser('~/Library/Application Support/Kataja')
        self.plugins_path = os.path.join(library_kat, 'plugins')
        if not os.access(self.plugins_path, os.F_OK):
            os.makedirs(library_kat, exist_ok=True)
            if os.access(library_kat, os.W_OK):
                local_plugin_path = os.path.join(app_path, 'Contents/Resources/lib/plugins')
                if (not os.access(self.plugins_path, os.F_OK)) and os.access(local_plugin_path,
                                                                             os.R_OK):
                    shutil.copytree(local_plugin_path, self.plugins_path)

        dir_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        # noinspection PyTypeChecker,PyCallByClass
        QtCore.QCoreApplication.addLibraryPath(f'{dir_path}/../plugins')
