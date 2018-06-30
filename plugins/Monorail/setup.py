# coding=utf-8
from Monorail.Constituent import Constituent
from Monorail.Document import Document
from Monorail.SyntaxConnection import SyntaxConnection

# see ExamplePlugin/readme.txt and ExamplePlugin/plugin.json

# List those classes that belong to this plugin and which are used to replace the standard Kataja
# classes. The classes themselves should follow the format of Kataja classes (see
# HiConstituent.py for example) to tell which Kataja class they aim to replace.
# Notice that you can either import these classes or define them here in this file. If you define
# them here, you have to put class definitions *before* the plugin_parts -line.

# plugin_parts = [PythonClass,...]
plugin_parts = [Constituent, Document, SyntaxConnection]

# When a plugin is enabled it will try to rebuild the instances of all replaced classes. It is a
# risky process, and all replaced classes can have their own _on_rebuild and _on_teardown methods
# to manually aid in this task. Before the rebuild, 'start_plugin' is called, which can
# initialize things that are not replacements of existing classes.
# When the plugin is disabled, or replaced with another, 'tear_down_plugin' is called where the
# previously initialized special structures can be destroyed.

reload_order = ['Monorail.Constituent', 'Monorail.SyntaxConnection',
                'Monorail.Document', 'Monorail.setup']

def start_plugin(main, ctrl, prefs):
    """ This is called when plugin is enabled and can be used for initializations, e.g. loading
    lexicons or adding new data to main, ctrl or prefs without reclassing them."""
    import kataja.globals as g
    ctrl.free_drawing_mode = False
    ctrl.ui.update_edit_mode()
    ctrl.settings.set('label_text_mode', g.SYN_LABELS_FOR_LEAVES, level=g.DOCUMENT)
    ctrl.settings.set('feature_positioning', g.HORIZONTAL_ROW, level=g.DOCUMENT)
    ctrl.settings.set('feature_check_display', g.NO_CHECKING_EDGE, level=g.DOCUMENT)
    ctrl.settings.set_edge_setting('visible', False, g.CONSTITUENT_EDGE, level=g.DOCUMENT)
    ctrl.ui.show_panel('LexiconPanel')


def tear_down_plugin(main, ctrl, prefs):
    """ This is called when plugin is disabled or when switching to another plugin that would
    conflict with this. Plugins should clean up after themselves! """
    pass
