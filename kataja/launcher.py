"""

usage: __main__.py [-h] [--reset_prefs] [--no_prefs] [-image_out IMAGE_OUT]
                   [-plugin PLUGIN]
                   [tree]

Launch Kataja visualisation environment.

positional arguments:
  tree                  bracket tree or source tree filename

optional arguments:
  -h, --help            show this help message and exit
  --reset_prefs         reset the current preferences file to default
  --no_prefs            don't use preferences file -- don't save it either
  -image_out IMAGE_OUT  draw tree into given file (name.pdf or name.png) and
                        exit
  -plugin PLUGIN        start with the given plugin (default: 'FreeDrawing'

or
import kataja
kataja.start(**kwargs)

Launch kataja with arguments

or
import kataja
kataja.draw(tree, image_out="kataja_tree.pdf", **kwargs])

Draw tree into file and exit kataja

"""
import datetime
import os
import sys
import argparse

from PyQt5 import QtWidgets, QtGui, QtCore
import kataja
from kataja.singletons import running_environment, log
# QtPrintSupport is imported here only because py2app then knows to add it as a framework.
# libqcocoa.dynlib requires QtPrintSupport. <-- not needed anymore?


def load_version():
    if running_environment.run_mode == 'source':
        parent = os.path.dirname(os.path.dirname(__file__))
        try:
            with open(os.path.join(parent, 'VERSION')) as version_file:
                version = version_file.read().strip()
        except FileNotFoundError:
            date = str(datetime.datetime.now())
            build_number = 1
            version_name = '0.1'
            version = ' | '.join([date, build_number, version_name])
    else:
        import pkg_resources
        version = pkg_resources.get_distribution('kataja').version

    return version


def bump_and_save_version(version_str):
    old_date, build_number, version_name = version_str.split(' | ', 2)
    build_number = int(build_number)
    date = str(datetime.datetime.now())
    build_number += 1
    new_version_str = ' | '.join([date, str(build_number), version_name])
    try:
        parent = os.path.dirname(os.path.dirname(__file__))
        with open(os.path.join(parent, 'VERSION'), 'w') as version_file:
            version_file.write(new_version_str)
            version_file.write('\n')
    except IOError:
        print('write failed')
    return new_version_str


def launch_from_command_line():
    parser = argparse.ArgumentParser(description='Launch Kataja visualisation environment.')
    parser.add_argument('--reset_prefs', action='store_true', default=False,
                        help='reset the current preferences file to default')
    parser.add_argument('--no_prefs', action='store_true', default=False,
                        help="don't use preferences file -- don't save it either")
    parser.add_argument('-image_out', type=str,
                        help="draw tree into given file (name.pdf or name.png) and exit")
    parser.add_argument('-plugin', type=str, default='FreeDrawing',
                        help="start with the given plugin (default: 'FreeDrawing'")
    parser.add_argument('tree', type=str, nargs='?',
                        help='bracket tree or source tree filename')
    kwargs = vars(parser.parse_args())
    silent = True if kwargs['image_out'] else False
    print(f"Launching Kataja {kataja.__version__} with Python {sys.version_info.major}.{sys.version_info.minor}")
    app = prepare_app()
    log.info('Starting Kataja...')
    if not silent:
        splash_color = QtGui.QColor(238, 232, 213)
        splash_pix = QtGui.QPixmap(os.path.join(running_environment.resources_path, 'katajalogo.png'))
        splash = QtWidgets.QSplashScreen(splash_pix)
        splash.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.SplashScreen |
                              QtCore.Qt.FramelessWindowHint | QtCore.Qt.NoDropShadowWindowHint)
        splash.showMessage(f'{kataja.__author__} | Fetching version...', QtCore.Qt.AlignBottom |
                           QtCore.Qt.AlignHCenter, splash_color)
        app.processEvents()
        splash.show()
        app.processEvents()
        version_str = load_version()
        if running_environment.run_mode == 'source':
            version_str = bump_and_save_version(version_str)

        splash.showMessage(f'{kataja.__author__} | {version_str}',
                           QtCore.Qt.AlignBottom | QtCore.Qt.AlignHCenter, splash_color)
        splash.repaint()
        app.processEvents()

    # importing KatajaMain here because it is slow, and splash screen is now up
    from kataja.KatajaMain import KatajaMain

    window = KatajaMain(app, **kwargs)
    if not silent:
        splash.finish(window)
        app.setActiveWindow(window)
    app.processEvents()
    app.exec_()


def start(**kwargs):
    from kataja.KatajaMain import KatajaMain
    app = prepare_app()
    window = KatajaMain(app, **kwargs)
    app.setActiveWindow(window)
    app.processEvents()
    app.exec_()


def draw(tree, image_out='kataja_tree.pdf', **kwargs):
    from kataja.KatajaMain import KatajaMain
    app = prepare_app()
    KatajaMain(app, tree=tree, image_out=image_out, **kwargs)
    app.processEvents()
    app.exec_()


def prepare_app():
    app = QtWidgets.QApplication(sys.argv)
    app.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps)
    app.setApplicationName('Kataja')
    app.setOrganizationName('Purma')
    app.setOrganizationDomain('purma.fi')
    app.setStyle('fusion')
    return app
