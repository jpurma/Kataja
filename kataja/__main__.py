"""
Created on 28.8.2013

usage: Kataja.py [-h] [--reset_prefs] [--no_prefs]

Launch Kataja visualisation environment.

optional arguments:
  -h, --help     show this help message and exit
  --reset_prefs  reset the current preferences file to default
  --no_prefs     don't use preferences file -- don't save it either

@author: Jukka Purma
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


def launch_kataja():
    author = 'Jukka Purma'
    parser = argparse.ArgumentParser(description='Launch Kataja visualisation environment.')
    parser.add_argument('--reset_prefs', action='store_true', default=False,
                        help='reset the current preferences file to default')
    parser.add_argument('--no_prefs', action='store_true', default=False,
                        help="don't use preferences file -- don't save it either")
    parser.add_argument('-image_out', type=str,
                        help="draw tree into given file (name.pdf or name.png) and exit")
    parser.add_argument('-plugin', type=str,
                        help="start with the given plugin")
    #parser.add_argument('--no_plugin', action='store_true', default=False,
    #                    help="disable plugin set by preferences")
    parser.add_argument('tree', type=str, nargs='?',
                        help='bracket tree')
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
        splash.showMessage(f'{author} | Fetching version...', QtCore.Qt.AlignBottom |
                           QtCore.Qt.AlignHCenter, splash_color)
        app.processEvents()
        splash.show()
        app.processEvents()
        version_str = load_version()
        if running_environment.run_mode == 'source':
            version_str = bump_and_save_version(version_str)

        splash.showMessage(f'{author} | {version_str}',
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


def prepare_app():
    app = QtWidgets.QApplication(sys.argv)
    app.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps)
    app.setApplicationName('Kataja')
    app.setOrganizationName('Purma')
    app.setOrganizationDomain('purma.fi')
    app.setStyle('fusion')
    return app


launch_kataja()
