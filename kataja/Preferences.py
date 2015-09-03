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

from collections import OrderedDict

from PyQt5 import QtGui, QtCore

from kataja.globals import *
from kataja.environment import default_userspace_path, resources_path, fonts

disable_saving_preferences = False
# Alternatives: Cambria Math, Asana Math, XITS Math


color_modes = OrderedDict(
    [('solarized_dk', {'name': 'Solarized dark', 'fixed': True, 'hsv': [0, 0, 0]}),
     ('solarized_lt', {'name': 'Solarized light', 'fixed': True, 'hsv': [0, 0, 0]}),
     ('random', {'name': 'Random for each treeset', 'fixed': False, 'hsv': [0, 0, 0]}),
     ('print', {'name': 'Print-friendly', 'fixed': True, 'hsv': [0.2, 0.2, 0.2]}),
     ('bw', {'name': 'Black and white', 'fixed': True, 'hsv': [0, 0, 0]}),
     ('random-light', {'name': 'Random on a light background', 'fixed': False, 'hsv': [0, 0, 0]}),
     ('random-dark', {'name': 'Against a dark background', 'fixed': False, 'hsv': [0, 0, 0]})])


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
    bms = (pm, pm.createMaskFromColor(color1, QtCore.Qt.MaskOutColor),
           pm.createMaskFromColor(color2, QtCore.Qt.MaskOutColor))
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

    """
    # Prefs are not saved in save command, but changes here are undoable,
    # so this must support the save protocol.
    not_saved = ['plugins']

    def __init__(self):
        self.save_key = 'preferences'
        self.draw_width = .5
        self.selection_width = 0.8
        self.thickness_multiplier = 2
        self.color_modes = color_modes
        self.shared_palettes = {}
        self.plugins = {}
        self.dpi = 300
        self._dpi_ui = {'tab': 'Print', 'choices': [72, 150, 300, 450, 600]}
        self.FPS = 30
        self._FPS_ui = {'tab': 'Performance'}

        self._fps_in_msec = 1000 / self.FPS
        self.default_visualization = 'Left first tree'

        # self.blender_app_path =
        # '/Applications/blender.app/Contents/MacOS/blender'
        # self.blender_env_path = '/Users/purma/Dropbox/bioling_blender'

        self.move_frames = 12
        self._move_frames_ui = {'tab': 'Performance'}
        self.curve = 'InQuad'

        # ## Default structural rules that apply to new trees
        self.default_use_projection = True
        self.default_who_projects = 'left_external'
        self.default_use_multidomination = True
        self.default_binary_branching = False

        # ## Default settings for new trees
        self.default_label_style = 2
        self.default_uses_multidomination = True
        self.default_traces_are_grouped_together = 0
        self.default_shows_constituent_edges = True
        self.default_shows_merge_order = False
        self.default_shows_select_order = False
        self.default_draw_features = True
        self.default_draw_width = 2
        self.my_palettes = {}
        self.default_color_mode = 'solarized_lt'
        self.default_hsv = None
        self.default_bracket_style = 0

        self.use_projection = True
        self.who_projects = 'left_external'
        self.use_multidomination = True
        self.binary_branching = False

        self.label_style = 2
        self.uses_multidomination = True
        self.traces_are_grouped_together = 0
        self.shows_constituent_edges = True
        self.shows_merge_order = False
        self.shows_select_order = False
        self.draw_features = True
        self.draw_width = 2
        self.color_mode = 'solarized_lt'
        self.hsv = None
        self.bracket_style = 0


        # ## Global preferences
        self.color_mode = self.default_color_mode
        self.fonts = fonts
        self.keep_vertical_order = False
        self.use_magnets = True
        self.edge_width = 20  # 20
        self.edge_height = 20
        self.hanging_gloss = True
        self.spacing_between_trees = 3
        self.include_features_to_label = False
        self.constituency_edge_shape = 1
        self.feature_edge_shape = 3
        self.move_effect = 0
        self.ui_speed = 8
        self.glow_effect = False
        self._glow_effect_ui = {'tab': 'Performance'}
        self.touch = True
        self.gloss_nodes = True
        self.feature_nodes = True
        self.show_gloss_text = True  # fixme: is it global preference?

        self.userspace_path = default_userspace_path
        self.debug_treeset = resources_path + 'trees.txt'
        self.file_name = 'savetest.kataja'
        self.print_file_path = ''
        self.print_file_name = 'kataja_print'
        self.include_gloss_to_print = True
        self._print_file_path_ui = {'tab': 'Print'}
        self._print_file_name_ui = {'tab': 'Print'}
        self._include_gloss_to_print_ui = {'tab': 'Print'}

        # Rest of the edges are defined in their corresponding node classes
        self.edges = {
            ARROW: {'shape_name': 'linear', 'color': 'accent4', 'pull': 0, 'visible': True,
                    'arrowhead_at_start': False, 'arrowhead_at_end': True, 'font': SMALL_CAPS,
                    'labeled': True},
            DIVIDER: {'shape_name': 'linear', 'color': 'accent6', 'pull': 0, 'visible': True,
                      'arrowhead_at_start': False, 'arrowhead_at_end': False, 'font': SMALL_CAPS,
                      'labeled': True, 'style': 'dashed'}}
        # Nodes are defined in their classes and preference dict is generated
        #  from those.
        self.nodes = {}
        self.node_types_order = []
        self.custom_colors = {}

    def import_node_classes(self, ctrl):
        for key, nodeclass in ctrl.node_classes.items():
            nd = nodeclass.default_style.copy()
            nd['name'] = nodeclass.name[0]
            nd['name_pl'] = nodeclass.name[1]
            nd['display'] = nodeclass.display
            nd['short_name'] = nodeclass.short_name
            self.nodes[key] = nd
            edge_key = nodeclass.default_style['edge']
            if nd['display']:
                self.node_types_order.append(key)
            self.edges[edge_key] = nodeclass.default_edge.copy()
        self.node_types_order.sort()

    def update(self, update_dict):
        """

        :param update_dict:
        """
        for key, value in update_dict.items():
            setattr(self, key, value)

    def add_color_mode(self, color_key, hsv, color_settings):
        """

        :param color_key:
        :param hsv:
        :param color_settings:
        """
        self.color_modes[color_key] = {'name': color_settings.get_color_name(hsv), 'fixed': True,
            'hsv': hsv}

    # ##### Save & Load ########################################

    def save_preferences(self):
        """ Save preferences uses QSettings, which is Qt:s abstraction over
        platform-dependant ini/preferences files.
        It doesn't need any parameters,
        """

        if disable_saving_preferences:
            return

        settings = QtCore.QSettings()
        settings.clear()
        d = vars(self)
        for key, value in d.items():
            if key in Preferences.not_saved:
                continue
            if isinstance(value, dict):
                settings.beginGroup(key)
                for dkey, dvalue in value.items():
                    settings.setValue(str(dkey), dvalue)
                settings.endGroup()
            else:
                settings.setValue(key, value)

    def load_preferences(self):

        if disable_saving_preferences:
            return

        print('loading preferences')
        settings = QtCore.QSettings()
        for key, default_value in vars(self).items():
            if key in Preferences.not_saved:
                continue
            if isinstance(default_value, dict):
                settings.beginGroup(key)
                d = getattr(self, key)
                for dkey in settings.childKeys():
                    d[dkey] = settings.value(dkey, None)
                setattr(self, key, d)
            elif isinstance(default_value, float):
                setattr(self, key, float(settings.value(key, default_value)))
            elif isinstance(default_value, bool):
                setattr(self, key, bool(settings.value(key, default_value)))
            elif isinstance(default_value, int):
                setattr(self, key, int(settings.value(key, default_value)))
            else:
                setattr(self, key, settings.value(key, default_value))


class QtPreferences:
    """ Preferences object that holds derived Qt objects like fonts and
    brushes. """

    def __init__(self):  # called to create a placeholder in early imports
        pass

    def late_init(self, preferences, fontdb):  # called when Qt app exists
        # graphics and fonts can be initiated only when QApplication exists
        """

        :param preferences:
        :param fontdb:
        """
        iconpath = resources_path + 'icons/'

        def pixmap(path, width=0):
            """

            :param path:
            :param width:
            :return:
            """
            p = QtGui.QPixmap(iconpath + path)
            p.setDevicePixelRatio(2.0)
            if width:
                p = p.scaledToWidth(width)
            return p

        def icon(path):
            """

            :param path:
            :param width:
            :return:
            """
            p = QtGui.QIcon(iconpath + path)
            return p

        # print("font families:", QtGui.QFontDatabase().families())
        self.easing_curve = []
        self.fontdb = fontdb
        self.prepare_fonts(preferences.fonts)
        self.prepare_easing_curve(preferences.curve, preferences.move_frames)
        self.no_pen = QtGui.QPen()
        self.no_pen.setStyle(QtCore.Qt.NoPen)
        self.no_brush = QtGui.QBrush()
        self.no_brush.setStyle(QtCore.Qt.NoBrush)
        self.lock_icon = icon('lock32.png')
        self.lock_pixmap = pixmap('lock32.png', 16)
        self.cut_icon = icon('cut_icon48.png')
        self.delete_icon = icon('backspace48.png')
        self.close_icon = icon('close24.png')
        self.fold_icon = icon('less24.png')
        self.more_icon = icon('more24.png')
        self.pin_drop_icon = icon('pin_drop24.png')
        self.left_arrow = extract_bitmaps(iconpath + 'left_2c.gif')
        self.right_arrow = extract_bitmaps(iconpath + 'right_2c.gif')
        self.add_icon = icon('add_box48.png')
        self.add_box_icon = icon('add_box24.png')
        self.settings_icon = icon('settings48.png')
        self.settings_pixmap = pixmap('settings48.png')
        self.triangle_icon = icon('triangle48.png')
        self.triangle_close_icon = icon('triangle_close48.png')
        self.font_icon = icon('text_format48.png')
        self.kataja_icon = icon('kataja.png')

    def update(self, preferences):
        """

        :param preferences:
        """
        self.prepare_fonts(preferences.fonts, preferences)
        self.prepare_easing_curve(preferences._curve, preferences.move_frames)

    def prepare_easing_curve(self, curve_type, frames):
        """

        :param curve_type:
        :param frames:
        :return:
        """
        curve = QtCore.QEasingCurve(getattr(QtCore.QEasingCurve, curve_type))

        def curve_value(x):
            """

            :param x:
            :return:
            """
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

    def prepare_fonts(self, fonts_dict):
        """


        :param preferences:
        :param fonts_dict:
        :param fontdb:
        """
        # print('preparing fonts...')
        self.fonts = {}
        for key, font_tuple in fonts_dict.items():
            name, style, size = font_tuple
            size = int(size)
            font = self.fontdb.font(name, style, size)
            # print(name, font.exactMatch())
            if name == 'Asana Math' and not font.exactMatch():
                print('Loading Asana Math locally')
                self.fontdb.addApplicationFont(resources_path + "Asana-Math.otf")
                font = self.fontdb.font(name, style, size)
            if style == 'Italic':
                font.setItalic(True)
            self.fonts[key] = font
        font = QtGui.QFontMetrics(self.fonts[MAIN_FONT])  # it takes 2 seconds to get FontMetrics
        # print('font leading: %s font height: %s ' % (font.leading(),
        # font.height()))
        main = self.fonts[MAIN_FONT]
        main.setHintingPreference(QtGui.QFont.PreferNoHinting)
        self.font_space_width = font.width(' ')
        self.font_bracket_width = font.width(']')
        self.font_bracket_height = font.height()
        # print('font metrics: ', font)
        # print(self.font_space_width, self.font_bracket_width,
        # self.font_bracket_height)
        self.fonts[SMALL_CAPS].setCapitalization(QtGui.QFont.SmallCaps)

    ### Font helper ###

    def font(self, name):
        """

        :param name:
        :return:
        """
        return self.fonts[name]

        # return self.fonts.get(name, self.fonts[MAIN_FONT])

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
