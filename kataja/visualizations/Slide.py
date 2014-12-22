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

from kataja.visualizations.BaseVisualization import BaseVisualization


class Slide(BaseVisualization):
    """

    """
    name = 'Presentation'

    def __init__(self):
        BaseVisualization.__init__(self)
        self.forest = None
        self._directed = False


    def prepare(self, forest, reset=True):
        """ If loading a state, don't reset.
        :param forest:Forest
        :param reset:boolean
        """
        self.forest = forest

    def draw(self):
        """


        """
        pass
        # if not ctrl.slide.scene():
        # ctrl.scene.addItem(ctrl.slide)
        #    ctrl.slide.show()
        # ctrl.slide.setPos(0,0)
