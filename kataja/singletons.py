from kataja.ForestSettings import ForestSettings
from kataja.Preferences import Preferences, QtPreferences
from kataja.Controller import Controller

__author__ = 'purma'


prefs = Preferences()
qt_prefs = QtPreferences()
forest_settings = ForestSettings(None, prefs)
ctrl = Controller()  # Controller()
