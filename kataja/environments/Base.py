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
        self.resources_path = 'resources'
        self.plugins_path = 'plugins'
        self.init_multiplatform_python_paths()
        if test_mode:
            self.run_mode = 'test'
            self.default_userspace_path = tempfile.gettempdir()
        else:
            self.run_mode = 'source'
            self.default_userspace_path = '.'
        self.fonts = linux_fonts
        self.cmd_or_ctrl = 'Ctrl'

    def switch_to_test_mode(self):
        """ Retroactively switch to test mode.
        :return:
        """
        self.run_mode = 'test'
        self.default_userspace_path = tempfile.gettempdir()

    def init_multiplatform_python_paths(self):
        """ When runnins as a python script, plugins, resources and default save location are
        based on the kataja code base.
        This is easier for development and active 'bold' use."""
        full_path_to_this_file = os.path.realpath(__file__)
        filename = os.path.basename(__file__)
        package_cut = os.path.join('environments', filename)
        package_root = full_path_to_this_file[:-len(package_cut)]
        self.resources_path = os.path.join(package_root, 'resources')
        self.plugins_path = os.path.join(package_root, 'plugins')
        print('resources_path: ', self.resources_path)
        print('plugins_path: ', self.plugins_path)
