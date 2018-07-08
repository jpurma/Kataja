# -*- coding: UTF-8 -*-
# ############################################################################
#
# *** Kataja - Biolinguistic Visualization tool ***
#
# Copyright 2013 Jukka Purma
#
# This file is part of Kataja.
#
# Kataja is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Kataja is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Kataja.  If not, see <http://www.gnu.org/licenses/>.
#
# ############################################################################
from mgtdbp.Parser import Parser
from mgtdbp.Constituent import Constituent
from mgtdbp.Feature import Feature
from mgtdbp.Document import Document
from mgtdbp.SyntaxAPI import SyntaxAPI
import os
from PyQt5 import QtCore

# see ExamplePlugin/readme.txt and ExamplePlugin/plugin.json

# List those classes that belong to this plugin and which are used to replace the standard Kataja
# classes. The classes themselves should follow the format of Kataja classes (see
# HiConstituent.py for example) to tell which Kataja class they aim to replace.
# Notice that you can either import these classes or define them here in this file. If you define
# them here, you have to put class definitions *before* the plugin_parts -line.

# plugin_parts = [PythonClass,...]
plugin_parts = [Feature, Constituent, Parser, Document, SyntaxAPI]

# When a plugin is enabled it will try to rebuild the instances of all replaced classes. It is a
# risky process, and all replaced classes can have their own _on_rebuild and _on_teardown methods
# to manually aid in this task. Before the rebuild, 'start_plugin' is called, which can
# initialize things that are not replacements of existing classes.
# When the plugin is disabled, or replaced with another, 'tear_down_plugin' is called where the
# previously initialized special structures can be destroyed.

# reload_order = ['myplugin.SyntaxAPI', 'myplugin.KDocument', 'myplugin.setup']
reload_order = ['mgtdbp.Constituent', 'mgtdbp.Feature',
                'mgtdbp.Parser', 'mgtdbp.Document', 'mgtdbp.SyntaxAPI',
                'mgtdbp.setup']

plugin_preferences = {}
# These are additional preferences added by plugin. They extend the bottom layer of preferences
# hierarchy and can have an UI elements in 'Preferences' panel. You can have custom panels or
# code to make them editable in document-, forest- or node/edge-level, or just programmatically
# store values there. They will be stored in prefs, document.settings, forest.settings,
# node.settings or edge.settings, managed by ctrl.settings -object. They compete for namespace with
# existing settings, so see kataja. Preferences to find out what is already there and use unique
# names.

def before_init(main, ctrl, prefs):
    """ This is called when plugin is enabled but before the new classes replace the existing.
    This is rarely needed, usually start_plugin is better place to do initialisations. """
    pass


def start_plugin(main, ctrl, prefs):
    """ This is called when plugin is enabled, after new classes are initialised. This can be
    used for initializations, e.g. loading lexicons or adding new data to main, ctrl or prefs
    without reclassing them."""
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


