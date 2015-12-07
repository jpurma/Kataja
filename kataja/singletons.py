from kataja.Preferences import Preferences, QtPreferences
from kataja.Controller import Controller
from kataja.RunningEnvironment import RunningEnvironment

__author__ = 'purma'

running_environment = RunningEnvironment()
prefs = Preferences(running_environment)
qt_prefs = QtPreferences()
ctrl = Controller()  # Controller()


def restore_default_preferences():
    global prefs
    prefs = Preferences(running_environment)
    qt_prefs.update(prefs, running_environment)
