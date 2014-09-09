# coding=utf-8
"""
This is a setup.py script generated by py2applet

Usage:
    python setup.py py2app
"""

from setuptools import setup

APP = ['Kataja.py']
DATA_FILES = ['resources']
OPTIONS = {'argv_emulation': True, 
'includes': ['sip', 'PyQt5'],
'iconfile': 'resources/icons/Kataja.icns'
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
#'sip', 'py2app', 