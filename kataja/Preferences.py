# -*- coding: UTF-8 -*-
#############################################################################
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
#############################################################################

import os
import time
from collections import OrderedDict
from PyQt5 import QtGui, QtCore
from kataja.globals import *

fonts = {'font': ('Palatino', 'Normal', 12), 'big_font': ('Palatino', 'Normal', 24),
         'menu_font': ('Monaco', 'Normal', 10), 'ui_font': ('Helvetica', 'Normal', 10),
         'phrase_label_font': ('Helvetica', 'Normal', 10), 'italic_font': ('Century', 'Normal', 10),
         'sc_font': ('Lao MN', 'Normal', 9), 'feature_small': ('Lao MN', 'Normal', 7),
         'symbol_font': ('Menlo', 'Normal', 14)}

color_modes = OrderedDict([('random', {'name': 'Random for each treeset', 'fixed': False, 'hsv': (0, 0, 0)}),
                           ('print', {'name': 'Print-friendly', 'fixed': True, 'hsv': (0.2, 0.2, 0.2)}),
                           ('bw', {'name': 'Black and white', 'fixed': True, 'hsv': (0, 0, 0)}),
                           ('random-light', {'name': 'Random on a light background', 'fixed': False, 'hsv': (0, 0, 0)}),
                           ('random-dark', {'name': 'Against a dark background', 'fixed': False, 'hsv': (0, 0, 0)})])


# fonts = {'font': ('Palatino', 12),
#     'big_font': ('Palatino', 24),
#     'menu_font': ('Palatino', 10),
#     'phrase_label_font': ('Palatino', 10),
#     'italic_font': ('Palatino', 10),
#     'sc_font': ('Palatino', 9),
#     'feature_small': ('Palatino', 7),
#     'symbol_font': ('Palatino', 14)
# }


class Preferences(object):
    """ Settings that affect globally, these can be pickled, but QtPreferences not. Primary singleton object, needs to support saving and loading. 

    Preferences should follow the following progression:

    element properties < forest settings < preferences

    Preferences is the largest group. It includes global preferences and default values for forest settings. If forest settings doesn't have a value set, it is get from preferences. Similarly if element doesn't have a property set, it is get from forest settings, and ultimately from preferences.

    This means that the implementation for getting and setting is done mostly in elements and in forest settings. Preferences it self can be written and read directly.

    """
    saved_fields = 'all'
    singleton_key = 'Preferences'

    def __init__(self):
        self.draw_width = .5
        self.selection_width = 0.8
        self.thickness_multiplier = 2
        self.color_mode = 'random'
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

        ### Default structural rules that apply to new trees
        self.default_use_projection = True
        self.default_who_projects = 'left_external'
        self.default_use_multidomination = True
        self.default_binary_branching = False

        ### Default settings for new trees
        self.default_label_style = 2
        self.default_uses_multidomination = True
        self.default_traces_are_grouped_together = 0 
        self.default_show_constituent_edges = True
        self.default_show_merge_order = True
        self.default_show_select_order = False
        self.default_draw_features = True
        self.default_draw_width = 2
        self.default_my_palettes = {}
        self.default_hsv = None
        self.default_bracket_style = 0 

        ### Global preferences
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
        self.touch = False
        self.app_path = self.solve_app_path()
        self.debug_treeset = self.app_path + '/trees.txt'
        self.file_name = 'savetest.kataja'
        self.print_file_path = self.app_path
        self.print_file_name = 'kataja_print'
        self.include_gloss_to_print = True

        ### Default edge settings 
        # Edge types
        # CONSTITUENT_EDGE = 1
        # FEATURE_EDGE = 2
        # GLOSS_EDGE = 3
        # ARROW = 4
        # PROPERTY_EDGE = 5
        # ABSTRACT_EDGE = 0
        # ATTRIBUTE_EDGE = 6

        self.edges = {
            CONSTITUENT_EDGE: {
                'shape_name': 'shaped_relative_cubic', 
                'color': 'key',
                'pull': .24, 
                'visible': True,
                'has_outline': True,
                'pen_width': 1,
                'is_filled': True
                },
            FEATURE_EDGE: {
                'shape_name': 'relative_cubic', 
                'color': 'analog1',
                'pull': .32, 
                'visible': True,
                'has_outline': True,
                'pen_width': 1,
                'is_filled': True
                },
            GLOSS_EDGE: {
                'shape_name': 'relative_cubic', 
                'color': 'analog2',
                'pull': .40, 
                'visible': True,
                'has_outline': True,
                'pen_width': 1,
                'is_filled': False
                },
            ARROW: {
                'shape_name': 'arrow', 
                'color': 'key',
                'pull': 0, 
                'visible': True,
                'has_outline': True,
                'pen_width': 1,
                'is_filled': True
                },
            PROPERTY_EDGE: {
                'shape_name': 'linear', 
                'color': 'key',
                'pull': .40, 
                'visible': True,
                'has_outline': True,
                'pen_width': 1,
                'is_filled': False
                },
            ABSTRACT_EDGE: {
                'shape_name': 'linear', 
                'color': 'key',
                'pull': .40, 
                'visible': True,
                'has_outline': True,
                'pen_width': 1,
                'is_filled': False
                },
            ATTRIBUTE_EDGE: {
                'shape_name': 'linear', 
                'color': 'key',
                'pull': .40, 
                'visible': True,
                'has_outline': True,
                'pen_width': 1,
                'is_filled': False
                },

        }

        ### Default node settings
        # Node types
        # ABSTRACT_NODE = 0
        # CONSTITUENT_NODE = 1
        # FEATURE_NODE = 2
        # ATTRIBUTE_NODE = 3
        # GLOSS_NODE = 4
        # PROPERTY_NODE = 5
        self.nodes = {
            ABSTRACT_NODE : {
                'color': 'key',
                'font': 'main',
                'font-size': 10
            },
            CONSTITUENT_NODE : {
                'color': 'key',
                'font': 'main',
                'font-size': 10                
            },
            FEATURE_NODE: {
                'color': 'analog1',
                'font': 'cursive',
                'font-size': 10
 
            },
            ATTRIBUTE_NODE: {
                'color': 'analog2',
                'font': 'small-caps',
                'font-size': 10
            },          
            GLOSS_NODE : {
                'color': 'analog2',
                'font': 'cursive',
                'font-size': 10
            },
            PROPERTY_NODE : {
                'color': 'key 0.7',
                'font': 'small-caps',
                'font-size': 10
            },

        }

    def solve_app_path(self):
        full_path = os.path.abspath(os.path.dirname(__file__))
        #         if getattr(sys, 'frozen', None) and hasattr(sys, '_MEIPASS'):
        #            print 'found meipass:',sys._MEIPASS
        #         else:
        #            print 'plain pathname:', os.path.dirname(__file__)
        path_list = full_path.split('/')
        if 'Kataja.app' in path_list:
            i = path_list.index('Kataja.app')
            path = '/'.join(path_list[:i])
        else:
            path = '/'.join(path_list[:-1])
        return path


    def update(self, update_dict):
        for key, value in update_dict.items():
            setattr(self, key, value)


    def add_color_mode(self, color_key, hsv, color_settings):
        self.color_modes[color_key] = {'name': color_settings.get_color_name(hsv), 'fixed': True, 'hsv': hsv}


    ###### Save & Load ########################################

    def save(self):
        """ Dumps the preferences as a dict """
        dump = vars(self)
        print 'written preferences, %s chars.' % len(unicode(dump))
        return dump

    def load(self, data):
        for key, value in data:
            setattr(self, key, value)


def extract_bitmaps(filename):
    pm = QtGui.QPixmap(filename)
    color1 = QtGui.QColor(0, 0, 255)
    color2 = QtGui.QColor(0, 0, 0)
    bms = (
        pm, pm.createMaskFromColor(color1, QtCore.Qt.MaskOutColor),
        pm.createMaskFromColor(color2, QtCore.Qt.MaskOutColor))
    #for bmp in bms:
    #    bmp.setMask(bmp.createMaskFromColor(QtGui.QColor(255,255,255))) 
    return bms


class QtPreferences:
    """ Preferences object that holds derived Qt objects like fonts and brushes. """

    def __init__(self):  # called to create a placeholder in early imports
        self.font = QtGui.QFont()
        self.big_font = QtGui.QFont()
        self.menu_font = QtGui.QFont()
        self.ui_font = QtGui.QFont()
        self.phrase_label_font = QtGui.QFont()
        self.italic_font = QtGui.QFont()
        self.feature_small = QtGui.QFont()
        self.sc_font = QtGui.QFont()

    def late_init(self, preferences, fontdb):  # called when Qt app exists
        # graphics and fonts can be initiated only when QApplication exists
        t = time.time()
        self.easing_curve = []
        self.prepare_fonts(preferences.fonts, fontdb)
        print '-- prepared fonts ... ', time.time() - t
        self.prepare_easing_curve(preferences._curve, preferences.move_frames)
        self.no_pen = QtGui.QPen()
        self.no_pen.setStyle(QtCore.Qt.NoPen)
        self.no_brush = QtGui.QBrush()
        self.no_brush.setStyle(QtCore.Qt.NoBrush)
        self.lock_icon = QtGui.QPixmap('icons/lock.png').scaledToWidth(16)
        self.left_arrow = extract_bitmaps('kataja/icons/triangle_left.gif')
        self.right_arrow = extract_bitmaps('kataja/icons/right_2c.png')
        print '-- loaded icon and scaled it ... ', time.time() - t

    def update(self, preferences):
        self.prepare_fonts(preferences.fonts)
        self.prepare_easing_curve(preferences._curve, preferences.move_frames)


    def prepare_easing_curve(self, curve_type, frames):
        curve = QtCore.QEasingCurve(getattr(QtCore.QEasingCurve, curve_type))

        def curve_value(x):
            z = 1.0 / frames
            y = float(x) / frames
            return z + y - curve.valueForProgress(y)

        self.easing_curve = [curve_value(x) for x in range(frames)]
        # self.easing_curve = [(1.0 / self.move_frames) + (float(x) / self.move_frames) - curve.valueForProgress(float(x) / self.move_frames) for x in range(self.move_frames)]
        # self.easing_curve=[(float(x)/self.move_frames)-curve.valueForProgress(float(x)/self.move_frames) for x in range(self.move_frames)]
        s = sum(self.easing_curve)
        self.easing_curve = [x / s for x in self.easing_curve]

    def prepare_fonts(self, fonts_dict, fontdb):
        for key, font_tuple in fonts_dict.items():
            setattr(self, '_' + key, font_tuple)
            setattr(self, key, fontdb.font(font_tuple[0], font_tuple[1], font_tuple[2]))
        font = QtGui.QFontMetrics(self.font)  # it takes 2 seconds to get FontMetrics
        self.font_space_width = font.width(' ')
        self.font_bracket_width = font.width(']')
        self.font_bracket_height = font.height()
        print self.font_space_width, self.font_bracket_width, self.font_bracket_height
        self.sc_font.setCapitalization(QtGui.QFont.SmallCaps)

