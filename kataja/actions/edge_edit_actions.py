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


class DisconnectEdge(EmbedAction):
    k_action_uid = 'disconnect_edge'
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
