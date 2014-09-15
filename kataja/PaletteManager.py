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

import random
import json
from collections import OrderedDict

from PyQt5.QtGui import QColor as c
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt
import PyQt5.QtGui as QtGui

from kataja.singletons import ctrl, prefs


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

sol = [c(0, 43, 54), c(7, 54, 66), c(88, 110, 117), c(101, 123, 131), c(131, 148, 150), c(147, 161, 161),
       c(238, 232, 213), c(253, 246, 227)]
accents = [c(181, 137, 0), c(203, 75, 22), c(220, 50, 47), c(211, 54, 130), c(108, 113, 196), c(38, 139, 210),
           c(42, 161, 152), c(133, 153, 0)]


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


def matching_hue(hue, color_list):
    min_d = 1.0
    best = 0
    optimal = 0.39166
    for i, color in enumerate(color_list):
        hueF = color.hsvHueF()
        if hue < optimal:
            hue += 1
        d = abs(optimal - (hue - hueF))
        if d < min_d:
            min_d = d
            best = i
    return best




def in_range(h, s, v):
    """

    :param h:
    :param s:
    :param v:
    :raise:
    """
    if h < 0:
        print("Hue not in range: " + h)
        h = 0
    if s < 0:
        print("Saturation not in range: " + s)
        s = 0
    if v < 0:
        print("Value (lightness) not in range: " + v)
        v = 0
    if h > 1:
        print("Hue not in range: " + h)
        h = 1
    if s > 1:
        print("Saturation not in range: " + s)
        s = 1
    if v > 1:
        print("Value (lightness) not in range: " + v)
        v = 1
    return h, s, v


class PaletteManager:
    """ Selects, creates and gives access to various palettes. The current palette is available in dict d with keys for default names and
        possibility to expand with custom colors. Includes methods for creating new palettes.

    ForestSettings or single elements map their color definitions to keys in palette.

    When a palette is saved, its QColors should be turned to HSV+A tuples. 
     """

    def __init__(self, hsv_key=None):
        print("*** Creating PaletteManager")
        try:
            f = open(prefs.resources_path + 'colors.json', 'r', encoding='UTF-8')
            self.color_map = json.load(f) # json.load(f, 'utf-8')

            f.close()
        except FileNotFoundError:
            self.color_map = {}

        if not hsv_key:
            hsv_key = (0.00, 0.29, 0.35)  # dark rose
        self.hsv = hsv_key
        self.d = OrderedDict()
        self.d['white'] = c(255, 255, 255)
        self.d['black'] = c(0, 0, 0)
        self.custom_colors = []
        self.transparent = Qt.transparent
        self.gradient = QtGui.QRadialGradient(0, 0, 300)
        self.gradient.setSpread(QtGui.QGradient.PadSpread)
        self.activate_color_mode('solarized_lt', cold_start=True)

    def current_color_mode(self, value=None):
        """

        :param value:
        :return:
        """
        return ctrl.fs.color_mode(value)

    def activate_color_mode(self, mode, refresh=False, cold_start=False):
        """
        Prepare root color (self.hsv), depending on what kind of color settings are active

        :param refresh:
        :param cold_start: bool -- use this if some color palette is required, but ctrl-infrastructure
            is not yet available
        """
        print('Activating color mode ', mode)
        store_last_hsv = True

        if mode == 'solarized_lt':
            base = sol[3]
            self.hsv = base.hueF(), base.saturationF(), base.valueF()
            self.build_solarized(light=True)
        elif mode == 'solarized_dk':
            base = sol[4]
            self.hsv = base.hueF(), base.saturationF(), base.valueF()
            self.build_solarized(light=False)
        elif mode == 'random':
            if not cold_start:
                remembered_value = ctrl.fs.last_key_color_for_mode(mode)
                if remembered_value and not refresh:
                    print('Using remembered value ', self.hsv, ' for color mode ', mode)
                    self.hsv = remembered_value
                    self.compute_palette(self.hsv)
                    return

            h = random.random()
            s = random.random()  # *0.2+0.8
            value_low_limit = int(0.38 * 255)
            value_high_limit = int(0.7 * 255)
            v = random.randint(value_low_limit, value_high_limit) / 255.0  # *0.2+0.8
            self.hsv = h, s, v
            self.compute_palette(self.hsv)

        elif mode == 'random-light':
            if not cold_start:
                remembered_value = ctrl.fs.last_key_color_for_mode(mode)
                if remembered_value and not refresh:
                    print('Using remembered value ', self.hsv, ' for color mode ', mode)
                    self.hsv = remembered_value
                    self.compute_palette(self.hsv)
                    return
            h = random.random()
            s = random.random()  # *0.2+0.8
            value_low_limit = int(0.12 * 255)
            value_high_limit = int(0.5 * 255)
            v = random.randint(value_low_limit, value_high_limit) / 255.0  # *0.2+0.8
            self.hsv = h, s, v
            self.compute_palette(self.hsv)

        elif mode == 'random-dark':
            if not cold_start:
                remembered_value = ctrl.fs.last_key_color_for_mode(mode)
                if remembered_value and not refresh:
                    print('Using remembered value ', self.hsv, ' for color mode ', mode)
                    self.hsv = remembered_value
                    self.compute_palette(self.hsv)
                    return
            h = random.random()
            s = random.random()  # *0.2+0.8
            value_low_limit = int(0.6 * 255)
            value_high_limit = int(0.8 * 255)
            v = random.randint(value_low_limit, value_high_limit) / 255.0  # *0.2+0.8
            self.hsv = h, s, v
            self.compute_palette(self.hsv)

        else:
            self.hsv = self.get_color_mode_data(mode)['hsv']
            self.compute_palette(self.hsv)
            store_last_hsv = False

        if store_last_hsv and not cold_start:
            ctrl.fs.last_key_color_for_mode(mode, self.hsv)


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
        self.activate_color_mode(self.current_color_mode(), refresh=refresh)


    def build_solarized(self, light=True):
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
        self.d['key'] = self.d['content1']
        self.d['accents'] = accents

        for i, accent in enumerate(accents):
            self.d['accent%s' % (i+1)] = accent
            tr = c(accent)
            tr.setAlphaF(0.5)
            tr9 = c(accent)
            tr9.setAlphaF(0.9)
            self.d['accent%str' % (i+1)] = tr
            self.d['accent%str9' % (i+1)] = tr9
        self.d['accents'] = accents

        self.gradient.setColorAt(1, self.d['background1'])
        self.gradient.setColorAt(0, self.d['background2'])



    def compute_palette(self, hsv):
        """ Create/get root color and build palette around it. 
        :param hsv:
        Leaves custom colors as they are. """
        self.hsv = hsv
        h, s, v = hsv
        # # This is the base color ##
        key = c()
        h, s, v = in_range(h, s, v)
        key.setHsvF(h, s, v)
        light_bg = v < 0.5 or (s > 0.7 and 0.62 < h < 0.95)
        self.d['key'] = key
        self.d['content1'] = key
        content2 = key.lighter(107)
        content3 = key.darker(107)
        self.d['content2'] = content2
        self.d['content3'] = content3
        self.d['accents'] = accents
        start_index = matching_hue(h, accents)
        rotated_accents = accents[start_index:] + accents[:start_index]
        for i, accent in enumerate(rotated_accents):
            self.d['accent%s' % (i+1)] = accent
            tr = c(accent)
            tr.setAlphaF(0.5)
            tr9 = c(accent)
            tr9.setAlphaF(0.9)
            self.d['accent%str' % (i+1)] = tr
            self.d['accent%str9' % (i+1)] = tr9
        self.d['accents'] = rotated_accents

        background1 = c()
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
        hp, sp, vp = in_range(hp, sp, vp)
        background1.setHsvF(hp, sp, vp)
        self.d['background1'] = background1
        if vp < 0.7:
            self.d['background2'] = background1.darker(107)
        else:
            self.d['background2'] = background1.lighter(107)

            # ## Gradient ###
        self.gradient.setColorAt(1, self.d['background1'])
        self.gradient.setColorAt(0, self.d['background2'])

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
        return self.d['accent1']

    def ui_paper(self) -> QColor:
        """ UI background color -- use for UI elements that float over main drawing.
        :return: QColor
        """
        return self.d['accent1tr9']

    def secondary(self) -> QColor:
        """


        :return:
        """
        return self.d['accent2']

    def selection(self):
        """


        :return:
        """
        return self.d['accent3']

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
        if self.light_on_dark():
            return color.lighter(120)
        else:
            return color.darker(120)
        #if color.value() > 230:
        #    return color.darker(120)
        #else:
        #    return color.lighter(120)


    def selected(self, color):
        """

        :param color:
        :return:
        """
        if self.light_on_dark():
            return color.lighter()
        else:
            return color.darker()

    def get_color_name(self, hsv):
        """

        :param hsv:
        :return:
        """
        if not self.color_map:
            return ''
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

    def light_on_dark(self):
        return self.d['background1'].value() < 100

    def use_glow(self):
        """ In dark backgrounds the glow effect is nice, in light we prefer not.
        :return: boolean
        """
        return self.light_on_dark()

    def get_qt_palette(self):
        """


        :return:
        """
        p = {'windowText': QtGui.QBrush(self.d['content1']), 'button': QtGui.QBrush(self.d['background1']),
             'light': QtGui.QBrush(self.d['content3']), 'dark': QtGui.QBrush(self.d['content2']),
             'mid': QtGui.QBrush(self.hovering(self.d['content1'])), 'text': QtGui.QBrush(self.d['content1']),
             'bright_text': QtGui.QBrush(self.d['accent1']), 'base': QtGui.QBrush(self.d['background2']),
             'window': QtGui.QBrush(self.d['background1'])}

        # p = {'windowText': QtGui.QBrush(self.d['key']), 'button': QtGui.QBrush(self.paper()),
        #      'light': QtGui.QBrush(self.active(self.d['complement'])), 'dark': QtGui.QBrush(self.d['complement 0.7']),
        #      'mid': QtGui.QBrush(self.hovering(self.d['complement'])), 'text': QtGui.QBrush(self.d['secondary']),
        #      'bright_text': QtGui.QBrush(self.d['secondary'].lighter()), 'base': QtGui.QBrush(self.paper2()),
        #      'window': QtGui.QBrush(self.paper())}

        return QtGui.QPalette(p['windowText'], p['button'], p['light'], p['dark'], p['mid'], p['text'],
                              p['bright_text'], p['base'], p['window'])



   # def compute_palette(self, hsv):
   #      """ Create/get root color and build palette around it.
   #      :param hsv:
   #      Leaves custom colors as they are. """
   #      self.hsv = hsv
   #      h, s, v = hsv
   #      # # This is the base color ##
   #      key = c()
   #      # in_range(h, s, v)
   #      key.setHsvF(h, s, v)
   #      light_bg = v < 0.5 or (s > 0.7 and 0.62 < h < 0.95)
   #      self.d['key'] = key
   #      key05 = c(key)
   #      key05.setAlphaF(0.5)
   #      self.d['key 0.5'] = key05
   #      key07 = c(key)
   #      key07.setAlphaF(0.7)
   #      self.d['key 0.7'] = key07
   #
   #      analog1 = c()
   #      h1, s1, v1 = colorize(rotating_add(h, -0.1), s, v)
   #      # in_range(h1, s1, v1)
   #      analog1.setHsvF(h1, s1, v1)
   #      self.d['analog1'] = analog1
   #
   #      analog2 = c()
   #      h2, s2, v2 = colorize(rotating_add(h, 0.1), s, v)
   #      # in_range(h2, s2, v2)
   #      analog2.setHsvF(h2, s2, v2)
   #      self.d['analog2'] = analog2
   #
   #      paper = c()
   #      hp = h  # -0.1
   #      sp = s / 4
   #      vp = (1 - v)
   #      if light_bg and vp < 0.6:
   #          vp += 0.3
   #      if abs(v - vp) <= 0.35:
   #          if light_bg:
   #              vp = limited_add(vp, 0.35)
   #          else:
   #              vp = limited_add(vp, -0.35)
   #      # in_range(hp, sp, vp)
   #      paper.setHsvF(hp, sp, vp)
   #      self.d['paper'] = paper
   #      paper08 = c(paper)
   #      paper08.setAlphaF(0.8)
   #      self.d['paper 0.8'] = paper08
   #      self.d['paper lighter'] = paper.lighter()
   #      if vp < 0.7:
   #          self.d['paper2'] = paper.darker(107)
   #      else:
   #          self.d['paper2'] = paper.lighter(107)
   #
   #      complement = c()
   #      hc = rotating_add(h, -0.5)
   #      sv = s
   #      if sv < 0.5:
   #          sv += 0.2
   #      # in_range(hc, sv, v)
   #      complement.setHsvF(hc, sv, v)
   #      self.d['complement'] = complement
   #      complement05 = c(complement)
   #      complement05.setAlphaF(0.5)
   #      self.d['complement 0.5'] = complement05
   #      complement07 = c(complement)
   #      complement07.setAlphaF(0.7)
   #      self.d['complement 0.7'] = complement07
   #
   #      secondary = c()
   #      secondary.setHsvF(abs(h - 0.2), s / 2, limited_add(v, 0.2))
   #      self.d['secondary'] = secondary
   #
   #      # ## Set of marker colors available for features ###
   #      if s < 0.5:
   #          ps = s + 0.4
   #      else:
   #          ps = s
   #      if v < 0.5:
   #          pv = v + 0.4
   #      else:
   #          pv = v
   #      for i in range(0, 10):
   #          self.d['rainbow_%s' % (i + 1)] = c().fromHsvF(i / 10.0, ps, pv)
   #
   #          # ## Gradient ###
   #      self.gradient.setColorAt(1, self.d['paper'])
   #      self.gradient.setColorAt(0, self.d['paper'].lighter())
