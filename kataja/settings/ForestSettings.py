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

from kataja.Shapes import SHAPE_PRESETS
from kataja.singletons import ctrl
from kataja.edge_styles import master_styles


class ForestSettings:

    def __init__(self, forest):
        self.host = forest
        self.next = ctrl.document.settings if ctrl.document else None
        self.flat_edge_dict = {}
        self.flat_shape_dict = {}

    def flatten(self):
        for edge_type in master_styles['fancy'].keys():
            d = self.data.get('edge_types', {}).get(edge_type, {})
            next_map = self.next.flat_edge_dict[edge_type]
            if isinstance(next_map, ChainMap):
                self.flat_edge_dict[edge_type] = next_map.new_child(d)
            else:
                self.flat_edge_dict[edge_type] = ChainMap(d, next_map)
        for shape_name in SHAPE_PRESETS.keys():
            d = self.data.get('edge_shapes', {}).get(shape_name, {})
            next_map = self.next.flat_shape_dict[shape_name]
            if isinstance(next_map, ChainMap):
                self.flat_shape_dict[shape_name] = next_map.new_child(d)
            else:
                self.flat_shape_dict[shape_name] = ChainMap(d, next_map)

    @property
    def data(self):
        return self.host._settings

    def get(self, key):
        v = self.data.get(key, None)
        if v is None:
            return self.next.get(key)

    def _get_in(self, key, subtype, subtype_container):
        sc = self.data.get(subtype_container, None)
        if sc:
            st = sc.get(subtype, None)
            if st:
                v = st.get(key, None)
                if v:
                    return v

    def get_for_node_type(self, key, node_type):
        v = self._get_in(key, node_type, 'node_types')
        if v is not None:
            return v
        return self.next.get_for_node_type(key, node_type)

    def get_for_edge_type(self, key, edge_type):
        v = self._get_in(key, edge_type, 'edge_types')
        if v is not None:
            return v
        return self.next.get_for_edge_type(key, edge_type)

    def get_for_edge_shape(self, key, edge_shape):
        v = self._get_in(key, edge_shape, 'edge_shapes')
        if v is not None:
            return v
        return self.next.get_for_edge_shape(key, edge_shape)

    def set(self, key, value):
        self.host.poke('_settings')
        self.data[key] = value

    def _set_in(self, key, value, subtype, subtype_container):
        self.host.poke('_settings')
        if subtype_container not in self.data:
            self.data[subtype_container] = {subtype: {key: value}}
        else:
            sc = self.data[subtype_container]
            if subtype not in sc:
                sc[subtype] = {key: value}
            else:
                sc[subtype][key] = value

    def set_for_node_type(self, key, value, node_type):
        self._set_in(key, value, node_type, 'node_types')

    def set_for_edge_type(self, key, value, edge_type):
        self._set_in(key, value, edge_type, 'edge_types')

    def set_for_edge_shape(self, key, value, edge_shape):
        self._set_in(key, value, edge_shape, 'edge_shapes')

    def delete(self, key):
        if key in self.data:
            self.host.poke('_settings')
            del self.data[key]

    def _del_in(self, key, subtype, subtype_container):
        self.host.poke('_settings')
        if subtype_container in self.data:
            sc = self.data[subtype_container]
            if subtype in sc and key in sc[subtype]:
                del sc[subtype][key]
                if not sc[subtype]:
                    del sc[subtype]

    def del_for_node_type(self, key, node_type):
        self._del_in(key, node_type, 'node_types')

    def del_for_edge_type(self, key, edge_type):
        self._del_in(key, edge_type, 'edge_types')

    def del_for_edge_shape(self, key, edge_shape):
        self._del_in(key, edge_shape, 'edge_shapes')
