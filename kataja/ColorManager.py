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

import random
import json
from collections import OrderedDict

from PyQt5.QtGui import QColor as c
from PyQt5.QtGui import QColor
import PyQt5.QtGui as QtGui

from kataja.singletons import ctrl, prefs




def rotating_add(base, added):
    """ Adds two numbers, but keeps result between (0,1) rotating over
    :param base:
    :param added:
    """
    result = base + added
    if result < 0:
        result += 1
        # result -= math.ceil(result)
    elif result > 1:
        result -= 1
        # result -= math.floor(result)
    return result


def limited_add(base, added):
    """ Adds two numbers, but limits result between (0,1) stopping at limits
    :param base:
    :param added:
    """
    result = base + added
    if result < 0:
        return 0
    if result > 1:
        return 1
    return result


def colorize(h, s, v):
    """ checks if color is bright enough to be recognized and adjusts it until it is
    :param h:
    :param s:
    :param v:
    """
    ns = s
    nv = v
    if ns < 0.3:
        ns += 0.4
    if nv < 0.3:
        nv += 0.4
    return h, ns, nv


def in_range(h, s, v):
    """

    :param h:
    :param s:
    :param v:
    :raise:
    """
    if h < 0 or h > 1:
        print('h: ', h)
        raise Exception("Hue not in range: " + h)
    if s < 0 or s > 1:
        print('s: ', s)
        raise Exception("Saturation not in range: " + s)
    if v < 0 or v > 1:
        print('v: ', v)
        raise Exception("Value (lightness) not in range: " + v)


class ColorManager:
    """ Selects, creates and gives access to various palettes. The current palette is available in dict d with keys for default names and
        possibility to expand with custom colors. Includes methods for creating new palettes.

    ForestSettings or single elements map their color definitions to keys in palette.

    When a palette is saved, its QColors should be turned to HSV+A tuples. 
     """

    def __init__(self, hsv_key=None):
        print("*** Creating ColorManager")
        f = open('colors.json', 'r')
        self.color_map = json.load(f) # json.load(f, 'utf-8')
        f.close()

        if not hsv_key:
            hsv_key = (0.00, 0.29, 0.35)  # dark rose
        self.hsv = hsv_key
        self.d = OrderedDict()
        self.custom_colors = []
        self.compute_palette(hsv_key)

    def current_color_mode(self, value=None):
        """

        :param value:
        :return:
        """
        return ctrl.fs.color_mode(value)

    def activate_color_mode(self, refresh=False):
        """

        :param refresh:
        """
        self._prepare_root_color(refresh=refresh)

    def get_color_mode_data(self, mode):
        """

        :param mode:
        :return:
        """
        data = prefs.color_modes.get(mode, None)
        if not data:
            data = prefs.custom_color_modes.get(mode, None)
            if not data:
                print('**** Missing color mode data for "%s" ****' % mode)
                data = prefs.color_modes['random']
        return data

    def get(self, key):
        """

        :param key:
        :return:
        """
        return self.d[key]

    def update_colors(self, prefs, settings, refresh=False, adjusting=False):
        """ Create/get root color and build palette around it
        :param prefs:
        :param settings:
        :param refresh:
        :param adjusting:
        """

        print('update colors called with refresh: %s adjusting: %s' % (refresh, adjusting))
        self.activate_color_mode(refresh=refresh)
        self.compute_palette(self.hsv)

    def compute_palette(self, hsv):
        """ Create/get root color and build palette around it. 
        :param hsv:
        Leaves custom colors as they are. """
        self.hsv = hsv
        h, s, v = hsv
        # # This is the base color ##
        key = c()
        # in_range(h, s, v)
        key.setHsvF(h, s, v)
        light_bg = v < 0.5 or (s > 0.7 and 0.62 < h < 0.95)
        self.d['key'] = key
        key05 = c(key)
        key05.setAlphaF(0.5)
        self.d['key 0.5'] = key05
        key07 = c(key)
        key07.setAlphaF(0.7)
        self.d['key 0.7'] = key07

        analog1 = c()
        h1, s1, v1 = colorize(rotating_add(h, -0.1), s, v)
        # in_range(h1, s1, v1)
        analog1.setHsvF(h1, s1, v1)
        self.d['analog1'] = analog1

        analog2 = c()
        h2, s2, v2 = colorize(rotating_add(h, 0.1), s, v)
        # in_range(h2, s2, v2)
        analog2.setHsvF(h2, s2, v2)
        self.d['analog2'] = analog2

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
        self.d['paper'] = paper
        paper08 = c(paper)
        paper08.setAlphaF(0.8)
        self.d['paper 0.8'] = paper08
        self.d['paper lighter'] = paper.lighter()

        complement = c()
        hc = rotating_add(h, -0.5)
        sv = s
        if sv < 0.5:
            sv += 0.2
        # in_range(hc, sv, v)
        complement.setHsvF(hc, sv, v)
        self.d['complement'] = complement
        complement05 = c(complement)
        complement05.setAlphaF(0.5)
        self.d['complement 0.5'] = complement05
        complement07 = c(complement)
        complement07.setAlphaF(0.7)
        self.d['complement 0.7'] = complement07

        secondary = c()
        secondary.setHsvF(abs(h - 0.2), s / 2, limited_add(v, 0.2))
        self.d['secondary'] = secondary
        self.d['white'] = c(255, 255, 255)
        self.d['black'] = c(0, 0, 0)

        # ## Set of marker colors available for features ###
        if s < 0.5:
            ps = s + 0.4
        else:
            ps = s
        if v < 0.5:
            pv = v + 0.4
        else:
            pv = v
        for i in range(0, 10):
            self.d['rainbow_%s' % (i + 1)] = c().fromHsvF(i / 10.0, ps, pv)

            # ## Gradient ###
        self.gradient = QtGui.QRadialGradient(0, 0, 300)
        self.gradient.setSpread(QtGui.QGradient.PadSpread)
        self.gradient.setColorAt(1, self.d['paper'])
        self.gradient.setColorAt(0, self.d['paper'].lighter())

    def drawing(self) -> QColor:
        """ Main drawing color for constituent branches
        :return: QColor
        """
        return self.d['key']

    def text(self) -> QColor:
        """ Main text color for constituent nodes
        :return: QColor
        """
        return self.d['analog2']

    def paper(self) -> QColor:
        """ Background color
        :return: QColor
        """
        return self.d['paper']

    def ui(self) -> QColor:
        """ Primary UI text color
        :return: QColor
        """
        return self.d['complement']

    def ui_paper(self) -> QColor:
        """ UI background color -- use for UI elements that float over main drawing.
        :return: QColor
        """
        return self.d['complement 0.5']

    def secondary(self) -> QColor:
        """


        :return:
        """
        return self.d['secondary']

    def selection(self):
        """


        :return:
        """
        return self.d['secondary']

    def rainbow(self, n):
        """

        :param n:
        :return:
        """
        return self.d['rainbow_%s' % (n % 10)]

    def add_custom_color(self, color, n=-1):
        """

        :param color:
        :param n:
        """
        if n == -1:
            # find the first free (empty) custom color
            j = -1
            found = True
            keys = list(self.d.keys())
            while found:
                j += 1
                found = ('custom_%s' % j) in keys
            n = j
        self.d['custom_%s' % n] = color

    def get_custom_color(self, n):
        """

        :param n:
        :return:
        """
        return self.get('custom_%s' % n)

    def active(self, color):
        """

        :param color:
        :return:
        """
        if color.value() > 230:
            return color.darker(300)
        else:
            return color.lighter(300)

    def inactive(self, color):
        """

        :param color:
        :return:
        """
        nc = c(color)
        nc.setAlphaF(0.5)
        return nc

    def hovering(self, color):
        """

        :param color:
        :return:
        """
        if color.value() > 230:
            return color.darker(200)
        else:
            return color.lighter(200)

    def selected(self, color):
        """

        :param color:
        :return:
        """
        if color.value() > 230:
            return color.darker()
        else:
            return color.lighter()

    def get_color_name(self, hsv):
        """

        :param hsv:
        :return:
        """
        cc = c()
        cc.setHsvF(hsv[0], hsv[1], hsv[2])
        r, g, b, a = cc.getRgb()
        d_min = 100000
        best = 'white'
        for key, color in self.color_map.items():
            o_rgb = color['rgb']
            d = (r - o_rgb[0]) * (r - o_rgb[0]) + (g - o_rgb[1]) * (g - o_rgb[1]) + (b - o_rgb[2]) * (b - o_rgb[2])
            if d < d_min:
                d_min = d
                best = key
        return self.color_map[best]['name']

    def _prepare_root_color(self, refresh=False):
        """ Prepare root color (self.hsv), depending on what kind of color settings are active """
        mode = self.current_color_mode()
        fs = ctrl.fs

        remembered_value = fs.last_key_color_for_mode(mode)
        if remembered_value and not refresh:
            self.hsv = remembered_value
        else:
            if mode == 'random':
                h = random.random()
                s = random.random()  # *0.2+0.8
                value_low_limit = int(0.38 * 255)
                value_high_limit = int(0.7 * 255)
                v = random.randint(value_low_limit, value_high_limit) / 255.0  # *0.2+0.8
                self.hsv = h, s, v
                fs.last_key_color_for_mode(mode, (h, s, v))
            elif mode == 'random-light':
                h = random.random()
                s = random.random()  # *0.2+0.8
                value_low_limit = int(0.12 * 255)
                value_high_limit = int(0.5 * 255)
                v = random.randint(value_low_limit, value_high_limit) / 255.0  # *0.2+0.8
                self.hsv = h, s, v
                fs.last_key_color_for_mode(mode, (h, s, v))

            elif mode == 'random-dark':
                h = random.random()
                s = random.random()  # *0.2+0.8
                value_low_limit = int(0.6 * 255)
                value_high_limit = int(0.8 * 255)
                v = random.randint(value_low_limit, value_high_limit) / 255.0  # *0.2+0.8
                self.hsv = h, s, v
                fs.last_key_color_for_mode(mode, (h, s, v))
            else:
                self.hsv = self.get_color_mode_data(mode)['hsv']


    def get_qt_palette(self):
        """


        :return:
        """
        p = {'windowText': QtGui.QBrush(self.d['key']), 'button': QtGui.QBrush(self.paper()),
             'light': QtGui.QBrush(self.active(self.d['complement'])), 'dark': QtGui.QBrush(self.d['complement 0.7']),
             'mid': QtGui.QBrush(self.hovering(self.d['complement'])), 'text': QtGui.QBrush(self.d['secondary']),
             'bright_text': QtGui.QBrush(self.d['secondary'].lighter()), 'base': QtGui.QBrush(self.paper()),
             'window': QtGui.QBrush(self.paper())}

        return QtGui.QPalette(p['windowText'], p['button'], p['light'], p['dark'], p['mid'], p['text'],
                              p['bright_text'], p['base'], p['window'])



        # def update_colors(self, prefs, settings, refresh=False, adjusting=False):
        # """ Create/get root color and build palette around it """

        # self._prepare_root_color(prefs, settings, refresh, adjusting)
        # h, s, v = self.hsv
        # # # This is the base color ##
        # key = c()
        #     # in_range(h, s, v)
        #     key.setHsvF(h, s, v)
        #     light_bg = v < 0.5 or (s > 0.7 and 0.62 < h < 0.95)

        #     analog1 = c()
        #     h1, s1, v1 = colorize(rotating_add(h, -0.1), s, v)
        #     # in_range(h1, s1, v1)
        #     analog1.setHsvF(h1, s1, v1)

        #     analog2 = c()
        #     h2, s2, v2 = colorize(rotating_add(h, 0.1), s, v)
        #     # in_range(h2, s2, v2)
        #     analog2.setHsvF(h2, s2, v2)

        #     paper = c()
        #     hp = h  # -0.1
        #     sp = s / 4
        #     vp = (1 - v)
        #     if light_bg and vp < 0.6:
        #         vp += 0.3
        #     if abs(v - vp) <= 0.35:
        #         if light_bg:
        #             vp = limited_add(vp, 0.35)
        #         else:
        #             vp = limited_add(vp, -0.35)
        #     # in_range(hp, sp, vp)
        #     paper.setHsvF(hp, sp, vp)
        #     complement = c()
        #     hc = rotating_add(h, -0.5)
        #     sv = s
        #     if sv < 0.5:
        #         sv += 0.2
        #     # in_range(hc, sv, v)
        #     complement.setHsvF(hc, sv, v)
        #     self.drawing = key
        #     self.drawing2 = analog1
        #     self.feature = analog2
        #     self.text = analog2
        #     self.paper = paper
        #     self.ui = complement
        #     self.ui_background = c(paper)
        #     self.ui_background.setAlphaF(0.8)
        #     self.ui_inactive = c(complement)
        #     self.ui_inactive.setAlphaF(0.5)
        #     self.ui_secondary = c()
        #     # in_range(abs(h-0.1), s/2, limited_add(v, 0.2))
        #     self.ui_secondary.setHsvF(abs(h - 0.2), s / 2, limited_add(v, 0.2))
        #     self.hover = c(key)
        #     self.hover.setAlphaF(0.5)
        #     self.active = c(key)
        #     self.active.setAlphaF(0.7)
        #     self.ui_hover = c(self.ui)
        #     self.ui_hover.setAlphaF(0.5)
        #     self.ui_active = c(self.ui)
        #     self.ui_active.setAlphaF(0.7)
        #     # if light_bg:
        #     #     self.hover = key.lighter()
        #     #     self.active = self.hover.lighter()
        #     #     self.ui_hover = self.ui.lighter()
        #     #     self.ui_active = self.ui_hover.lighter()
        #     # else:
        #     #     self.hover = key.darker()
        #     #     self.active = self.hover.darker()
        #     #     self.ui_hover = self.ui.darker()
        #     #     self.ui_active = self.ui_hover.darker()

        #     self.selected = analog1
        #     self.console = complement
        #     if False:  ## Debug colors
        #         print '--------- color scheme ----------'
        #         print 'base hue: %.3f' % self.hsv[0]
        #         print 'base saturation: %.3f' % self.hsv[1]
        #         print 'base value: %.3f' % self.hsv[2]
        #         print 'key:     ', self.color_as_string(key)
        #         print 'analog1: ', self.color_as_string(analog1)
        #         print 'analog2: ', self.color_as_string(analog2)
        #         print 'paper:   ', self.color_as_string(paper)
        #         print 'complement: ', self.color_as_string(complement)
        #         print '---------------'
        #         print 'dist between saturation, key - paper: %.3f' % (key.saturationF() - paper.saturationF())
        #         print 'dist between value, key - paper: %.3f' % (key.valueF() - paper.valueF())
        #         print 'dist between saturation, complement - paper: %.3f' % (key.saturationF() - paper.saturationF())
        #         print 'dist between value, complement - paper: %.3f' % (key.valueF() - paper.valueF())

        #         print '---------------'
        #         print 'drawing (key):  ', self.color_as_string(self.drawing)
        #         print 'drawing2 (analog1): ', self.color_as_string(self.drawing2)
        #         print 'feature(analog2): ', self.color_as_string(self.feature)
        #         print 'text (analog2):     ', self.color_as_string(self.text)
        #         print 'paper (paper):    ', self.color_as_string(self.paper)
        #         print 'ui (complement):       ', self.color_as_string(self.ui)
        #         print 'ui_inactive (complement a=100): ', self.color_as_string(self.ui_inactive)
        #         print 'ui_secondary (shifted complement): ', self.color_as_string(self.ui_secondary)
        #         print 'selected: (analog1)', self.color_as_string(self.selected)
        #         print 'hover: ', self.color_as_string(self.hover)
        #         print 'active: ', self.color_as_string(self.active)
        #         print 'ui_hover: ', self.color_as_string(self.ui_hover)
        #         print 'ui_active: ', self.color_as_string(self.ui_active)
        #         print 'console: ', self.color_as_string(self.console)


        #     ### Gradient ###
        #     self.gradient = QtGui.QRadialGradient(0, 0, 300)
        #     self.gradient.setSpread(QtGui.QGradient.PadSpread)
        #     self.gradient.setColorAt(1, self.paper)
        #     self.gradient.setColorAt(0, self.paper.lighter())

        #     ### Pens ###
        #     self.update_pens(prefs)

        #     ### Set of marker colors available for features ###
        #     if s < 0.5:
        #         ps = s + 0.4
        #     else:
        #         ps = s
        #     if v < 0.5:
        #         pv = v + 0.4
        #     else:
        #         pv = v
        #     self.feature_palette = [c().fromHsvF(hh / 10.0, ps, pv) for hh in range(0, 10)]

        # rose: H 0.00 S 0.29 L 0.35
        # darker rose: H: 0.97849560877 S: 0.518232476278 L: 0.476821036259
        # (windowText, button, light, dark, mid, text, bright_text, base, window)

        #self.palette = QtGui.QPalette(QtGui.QBrush(self.text), QtGui.QBrush(self.ui), QtGui.QBrush(self.ui_active), QtGui.QBrush(self.ui_inactive), QtGui.QBrush(self.ui), QtGui.QBrush(self.console), QtGui.QBrush(self.console.lighter()), QtGui.QBrush(self.paper), QtGui.QBrush(self.paper))
        # p = {'windowText': QtGui.QBrush(self.text), 'button': QtGui.QBrush(self.paper),
        #      'light': QtGui.QBrush(self.ui_active), 'dark': QtGui.QBrush(self.ui_inactive),
        #      'mid': QtGui.QBrush(self.ui), 'text': QtGui.QBrush(self.console),
        #      'bright_text': QtGui.QBrush(self.console.lighter()), 'base': QtGui.QBrush(self.paper),
        #      'window': QtGui.QBrush(self.paper)}

        # self.palette = QtGui.QPalette(p['windowText'], p['button'], p['light'], p['dark'], p['mid'], p['text'],
        #                               p['bright_text'], p['base'], p['window'])

        # return (h, s, v)




        # def update_pens(self, prefs):
        #     print 'updating pens, base width: ', prefs.draw_width
        #     self.drawing_pen = QtGui.QPen(self.drawing, prefs.draw_width)
        #     self.drawing_pen2 = QtGui.QPen(self.drawing, prefs.draw_width)
        #     self.drawing_pen.setCapStyle(QtCore.Qt.RoundCap)
        #     self.drawing_pen.setJoinStyle(QtCore.Qt.RoundJoin)
        #     self.thin = prefs.draw_width / 2.0
        #     self.normal = prefs.draw_width

        #     self.writing_pen = QtGui.QPen(self.text, 0)
        #     self.selection_pen = QtGui.QPen(self.ui, prefs.selection_width)
        #     self.thin_pen = QtGui.QPen(self.drawing, prefs.draw_width / 2.0)
        #     self.thin_pen2 = QtGui.QPen(self.drawing2, prefs.draw_width / 2.0)

        #     self.white_pen = QtGui.QPen(c(255, 255, 255), prefs.draw_width)
        #     self.thick_drawing_pen = QtGui.QPen(self.drawing, prefs.draw_width * prefs.thickness_multiplier)

        #     for pen in [self.drawing_pen, self.drawing_pen2, self.selection_pen, self.thin_pen, self.thin_pen2,
        #                 self.white_pen, self.thick_drawing_pen]:
        #         pen.setCapStyle(QtCore.Qt.RoundCap)
        #         pen.setJoinStyle(QtCore.Qt.RoundJoin)



