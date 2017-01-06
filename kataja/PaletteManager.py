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

import math
import operator
import random
from collections import OrderedDict

import PyQt5.QtGui as QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtGui import QColor as c

from kataja.globals import FOREST
from kataja.color_names import color_names
from kataja.singletons import ctrl, prefs, log

# Solarized colors from http://ethanschoonover.com/solarized  (Ethan Schoonover)
# We are going to have one theme built around these.

# SOLARIZED HEX     16/8 TERMCOL  XTERM/HEX   L*A*B      RGB         HSB
# --------- ------- ---- -------  ----------- ---------- ----------- -----------
# base03    #002b36  8/4 brblack  234 #1c1c1c 15 -12 -12   0  43  54 193 100  21
# base02    #073642  0/4 black    235 #262626 20 -12 -12   7  54  66 192  90  26
# base01    #586e75 10/7 brgreen  240 #585858 45 -07 -07  88 110 117 194  25  46
# base00    #657b83 11/7 bryellow 241 #626262 50 -07 -07 101 123 131 195  23  51
# base0     #839496 12/6 brblue   244 #808080 60 -06 -03 131 148 150 186  13  59
# base1     #93a1a1 14/4 brcyan   245 #8a8a8a 65 -05 -02 147 161 161 180   9  63
# base2     #eee8d5  7/7 white    254 #e4e4e4 92 -00  10 238 232 213  44  11  93
# base3     #fdf6e3 15/7 brwhite  230 #ffffd7 97  00  10 253 246 227  44  10  99
# yellow    #b58900  3/3 yellow   136 #af8700 60  10  65 181 137   0  45 100  71
# orange    #cb4b16  9/3 brred    166 #d75f00 50  50  55 203  75  22  18  89  80
# red       #dc322f  1/1 red      160 #d70000 50  65  45 220  50  47   1  79  86
# magenta   #d33682  5/5 magenta  125 #af005f 50  65 -05 211  54 130 331  74  83
# violet    #6c71c4 13/5 brmagenta 61 #5f5faf 50  15 -45 108 113 196 237  45  77
# blue      #268bd2  4/4 blue      33 #0087ff 55 -10 -45  38 139 210 205  82  82
# cyan      #2aa198  6/6 cyan      37 #00afaf 60 -35 -05  42 161 152 175  74  63
# green     #859900  2/2 green     64 #5f8700 60 -20  65 133 153   0  68 100  60

sol = [c(0, 43, 54), c(7, 54, 66), c(88, 110, 117), c(101, 123, 131), c(131, 148, 150),
       c(147, 161, 161), c(238, 232, 213), c(253, 246, 227)]
accents = [c(181, 137, 0), c(203, 75, 22), c(220, 50, 47), c(211, 54, 130), c(108, 113, 196),
           c(38, 139, 210), c(42, 161, 152), c(133, 153, 0)]


color_themes = OrderedDict([('solarized_dk', {
    'name': 'Solarized dark',
    'hsv': [sol[3].hueF(), sol[3].saturationF(), sol[3].valueF()],
    'build': 'solarized_dk'
}), ('solarized_lt', {
    'name': 'Solarized light',
    'hsv': [sol[4].hueF(), sol[4].saturationF(), sol[4].valueF()],
    'build': 'solarized_lt',
}), ('random', {
    'name': 'Random for each treeset',
    'build': 'random',
}), ('print', {
    'name': 'Print-friendly',
    'build': 'fixed',
    'contrast': 72,
    'hsv': [0.2, 0.2, 0.2],
}), ('bw', {
    'name': 'Black and white',
    'build': 'fixed',
    'contrast': 100,
    'bw': True
}), ('random-light', {
    'name': 'Random on a light background',
    'build': 'random',
    'lu_max': 50
}), ('random-dark', {
    'name': 'Against a dark background',
    'build': 'random',
    'lu_min': 55
}), ('gray', {
    'name': 'Sketch',
    'build': 'fixed',
    'contrast': 50,
    'hsv': [0, 0, 0.3],
    'faded': True,
}), ('dk_gray', {
    'name': 'Sketch dark',
    'build': 'fixed',
    'contrast': 50,
    'hsv': [0, 0, 0.7],
    'faded': True,
}), ])


def adjust_lightness(color, amount):
    r, g, b, a = color.getRgbF()
    hu, s, l = rgb_to_husl(r, g, b)
    l += amount
    c = QColor()
    r, g, b = husl_to_rgb(hu, s, l)
    c.setRgbF(min(r, 1), min(g, 1), min(b, 1))
    return c


def shady(color, alpha):
    c = QColor(color)
    c.setAlphaF(alpha)
    return c


class PaletteManager:
    """ Provides detailed access to current active palette and means to create and choose
        palettes.

        ForestSettings or single elements map their color definitions to keys in palette.

        When a palette is saved, its QColors should be turned to HSV+A tuples.
     """

    def __init__(self):
        # Current theme
        self.theme_key = ''
        self.hsv = [0.00, 0.29, 0.35]  # dark rose
        self.d = OrderedDict()
        self.d['white'] = c(255, 255, 255)
        self.d['black'] = c(0, 0, 0)
        self.custom_colors = ['custom%s' % i for i in range(0, 10)]
        self._ui_palette = None
        self._palette = None
        self._accent_palettes = {}
        self.current_hex = ''
        self.transparent = Qt.transparent
        self.gradient = QtGui.QRadialGradient(0, 0, 300)
        self.gradient.setSpread(QtGui.QGradient.PadSpread)
        self.custom = False
        self.color_keys = ['content1', 'content2', 'content3', 'background1', 'background2',
                           'accent1', 'accent2', 'accent3', 'accent4', 'accent5', 'accent6',
                           'accent7', 'accent8', 'accent1tr', 'accent2tr', 'accent3tr', 'accent4tr',
                           'accent5tr', 'accent6tr', 'accent7tr', 'accent8tr']

        # Theme management
        self.default_themes = color_themes
        self.custom_themes = OrderedDict()

        # Create some defaults
        self.activate_color_theme('solarized_lt', try_to_remember=False)

    def list_available_themes(self):
        l = [(key, data['name']) for key, data in self.default_themes.items()]
        ll = [(key, data['name']) for key, data in self.custom_themes.items()]
        return l + ll

    def update_color_themes(self):
        self.ordered_color_themes = color_themes
        self.ordered_color_themes.update(OrderedDict(sorted(prefs.user_palettes.items())))
        ctrl.call_watchers(self, 'color_themes_changed')

    def create_theme_from_color(self, hex_key, hsv):
        prefs.user_palettes[hex_key] = {
            'name': self.get_color_name(hsv),
            'fixed': True,
            'hsv': hsv,
            'custom': True
        }
        self.custom = True
        self.update_color_themes()
        return hex_key

    def create_custom_theme_from_modification(self):
        pass

    def remove_current_palette(self):
        pass

    def create_theme_from_current_color(self):
        key = self.create_theme_from_color(self.current_hex, self.hsv)
        return key

    def activate_color_theme(self, theme_key, try_to_remember=True):
        """ Prepare root color (self.hsv), depending on what kind of color settings are active
        :param theme_key:
        :param try_to_remember: bool -- try to restore the previous base color, effective only
        for randomising palettes.
        """

        self.theme_key = theme_key
        if theme_key in self.default_themes:
            data = self.default_themes[theme_key]
        elif theme_key in self.custom_themes:
            data = self.custom_themes[theme_key]
        else:
            self.theme_key = 'solarized_lt'
            data = self.default_themes[self.theme_key]
            log.error(f'Unable to find color theme "{theme_key}"')

        self.hsv = data.get('hsv', [0.00, 0.29, 0.35])  # dark rose)
        contrast = data.get('contrast', 55)
        faded = data.get('faded', False)
        bw = data.get('bw', False)

        build = data.get('build', '')
        if build == 'solarized_lt':
            self.build_solarized(light=True)
            return
        elif build == 'solarized_dk':
            self.build_solarized(light=False)
            return
        elif build == 'random':
            found = False
            if try_to_remember:
                remembered = ctrl.settings.get('last_key_colors') # found from forest's settings
                if theme_key in remembered:
                    self.hsv = list(remembered[theme_key])
                    found = True
            if not found:
                lu_min = data.get('lu_min', 25)
                lu = 101
                lu_max = data.get('lu_max', 95)
                while not (lu_min < lu < lu_max):
                    r = random.random()
                    g = random.random()
                    b = random.random()
                    hu, su, lu = rgb_to_husl(r, g, b)
                key_color = c.fromRgbF(r, g, b)
                self.hsv = list(key_color.getHsvF())[:3]
                if ctrl.forest:
                    remembered = ctrl.settings.get('last_key_colors')
                    if remembered:
                        remembered[theme_key] = self.hsv
                    else:
                        remembered = {theme_key: self.hsv}
                    ctrl.settings.set('last_key_colors', remembered, level=FOREST)
        self.compute_palette(self.hsv, contrast=contrast, faded=faded, bw=bw)

    def can_randomise(self):
        data = self.default_themes.get(self.theme_key, None)
        return data and data.get('build', '') == 'random'

    def is_custom(self):
        return self.theme_key in self.custom_themes

    def get(self, key) -> QColor:
        """ Shortcut to palette dictionary (self.d) """
        return self.d.get(key, None)

    def update_colors(self, randomise=False):
        """ Create/get root color and build palette around it
        :param prefs:
        :param settings:
        :param randomise: if color mode allows, generate new base color
        """
        theme_key = ctrl.settings.get('temp_color_theme') or ctrl.settings.get('color_theme')
        self.activate_color_theme(theme_key, try_to_remember=not randomise)
        self.get_qt_palette(cached=False)
        self.get_qt_palette_for_ui(cached=False)
        self.create_accent_palettes()

    def build_solarized(self, light=True):
        """

        :param light:
        """
        if light:
            # Solarized light
            # base3     #fdf6e3 15/7 brwhite  230 #ffffd7 97  00  10 253 246 227  44  10  99
            self.d['background1'] = sol[7]
            # base2     #eee8d5  7/7 white    254 #e4e4e4 92 -00  10 238 232 213  44  11  93
            self.d['background2'] = sol[6]
            # base00    #657b83 11/7 bryellow 241 #626262 50 -07 -07 101 123 131 195  23  51
            self.d['content1'] = sol[3]
            # base1     #93a1a1 14/4 brcyan   245 #8a8a8a 65 -05 -02 147 161 161 180   9  63
            self.d['content2'] = sol[5]
            # base01    #586e75 10/7 brgreen  240 #585858 45 -07 -07  88 110 117 194  25  46
            self.d['content3'] = sol[2]
        else:
            # Solarized dark
            self.d['background1'] = sol[0]
            self.d['background2'] = sol[1]
            self.d['content1'] = sol[4]
            self.d['content2'] = sol[2]
            self.d['content3'] = sol[5]
        for i, accent in enumerate(accents):
            self.d['accent%s' % (i + 1)] = accent
            self.d['accent%str' % (i + 1)] = shady(accent, 0.5)
            self.d['accent%str9' % (i + 1)] = shady(accent, 0.9)
        self.d['background1tr'] = shady(self.d['background1'], 0.7)
        tr = c(self.d['background2'])
        tr.setAlphaF(0.7)
        self.d['background2tr'] = shady(self.d['background2'], 0.7)
        self.gradient.setColorAt(1, self.d['background1'])
        self.gradient.setColorAt(0, self.d['background1'].lighter())

    def compute_palette(self, hsv, contrast=55, bw=False, faded=False):
        """ Create/get root color and build palette around it.
        :param hsv:
        Leaves custom colors as they are. """

        self.hsv = hsv
        # # This is the base color ##
        key = c()
        key.setHsvF(*hsv)
        self.current_hex = key.name()
        r, g, b, a = key.getRgbF()
        h, s, l = rgb_to_husl(r, g, b)
        if l > 50:
            back_l = max(0, l - contrast)
            accent_l = min(l, 62)
        else:
            back_l = min(99, l + contrast)
            accent_l = max(45, l)
        background1 = c()
        bg_rgb = husl_to_rgb(h, s, back_l)
        background1.setRgbF(*bg_rgb)
        self.d['content1'] = key
        self.d['content2'] = adjust_lightness(key, 4)
        self.d['content3'] = adjust_lightness(key, -4)
        for i, accent in enumerate(accents):
            # accent colors have the same luminence as key color
            adjusted_accent = c(accent)
            ar, ag, ab, aa = accent.getRgbF()
            ach, acs, acl = rgb_to_husl(ar, ag, ab)
            # if bw:
            #    acs = 0
            if faded:
                acs /= 2
            ar, ag, ab = husl_to_rgb(ach, acs, accent_l)
            adjusted_accent.setRgbF(ar, ag, max(0, ab))
            self.d['accent%s' % (i + 1)] = adjusted_accent
            self.d['accent%str' % (i + 1)] = shady(adjusted_accent, 0.5)
            self.d['accent%str9' % (i + 1)] = shady(adjusted_accent, 0.9)
        self.d['background1'] = background1
        if l < 0.7:
            background2 = adjust_lightness(background1, -4)
        else:
            background2 = adjust_lightness(background1, 4)
        self.d['background2'] = background2
        self.d['background1tr'] = shady(background1, 0.7)
        self.d['background2tr'] = shady(background2, 0.7)
        # ## Gradient ###
        self.gradient.setColorAt(1, self.d['background1'])
        self.gradient.setColorAt(0, self.d['background1'].lighter())

    def drawing(self) -> QColor:
        """ Main drawing color for constituent branches
        :return: QColor
        """
        return self.d['content1']

    def text(self) -> QColor:
        """ Main text color for constituent nodes
        :return: QColor
        """
        return self.d['content1']

    def paper(self) -> QColor:
        """ Background color
        :return: QColor
        """
        return self.d['background1']

    def paper2(self) -> QColor:
        """ Background color
        :return: QColor
        """
        return self.d['background2']

    def ui(self) -> QColor:
        """ Primary UI text color
        :return: QColor
        """
        return self.d['accent8']

    def ui_tr(self) -> QColor:
        """ Transparent UI color
        :return: QColor
        """
        return self.d['accent8tr']

    def ui_paper(self) -> QColor:
        """ UI background color -- use for UI elements that float over main drawing.
        :return: QColor
        """
        return self.d['accent8tr9']

    def secondary(self) -> QColor:
        """

        :return:
        """
        return self.d['accent2']

    def selection(self) -> QColor:
        """

        :return:
        """
        return self.d['accent3']

    def hover(self) -> QColor:
        """

        :return:
        """
        return self.d['accent3tr']

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
        if self.light_on_dark():
            return color.lighter(160)
        else:
            return color.darker(160)

    def lighter(self, color):
        return color.lighter(110)

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
        return color.lighter(120)

    def selected(self, color):
        """

        :param color:
        :return:
        """
        if self.light_on_dark():
            return color.lighter()
        else:
            return color.darker()

    def broken(self, color):
        """

        :param color:
        :return:
        """
        if self.light_on_dark():
            if isinstance(color, QtGui.QBrush):
                return QtGui.QBrush(color.color().darker())
            else:
                return color.darker()

        else:
            if isinstance(color, QtGui.QBrush):
                return QtGui.QBrush(color.color().lighter())
            else:
                return color.lighter()

    def get_color_name(self, color):
        """ Try to find the closest matching color from a dictionary of color names
        :param color: can be HSV(!) tuple, palette key (str) or QColor
        :return:
        """
        if isinstance(color, (tuple, list)):
            cc = c()
            cc.setHsvF(color[0], color[1], color[2])
        elif isinstance(color, str):
            cc = self.get(color)
        elif isinstance(color, QColor):
            cc = color
        else:
            print('Unknown color: ', color)
        r, g, b, a = cc.getRgb()
        d_min = 100000
        best = 0
        for i, (name, hex, rgb) in enumerate(color_names):
            ir, ig, ib = rgb
            d = (r - ir) * (r - ir) + (g - ig) * (g - ig) + (b - ib) * (b - ib)
            if d < d_min:
                d_min = d
                best = i
        return color_names[best][0]

    def palette_from_key(self, key, ui=False):
        """

        :param key:
        :param ui:
        :return:
        """
        if ui:
            palette = QtGui.QPalette(self.get_qt_palette_for_ui())
        else:
            palette = QtGui.QPalette(self.get_qt_palette())

        palette.setColor(QtGui.QPalette.WindowText, self.d[key])
        palette.setColor(QtGui.QPalette.Text, self.d[key])
        return palette

    def light_on_dark(self):
        """


        :return:
        """
        return self.d['background1'].value() < 100

    def use_glow(self):
        """ In dark backgrounds the glow effect is nice, in light we prefer not.
        :return: boolean
        """
        return prefs.glow_effect and self.light_on_dark()

    def create_accent_palette(self, key):
        base = self.d[key]
        bbase = QtGui.QBrush(base)
        pr, pg, pb, pa = self.paper().getRgb()
        br, bg, bb, ba = base.getRgb()
        base_melded = QtGui.QColor.fromRgb((pr + br) / 2, (pg + bg) / 2, (pb + bb) / 2)
        base_melded.setAlphaF(0.9)
        bb_melded = QtGui.QBrush(base_melded)
        bb_lt = QtGui.QBrush(base_melded.lighter())
        bb_dk = QtGui.QBrush(base_melded.darker())
        paper2 = QtGui.QBrush(self.d['background2'])
        p = {
            'windowText': self.text(),
            'button': self.paper(),
            'light': bb_lt,
            'dark': bb_dk,
            'mid': bbase,
            'text': bbase,
            'bright_text': bb_lt,
            'base': paper2,
            'window': bb_melded
        }
        pal = QtGui.QPalette(p['windowText'], p['button'], p['light'], p['dark'], p['mid'],
                             p['text'], p['bright_text'], p['base'], p['window'])
        pal = self.add_disabled_palette(pal, p)
        self._accent_palettes[key] = pal

    def create_accent_palettes(self):
        self._accent_palettes = {}
        for i in range(1, 9):
            self.create_accent_palette('accent%s' % i)

    def get_accent_palette(self, key):
        if key not in self._accent_palettes:
            self.create_accent_palette(key)
        return self._accent_palettes[key]

    def get_qt_palette(self, cached=True):
        """

        :param cached:
        :return:
        """
        if cached and self._palette:
            return self._palette
        p = {
            'windowText': QtGui.QBrush(self.d['content1']),
            'button': QtGui.QBrush(self.d['background1']),
            'light': QtGui.QBrush(self.d['content3']),
            'dark': QtGui.QBrush(self.d['content2']),
            'mid': QtGui.QBrush(self.hovering(self.d['content1'])),
            'text': QtGui.QBrush(self.d['content1']),
            'bright_text': QtGui.QBrush(self.d['accent8']),
            'base': QtGui.QBrush(self.d['background2']),
            'window': QtGui.QBrush(self.d['background1'])
        }

        self._palette = QtGui.QPalette(p['windowText'], p['button'], p['light'], p['dark'],
                                       p['mid'], p['text'], p['bright_text'], p['base'],
                                       p['window'])

        self._palette = self.add_disabled_palette(self._palette, p)
        return self._palette

    def get_qt_palette_for_ui(self, cached=True):
        """

        :param cached:
        :return:
        """
        if cached and self._ui_palette:
            return self._ui_palette

        p = {
            'windowText': QtGui.QBrush(self.d['accent8']),
            'button': QtGui.QBrush(self.d['background1']),
            'light': QtGui.QBrush(self.d['accent8'].lighter()),
            'dark': QtGui.QBrush(self.d['accent8'].darker()),
            'mid': QtGui.QBrush(self.hovering(self.d['accent8'])),
            'text': QtGui.QBrush(self.d['accent8']),
            'bright_text': QtGui.QBrush(self.d['accent2']),
            'base': QtGui.QBrush(self.d['background2']),
            'window': QtGui.QBrush(self.d['background1'])
        }
        self._ui_palette = QtGui.QPalette(p['windowText'], p['button'], p['light'], p['dark'],
                                          p['mid'], p['text'], p['bright_text'], p['base'],
                                          p['window'])
        self._ui_palette.setColor(QtGui.QPalette.AlternateBase, self.d['background2tr'])
        self._ui_palette = self.add_disabled_palette(self._ui_palette, p)
        return self._ui_palette

    def add_disabled_palette(self, palette, p):

        palette.setColorGroup(QtGui.QPalette.Disabled, self.broken(p['windowText']),
                              self.broken(p['button']), self.broken(p['light']),
                              self.broken(p['dark']), self.broken(p['mid']), self.broken(p['text']),
                              self.broken(p['bright_text']), p['base'], p['window'])
        return palette


# HUSL colors and the code for creating them is from here:
# https://github.com/husl-colors/husl-python
# License for this portion of code:
# Copyright (c) 2015 Alexei Boronine
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

m = [[3.240969941904521, -1.537383177570093, -0.498610760293],
     [-0.96924363628087, 1.87596750150772, 0.041555057407175],
     [0.055630079696993, -0.20397695888897, 1.056971514242878], ]
m_inv = [[0.41239079926595, 0.35758433938387, 0.18048078840183],
         [0.21263900587151, 0.71516867876775, 0.072192315360733],
         [0.019330818715591, 0.11919477979462, 0.95053215224966], ]
refX = 0.95045592705167
refY = 1.0
refZ = 1.089057750759878
refU = 0.19783000664283
refV = 0.46831999493879
kappa = 903.2962962
epsilon = 0.0088564516


# Public API

def husl_to_rgb(h, s, l):
    return lch_to_rgb(*husl_to_lch([h, s, l]))


def rgb_to_husl(r, g, b):
    return lch_to_husl(rgb_to_lch(r, g, b))


def lch_to_rgb(l, c, h):
    return xyz_to_rgb(luv_to_xyz(lch_to_luv([l, c, h])))


def rgb_to_lch(r, g, b):
    return luv_to_lch(xyz_to_luv(rgb_to_xyz([r, g, b])))


def get_bounds(L):
    sub1 = ((L + 16.0) ** 3.0) / 1560896.0
    sub2 = sub1 if sub1 > epsilon else L / kappa
    ret = []
    for [m1, m2, m3] in m:
        for t in [0, 1]:
            top1 = (284517.0 * m1 - 94839.0 * m3) * sub2
            top2 = (838422.0 * m3 + 769860.0 * m2 + 731718.0 * m1) * L * sub2 - 769860.0 * t * L
            bottom = (632260.0 * m3 - 126452.0 * m2) * sub2 + 126452.0 * t
            ret.append((top1 / bottom, top2 / bottom))
    return ret


def intersect_line_line(line1, line2):
    return (line1[1] - line2[1]) / (line2[0] - line1[0])


def length_of_ray_until_intersect(theta, line):
    m1, b1 = line
    length = b1 / (math.sin(theta) - m1 * math.cos(theta))
    if length < 0:
        return None
    return length


def max_chroma_for_LH(L, H):
    hrad = H / 360.0 * math.pi * 2.0
    lengths = []
    for line in get_bounds(L):
        l = length_of_ray_until_intersect(hrad, line)
        if l is not None:
            lengths.append(l)
    return min(lengths)


def dot_product(a, b):
    return sum(map(operator.mul, a, b))


def f(t):
    if t > epsilon:
        return 116 * math.pow((t / refY), 1.0 / 3.0) - 16.0
    else:
        return (t / refY) * kappa


def f_inv(t):
    if t > 8:
        return refY * math.pow((t + 16.0) / 116.0, 3.0)
    else:
        return refY * t / kappa


def from_linear(c):
    if c <= 0.0031308:
        return 12.92 * c
    else:
        return (1.055 * math.pow(c, 1.0 / 2.4) - 0.055)


def to_linear(c):
    a = 0.055

    if c > 0.04045:
        return (math.pow((c + a) / (1.0 + a), 2.4))
    else:
        return (c / 12.92)


def xyz_to_rgb(triple):
    xyz = map(lambda row: dot_product(row, triple), m)
    return list(map(from_linear, xyz))


def rgb_to_xyz(triple):
    rgbl = list(map(to_linear, triple))
    return list(map(lambda row: dot_product(row, rgbl), m_inv))


def xyz_to_luv(triple):
    X, Y, Z = triple

    if X == Y == Z == 0.0:
        return [0.0, 0.0, 0.0]

    varU = (4.0 * X) / (X + (15.0 * Y) + (3.0 * Z))
    varV = (9.0 * Y) / (X + (15.0 * Y) + (3.0 * Z))
    L = f(Y)

    # Black will create a divide-by-zero error
    if L == 0.0:
        return [0.0, 0.0, 0.0]

    U = 13.0 * L * (varU - refU)
    V = 13.0 * L * (varV - refV)

    return [L, U, V]


def luv_to_xyz(triple):
    L, U, V = triple

    if L == 0:
        return [0.0, 0.0, 0.0]

    varY = f_inv(L)
    varU = U / (13.0 * L) + refU
    varV = V / (13.0 * L) + refV
    Y = varY * refY
    X = 0.0 - (9.0 * Y * varU) / ((varU - 4.0) * varV - varU * varV)
    Z = (9.0 * Y - (15.0 * varV * Y) - (varV * X)) / (3.0 * varV)

    return [X, Y, Z]


def luv_to_lch(triple):
    L, U, V = triple

    C = (math.pow(math.pow(U, 2) + math.pow(V, 2), (1.0 / 2.0)))
    hrad = (math.atan2(V, U))
    H = math.degrees(hrad)
    if H < 0.0:
        H = 360.0 + H

    return [L, C, H]


def lch_to_luv(triple):
    L, C, H = triple

    Hrad = math.radians(H)
    U = (math.cos(Hrad) * C)
    V = (math.sin(Hrad) * C)

    return [L, U, V]


def husl_to_lch(triple):
    H, S, L = triple

    if L > 99.9999999:
        return [100, 0.0, H]
    if L < 0.00000001:
        return [0.0, 0.0, H]

    mx = max_chroma_for_LH(L, H)
    C = mx / 100.0 * S

    return [L, C, H]


def lch_to_husl(triple):
    L, C, H = triple

    if L > 99.9999999:
        return [H, 0.0, 100.0]
    if L < 0.00000001:
        return [H, 0.0, 0.0]

    mx = max_chroma_for_LH(L, H)
    S = C / mx * 100.0

    return [H, S, L]
