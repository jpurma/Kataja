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

import os
from copy import deepcopy

from PyQt6 import QtGui, QtCore

import kataja
from kataja.Shapes import SHAPE_PRESETS
from kataja.edge_styles import master_styles
from kataja.globals import *

# Disable these if necessary for debugging
enable_loading_preferences = True
enable_saving_preferences = True

curves = ['Linear', 'InQuad', 'OutQuad', 'InOutQuad', 'OutInQuad', 'InCubic', 'OutCubic',
          'InOutCubic', 'OutInCubic', 'InQuart', 'OutQuart', 'InOutQuart', 'OutInQuart', 'InQuint',
          'OutQuint', 'InOutQuint', 'OutInQuint', 'InSine', 'OutSine', 'InOutSine', 'OutInSine',
          'InExpo', 'OutExpo', 'InOutExpo', 'OutInExpo', 'InCirc', 'OutCirc', 'InOutCirc',
          'OutInCirc', 'InElastic', 'OutElastic', 'InOutElastic', 'OutInElastic', 'InBack',
          'OutBack', 'InOutBack', 'OutInBack', 'InBounce', 'OutBounce', 'InOutBounce',
          'OutInBounce']


def extract_bitmaps(filename):
    """
    Helper method to turn 3-color image (blue, black, transparent) into
    bitmap masks.
    :param filename:
    :return: tuple(original as pixmap, color1 as mask (bitmap), color2 as mask)
    """
    pm = QtGui.QPixmap(filename)
    color1 = QtGui.QColor(0, 0, 255)
    color2 = QtGui.QColor(0, 0, 0)
    bms = (pm, pm.createMaskFromColor(color1, QtCore.Qt.MaskMode.MaskOutColor),
           pm.createMaskFromColor(color2, QtCore.Qt.MaskMode.MaskOutColor))
    return bms


class Preferences(object):
    """ Settings that affect globally, these can be pickled,
    but QtPreferences not. Primary singleton object, needs to
    support saving and loading.

    Preferences should follow the following progression:

    element properties < forest settings < preferences

    Preferences is the largest group. It includes global preferences and
    default values for forest settings.
    If forest settings doesn't have a value set, it is get from preferences.
    Similarly if element doesn't have a
    property set, it is get from forest settings, and ultimately from
    preferences.

    This means that the implementation for getting and setting is done mostly
    in elements and in forest settings.
    Preferences it self can be written and read directly.

    preferences with underscore are not saved, they can be used for information about UI drawing

    """
    # Prefs are not saved in save command, but changes here are undoable,
    # so this must support the save protocol.
    not_saved = []

    def __init__(self, running_environment):
        self.save_key = 'preferences'
        self.version = None
        self.tab_order = ['General', 'Drawing', 'Printing', 'Animation', 'Syntax', 'Node styles',
                          'Performance', 'Plugins', 'Advanced']

        self.color_theme = 'solarized_lt'
        self._color_theme_ui = {
            'tab': 'General',
            'special': 'color_themes',
            'label': 'Default colors',
            'help': 'Color theme used for both trees and editor',
            'on_change': 'update_colors',
            'order': 10
        }
        self.hsv = None

        self.syntactic_mode = False
        self.style = 'fancy'
        self.available_styles = ['plain', 'fancy']

        self.touch = True
        self._touch_ui = {
            'tab': 'General',
            'order': 20,
            'label': 'Touch-friendly UI',
            'help': 'Draggable items are larger'
        }

        self.gloss_nodes = True
        self._gloss_nodes_ui = {
            'tab': 'General',
            'order': 30
        }

        self.feature_nodes = True
        self._feature_nodes_ui = {
            'tab': 'General',
            'order': 31,
            'help': 'Draw glosses or features as separate nodes, or include '
                    'them as lines in constituent nodes.'
        }

        self.fonts = running_environment.fonts
        print(f'{running_environment.fonts=}')
        self._fonts_ui = {
            'tab': 'General',
            'special': 'fonts'
        }

        self.large_ui_text = False
        self._large_ui_text_ui = {
            'tab': 'General',
            'label': 'Big UI',
            'help': 'Force user interface to use at least 14pt font.',
            'on_change': 'resize_ui_font',
            'order': 40
        }

        self.auto_pan_select = False
        self._auto_pan_select_ui = {
            'tab': 'General',
            'label': 'Switch to pan / select based on zoom level',
            'help': 'Change mouse mode to Move when zoomed in and Select '
                    'when zoomed out',
            'order': 42
        }

        self.zoom_to_center = True
        self._zoom_to_center_ui = {
            'tab': 'General',
            'label': 'Zoom to center',
            'help': 'Zoom aims to middle of visible region or to '
                    'position of mouse pointer',
            'order': 43
        }

        self.visualization = 'Balanced grid-based tree'
        self._visualization_ui = {
            'tab': 'Drawing',
            'special': 'visualizations',
            'help': 'Default visualization for new trees.',
            'order': 10,
            'on_change': 'update_visualization'
        }

        self.thickness_multiplier = 2
        self._thickness_multiplier_ui = {
            'tab': 'Drawing',
            'range': (0.5, 6.0),
            'order': 50,
            'help': 'If the visualization draws some edges as thicker, '
                    'this defines how much thicker.'
        }

        self.cn_shape = 0
        self._cn_shape_ui = {
            'tab': 'Drawing',
            'choices': [(0, 'Normal'), (1, 'Box'), (2, 'Bracketed'), (3, 'Card'), (4, 'Feature')],
            'label': 'Node shapes',
            'help': 'Overall shape when drawing a constituent node. '
                    'Visualizations may override this.',
            'order': 30
        }

        self.projection_highlights = False
        self._projection_highlights_ui = {
            'tab': 'Drawing',
            'label': 'Highlight projections',
            'help': 'Draw thick lines from projecting heads',
            'order': 31
        }

        self.use_magnets = 3
        self._use_magnets_ui = {
            'tab': 'Drawing',
            'choices': [(0, 'Aim at center of node'), (1, 'Magnets at top and bottom'),
                        (2, 'Align magnets to parent')],
            'help': 'Branches can link to "magnets" in node outlines, '
                    'and magnet placement may be affected by parent node',
            'order': 40
        }
        self.feature_check_display = 1
        self._feature_check_display_ui = {
            'tab': 'Drawing',
            'choices': [(0, "Don't show checking"), (1, 'Features plug into each other'),
                        (2, 'Features are connected by line')],
            'help': "Features can 'check out' matching features. This can be "
                    "explicitly shown or left as implicit.",
            'order': 32
        }

        self.edge_visibility_rule = 0
        self._edge_visibility_rule = {
            'tab': 'Drawing',
            'choices': [(0, "No special rules"), (1, "Hide unjustified edges")],
            'help': "Plugins may use special rules to hide superfluous edges."
        }

        self.edge_width = 16  # 20
        self._edge_width_ui = {
            'tab': 'Drawing',
            'range': (0, 60),
            'order': 20
        }

        self.edge_height = 24
        self._edge_height_ui = {
            'tab': 'Drawing',
            'range': (0, 60),
            'order': 21,
            'help': 'Default width and height for branches'
        }

        self.spacing_between_trees = 3
        self._spacing_between_trees_ui = {
            'tab': 'Drawing',
            'range': (0, 4),
            'help': 'When there are several trees algorithms try to '
                    'use multiples of "edge width" as padding '
                    'between trees.'
        }

        self.show_node_labels = True
        # self._show_node_labels_ui = {'tab': 'Drawing',
        #                             'help': "Nodes can have their own labels defined. "
        #                                     "These are aliases that are not used for"
        #                                     "syntactic computation but may help readability"
        #                                     "Either show them and syntactic labels or show "
        #                                     "only syntactic labels. "}
        self.label_text_mode = 2
        self._label_text_mode_ui = {
            'tab': 'Drawing',
            'choices': [(CHECKED_FEATURES, 'Checked features'),
                        (NODE_LABELS, 'Show all labels'),
                        (NODE_LABELS_FOR_LEAVES, 'Show labels for leaves'),
                        (NO_LABELS, 'No labels for constituents')],
            'label': 'Node label text',
            'help': 'Should the tree show freely editable labels (node '
                    'labels) or labels used in syntactic computation. ',
            'order': 2
        }

        self.linearization_mode = 0
        self._linearization_mode_ui = {
            'tab': 'Syntax',
            'choices': [(IMPLICIT_ORDERING, 'Implicit ordering (use lists)'),
                        (NO_LINEARIZATION, 'Show as unordered sets, disable linearization'),
                        (RANDOM_NO_LINEARIZATION, 'Show as sets, shuffle on redraw'),
                        (USE_LINEARIZATION, 'Use provided linearization algorithm')]
        }

        self.lock_glosses_to_label = 0
        self._lock_glosses_to_label_ui = {
            'tab': 'Drawing',
            'label': 'Lock glosses to labels',
            'help': "Glosses are drawn as part of node's label "
                    "complex or as independent entities",
            'order': 21
        }

        self.feature_positioning = 2
        self._feature_positioning_ui = {
            'tab': 'Drawing',
            'choices': [(0, 'Hanging free'), (1, 'Vertical column'), (2, 'Horizontal row'),
                        (3, 'Two columns')],
            'label': 'Feature arrangement',
            'help': 'How features are arranged below nodes.',
            'order': 28
        }
        self.highlight_dominated_nodes_on_selection = True
        self.hide_edges_if_nodes_overlap = True

        self.trace_strategy = 0
        self._trace_strategy_ui = {
            'tab': 'Drawing',
            'choices': [(0, 'Use multidomination'), (1, 'Make traces'),
                        (2, 'Show traces clustered near original')],
            'label': 'Trace strategy',
            'help': 'How to display moved constituents',
            'order': 29
        }
        self.last_key_colors = {}

        self.show_semantics = False
        self._show_semantics_ui = {
            'tab': 'Syntax',
            'label': 'Show semantics',
            'help': '(If the plugin supports them)',
            'order': 3
        }

        self.single_click_editing = False
        self._single_click_editing_ui = {
            'tab': 'General',
            'label': 'Single click editing',
            'help': 'Selecting a node triggers editing its label'
        }

        self.dpi = 300
        self._dpi_ui = {
            'tab': 'Printing',
            'choices': [72, 150, 300, 450, 600],
            'label': 'DPI',
            'help': 'Dots Per Inch setting when exporting images',
            'order': 20
        }

        self.print_format = 'pdf'
        self._print_format_ui = {
            'tab': 'Printing',
            'choices': ['pdf', 'png'],
            'order': 10
        }

        self.print_file_name = 'kataja_print'
        self._print_file_name_ui = {
            'tab': 'Printing',
            'type': 'text',
            'order': 31,
            'label': 'Quick print file name',
            'help': 'Quick print (Ctrl-p) will print a snapshot of the '
                    'current tree into a file, file names will be '
                    'generated as "katajaprint.pdf", "katajaprint1.pdf", '
                    '"katajaprint2.pdf"... and so on.'
        }

        self.animation_file_name = 'kataja_clip'
        self._animation_file_name_ui = {
            'tab': 'Animation',
            'type': 'text',
            'order': 32,
            'label': 'Animation clip file name',
            'help': 'Recording a clip (Ctrl-r) creates a gif animation of actions.'
                    'File names will be '
                    'generated as "kataja_clip.gif", "kataja_clip1.gif"... and so on.'
        }

        self.animation_width = 640
        self._animation_width_ui = {
            'tab': 'Animation',
            'range': (200, 2048),
            'order': 41
        }
        self.animation_height = 400
        self._animation_height_ui = {
            'tab': 'Animation',
            'range': (200, 2048),
            'order': 42,
            'help': 'Animation file size grows very fast with width and height.'
        }
        self.animation_skip_frames = 2
        self._animation_skip_frames_ui = {
            'tab': 'Animation',
            'range': (1, 4),
            'order': 43,
            'help': 'Include only every nth frame.'
        }
        self.animation_gif = True
        self._animation_gif_ui = {
            'label': 'Save as GIF',
            'tab': 'Animation',
            'order': 44,
        }
        self.animation_webp = False
        self._animation_webp_ui = {
            'label': 'Save as WebP',
            'tab': 'Animation',
            'order': 45,
        }
        self.animation_max_frames = 400
        self._animation_max_frames_ui = {
            'tab': 'Animation',
            'range': (20, 1000),
            'order': 46,
            'help': 'Gif animations store drawing frames in memory before compiling them into an '
                    'animation. Too long animations may cause out of memory problems.'
        }

        self.include_gloss_to_print = True
        self._include_gloss_to_print_ui = {
            'tab': 'Printing'
        }

        self.binary_branching = False
        self._binary_branching_ui = {
            'tab': 'Syntax'
        }

        # Rest of the edges are defined in their corresponding node classes
        self.edges = deepcopy(master_styles['fancy'])
        # Nodes are defined in their classes and preference dict is generated
        #  from those.
        self.nodes = {}
        self._nodes_ui = {
            'tab': 'Node styles',
            'special': 'nodes'
        }

        self.plugins_path = ''
        self.active_plugin_name = 'FreeDrawing'
        self._active_plugin_name_ui = {
            'tab': 'Plugins',
            'special': 'plugins',
            'label': 'Plugins'
        }

        self.FPS = 30
        self._FPS_ui = {
            'tab': 'Performance',
            'range': (10, 60),
            'label': 'Target FPS'
        }
        self.fps_in_msec = int(1000 / self.FPS)

        self.move_frames = 10
        self._move_frames_ui = {
            'tab': 'Performance',
            'range': (0, 30),
            'on_change': 'prepare_easing_curve',
            'label': 'Animation frames'
        }
        self.curve = 'InOutQuad'
        self._curve_ui = {
            'tab': 'Performance',
            'choices': curves,
            'on_change': 'prepare_easing_curve',
            'help': 'Easing curve used to compute the intermediate steps in '
                    'animations. Some options are just silly.'
        }

        self.move_effect = False
        self._move_effect_ui = {
            'tab': 'Performance',
            'help': "Highlight moving nodes. "
        }
        self.glow_effect = False
        self._glow_effect_ui = {
            'tab': 'Performance',
            "help": "Glow effect for selected nodes. Nice effect for dark "
                    "backgrounds, but may look messy on print."
        }

        # self.blender_app_path =
        # '/Applications/blender.app/Contents/MacOS/blender'
        # self.blender_env_path = '/Users/purma/Dropbox/bioling_blender'

        self.userspace_path = 'workspace'
        self._userspace_path_ui = {
            'tab': 'General',
            'type': 'folder',
            'order': 0,
            'label': 'Workspace path',
            'help': 'Default folder for saving, loading and printing trees'
        }

        self.custom_themes = {}
        self.custom_colors = {}

        self.gloss_strategy = 'no'
        # 'message', 'no', 'linearize', 'manual'
        self._gloss_strategy_ui = {
            'tab': 'Drawing',
            'choices': [('message', 'Message provided by parser'),
                        ('linearize', 'Linearisation of current trees'),
                        ('manual', 'Your title/gloss'), ('no', 'No title'), ],
            'help': 'Forests can draw additional text for e.g. gloss, '
                    'linearisation or parser output',
            'order': 40
        }

        self.left_first_rotation = False
        self.log_level = 20

    def import_node_classes(self, classes):
        node_classes = classes.nodes
        for key, nodeclass in node_classes.items():
            self.nodes[key] = deepcopy(nodeclass.default_style['fancy'])

    def restore_default_preferences(self, qt_prefs, running_environment, classes, log):
        source_prefs = Preferences(running_environment)
        self.copy_preferences_from(source_prefs)
        self.import_node_classes(classes)
        qt_prefs.update(self, running_environment, log)

    def update(self, update_dict):
        for key, value in update_dict.items():
            setattr(self, key, value)

    def copy_preferences_from(self, source):
        for key, default_value in vars(self).items():
            if key.startswith('_') or key in Preferences.not_saved:
                continue
            setattr(self, key, getattr(source, key))

    # ##### Reuse preferences display data

    def get_display_data(self, pref_name):
        return getattr(self, f'_{pref_name}_ui', {})

    def get_display_choices(self, pref_name):
        display_data = self.get_display_data(pref_name)
        return display_data.get('choices', [])

    def get_ui_text_for_choice(self, choice, pref_name):
        display_data = self.get_display_data(pref_name)
        if display_data:
            for value, text in display_data.get('choices', []):
                if value == choice:
                    return text
        return ''

    # ##### Save & Load ########################################

    def save_preferences(self):
        """ Save preferences uses QSettings, which is Qt:s abstraction over
        platform-dependant ini/preferences files.
        """

        def string_keyed_dict(value):
            if isinstance(value, dict):
                new = {}
                for k, v in value.items():
                    v = string_keyed_dict(v)
                    if isinstance(k, int):
                        new[str(k)] = v
                    else:
                        new[k] = v
                return new
            else:
                return value

        if not enable_saving_preferences:
            return

        settings = QtCore.QSettings()
        settings.clear()
        d = vars(self)
        for key, value in d.items():
            if key.startswith('_') or key in Preferences.not_saved:
                continue
            value = string_keyed_dict(value)
            settings.setValue(key, value)
        settings.sync()
        print('saved preferences to ', settings.fileName())

    def load_preferences(self, disable=False):

        def string_keys_to_ints(val):
            """ Preferences file only understands strings as dict keys. Convert back to ints
            :param val:
            :return:
            """
            if isinstance(val, dict):
                new = {}
                for k, v in val.items():
                    if k.isdigit():
                        k = int(k)
                    v = string_keys_to_ints(v)
                    new[k] = v
                return new
            else:
                return val

        def pythonify_prefs(settings):
            result = {}
            for group_key in settings.childGroups():
                settings.beginGroup(group_key)
                if group_key.isdigit():
                    group_key = int(group_key)
                result[group_key] = pythonify_prefs(settings)
                settings.endGroup()
            for data_key in settings.childKeys():
                value = string_keys_to_ints(settings.value(data_key))
                if isinstance(value, str) and (value == 'false' or value == 'true'):
                    value = bool(value == 'true')
                if data_key.isdigit():
                    result[int(data_key)] = value
                else:
                    result[data_key] = value
            return result

        if not enable_loading_preferences:
            print('skipping loading preferences because disable_loading_preferences -flag in code')
            return
        elif disable:
            print('skipping loading preferences because command line argument')
            return

        self.version = kataja.__version__
        settings = QtCore.QSettings()
        print('loading preferences from ', settings.fileName())
        ldict = pythonify_prefs(settings)
        if ldict.get('version', '') != self.version:
            print("Skipping possibly mismatching preferences from a previous version."
                  f"Now: {ldict.get('version', '')} Saved prefs: {self.version}")
            return
        for key, default_value in list(vars(self).items()):
            # print(f'setting {key}: {default_value}')
            if key.startswith('_') or key in Preferences.not_saved:
                continue
            if key in ldict:
                # print(f'set to {repr(ldict[key])}')
                setattr(self, key, ldict[key])

    # Support settings-interface ########################

    @property
    def flat_edge_dict(self):
        return master_styles['fancy']

    @property
    def flat_shape_dict(self):
        return SHAPE_PRESETS

    def get(self, key):
        return getattr(self, key)

    def get_for_node_type(self, key, node_type):
        return self.nodes[node_type][key]

    def get_for_edge_type(self, key, edge_type):
        return self.edges[edge_type][key]

    @staticmethod
    def get_for_edge_shape(key, edge_shape):
        return SHAPE_PRESETS[edge_shape].defaults[key]

    def set(self, key, value):
        setattr(self, key, value)

    def set_for_node_type(self, key, value, node_type):
        self.nodes[node_type][key] = value

    def set_for_edge_type(self, key, value, edge_type):
        self.edges[edge_type][key] = value

    def set_for_edge_shape(self, key, value, edge_shape):
        pass

    def delete(self, key):
        pass

    def del_for_node_type(self, key, node_type):
        pass

    def del_for_edge_type(self, key, edge_type):
        pass

    def del_for_edge_shape(self, key, edge_shape):
        pass


class QtPreferences:
    """ Preferences object that holds derived Qt objects like fonts and
    brushes. """

    def __init__(self):  # called to create a placeholder in early imports
        self.easing_curve = []
        self.curve = None
        self.fonts = {}
        self.font_space_width = 0
        self.font_bracket_width = 0
        self.font_bracket_height = 0
        self.no_pen = None
        self.no_brush = None
        self.lock_icon = None
        self.unlock_icon = None
        self.cut_icon = None
        self.delete_icon = None
        self.close_icon = None
        self.fold_pixmap = None
        self.more_pixmap = None
        self.pin_drop_icon = None
        self.left_arrow = None
        self.right_arrow = None
        self.add_icon = None
        self.add_box_icon = None
        self.leaf_pixmap = None
        self.pan_icon = None
        self.select_all_icon = None
        self.center_focus_icon = None
        self.cursor_icon = None
        self.full_icon = None
        self.autozoom_icon = None
        self.settings_icon = None
        self.settings_pixmap = None
        self.triangle_icon = None
        self.triangle_close_icon = None
        self.font_icon = None
        self.info_icon = None
        self.flag_icon = None
        self.v_refresh_icon = None
        self.v_refresh_small_icon = None
        self.h_refresh_icon = None
        self.h_refresh_small_icon = None
        self.camera_icon = None
        self.card_icon = None
        self.eye_pixmap = None
        self.closed_eye_pixmap = None
        self.undo_icon = None
        self.redo_icon = None
        self.kataja_icon = None
        self.italic_icon = None
        self.bold_icon = None
        self.strikethrough_icon = None
        self.underline_icon = None
        self.subscript_icon = None
        self.superscript_icon = None
        self.left_align_icon = None
        self.center_align_icon = None
        self.right_align_icon = None
        self.down_arrow = None
        self.up_arrow = None
        self.remove_styles_icon = None
        self.shape_icon_card = None
        self.shape_icon_plain = None
        self.shape_icon_box = None
        self.shape_icon_scope = None
        self.shape_icon_brackets = None
        self.features_locked_icon = None
        self.features_connected_icon = None
        self.features_apart_icon = None
        self.feature_column_icon = None
        self.feature_2_columns_icon = None
        self.feature_row_icon = None
        self.feature_hanging_icon = None
        self.play_pixmap = None
        self.pause_pixmap = None
        self.record_pixmap = None
        self.stop_pixmap = None
        self.trash_icon = None

    def late_init(self, running_environment, preferences, log):
        """ Here are initializations that require Qt app to exist, to findout dpi etc. These are
        qt requirements that are difficult to get around.
        """
        iconpath = os.path.join(running_environment.resources_path, 'icons')

        def pixmap(path, width=0):
            p = QtGui.QPixmap(os.path.join(iconpath, path))
            if width:
                p = p.scaledToWidth(width)
            return p

        def icon(path):
            p = QtGui.QIcon(os.path.join(iconpath, path))
            return p

        self.prepare_fonts(preferences.fonts, running_environment, log)
        self.prepare_easing_curve(preferences.curve, preferences.move_frames)
        self.toggle_large_ui_font(preferences.large_ui_text, preferences.fonts)
        self.no_pen = QtGui.QPen()
        self.no_pen.setStyle(QtCore.Qt.PenStyle.NoPen)
        self.no_brush = QtGui.QBrush()
        self.no_brush.setStyle(QtCore.Qt.BrushStyle.NoBrush)
        self.lock_icon = icon('lock48.png')
        self.unlock_icon = icon('lock_open48.png')
        self.cut_icon = icon('cut_icon48.png')
        self.delete_icon = icon('backspace48.png')
        self.close_icon = icon('close24.png')
        self.fold_pixmap = pixmap('less24.png')
        self.more_pixmap = pixmap('more24.png')
        self.pin_drop_icon = icon('pin_drop24.png')
        self.left_arrow = extract_bitmaps(os.path.join(iconpath, 'left_2c.gif'))
        self.right_arrow = extract_bitmaps(os.path.join(iconpath, 'right_2c.gif'))
        self.down_arrow = extract_bitmaps(os.path.join(iconpath, 'down_2c.gif'))
        self.up_arrow = extract_bitmaps(os.path.join(iconpath, 'up_2c.gif'))
        self.add_icon = icon('add_box48.png')
        self.leaf_pixmap = pixmap('leaf.png')
        self.add_box_icon = icon('add_box24.png')
        self.settings_icon = icon('settings48.png')
        self.settings_pixmap = pixmap('settings48.png')
        self.flag_icon = icon('flag24.png')
        self.triangle_icon = icon('triangle48.png')
        self.triangle_close_icon = icon('triangle_close48.png')
        self.font_icon = icon('text_format48.png')
        self.v_refresh_icon = icon('v_refresh48.png')
        self.v_refresh_small_icon = icon('v_refresh24.png')
        self.h_refresh_icon = icon('h_refresh48.png')
        self.h_refresh_small_icon = icon('h_refresh24.png')
        self.pan_icon = icon('pan48.png')
        self.select_all_icon = icon('select_all48.png')
        self.cursor_icon = icon('cursor48.png')
        self.center_focus_icon = icon('center_focus48.png')
        self.autozoom_icon = icon('autozoom48.png')
        self.full_icon = icon('full48.png')
        self.camera_icon = icon('camera48.png')
        self.card_icon = icon('card48.png')
        self.closed_eye_pixmap = pixmap('eye_shut48.png')
        self.eye_pixmap = pixmap('eye48.png')
        self.info_icon = icon('info48.png')
        self.undo_icon = icon('undo48.png')
        self.redo_icon = icon('redo48.png')
        self.kataja_icon = icon('kataja.png')
        self.italic_icon = icon('italic48.png')
        self.bold_icon = icon('bold48.png')
        self.strikethrough_icon = icon('strikethrough48.png')
        self.underline_icon = icon('underline48.png')
        self.subscript_icon = icon('subscript48.png')
        self.superscript_icon = icon('superscript48.png')
        self.left_align_icon = icon('align_left48.png')
        self.center_align_icon = icon('align_center48.png')
        self.right_align_icon = icon('align_right48.png')
        self.remove_styles_icon = icon('no_format48.png')
        self.shape_icon_card = icon('shape_button_card.png')
        self.shape_icon_plain = icon('shape_button_plain.png')
        self.shape_icon_box = icon('shape_button_box.png')
        self.shape_icon_scope = icon('shape_button_scope.png')
        self.shape_icon_brackets = icon('shape_button_brackets.png')
        self.features_locked_icon = icon('features_locked.png')
        self.features_connected_icon = icon('features_connected.png')
        self.features_apart_icon = icon('features_apart.png')
        self.feature_column_icon = icon('feature_column.png')
        self.feature_2_columns_icon = icon('feature_2_columns.png')
        self.feature_row_icon = icon('feature_row.png')
        self.feature_hanging_icon = icon('feature_hanging.png')
        self.play_pixmap = pixmap('play72.png')
        self.pause_pixmap = pixmap('pause72.png')
        self.record_pixmap = pixmap('record48.png')
        self.stop_pixmap = pixmap('stop36.png')
        self.trash_icon = icon('trash24.svg')

    def update(self, preferences, running_environment, log):
        print('qt prefs update with ', preferences.fonts)
        self.prepare_fonts(preferences.fonts, running_environment, log)
        self.prepare_easing_curve(preferences.curve, preferences.move_frames)
        self.toggle_large_ui_font(preferences.large_ui_text, preferences.fonts)

    def prepare_easing_curve(self, curve_type, frames):
        curve = QtCore.QEasingCurve(getattr(QtCore.QEasingCurve.Type, curve_type))

        def curve_value(x):
            z = 1.0 / frames
            y = float(x) / frames
            return z + y - curve.valueForProgress(y)

        self.easing_curve = [curve_value(x) for x in range(frames)]
        # self.easing_curve = [(1.0 / self.move_frames) + (float(x) /
        # self.move_frames) - curve.valueForProgress(float(x) /
        # self.move_frames) for x in range(self.move_frames)]
        # self.easing_curve=[(float(
        # x)/self.move_frames)-curve.valueForProgress(float(
        # x)/self.move_frames) for x in range(self.move_frames)]
        s = sum(self.easing_curve)
        self.easing_curve = [x / s for x in self.easing_curve]
        self.curve = curve

    def prepare_fonts(self, fonts_dict, running_environment, log):

        self.fonts = {}
        asana_math = QtGui.QFontDatabase.addApplicationFont(
            os.path.join(running_environment.resources_path, "Asana-Math.otf"))
        if asana_math == -1:
            log.warning("Failed to load 'Asana-Math.otf' from %s, if it is not provided by "
                        "system, things can get ugly.")
        for key, font_tuple in fonts_dict.items():
            if isinstance(font_tuple, list) and len(font_tuple) < 3:
                font_tuple = font_tuple[0]
            name, style, size = font_tuple
            size = int(size)
            font = QtGui.QFontDatabase.font(name, style, size)
            if style == 'Italic':
                font.setItalic(True)
            self.fonts[key] = font
        font = QtGui.QFontMetrics(self.fonts[MAIN_FONT])
        main = self.fonts[MAIN_FONT]
        main.setHintingPreference(QtGui.QFont.HintingPreference.PreferNoHinting)
        self.font_space_width = font.horizontalAdvance(' ')
        self.font_bracket_width = font.horizontalAdvance(']')
        self.font_bracket_height = font.height()

    def toggle_large_ui_font(self, enabled, fonts_dict):
        ui_font = self.fonts[UI_FONT]
        console_font = self.fonts[CONSOLE_FONT]
        if enabled:
            if ui_font.pointSize() < 14:
                ui_font.setPointSize(14)
            if console_font.pointSize() < 14:
                console_font.setPointSize(14)
        else:
            ui_font_def = fonts_dict[UI_FONT]
            ui_font_def = ui_font_def[0] if isinstance(ui_font_def[0], list) else ui_font_def
            ui_font.setPointSize(ui_font_def[2])
            console_font_def = fonts_dict[CONSOLE_FONT]
            console_font_def = console_font_def[0] if isinstance(console_font_def[0], list) else console_font_def
            console_font.setPointSize(console_font_def[2])

    def get_font(self, name) -> QtGui.QFont:
        """
        :param name:
        :return: QFont
        """
        return self.fonts[name]

    def get_key_for_font(self, font):
        """ Find the key for given QFont. Keys are cheaper to store than actual fonts.
        If matching font is not found in current font dict, it is created as custom_n
        :param font: QFont
        :return: string
        """
        for key, value in self.fonts.items():
            if font == value:
                return key
        key_suggestion = 'custom_1'
        i = 1
        while key_suggestion in self.fonts:
            i += 1
            key_suggestion = 'custom_%s' % i
        self.fonts[key_suggestion] = font
        return key_suggestion
