import sys
from pathlib import Path
from kataja.environments.Base import Base

from kataja.globals import *


class Win(Base):
    """ Fonts and resource paths when running in Windows """

    def __init__(self, test_mode=False):
        super().__init__(test_mode=test_mode)
        if not test_mode and Path(sys.argv[0]).parts[-1].endswith('.exe'):
            self.code_mode = 'build'
            self.init_win_exe_paths()

        self.fonts = {
             MAIN_FONT: ['Cambria', 'Normal', 11], CONSOLE_FONT: ['Consolas', 'Normal', 11],
             UI_FONT: ['Droid Sans', 'Normal', 10], ITALIC_FONT: ['Cambria', 'Italic', 10],
             BOLD_FONT: ['Cambria', 'Bold', 10], SMALL_CAPS: ['Lao MN', 'Normal', 9],
             SMALL_FEATURE: ['Lao MN', 'Normal', 7],
             CUSTOM_FONT1: ['Cambria', 'Normal', 10],
             CUSTOM_FONT2: ['Cambria', 'Normal', 10],
             CUSTOM_FONT3: ['Cambria', 'Normal', 10]
        }

    def init_win_exe_paths(self):
        """ Is this enough for windows exe?
        :return:
        """
        # my_path = Path(sys.argv[0]).parts
        self.plugins_path = 'plugins'
        self.resources_path = 'resources'
        self.default_userspace_path = 'workspace'

