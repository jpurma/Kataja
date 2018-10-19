
from ExamplePlugin.HiConstituent import HiConstituent

# see ExamplePlugin/readme.txt and ExamplePlugin/plugin.json

# List those classes that belong to this plugin and which are used to replace the standard Kataja
# classes. The classes themselves should follow the format of Kataja classes (see
# HiConstituent.py for example) to tell which Kataja class they aim to replace.
# Notice that you can either import these classes or define them here in this file. If you define
# them here, you have to put class definitions *before* the plugin_classes -line.

# plugin_classes = [PythonClass,...]
plugin_classes = [HiConstituent]

# When a plugin is enabled it will try to rebuild the instances of all replaced classes. It is a
# risky process, and all replaced classes can have their own _on_rebuild and _on_teardown methods
# to manually aid in this task. Before the rebuild, 'start_plugin' is called, which can
# initialize things that are not replacements of existing classes.
# When the plugin is disabled, or replaced with another, 'tear_down_plugin' is called where the
# previously initialized special structures can be destroyed.


def start_plugin(main, ctrl, prefs):
    """ This is called when plugin is enabled and can be used for initializations, e.g. loading
    lexicons or adding new data to main, ctrl or prefs without reclassing them."""
    pass


def tear_down_plugin(main, ctrl, prefs):
    """ This is called when plugin is disabled or when switching to another plugin that would
    conflict with this. Plugins should clean up after themselves! """
    pass
