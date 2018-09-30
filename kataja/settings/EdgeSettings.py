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

from collections import ChainMap

class EdgeSettings:
    def __init__(self, edge: 'kataja.saved.Edge'):
        self.edge = edge
        self.flat_dict = {}

    def flatten(self):
        self.flat_dict = ChainMap(self.data,
                                  *self.edge.forest.settings.flat_edge_dict[self.edge.edge_type].maps,
                                  *self.edge.forest.settings.flat_shape_dict[self.edge.shape_name].maps)

    @property
    def data(self):
        return self.edge._settings

    def get(self, key):
        v = self.data.get(key, None)
        if v is None:
            return self.edge.forest.settings.get_for_edge_type(key, self.edge.edge_type)

    def get_shape(self, key):
        v = self.data.get(key, None)
        if v is None:
            return self.edge.forest.settings.get_for_edge_shape(key, self.edge.shape_name)

    def set(self, key, value):
        self.edge.poke('_settings')
        self.data[key] = value

    def delete(self, key):
        if key in self.data:
            self.edge.poke('_settings')
            del self.data[key]
