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

import random
import json

from PyQt5.QtGui import QColor as c
import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui


f = open('colors.json', 'r')
color_map = json.load(f, 'utf-8')
f.close()


def rotating_add(base, added):
    """ Adds two numbers, but keeps result between (0,1) rotating over """
    result = base + added
    if result < 0:
        result += 1
        # result -= math.ceil(result)
    elif result > 1:
        result -= 1
        # result -= math.floor(result)
    return result


def limited_add(base, added):
    """ Adds two numbers, but limits result between (0,1) stopping at limits """
    result = base + added
    if result < 0:
        return 0
    if result > 1:
        return 1
    return result


def colorize(h, s, v):
    """ checks if color is bright enough to be recognized and adjusts it until it is """
    ns = s
    nv = v
    if ns < 0.3:
        ns += 0.4
    if nv < 0.3:
        nv += 0.4
    return h, ns, nv


def in_range(h, s, v):
    if h < 0 or h > 1:
        print 'h: ', h
        raise
    if s < 0 or s > 1:
        print 's: ', s
        raise
    if v < 0 or v > 1:
        print 'v: ', v
        raise


class QtColors:
    """ Settings that store Qt object types. These are derived from ForestSettings """

    def __init__(self, prefs, forest_settings=None):
        self.transparent = QtCore.Qt.transparent
        self.white = c(255, 255, 255)
        self.dark_gray = c(80, 80, 80)
        self.gray = self.dark_gray.lighter(200)
        self.black = c(0, 0, 0)
        self.red = c(255, 0, 0, 125)
        self.green = c(0, 255, 0, 125)
        self.blue = c(0, 0, 255, 125)
        self.depth_colors = False

        # Init empty colors to help code detection tools catch problems
        self.drawing = c()
        self.drawing2 = c()
        self.text = c()
        self.paper = c()
        self.ui = c()
        self.ui_inactive = c()
        self.ui_hover = c()
        self.ui_active = c()
        self.ui_secondary = c()
        self.selected = c()
        self.hover = c()
        self.active = c()
        self.console = c()
        ### Gradient ###
        self.gradient = QtGui.QRadialGradient()

        ### Pens ###
        self.drawing_pen = QtGui.QPen()
        self.drawing_pen2 = QtGui.QPen()
        self.writing_pen = QtGui.QPen()
        self.selection_pen = QtGui.QPen()
        self.thin_pen = QtGui.QPen()
        self.thin_pen2 = QtGui.QPen()

        self.white_pen = QtGui.QPen()
        self.thick_drawing_pen = QtGui.QPen()

        ### Set of marker colors available for features ###
        self.feature_palette = []

        self.palette = QtGui.QPalette()

        # Create real colors
        self.update_colors(prefs, forest_settings)


    def color_as_string(self, color):
        return 'h:%.3f s:%.3f v:%.3f alpha:%.3f' % color.getHsvF()


    def get_color_name(self, hsv):
        cc = c()
        cc.setHsvF(hsv[0], hsv[1], hsv[2])
        r, g, b, a = cc.getRgb()
        d_min = 100000
        best = 'white'
        for key, color in color_map.items():
            o_rgb = color['rgb']
            d = (r - o_rgb[0]) * (r - o_rgb[0]) + (g - o_rgb[1]) * (g - o_rgb[1]) + (b - o_rgb[2]) * (b - o_rgb[2])
            if d < d_min:
                d_min = d
                best = key
        return color_map[best]['name']

    def _prepare_root_color(self, prefs, settings, refresh=False, adjusting=False):
        """ Prepare root color (self.hsv), depending on what kind of color settings are active """
        pal = settings.my_palettes()
        if adjusting:
            print 'adjusting...'
            self.hsv = settings.hsv()
            pal[prefs.color_mode] = self.hsv
            return

        if prefs.color_mode == 'random':
            value_low_limit = int(0.38 * 255)
            value_high_limit = int(0.7 * 255)
            if refresh or 'random' not in settings.my_palettes():
                h = random.random()
                s = random.random()  # *0.2+0.8
                v = random.randint(value_low_limit, value_high_limit) / 255.0  # *0.2+0.8
                self.hsv = h, s, v
                pal['random'] = h, s, v
            else:
                self.hsv = pal['random']
        elif prefs.color_mode == 'random-light':
            value_low_limit = int(0.12 * 255)
            value_high_limit = int(0.5 * 255)
            if refresh or 'random-light' not in pal:
                h = random.random()
                s = random.random()  # *0.2+0.8
                v = random.randint(value_low_limit, value_high_limit) / 255.0  # *0.2+0.8
                self.hsv = h, s, v
                pal['random-light'] = h, s, v
            else:
                self.hsv = pal['random-light']


        elif prefs.color_mode == 'random-dark':
            value_low_limit = int(0.6 * 255)
            value_high_limit = int(0.8 * 255)
            if refresh or 'random-dark' not in pal:
                h = random.random()
                s = random.random()  # *0.2+0.8
                v = random.randint(value_low_limit, value_high_limit) / 255.0  # *0.2+0.8
                self.hsv = h, s, v
                pal = h, s, v
            else:
                self.hsv = pal['random-dark']

        elif prefs.color_mode in prefs.color_modes:  # fixed colors and custom colors
            if refresh or prefs.color_mode not in prefs.shared_palettes:
                self.hsv = prefs.color_modes[prefs.color_mode]['hsv']
                prefs.shared_palettes[prefs.color_mode] = self.hsv
            else:
                self.hsv = prefs.shared_palettes[prefs.color_mode]
        settings.hsv(self.hsv)


    def update_colors(self, prefs, settings, refresh=False, adjusting=False):
        """ Create/get root color and build palette around it """
        self._prepare_root_color(prefs, settings, refresh, adjusting)
        h, s, v = self.hsv
        # # This is the base color ##
        key = c()
        # in_range(h, s, v)
        key.setHsvF(h, s, v)
        light_bg = v < 0.5 or (s > 0.7 and 0.62 < h < 0.95)

        analog1 = c()
        h1, s1, v1 = colorize(rotating_add(h, -0.1), s, v)
        # in_range(h1, s1, v1)
        analog1.setHsvF(h1, s1, v1)

        analog2 = c()
        h2, s2, v2 = colorize(rotating_add(h, 0.1), s, v)
        # in_range(h2, s2, v2)
        analog2.setHsvF(h2, s2, v2)

        paper = c()
        hp = h  # -0.1
        sp = s / 4
        vp = (1 - v)
        if light_bg and vp < 0.6:
            vp += 0.3
        if abs(v - vp) <= 0.35:
            if light_bg:
                vp = limited_add(vp, 0.35)
            else:
                vp = limited_add(vp, -0.35)
        # in_range(hp, sp, vp)
        paper.setHsvF(hp, sp, vp)
        complement = c()
        hc = rotating_add(h, -0.5)
        sv = s
        if sv < 0.5:
            sv += 0.2
        # in_range(hc, sv, v)
        complement.setHsvF(hc, sv, v)
        self.drawing = key
        self.drawing2 = analog1
        self.feature = analog2
        self.text = analog2
        self.paper = paper
        self.ui = complement
        self.ui_background = c(paper)
        self.ui_background.setAlphaF(0.8)
        self.ui_inactive = c(complement)
        self.ui_inactive.setAlphaF(0.5)
        self.ui_secondary = c()
        # in_range(abs(h-0.1), s/2, limited_add(v, 0.2))
        self.ui_secondary.setHsvF(abs(h - 0.2), s / 2, limited_add(v, 0.2))
        self.hover = c(key)
        self.hover.setAlphaF(0.5)
        self.active = c(key)
        self.active.setAlphaF(0.7)
        self.ui_hover = c(self.ui)
        self.ui_hover.setAlphaF(0.5)
        self.ui_active = c(self.ui)
        self.ui_active.setAlphaF(0.7)
        # if light_bg:
        #     self.hover = key.lighter()
        #     self.active = self.hover.lighter()
        #     self.ui_hover = self.ui.lighter()
        #     self.ui_active = self.ui_hover.lighter()
        # else:
        #     self.hover = key.darker()
        #     self.active = self.hover.darker()
        #     self.ui_hover = self.ui.darker()
        #     self.ui_active = self.ui_hover.darker()

        self.selected = analog1
        self.console = complement
        if False:  ## Debug colors
            print '--------- color scheme ----------'
            print 'base hue: %.3f' % self.hsv[0]
            print 'base saturation: %.3f' % self.hsv[1]
            print 'base value: %.3f' % self.hsv[2]
            print 'key:     ', self.color_as_string(key)
            print 'analog1: ', self.color_as_string(analog1)
            print 'analog2: ', self.color_as_string(analog2)
            print 'paper:   ', self.color_as_string(paper)
            print 'complement: ', self.color_as_string(complement)
            print '---------------'
            print 'dist between saturation, key - paper: %.3f' % (key.saturationF() - paper.saturationF())
            print 'dist between value, key - paper: %.3f' % (key.valueF() - paper.valueF())
            print 'dist between saturation, complement - paper: %.3f' % (key.saturationF() - paper.saturationF())
            print 'dist between value, complement - paper: %.3f' % (key.valueF() - paper.valueF())

            print '---------------'
            print 'drawing (key):  ', self.color_as_string(self.drawing)
            print 'drawing2 (analog1): ', self.color_as_string(self.drawing2)
            print 'feature(analog2): ', self.color_as_string(self.feature)
            print 'text (analog2):     ', self.color_as_string(self.text)
            print 'paper (paper):    ', self.color_as_string(self.paper)
            print 'ui (complement):       ', self.color_as_string(self.ui)
            print 'ui_inactive (complement a=100): ', self.color_as_string(self.ui_inactive)
            print 'ui_secondary (shifted complement): ', self.color_as_string(self.ui_secondary)
            print 'selected: (analog1)', self.color_as_string(self.selected)
            print 'hover: ', self.color_as_string(self.hover)
            print 'active: ', self.color_as_string(self.active)
            print 'ui_hover: ', self.color_as_string(self.ui_hover)
            print 'ui_active: ', self.color_as_string(self.ui_active)
            print 'console: ', self.color_as_string(self.console)


        ### Gradient ###
        self.gradient = QtGui.QRadialGradient(0, 0, 300)
        self.gradient.setSpread(QtGui.QGradient.PadSpread)
        self.gradient.setColorAt(1, self.paper)
        self.gradient.setColorAt(0, self.paper.lighter())

        ### Pens ###
        self.update_pens(prefs)

        ### Set of marker colors available for features ###
        if s < 0.5:
            ps = s + 0.4
        else:
            ps = s
        if v < 0.5:
            pv = v + 0.4
        else:
            pv = v
        self.feature_palette = [c().fromHsvF(hh / 10.0, ps, pv) for hh in range(0, 10)]

        # rose: H 0.00 S 0.29 L 0.35
        # darker rose: H: 0.97849560877 S: 0.518232476278 L: 0.476821036259
        # (windowText, button, light, dark, mid, text, bright_text, base, window)

        #self.palette = QtGui.QPalette(QtGui.QBrush(self.text), QtGui.QBrush(self.ui), QtGui.QBrush(self.ui_active), QtGui.QBrush(self.ui_inactive), QtGui.QBrush(self.ui), QtGui.QBrush(self.console), QtGui.QBrush(self.console.lighter()), QtGui.QBrush(self.paper), QtGui.QBrush(self.paper))
        p = {'windowText': QtGui.QBrush(self.text), 'button': QtGui.QBrush(self.paper),
             'light': QtGui.QBrush(self.ui_active), 'dark': QtGui.QBrush(self.ui_inactive),
             'mid': QtGui.QBrush(self.ui), 'text': QtGui.QBrush(self.console),
             'bright_text': QtGui.QBrush(self.console.lighter()), 'base': QtGui.QBrush(self.paper),
             'window': QtGui.QBrush(self.paper)}

        self.palette = QtGui.QPalette(p['windowText'], p['button'], p['light'], p['dark'], p['mid'], p['text'],
                                      p['bright_text'], p['base'], p['window'])

        return (h, s, v)


    def update_pens(self, prefs):
        print 'updating pens, base width: ', prefs.draw_width
        self.drawing_pen = QtGui.QPen(self.drawing, prefs.draw_width)
        self.drawing_pen2 = QtGui.QPen(self.drawing, prefs.draw_width)
        self.drawing_pen.setCapStyle(QtCore.Qt.RoundCap)
        self.drawing_pen.setJoinStyle(QtCore.Qt.RoundJoin)
        self.thin = prefs.draw_width / 2.0
        self.normal = prefs.draw_width

        self.writing_pen = QtGui.QPen(self.text, 0)
        self.selection_pen = QtGui.QPen(self.ui, prefs.selection_width)
        self.thin_pen = QtGui.QPen(self.drawing, prefs.draw_width / 2.0)
        self.thin_pen2 = QtGui.QPen(self.drawing2, prefs.draw_width / 2.0)

        self.white_pen = QtGui.QPen(c(255, 255, 255), prefs.draw_width)
        self.thick_drawing_pen = QtGui.QPen(self.drawing, prefs.draw_width * prefs.thickness_multiplier)

        for pen in [self.drawing_pen, self.drawing_pen2, self.selection_pen, self.thin_pen, self.thin_pen2,
                    self.white_pen, self.thick_drawing_pen]:
            pen.setCapStyle(QtCore.Qt.RoundCap)
            pen.setJoinStyle(QtCore.Qt.RoundJoin)

