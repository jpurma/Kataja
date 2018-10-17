import os
import tempfile

from kataja.globals import *

linux_fonts = {MAIN_FONT: ['Asana Math', 'Normal', 12], CONSOLE_FONT: ['Courier', 'Normal', 11],
               UI_FONT: ['Droid Sans', 'Normal', 10], ITALIC_FONT: ['Asana Math', 'Italic', 12],
               BOLD_FONT: ['STIX', 'Bold', 12], SMALL_CAPS: ['Lao MN', 'Normal', 10],
               SMALL_FEATURE: ['Lao MN', 'Normal', 7],
               CUSTOM_FONT1: ['Asana Math', 'Normal', 12],
               CUSTOM_FONT2: ['Asana Math', 'Normal', 12],
               CUSTOM_FONT3: ['Asana Math', 'Normal', 12]}


class Base:
    """ Default fonts and resource paths. These are used when running in Linux and as a base for Mac/Win """

    def __init__(self, test_mode=False):
        self.resources_path = ''
        self.plugins_path = 'plugins'
        self.default_userspace_path = 'workspace'
        if test_mode:
            self.code_mode = 'test'
            self.init_test_paths()
        else:
            self.code_mode = 'python'
            self.init_multiplatform_python_paths()
        self.fonts = linux_fonts
        self.cmd_or_ctrl = 'Ctrl'

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
        full_path_to_this_file = os.path.realpath(__file__)
        filename = os.path.basename(__file__)
        cut = os.path.join('kataja', 'environments', filename)
        kataja_root = full_path_to_this_file[:-len(cut)]
        self.resources_path = os.path.join(kataja_root, 'resources')
        self.plugins_path = os.path.join(kataja_root, 'plugins')
        self.default_userspace_path = os.path.join(kataja_root, 'workspace')
