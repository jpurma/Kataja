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
from pathlib import Path
import plistlib
import time
from collections import OrderedDict

from PyQt5 import QtGui, QtCore
import sys

from kataja.globals import *
from kataja.utils import time_me

# Alternatives: Cambria Math, Asana Math, XITS Math

mac_fonts = {MAIN_FONT: ('Asana Math', 'Normal', 12),
         CONSOLE_FONT: ('Monaco', 'Normal', 10),
         UI_FONT: ('Helvetica', 'Normal', 10),
         BOLD_FONT: ('STIX', 'Bold', 12),
         ITALIC_FONT: ('Asana Math', 'Italic', 12),
         SMALL_CAPS: ('Lao MN', 'Normal', 10),
         SMALL_FEATURE: ('Lao MN', 'Normal', 7)}

linux_fonts = {MAIN_FONT: ('Asana Math', 'Normal', 12),
         CONSOLE_FONT: ('Courier', 'Normal', 10),
         UI_FONT: ('Droid Sans', 'Normal', 10),
         ITALIC_FONT: ('Asana Math', 'Italic', 12),
         BOLD_FONT: ('STIX', 'Bold', 12),
         SMALL_CAPS: ('Lao MN', 'Normal', 9),
         SMALL_FEATURE: ('Lao MN', 'Normal', 7)}

if sys.platform == 'darwin':
    fonts = mac_fonts
else:
    fonts = linux_fonts

color_modes = OrderedDict([
        ('solarized_dk', {'name': 'Solarized dark', 'fixed': True, 'hsv': (0, 0, 0)}),
        ('solarized_lt', {'name': 'Solarized light', 'fixed': True, 'hsv': (0, 0, 0)}),
        ('random', {'name': 'Random for each treeset', 'fixed': False, 'hsv': (0, 0, 0)}),
                           ('print', {'name': 'Print-friendly', 'fixed': True, 'hsv': (0.2, 0.2, 0.2)}),
                           ('bw', {'name': 'Black and white', 'fixed': True, 'hsv': (0, 0, 0)}),
                           ('random-light', {'name': 'Random on a light background', 'fixed': False, 'hsv': (0, 0, 0)}),
                           ('random-dark', {'name': 'Against a dark background', 'fixed': False, 'hsv': (0, 0, 0)})])



class Preferences(object):
    """ Settings that affect globally, these can be pickled, but QtPreferences not. Primary singleton object, needs to support saving and loading. 

    Preferences should follow the following progression:

    element properties < forest settings < preferences

    Preferences is the largest group. It includes global preferences and default values for forest settings. If forest settings doesn't have a value set, it is get from preferences. Similarly if element doesn't have a property set, it is get from forest settings, and ultimately from preferences.

    This means that the implementation for getting and setting is done mostly in elements and in forest settings. Preferences it self can be written and read directly.

    """
    # Prefs are not saved in save command, but changes here are undoable, so this must support the save protocol.
    saved_fields = 'all'
    not_saved = ['resources_path', 'default_userspace_path', 'preferences_path', 'in_app']


    def __init__(self):
        self.save_key = 'preferences'
        self.draw_width = .5
        self.selection_width = 0.8
        self.thickness_multiplier = 2
        self.color_modes = color_modes
        self.shared_palettes = {}

        self.dpi = 300
        self.FPS = 30
        self.fps_in_msec = 1000 / self.FPS
        self.default_visualization = 'Left first tree'

        self.blender_app_path = '/Applications/blender.app/Contents/MacOS/blender'
        self.blender_env_path = '/Users/purma/Dropbox/bioling_blender'

        self.move_frames = 12
        self._curve = 'InQuad'

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
        self.default_color_mode = 'solarized_dk'
        self.default_hsv = None
        self.default_bracket_style = 0

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
        self.console_visible = False
        self.ui_speed = 8
        self.touch = True

        my_path = Path(__file__).parts
        if sys.platform == 'darwin' and 'Kataja.app' in my_path:
            print(my_path)
            i = my_path.index('Kataja.app')
            self.resources_path = str(Path(*list(my_path[:i + 1]) + ['Contents', 'Resources', 'resources', ''])) + '/'
            self.default_userspace_path = '~/'
            self.preferences_path = '~/Library/Preferences/Kataja.plist'
            self.in_app = True
        else:
            self.resources_path = './resources/'
            self.default_userspace_path = './'
            self.preferences_path = './Kataja.plist'
            self.in_app = False
        print("resources_path: ", self.resources_path)
        print("default_userspace_path: ", self.default_userspace_path)
        print("preferences_path: ", self.preferences_path)
        self.userspace_path = ''
        self.debug_treeset = self.resources_path + 'trees.txt'
        self.file_name = 'savetest.kataja'
        self.print_file_path = ''
        self.print_file_name = 'kataja_print'
        self.include_gloss_to_print = True

        # ## Default edge settings
        # Edge types
        # CONSTITUENT_EDGE = 1
        # FEATURE_EDGE = 2
        # GLOSS_EDGE = 3
        # ARROW = 4
        # PROPERTY_EDGE = 5
        # ABSTRACT_EDGE = 0
        # ATTRIBUTE_EDGE = 6

        self.edges = {
            CONSTITUENT_EDGE: {'shape_name': 'shaped_cubic', 'color': 'content1', 'pull': .24, 'visible': True,
                               'arrowhead_at_start': False, 'arrowhead_at_end': False, 'labeled': False},
            FEATURE_EDGE: {'shape_name': 'cubic', 'color': 'accent2', 'pull': .32, 'visible': True,
                           'arrowhead_at_start': False, 'arrowhead_at_end': False, 'labeled': False},
            GLOSS_EDGE: {'shape_name': 'cubic', 'color': 'accent4', 'pull': .40, 'visible': True,
                         'arrowhead_at_start': False, 'arrowhead_at_end': False, 'labeled': False},
            ARROW: {'shape_name': 'linear', 'color': 'accent4', 'pull': 0, 'visible': True,
                    'arrowhead_at_start': False, 'arrowhead_at_end': True, 'font': SMALL_CAPS, 'labeled': True},
            DIVIDER: {'shape_name': 'linear', 'color': 'accent6', 'pull': 0, 'visible': True,
                    'arrowhead_at_start': False, 'arrowhead_at_end': False, 'font': SMALL_CAPS, 'labeled': True, 'style':'dashed'},
            PROPERTY_EDGE: {'shape_name': 'linear', 'color': 'accent5', 'pull': .40, 'visible': True,
                            'arrowhead_at_start': False, 'arrowhead_at_end': False, 'labeled': False},
            ABSTRACT_EDGE: {'shape_name': 'linear', 'color': 'content1', 'pull': .40, 'visible': True,
                            'arrowhead_at_start': False, 'arrowhead_at_end': False, 'labeled': False},
            ATTRIBUTE_EDGE: {'shape_name': 'linear', 'color': 'content1', 'pull': .50, 'visible': True,
                             'arrowhead_at_start': False, 'arrowhead_at_end': False, 'labeled': False},
        }

        ### Default node settings
        # Node types
        # ABSTRACT_NODE = 0
        # CONSTITUENT_NODE = 1
        # FEATURE_NODE = 2
        # ATTRIBUTE_NODE = 3
        # GLOSS_NODE = 4
        # PROPERTY_NODE = 5
        self.nodes = {ABSTRACT_NODE: {'color': 'content1', 'font': MAIN_FONT, 'font-size': 10},
                      CONSTITUENT_NODE: {'color': 'content1', 'font': MAIN_FONT, 'font-size': 10},
                      FEATURE_NODE: {'color': 'accent2', 'font': ITALIC_FONT, 'font-size': 10},
                      ATTRIBUTE_NODE: {'color': 'accent4', 'font': SMALL_CAPS, 'font-size': 10},
                      GLOSS_NODE: {'color': 'accent5', 'font': ITALIC_FONT, 'font-size': 10},
                      PROPERTY_NODE: {'color': 'accent6', 'font': SMALL_CAPS, 'font-size': 10},

        }
        self.custom_colors = {}
        if not self.load_preferences():
            print("Didn't find any settings plist -file, trying to write one.")
            self.save_preferences(path=self.resources_path+'default.plist')


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
        self.color_modes[color_key] = {'name': color_settings.get_color_name(hsv), 'fixed': True, 'hsv': hsv}


    # ##### Save & Load ########################################

    def save(self):
        """ Dumps the preferences as a dict """
        dump = vars(self)
        print('written preferences, %s chars.' % len(str(dump)))
        return dump

    def load(self, data):
        """

        :param data:
        """
        for key, value in data:
            setattr(self, key, value)

    def save_preferences(self, path=None):
        """ Save preferences as a plist file. Since plists can only have string keys, all int keys are turned into
        _ikey_%s - form, and restored when loaded.
        If argument path is given, save preferences there, otherwise save to environment's default preference location.
        :param path: (optional) string for location and filename where to save.
        :return: None
        """
        # some 'preferences' are set based on environment where we are running and shouldn't be saved
        # or loaded from file.

        def int_keys_to_str(dd):
            """ Recursively turn int keys to strings
            :param dd: dict
            :return: new dict where int keys are turned to strings
            """
            nl = {}
            for key, item in dd.items():
                if item is None:
                    item = '_None'
                if isinstance(key, int):
                    key = '_ikey_%s' % key
                if isinstance(item, dict):
                    item = int_keys_to_str(item)
                nl[key] = item
            return nl

        if not path:
            path = self.preferences_path
        d = dict(vars(self))
        for k in Preferences.not_saved:
            del d[k]
        d = int_keys_to_str(d)

        f = open(path, 'wb')
        plistlib.dump(d, f)
        f.close()
        print("Wrote settings to: " + path)


    @time_me
    def load_preferences(self):
        """ Tries to load preferences from plist and overwrite values in this object.
        Looks to preferences path (~/Library/Preferences/Kataja.plist) and
        if not there, takes default preferences from resources/default.plist.
        If even that fails, takes the current preferences and makes a
        resources/default.plist out of that.
        :return: None
        """

        def str_keys_to_int(dd):
            """ Recursively turn encoded (_ikey_%) string keys back to ints and None -values replaced with '_None'
            :param dd: dict
            :return: new dict where string keys are turned back to ints
            """
            nl = {}
            for key, item in dd.items():
                if key.startswith('_ikey_'):
                    key = int(key[6:])
                if isinstance(item, str) and item == '_None':
                    item = None
                if isinstance(item, dict):
                    item = str_keys_to_int(item)
                nl[key] = item
            return nl

        paths = [self.preferences_path, self.resources_path+'default.plist']
        found = False
        for path in paths:
            if os.path.exists(path):
                f = open(path, 'rb')
                d = plistlib.load(f)
                d = str_keys_to_int(d)

                writables = dict(vars(self))
                for k in Preferences.not_saved:
                    del writables[k]
                good_keys = list(writables.keys())

                for key, value in d.items():
                    if key in good_keys:
                        setattr(self, key, value)
                print('loaded settings: ', d)
                found = True
                break
        return found


def extract_bitmaps(filename):
    """
    Helper method to turn 3-color image (blue, black, transparent) into bitmap masks.
    :param filename:
    :return: tuple(original as pixmap, color1 as mask (bitmap), color2 as mask)
    """
    pm = QtGui.QPixmap(filename)
    color1 = QtGui.QColor(0, 0, 255)
    color2 = QtGui.QColor(0, 0, 0)
    bms = (
        pm, pm.createMaskFromColor(color1, QtCore.Qt.MaskOutColor),
        pm.createMaskFromColor(color2, QtCore.Qt.MaskOutColor))
    return bms


class QtPreferences:
    """ Preferences object that holds derived Qt objects like fonts and brushes. """

    def __init__(self):  # called to create a placeholder in early imports
        pass

    def late_init(self, preferences, fontdb):  # called when Qt app exists
        # graphics and fonts can be initiated only when QApplication exists
        """

        :param preferences:
        :param fontdb:
        """
        pm = QtGui.QPixmap
        iconpath = preferences.resources_path+'icons/'
        print("font families:", QtGui.QFontDatabase().families())
        self.easing_curve = []
        self.prepare_fonts(preferences.fonts, fontdb, preferences)
        self.prepare_easing_curve(preferences._curve, preferences.move_frames)
        self.no_pen = QtGui.QPen()
        self.no_pen.setStyle(QtCore.Qt.NoPen)
        self.no_brush = QtGui.QBrush()
        self.no_brush.setStyle(QtCore.Qt.NoBrush)
        self.lock_icon = pm(iconpath + 'lock.png').scaledToWidth(16)
        self.cut_icon = pm(iconpath + 'cut_icon48.png').scaledToWidth(24)
        self.delete_icon = pm(iconpath + 'backspace48.png').scaledToWidth(24)
        self.close_icon = pm(iconpath + 'close24.png') #.scaledToWidth(24)
        self.fold_icon = pm(iconpath + 'less24.png') #.scaledToWidth(24)
        self.more_icon = pm(iconpath + 'more24.png') #.scaledToWidth(24)
        self.pin_drop_icon = pm(iconpath + 'pin_drop24.png') #.scaledToWidth(24)
        self.left_arrow = extract_bitmaps(iconpath + 'left_2c.gif')
        self.right_arrow = extract_bitmaps(iconpath + 'right_2c.gif')
        self.triangle_icon = pm(iconpath + 'triangle48.png')
        self.triangle_close_icon = pm(iconpath + 'triangle_close48.png')
        #self.gear_icon = extract_bitmaps(preferences.resources_path+'icons/gear2_16.gif')

    def update(self, preferences):
        """

        :param preferences:
        """
        self.prepare_fonts(preferences.fonts)
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
        # self.easing_curve = [(1.0 / self.move_frames) + (float(x) / self.move_frames) - curve.valueForProgress(float(x) / self.move_frames) for x in range(self.move_frames)]
        # self.easing_curve=[(float(x)/self.move_frames)-curve.valueForProgress(float(x)/self.move_frames) for x in range(self.move_frames)]
        s = sum(self.easing_curve)
        self.easing_curve = [x / s for x in self.easing_curve]

    def prepare_fonts(self, fonts_dict, fontdb, preferences):
        """

        :param fonts_dict:
        :param fontdb:
        """
        self.fonts = {}
        for key, font_tuple in fonts_dict.items():
            name, style, size = font_tuple
            font = fontdb.font(name, style, size)
            if name == 'Asana Math' and not font.exactMatch():
                print('Loading Asana Math locally')
                fontdb.addApplicationFont(preferences.resources_path + "Asana-Math.otf")
                font = fontdb.font(name, style, size)
            self.fonts[key] = font
        font = QtGui.QFontMetrics(self.fonts[MAIN_FONT])  # it takes 2 seconds to get FontMetrics
        self.font_space_width = font.width(' ')
        self.font_bracket_width = font.width(']')
        self.font_bracket_height = font.height()
        #print(self.font_space_width, self.font_bracket_width, self.font_bracket_height)
        self.fonts[SMALL_CAPS].setCapitalization(QtGui.QFont.SmallCaps)

    ### Font helper ###

    def font(self, name):
        return self.fonts.get(name, self.fonts[MAIN_FONT])

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

