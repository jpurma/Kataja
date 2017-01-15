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



import kataja.globals as g
from kataja.singletons import ctrl
from kataja.utils import time_me


@time_me
def nodes_to_synobjs(forest, syntax, roots: list):


    visited_nodes = set()
    converted_nodes = set()
    checking_features = set()

    def convert_node(node):
        if node in visited_nodes or node in converted_nodes:
            return
        visited_nodes.add(node)
        if node.node_type == g.CONSTITUENT_NODE:
            children = node.get_children(visible=False, similar=True)
            feature_nodes = node.get_children(visible=False, similar=False, of_type=g.FEATURE_EDGE)
            features = []
            for fnode in feature_nodes:
                if fnode in converted_nodes:
                    features.append(fnode.syntactic_object)
                else:
                    fobj = syntax.create_feature(name=fnode.name, value=fnode.value,
                                                 family=fnode.family)
                    features.append(fobj)
                    converted_nodes.add(fnode)
                    fnode.set_syntactic_object(fobj)
                    for checked in fnode.get_children(visible=False, similar=True):
                        checking_features.add((fnode, checked))
            if len(children) == 2:
                for child in children:
                    convert_node(child)
                synobj = syntax.merge(*children)
                node.is_syntactically_valid = True
                node.set_syntactic_object(synobj)
                if features:
                    node.is_syntactically_valid = False
                    synobj.features += features
                else:
                    node.is_syntactically_valid = True
            else:
                for child in children:
                    convert_node(child)
                synobj = syntax.create_constituent(label=node.label)
                node.set_syntactic_object(synobj)
                if not children:
                    node.is_syntactically_valid = True
                else:
                    node.is_syntactically_valid = False
                synobj.features = features
            converted_nodes.add(node)

    for root in roots:
        convert_node(root)
        for checker, checked in checking_features:
            checker.syntactic_object.checks = checked.syntactic_object
