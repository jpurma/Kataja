# coding=utf-8
import os
import sys

# this path should point to folder cloned from https://github.com/pajubrat/parser-grammar. It is assumed that they are
# in a directory beside Kataja directory, e.g. github/Kataja and github/parser-grammar. You can use absolute path if the
# files are in some other place.
parser_path = '../parser-grammar'
sys.path.append(parser_path)

from plugins.LinearPhaseParser.Document import Document
from plugins.LinearPhaseParser.SyntaxAPI import SyntaxAPI
from plugins.LinearPhaseParser.Feature import Feature
from kataja.singletons import prefs

plugin_path = os.path.dirname(os.path.realpath(__file__))


class PluginSettings:
    test_set_name = os.path.join(parser_path, 'null_subjects_corpus.txt')
    lexicon_file = os.path.join(parser_path, 'lexicon.txt')
    ug_morphemes_file = os.path.join(parser_path, 'ug_morphemes.txt')
    redundancy_rules_file = os.path.join(parser_path, 'redundancy_rules.txt')

    test_set_base = test_set_name.rsplit('.', 1)[0]

    log_file_name = os.path.join(prefs.userspace_path, f'{test_set_base}_log.txt')
    results_file_name = os.path.join(prefs.userspace_path, f'{test_set_base}_results.txt')


# see ExamplePlugin/readme.txt and ExamplePlugin/plugin.json

# List those classes that belong to this plugin and which are used to replace the standard Kataja
# classes. The classes themselves should follow the format of Kataja classes (see
# Constituent.py for example) to tell which Kataja class they aim to replace.

# plugin_classes = [PythonClass,...]
plugin_classes = [Document, SyntaxAPI, Feature]

# When a plugin is enabled it will try to rebuild the instances of all replaced classes.
# Before the rebuild, 'start_plugin' is called, which can initialize things that are not replacements of existing
# classes.


# When the plugin is ordered to reload, we have to manually list here which modules we want to reload. Otherwise their
# code changes are not recognized. After reload the plugin is initialized again, so data files will probably be reloaded
# without explicitly telling. Also the module reload order may be sensitive, so here you can set it.
reload_order = ['LinearPhaseParser.Feature', 'LinearPhaseParser.SyntaxAPI', 'LinearPhaseParser.Document',
                'LinearPhaseParser.LinearPhaseParser', 'LinearPhaseParser.setup']


def start_plugin(main, ctrl, prefs):
    """ This is called when plugin is enabled and can be used for initializations, e.g. changing settings
    or adding new data to main, ctrl or prefs without reclassing them."""
    import kataja.globals as g
    ctrl.plugin_settings = PluginSettings
    ctrl.doc_settings.set('label_text_mode', g.NODE_LABELS)
    ctrl.doc_settings.set('feature_positioning', g.VERTICAL_COLUMN)
    ctrl.doc_settings.set('feature_check_display', g.SHOW_CHECKING_EDGE)
    ctrl.doc_settings.set_for_edge_type('visible', True, g.CONSTITUENT_EDGE)
    ctrl.doc_settings.set_for_edge_type('visible', False, g.FEATURE_EDGE)
    ctrl.ui.show_panel('LexiconPanel')


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
