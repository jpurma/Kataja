from ForestSettings import ForestSettings
from Preferences import Preferences, QtPreferences
from Controller import Controller

__author__ = 'purma'


prefs = Preferences()
qt_prefs = QtPreferences()
forest_settings = ForestSettings(None, prefs)
ctrl = Controller()  # Controller()
