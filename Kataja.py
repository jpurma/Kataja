#! /usr/bin/env python3.7
# coding=utf-8
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

from kataja.singletons import running_environment, log
# QtPrintSupport is imported here only because py2app then knows to add it as a framework.
# libqcocoa.dynlib requires QtPrintSupport. <-- not needed anymore?


def launch_kataja():

    rp = running_environment.resources_path

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

    print("Launching Kataja with Python %s.%s" % (sys.version_info.major, sys.version_info.minor))
    app = prepare_app()
    log.info('Starting Kataja...')
    if not silent:
        splash_color = QtGui.QColor(238, 232, 213)
        splash_pix = QtGui.QPixmap(os.path.join(rp, 'katajalogo.png'))
        splash = QtWidgets.QSplashScreen(splash_pix)
        splash.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.SplashScreen |
                              QtCore.Qt.FramelessWindowHint | QtCore.Qt.NoDropShadowWindowHint)
        splash.showMessage('%s | Fetching version...' % author, QtCore.Qt.AlignBottom |
                           QtCore.Qt.AlignHCenter, splash_color)
        app.processEvents()
        splash.show()
        app.processEvents()

        # Update version number in file
        version = None
        if running_environment.code_mode == 'python':
            try:
                version_file = open(os.path.join(rp, 'version.txt'), 'r')
                version = version_file.readlines()
                version_file.close()
            except FileNotFoundError:
                pass

        if version:
            date, running_number, version_name = version[0].split(' | ', 2)
            running_number = int(running_number[2:])
            date = str(datetime.datetime.now())
            running_number += 1
        else:
            date = str(datetime.datetime.now())
            running_number = 1
            version_name = ''

        if running_environment.code_mode == 'python':
            try:
                version_file = open(os.path.join(rp, 'version.txt'), 'w')
                version_file.write('%s | v. %s | %s' % (date, running_number, version_name.strip()))
                version_file.close()
            except IOError:
                print('write failed')
                pass

        splash.showMessage('%s | %s | v. %s | %s' % (author, date, running_number, version_name.strip()),
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


if __name__ == '__main__':
    launch_kataja()
