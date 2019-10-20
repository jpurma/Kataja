# coding=utf-8
from kataja.plugins.SpreadNet.Constituent import Constituent
from kataja.plugins.SpreadNet.Document import Document
from kataja.plugins.SpreadNet.Feature import Feature
from kataja.plugins.SpreadNet.SyntaxAPI import SyntaxAPI

# see ExamplePlugin/readme.txt and ExamplePlugin/plugin.json

# List those classes that belong to this plugin and which are used to replace the standard Kataja
# classes. The classes themselves should follow the format of Kataja classes (see
# Constituent.py for example) to tell which Kataja class they aim to replace.

# plugin_classes = [PythonClass,...]
plugin_classes = [Feature, Constituent, Document, SyntaxAPI]

# When a plugin is enabled it will try to rebuild the instances of all replaced classes.
# Before the rebuild, 'start_plugin' is called, which can initialize things that are not replacements of existing
# classes.


# When the plugin is ordered to reload, we have to manually list here which modules we want to reload. Otherwise their
# code changes are not recognized. After reload the plugin is initialized again, so data files will probably be reloaded
# without explicitly telling. Also the module reload order may be sensitive, so here you can set it.
reload_order = ['SpreadNet.Feature', 'SpreadNet.Constituent', 'SpreadNet.SyntaxAPI', 'SpreadNet.Document',
                'SpreadNet.Parser',
                'SpreadNet.setup']


def start_plugin(main, ctrl, prefs):
    """ This is called when plugin is enabled and can be used for initializations, e.g. changing settings
    or adding new data to main, ctrl or prefs without reclassing them."""
    import kataja.globals as g
    ctrl.doc_settings.set('label_text_mode', g.NODE_LABELS)
    ctrl.doc_settings.set('feature_positioning', g.VERTICAL_COLUMN)
    ctrl.doc_settings.set('feature_check_display', g.NO_CHECKING_EDGE)
    ctrl.doc_settings.set('gloss_strategy', 'message')
    ctrl.doc_settings.set_for_edge_type('visible', False, g.CONSTITUENT_EDGE)
    ctrl.doc_settings.set_for_edge_type('visible', True, g.FEATURE_EDGE)


# When the plugin is disabled, or replaced with another, 'tear_down_plugin' is called where the
# previously initialized special structures can be destroyed.


def tear_down_plugin(main, ctrl, prefs):
    """ This is called when plugin is disabled. Plugins should clean up after themselves! """
    pass

# Typical call stack when starting a plugin, or starting Kataja with plugin enabled:
#
# 1. Plugin classes replace default classes through KatajaMain.enable_plugin.
# 2. KatajaMain.enable_plugin calls plugin's start_plugin-method (if it exists)
# 3. KatajaMain.enable_plugin initialises new empty document is initialized using KatajaDocument.__init__
# 4. KatajaMain.__init__ calls KatajaDocument.load_default_forests
# 5. Which calls KatajaDocument.create_forests, which is typically reimplemented by plugin.
#   Usually create_forests needs to do the following:
#   a. load a file of example sentences
#   b. if they share a lexicon load it
#   c. iterate through each example sentences:
#       - Create new SyntaxAPI for each sentence.
#       - Assign the given sentence for SyntaxAPI instance's 'input_text' or 'input_tree'.
#       - Assign a lexicon for SyntaxAPI instance.
#       - Store any else metadata needed from parsing into SyntaxAPI instance
#       - Create a Forest instance which has the SyntaxAPI instance as its syntax-parameter.
#       - Append the Forest instance into KatajaDocument's forests.
#   Now the Forests are in place, but they are 'lazy', they remain unparsed until the first time you view them.
#   This way you can handle large sets of input sentences without taking a large hit to Kataja's startup time.
#   When you navigate into Forest instance with False .is_parsed -property, it attempts to parse it by calling
#   self.syntax.create_derivation(forest=self). Syntax refers to SyntaxAPI instance and create_derivation
#   should be implemented by your plugin.
#   SyntaxAPI now can call your parse method, using the sentence and lexicon stored within.
#
#   Notes on parse -methods:
#
#   It is good to have parse methods that both work with Kataja Constituents and allow running parser from command line,
#   without Kataja. It is more efficient to parse large sets of sentences, when the overhead of creating
#   various Kataja-objects is optional, while Kataja visualisations are still available to debug when something goes
#   wrong. This requires that your parser:
#       - Reimplements Constituents and Features conditionally: if there is Kataja available in import environment,
#         use Constituent class that inherits Kataja's BaseConstituent and if not, rely on your own. Of course, they
#         should share as much code as possible. Same with Features, they should inherit BaseFeatures when in Kataja.
#         See Monorail's Constituent.py for example.
#       - If constituents and features have properties that you want available for Kataja visualisations and
#         inspections, annotate them as SavedFields in your BaseConstituent/BaseFeature-derived class.
#       - Let your parse-method to take forest as an optional argument. When a forest is present it should store
#         derivation steps during parse's operations. Derivation steps are created by creating SyntaxState-instances and
#         passing them to forest.add_step-method. For Kataja, parse method doesn't need to return anything: the result
#         of parse is written into forest's derivation steps. For command line use, the parse method can return results
#         in a manner you want.
#
