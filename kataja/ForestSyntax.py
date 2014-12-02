from kataja.ConstituentNode import ConstituentNode
from kataja.FeatureNode import FeatureNode
from kataja.debug import syntax
import kataja.globals as g
from kataja.singletons import ctrl

__author__ = 'purma'

class ForestSyntaxError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


#class ForestUG:
""" Class of staticmethods that work as an interface to syntactic objects.
All changes to syntactic objects need to use methods offered here  -- the purpose is to help debugging
and to avoid overlapping changes to UG.
"""

def connect_edge(edge):
    """ A special case where a stub edge (edge where other end is not connected anywhere) gets connected.
    For this to have a syntactic reflection edge types and end point types must match, and other conditions
    also need to apply.

    The edge instance already presents the intended connection: this method makes sure that a similar connection
    exists in syntax.

    CALL ONLY IF THE EDGE AND THE NODES ALREADY EXIST

    :param edge: edge where the other end is free.
    :return:
    """
    etype = edge.edge_type
    if etype is g.ARROW:
        # Arrows don't exist in syntax
        return
    if not (edge.start and edge.end):
        raise ForestSyntaxError("Cannot make a connection based on edge, is the other end of edge is empty: %s" % edge)

    if etype is g.CONSTITUENT_EDGE:
        if isinstance(edge.start, ConstituentNode) and isinstance(edge.end, ConstituentNode):
            constituent_start = edge.start.syntactic_object
            constituent_end = edge.end.syntactic_object
            if not constituent_start:
                #Placeholder (empty) constituent cannot have children
                return
            if not constituent_end:
                # setting a placeholder constituent doesn't have a syntactic effect
                return
            left, right = constituent_start.left, constituent_start.right
            if left and right:
                if constituent_end is left:
                    syntax("Set child: This relation already exists: %s .left = %s" % (constituent_start, constituent_end))
                    return
                elif constituent_end is right:
                    syntax("Set child: This relation already exists: %s .right = %s" % (constituent_start, constituent_end))
                    return
                else:
                    raise ForestSyntaxError("Trying to put child node %s, but parent node %s already has two children: (%s, %s)" % (constituent_end, constituent_start, left, right))
            elif left and not right:
                syntax("%s Set right:  %s " % (constituent_start, constituent_end))
                constituent_start.right = constituent_end
            elif right and not left:
                syntax("%s Set left:  %s " % (constituent_start, constituent_end))
                constituent_start.left = constituent_end
            else:
                # Default, but unjustified: connect right child first
                syntax("%s Set right:  %s " % (constituent_start, constituent_end))
                constituent_start.right = constituent_end
        else:
            raise ForestSyntaxError("Cannot make a constituent edge connection if "
                              "one of the ends is not a constituent node")
    elif etype is g.FEATURE_EDGE:
        if isinstance(edge.start, ConstituentNode) and isinstance(edge.end, FeatureNode):
            print('Connecting a feature')
            constituent = edge.start.syntactic_object
            feature = edge.end.syntactic_object
            if not constituent:
                raise ForestSyntaxError("Placeholder (empty) constituent cannot have features")
            if not feature:
                # setting a placeholder feature doesn't have a syntactic effect
                return
            if feature in constituent.features:
                raise ForestSyntaxError("Constituent %s already has feature %s")
            else:
                constituent.set_feature(feature.key, feature)


def disconnect_edge(edge):
    """ Reflect disconnected edge in syntax: Makes sure that items at start and end are not connected anymore by
    constituent, feature or other relation, depicted by the edge.

    CALL THIS BEFORE MODIFYING THE EDGE OBJECT -- IT NEEDS START AND END TO STILL BE IN PLACE

    :param edge: edge instance, where the syntactic disconnection should happen
    :return:
    """
    etype = edge.edge_type
    if etype is g.ARROW:
        # Arrows don't have syntactic role
        return
    if not (edge.start and edge.end):
        # syntactically relationship doesn't exist unless it has both elements
        return
    if etype is g.CONSTITUENT_EDGE:
        if isinstance(edge.start, ConstituentNode) and edge.end:
            # Remove child (edge.end) from constituent
            start_constituent = edge.start.syntactic_object
            if not start_constituent:
                # placeholder constituent doesn't have syntactic presence
                return
            end_constituent = edge.end.syntactic_object
            if not (start_constituent and end_constituent):
                # placeholder constituent doesn't have syntactic presence
                return
            ### Obey the syntax API ###
            left, right = start_constituent.left, start_constituent.right
            if left is end_constituent:
                start_constituent.left = None
            elif right is end_constituent:
                start_constituent.right = None
    elif etype is g.FEATURE_EDGE:
        if isinstance(edge.start, ConstituentNode) and edge.end:
            # Remove feature (edge.end) from constituent
            start_constituent = edge.start.syntactic_object
            end_feature = edge.end.syntactic_object
            ### Obey the syntax API ###
            start_constituent.remove_feature(end_feature)
    else:
        raise ForestSyntaxError("Not implemented: What to do syntactically when disconnecting edge: %s" % edge)

def constituent_merge(left_node, right_node):
    lc = left_node.syntactic_object
    rc = right_node.syntactic_object
    if not (lc and rc):
        raise ForestSyntaxError('Merge needs two constituents, got (%s, %s).' % (lc, rc))
    return ctrl.UG.Merge(lc, rc)

def which_selects(left_node, right_node):
    lc = left_node.syntactic_object
    rc = right_node.syntactic_object
    if not (lc and rc):
        raise ForestSyntaxError('Selection needs two constituents, got (%s, %s).' % (lc, rc))
    sc = ctrl.UG.merge_selects(lc, rc)
    if sc is lc:
        return left_node
    elif sc is rc:
        return right_node
    else:
        return None

def set_constituent_features(node):
    c = node.syntactic_object
    new_features = ctrl.forest.get_feature_nodes(node)
    old_features = c.features
    remainders = set(old_features)
    for feature in new_features:
        if feature.syntactic_object not in old_features:
            c.add_feature(feature.syntactic_object.key, feature.syntactic_object)
        else:
            remainders.remove(feature.syntactic_object)
    for feature in remainders:
        c.del_feature(feature.syntactic_object.key)

def constituent_copy(node):
    if not node or not node.syntactic_object:
        raise ForestSyntaxError("Trying to copy empty node")
    return node.syntactic_object.copy()

def new_constituent(label, source=None):
    return ctrl.Constituent(label, source=source)

def set_constituent_index(constituent, index):
    constituent.index = index
