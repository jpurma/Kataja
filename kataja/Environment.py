import os
import shutil
import sys
import tempfile
from pathlib import Path

from kataja.globals import *

__author__ = 'purma'

# Alternatives: Cambria Math, Asana Math, XITS Math
mac_fonts = {MAIN_FONT: ['Asana Math', 'Normal', 12], CONSOLE_FONT: ['Menlo', 'Normal', 11],
             UI_FONT: ['Helvetica Neue', 'Normal', 10], BOLD_FONT: ['STIX', 'Bold', 12],
             ITALIC_FONT: ['Asana Math', 'Italic', 12],
             SMALL_CAPS: ['Menlo', 'Normal', 10],
             SMALL_FEATURE: ['Helvetica Neue', 'Normal', 7],
             CUSTOM_FONT1: ['Asana Math', 'Normal', 12],
             CUSTOM_FONT2: ['Asana Math', 'Normal', 12],
             CUSTOM_FONT3: ['Asana Math', 'Normal', 12]}

linux_fonts = {MAIN_FONT: ['Asana Math', 'Normal', 12], CONSOLE_FONT: ['Courier', 'Normal', 11],
               UI_FONT: ['Droid Sans', 'Normal', 10], ITALIC_FONT: ['Asana Math', 'Italic', 12],
               BOLD_FONT: ['STIX', 'Bold', 12], SMALL_CAPS: ['Lao MN', 'Normal', 10],
               SMALL_FEATURE: ['Lao MN', 'Normal', 7],
               CUSTOM_FONT1: ['Asana Math', 'Normal', 12],
               CUSTOM_FONT2: ['Asana Math', 'Normal', 12],
               CUSTOM_FONT3: ['Asana Math', 'Normal', 12]}

windows_fonts = {MAIN_FONT: ['Cambria', 'Normal', 11], CONSOLE_FONT: ['Consolas', 'Normal', 10],
                 UI_FONT: ['Droid Sans', 'Normal', 10], ITALIC_FONT: ['Cambria', 'Italic', 10],
                 BOLD_FONT: ['Cambria', 'Bold', 10], SMALL_CAPS: ['Lao MN', 'Normal', 9],
                 SMALL_FEATURE: ['Lao MN', 'Normal', 7],
                 CUSTOM_FONT1: ['Cambria', 'Normal', 10],
                 CUSTOM_FONT2: ['Cambria', 'Normal', 10],
                 CUSTOM_FONT3: ['Cambria', 'Normal', 10]}

platforms = {'darwin': 'mac', 'win32': 'win', 'default': 'nix'}
font_map = {'mac': mac_fonts, 'win': windows_fonts, 'nix': linux_fonts, 'default': linux_fonts}


class Environment:
    """ This single instance object will host the environment dependant variables like paths to
    preferences and typically available fonts.

    Environment can be toggled to test mode, where writing operations go to temp.
    """

    def __init__(self, test_mode=False):
        self.platform = platforms.get(sys.platform, platforms['default'])
        if test_mode:
            self.code_mode = 'test'
        elif self.platform == 'mac' and 'Kataja.app' in Path(sys.argv[0]).parts:
            self.code_mode = 'build'
        elif self.platform == 'win' and Path(sys.argv[0]).parts[-1].endswith('.exe'):
            self.code_mode = 'build'
        else:
            self.code_mode = 'python'
        self.fonts = font_map.get(self.platform, font_map['default'])
        self.resources_path = ''
        self.default_userspace_path = ''
        self.plugins_path = ''
        if self.platform == 'mac':
            self.cmd_or_ctrl = '⌘'
        else:
            self.cmd_or_ctrl = 'Ctrl'

        if self.code_mode == 'test':
            self.init_test_paths()
        elif self.code_mode == 'build':
            if self.platform == 'mac':
                self.init_mac_app_paths()
            elif self.platform == 'win':
                self.init_win_exe_paths()
        elif self.code_mode == 'python':
            self.init_multiplatform_python_paths()

    def switch_to_test_mode(self):
        """ Retroactively switch to test mode.
        :return:
        """
        self.code_mode = 'test'
        self.init_test_paths()

    def init_test_paths(self):
        """ Call this when building a test environment, afte
        :return:
        """
        self.init_multiplatform_python_paths()
        self.default_userspace_path = tempfile.gettempdir()
        print('---- writing to tempdir %s ' % self.default_userspace_path)

    def init_multiplatform_python_paths(self):
        """ When runnins as a python script, plugins, resources and default save location are
        based on the kataja code base.
        This is easier for development and active 'bold' use."""
        prefs_code = os.path.realpath(__file__)
        filename = __file__.split('/')[-1]
        kataja_root = prefs_code[:-len('kataja/' + filename)]
        self.resources_path = kataja_root + 'resources/'
        self.plugins_path = kataja_root + 'plugins'
        self.default_userspace_path = kataja_root

    def init_win_exe_paths(self):
        """ Is this enough for windows exe?
        :return:
        """
        # my_path = Path(sys.argv[0]).parts
        self.plugins_path = 'plugins'
        self.resources_path = 'resources/'
        self.default_userspace_path = ''

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
        self.resources_path = app_path + '/Contents/Resources/resources/'
        self.default_userspace_path = os.path.expanduser('~/')
        # Make sure that 'plugins'-dir is available in Application Support
        library_kat = os.path.expanduser('~/Library/Application Support/Kataja')
        self.plugins_path = library_kat + '/plugins'
        if not os.access(self.plugins_path, os.F_OK):
            os.makedirs(library_kat, exist_ok=True)
            if os.access(library_kat, os.W_OK):
                local_plugin_path = app_path + '/Contents/Resources/lib/plugins'
                if (not os.access(self.plugins_path, os.F_OK)) and os.access(local_plugin_path,
                                                                             os.R_OK):
                    shutil.copytree(local_plugin_path, self.plugins_path)

