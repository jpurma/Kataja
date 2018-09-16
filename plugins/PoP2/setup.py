# coding=utf-8
from PoP2.ConstituentB import Constituent
from PoP2.FeatureB import Feature
from PoP2.PoPDeriveK import Generate
from PoP2.ForestKeeper import PoPDocument

# see ExamplePlugin/readme.txt and ExamplePlugin/plugin.json

# List those classes that belong to this plugin and which are used to replace the standard Kataja
# classes. The classes themselves should follow the format of Kataja classes (see
# HiConstituent.py for example) to tell which Kataja class they aim to replace.
# Notice that you can either import these classes or define them here in this file. If you define
# them here, you have to put class definitions *before* the plugin_classes -line.

# plugin_classes = [PythonClass,...]
plugin_classes = [Constituent, Feature, Generate, PoPDocument]

# When a plugin is enabled it will try to rebuild the instances of all replaced classes. It is a
# risky process, and all replaced classes can have their own _on_rebuild and _on_teardown methods
# to manually aid in this task. Before the rebuild, 'start_plugin' is called, which can
# initialize things that are not replacements of existing classes.
# When the plugin is disabled, or replaced with another, 'tear_down_plugin' is called where the
# previously initialized special structures can be destroyed.

plugin_preferences = {'play_nice': True}
# These are additional preferences added by plugin. They extend the bottom layer of preferences
# hierarchy and can have an UI elements in 'Preferences' panel. You can have custom panels or
# code to make them editable in document-, forest- or node/edge-level, or just programmatically
# store values there. They will be stored in prefs, doc_settings. forest.settings,
# node.settings or edge.settings. They compete for namespace with
# existing settings, so see kataja.Preferences to find out what is already there and use unique
# names.

def before_init(main, ctrl, prefs):
    """ This is called when plugin is enabled but before the new classes replace the existing.
    This is rarely needed, usually start_plugin is better place to do initialisations. """
    pass


def start_plugin(main, ctrl, prefs):
    """ This is called when plugin is enabled, after new classes are initialised. This can be
    used for initializations, e.g. loading lexicons or adding new data to main, ctrl or prefs
    without reclassing them."""


def tear_down_plugin(main, ctrl, prefs):
    """ This is called when plugin is disabled or when switching to another plugin that would
    conflict with this. Plugins should clean up after themselves! """
    pass


