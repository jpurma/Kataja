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


class NodeSettings:

    def __init__(self, node: 'kataja.saved.movables.Node'):
        self.node = node

    @property
    def data(self):
        return self.node._settings

    def get(self, key):
        v = self.data.get(key, None)
        if v is None:
            return self.node.forest.settings.get_for_node_type(key, self.node.node_type)

    def set(self, key, value):
        self.node.poke('_settings')
        self.data[key] = value

    def delete(self, key):
        if key in self.data:
            self.node.poke('_settings')
            del self.data[key]
