import os
import shutil
from kataja.globals import *
from pathlib import Path
import sys

__author__ = 'purma'


mac_fonts = {MAIN_FONT: ['Asana Math', 'Normal', 12], CONSOLE_FONT: ['Monaco', 'Normal', 10],
             UI_FONT: ['Helvetica', 'Normal', 10], BOLD_FONT: ['STIX', 'Bold', 12],
             ITALIC_FONT: ['Asana Math', 'Italic', 12], SMALL_CAPS: ['Lao MN', 'Normal', 10],
             SMALL_FEATURE: ['Lao MN', 'Normal', 7]}

linux_fonts = {MAIN_FONT: ['Asana Math', 'Normal', 12], CONSOLE_FONT: ['Courier', 'Normal', 10],
               UI_FONT: ['Droid Sans', 'Normal', 10], ITALIC_FONT: ['Asana Math', 'Italic', 12],
               BOLD_FONT: ['STIX', 'Bold', 12], SMALL_CAPS: ['Lao MN', 'Normal', 9],
               SMALL_FEATURE: ['Lao MN', 'Normal', 7]}

windows_fonts = {MAIN_FONT: ['Cambria', 'Normal', 10], CONSOLE_FONT: ['Consolas', 'Normal', 10],
                 UI_FONT: ['Droid Sans', 'Normal', 10], ITALIC_FONT: ['Cambria', 'Italic', 10],
                 BOLD_FONT: ['Cambria', 'Bold', 10], SMALL_CAPS: ['Lao MN', 'Normal', 8],
                 SMALL_FEATURE: ['Lao MN', 'Normal', 7]}


running_environment = ''

if sys.platform == 'darwin':
    fonts = mac_fonts
    if 'Kataja.app' in Path(__file__).parts:
        running_environment = 'mac app'
    else:
        running_environment = 'mac python'
elif sys.platform == 'win32':
    fonts = windows_fonts
    running_environment = 'win python'
else:
    fonts = linux_fonts
    running_environment = 'nix python'

resources_path = ''
default_userspace_path = ''
plugins_path = ''

if running_environment == 'mac app':
    # When runnins as a mac app, the plugins directory is put to Application Support/Kataja/plugins
    # code there is loaded on launch.
    # Also the resoruces folder is inside the app package, and default save location is user's
    # home path.
    my_path = Path(__file__).parts
    i = my_path.index('Kataja.app')
    app_path = str(Path(*list(my_path[:i + 1])))
    resources_path = app_path + '/Contents/Resources/resources/'
    default_userspace_path = os.path.expanduser('~/')
    print('running from inside Mac OS X .app -container')
    # Make sure that 'plugins'-dir is available in Application Support
    library_kat = os.path.expanduser('~/Library/Application Support/Kataja')
    plugins_path = library_kat+'/plugins'
    if not os.access(plugins_path, os.F_OK):
        os.makedirs(library_kat, exist_ok=True)
        if os.access(library_kat, os.W_OK):
            local_plugin_path = app_path + '/Contents/Resources/lib/plugins'
            if (not os.access(plugins_path, os.F_OK)) and os.access(local_plugin_path, os.W_OK):
                print("Copying 'plugins' to /~Library/Application Support/Kataja")
                shutil.copytree(local_plugin_path, plugins_path)
elif running_environment == 'mac python':
    # When runnins as a mac python script, plugins, resources and default save location are
    # based on the kataja code base.
    # This is easier for development and active 'bold' use.
    prefs_code = os.path.realpath(__file__)
    filename = __file__.split('/')[-1]
    kataja_root = prefs_code[:-len('kataja/'+filename)]
    resources_path = kataja_root + 'resources/'
    plugins_path = kataja_root + 'kataja/plugins'
    default_userspace_path = kataja_root
    print('running as a python script')
print("resources_path: ", resources_path)
print("default_userspace_path: ", default_userspace_path)
