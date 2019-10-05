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

from kataja.visualizations.AsymmetricElasticTree import AsymmetricElasticTree
from kataja.visualizations.BalancedTree import BalancedTree
from kataja.visualizations.BracketedLinearization import BracketedLinearization
from kataja.visualizations.DivideAndConquerTree import DivideAndConquerTree
from kataja.visualizations.EquidistantElasticTree import EquidistantElasticTree
from kataja.visualizations.GridlessDivideAndConquerTree import GridlessDivideAndConquerTree
from kataja.visualizations.HeadDownTree import HeadDownTree
from kataja.visualizations.LeftFirstTree import LeftFirstTree
from kataja.visualizations.LinearizedDynamicTree import LinearizedDynamicTree
from kataja.visualizations.SpirallingTree import SpirallingTree
from kataja.visualizations.SymmetricElasticTree import SymmetricElasticTree

# These will be mapped to number keys 1...0,+ in given order.

visualizations_list = [GridlessDivideAndConquerTree,
                       DivideAndConquerTree,
                       BalancedTree,
                       HeadDownTree,
                       LeftFirstTree,
                       BracketedLinearization,
                       LinearizedDynamicTree,
                       AsymmetricElasticTree,
                       SymmetricElasticTree,
                       EquidistantElasticTree,
                       SpirallingTree]

VISUALIZATIONS = OrderedDict()

shortcut = 1
for vclass in visualizations_list:
    if shortcut == 10:
        shortcut_char = '0'
    elif shortcut == 11:
        shortcut_char = '+'
    elif shortcut > 11:
        shortcut_char = ''
    else:
        shortcut_char = str(shortcut)
    vis = vclass()
    vis.shortcut = shortcut_char
    VISUALIZATIONS[vclass.name] = vis
    shortcut += 1
