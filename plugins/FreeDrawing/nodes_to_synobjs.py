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
from kataja.parser.INodes import as_text, extract_triangle


def figure_out_syntactic_label(cn):
    if cn.triangle_stack:
        # as_text -function puts triangle symbol before triangle content, [1:] removes it.
        return as_text(extract_triangle(cn.label), omit_index=True)[1:]
    l = as_text(cn.label, omit_index=True)
    if l:
        return l.splitlines()[0]
    else:
        return ''


# @time_me
def nodes_to_synobjs(forest, syntax, roots: list):
    """ Rebuild syntactic objects based on information in nodes. Understand that this means that
    syntactic objects cannot have data directly set to them -- it will be overwritten or ignored
    by this operation.

    This is called after every tree-changing operation in free drawing -mode

    :param forest:
    :param syntax:
    :param roots:
    :return:
    """

    # print('*********************************')
    # print('**** Nodes to synobjs called ****')
    # print('*********************************')

    if roots is None:
        roots = []

    visited_nodes = set()
    converted_nodes = set()
    checking_features = set()

    def define_label(node):
        n = len(node.heads)
        if n == 0:
            return ''
        elif n == 1:
            return figure_out_syntactic_label(node.heads[0])
        else:
            l = []
            for head in node.heads:
                l.append(figure_out_syntactic_label(head))
            joined = ', '.join(l)
            return f'({joined})'

    def convert_node(node):
        if node in visited_nodes or node in converted_nodes:
            return
        visited_nodes.add(node)
        if node.node_type == g.CONSTITUENT_NODE:
            if node.index and node.is_trace:
                head, traces = forest.get_nodes_by_index(node.index)
                if head not in converted_nodes:
                    convert_node(head)
                node.syntactic_object = head.syntactic_object
                converted_nodes.add(node)
                return
            children = node.get_children(visible=False, similar=True)
            feature_nodes = node.get_children(visible=False, similar=False, of_type=g.FEATURE_EDGE)
            features = []
            for fnode in feature_nodes:
                if fnode.node_type != g.FEATURE_NODE:
                    continue
                if fnode in converted_nodes:
                    features.append(fnode.syntactic_object)
                else:
                    if fnode.syntactic_object:
                        fobj = fnode.syntactic_object
                        fobj.name = fnode.name
                        fobj.value = fnode.value
                        fobj.family = fnode.family
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
                n1, n2 = children
                synobj = syntax.merge(n1.syntactic_object, n2.syntactic_object,
                                      c=node.syntactic_object)
                synobj.label = define_label(node)
                node.is_syntactically_valid = True
                node.set_syntactic_object(synobj)
                if features:
                    node.is_syntactically_valid = False
                    synobj.features += features
                else:
                    node.is_syntactically_valid = True
            elif len(children) == 1:
                n1 = children[0]
                convert_node(n1)
                synobj = node.syntactic_object
                if not synobj:
                    synobj = syntax.create_constituent(label='')
                synobj.parts = [n1.syntactic_object]
                synobj.label = define_label(node)
                node.is_syntactically_valid = False
                node.set_syntactic_object(synobj)
                if features:
                    synobj.features += features
            elif len(children) == 0:
                label = define_label(node)
                synobj = node.syntactic_object
                if not synobj:
                    synobj = syntax.create_constituent(label=label)
                node.set_syntactic_object(synobj)
                node.is_syntactically_valid = True
                synobj.features = features
            else:
                for child in children:
                    convert_node(child)
                label = define_label(node)
                synobj = node.syntactic_object
                if not synobj:
                    synobj = syntax.create_constituent(label=label)
                synobj.parts = [x.syntactic_object for x in children]
                node.set_syntactic_object(synobj)
                node.is_syntactically_valid = False
                synobj.features = features
            converted_nodes.add(node)

    for root in roots:
        convert_node(root)
        for checker, checked in checking_features:
            checker.syntactic_object.checks = checked.syntactic_object

    print('visited %s nodes, converted %s nodes to synobjs' % (
        len(visited_nodes), len(converted_nodes)))
