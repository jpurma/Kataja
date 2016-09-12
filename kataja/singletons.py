import logging
from kataja.Preferences import Preferences, QtPreferences
from kataja.Controller import Controller
from kataja.Environment import Environment
from kataja.KatajaFactory import KatajaFactory
from kataja.LogWidgetPusher import LogWidgetPusher

__author__ = 'purma'

running_environment = Environment()
prefs = Preferences(running_environment)
qt_prefs = QtPreferences()
ctrl = Controller()  # Controller()
classes = KatajaFactory()
log = logging.getLogger('kataja')
log.setLevel(logging.DEBUG)
log.log_handler = LogWidgetPusher()
log.addHandler(log.log_handler)


