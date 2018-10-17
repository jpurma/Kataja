import logging
import sys
from kataja.settings.Preferences import Preferences, QtPreferences
from kataja.Controller import Controller
from kataja.environments.Base import Base
from kataja.environments.Mac import Mac
from kataja.environments.Win import Win
from kataja.KatajaFactory import KatajaFactory
from kataja.LogWidgetPusher import LogWidgetPusher

if sys.platform == 'darwin':
    running_environment = Mac()
elif sys.platform.startswith('win'):
    running_environment = Win()
else:
    running_environment = Base()

prefs = Preferences(running_environment)
qt_prefs = QtPreferences()
ctrl = Controller(prefs)  # Controller()
classes = KatajaFactory()
log = logging.getLogger('kataja')
log.setLevel(logging.DEBUG)
log.log_handler = LogWidgetPusher()
log.addHandler(log.log_handler)



