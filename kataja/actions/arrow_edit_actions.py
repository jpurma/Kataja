# coding=utf-8

from PyQt5 import QtCore
from kataja.KatajaAction import KatajaAction
from kataja.ui_widgets.UIEmbed import EmbedAction
from kataja.singletons import ctrl, log


# ==== Class variables for KatajaActions:
#
# k_action_uid : unique id for calling this action. required, other are optional
# k_command : text used for menu command and log feedback, unless the method returns a fdback string
# k_tooltip : tooltip text for ui element. If not given, uses k_command as tooltip.
# k_undoable : is the action undoable, default is True
# k_shortcut : keyboard shortcut given as string, e.g. 'Ctrl+x'
# k_shortcut_context : can be nothing or 'parent_and_children' if shortcut is active only when the
#                      parent widget is visible and active
# k_checkable : should the action be checkable, default False
#
# ==== Methods:
#
# method : gets called when action is triggered. If it returns a string, this is used as a command
#          feedback string, otherwise k_command is printed to log.
# getter : if there is an UI element that can show state or display value, this method returns the
#          value. These are called quite often, but with values that have to change e.g. when item
#          is dragged, you'll have to update manually.
# enabler : if enabler is defined, the action is active (also reflected into its UI elements) only
#           when enabler returns True
#


class EditArrowLabelEnterText(EmbedAction):
    k_action_uid = 'edit_edge_label_enter_text'
    k_command = 'Enter'

    # k_shortcut = 'Return'
    # k_shortcut_context = 'parent_and_children'

    def prepare_parameters(self, args, kwargs):
        if self.embed:
            edge_uid = self.embed.host.uid
            text = self.embed.input_line_edit.text()
        else:
            edge_uid = ''
            text = ''
        return [edge_uid, text], kwargs

    def method(self, edge_uid: str, text: str):
        """ Set text for edge. (mostly used for labeling arrows)
        :param edge_uid: str
        :param text: str
        :return None:
        """
        try:
            edge = ctrl.forest.edges[edge_uid]
        except KeyError:
            log.error(f'No such edge: {edge_uid}.')
            return
        edge.set_label_text(text)
        ctrl.ui.close_active_embed()


class DisconnectArrow(EmbedAction):
    k_action_uid = 'disconnect_arrow'
    k_command = 'Disconnect nodes'
    k_tooltip = 'Disconnect nodes and remove this edge.'

    def prepare_parameters(self, args, kwargs):
        if self.embed:
            edge_uid = self.embed.host.uid
        else:
            edge_uid = ''
        return [edge_uid], kwargs

    def method(self, edge_uid: str):
        """ Remove connection between two nodes, this is triggered from the edge.
        :return: None
        """
        try:
            edge = ctrl.forest.edges[edge_uid]
        except KeyError:
            log.error(f'No such edge: {edge_uid}.')
            return
        ctrl.free_drawing.disconnect_edge(edge)
        ctrl.ui.update_selections()
        ctrl.forest.forest_edited()


class NewArrow(EmbedAction):
    k_action_uid = 'new_arrow'
    k_command = 'New arrow'

    # k_shortcut = 'a'
    # k_shortcut_context = 'parent_and_children'

    def prepare_parameters(self, args, kwargs):
        p1, p2 = self.embed.get_marker_points()
        end_point = int(p1.x()), int(p1.y())
        focus_point = int(p2.x()), int(p2.y())
        text = embed.input_line_edit.text()
        return [focus_point, end_point, text], kwargs

    def method(self, focus_point, end_point, text):
        """ Create a new arrow into embed menu's location
        """
        ctrl.free_drawing.create_arrow(focus_point, end_point, text)
        ctrl.ui.close_active_embed()
        ctrl.forest.forest_edited()


class StartArrowFromNode(EmbedAction):
    k_action_uid = 'start_arrow_from_node'
    k_command = 'Add arrow from here to...'

    # k_shortcut = 'a'
    # k_shortcut_context = 'parent_and_children'

    def prepare_parameters(self, args, kwargs):
        node_uid = self.embed.host.uid
        return [node_uid], kwargs

    def method(self, node_uid: str):
        """ Create an arrow starting from a given node
        :param node_uid: str
        :return:
        """
        try:
            node = ctrl.forest.nodes[node_uid]
        except KeyError:
            log.error(f'No such node: {node_uid}.')
            return
        ex, ey = node.bottom_center_magnet()
        end_pos = QtCore.QPointF(ex + 20, ey + 40)
        ctrl.free_drawing.create_arrow(start=node, end=end_pos)


class SetArrowStart(KatajaAction):
    k_action_uid = 'set_arrow_start'
    k_command = 'Set arrow start point'
    k_undoable = True
    k_tooltip = 'Set the starting point for an arrow'

    def method(self, arrow_uid, x=0, y=0, node_uid=None):
        """ Immediately move arrow to start at given scene position or from a specific node.
        :param arrow_uid:
        :param x:
        :param y:
        :param node_uid:
        :return:
        """
        arrow = ctrl.forest.arrows[arrow_uid]
        if node_uid and node_uid in ctrl.forest.nodes:
            arrow.connect_start(ctrl.forest.nodes[node_uid])
        else:
            arrow.set_start_point(x, y)


class SetArrowEnd(KatajaAction):
    k_action_uid = 'set_arrow_end'
    k_command = 'Set arrow end point'
    k_undoable = True
    k_tooltip = 'Set the ending point for an arrow'

    def method(self, arrow_uid, x=0, y=0, node_uid=None):
        """ Immediately move arrow to start at given scene position or from a specific node.
        :param arrow_uid:
        :param x:
        :param y:
        :param node_uid:
        :return:
        """
        arrow = ctrl.forest.arrows[arrow_uid]
        if node_uid and node_uid in ctrl.forest.nodes:
            arrow.connect_end(ctrl.forest.nodes[node_uid])
        else:
            arrow.set_end_point(x, y)


class SetArrowMiddlePoint(KatajaAction):
    k_action_uid = 'set_arrow_middle'
    k_command = 'Set arrow middle point'
    k_undoable = True
    k_tooltip = 'Set the middle point (curve) for an arrow'

    def method(self, arrow_uid, x=0, y=0, node_uid=None):
        arrow = ctrl.forest.arrows[arrow_uid]
        arrow.set_curve_point(x, y)
