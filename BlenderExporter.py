#!/usr/bin/env python
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


import PyQt5.QtCore as QtCore, PyQt5.QtGui as QtGui
from PyQt5.QtCore import QPointF as Pf, QPoint as P, Qt
from .kataja.ConstituentNode import ConstituentNode
from .kataja.Controller import colors
import collections, json

def export_visible_items(path = 'tempdata.json', scene = None, forest = None, prefs = None):
    """

    :param path:
    :param scene:
    :param forest:
    :param prefs:
    :return:
    """
    data = collections.OrderedDict()
    for n, node in enumerate(scene.visible_nodes()):
        nobj = collections.OrderedDict([('Type', 'ConstituentNode'),
        ('location', node.current_position),
        ('label', node.cosmetic_label or node.constituent.label),
        ('alias', node.cosmetic_label),
        ('parents', [ x.key for x in node.get_parents()]),
        ('children', [x.key for x in node.get_children()]),
        ('edges', [x.key for x in node.relations_down])
        ])
        data[node.key] = nobj
    data['Preferences'] = {
    'Type' : 'Preferences',
    'color' : colors.drawing.getRgbF()[ :3],
    'text_color' : colors.text.getRgbF()[ :3],
    'background' : colors.paper.getRgbF()[ :3],
    'background_lighter' : colors.paper.lighter().getRgbF()[ :3]
    }
    print('exporting to ', path)
    f = open(path, 'w')
    f.write(json.dumps(data, indent = 4))
    f.close()
    return path

