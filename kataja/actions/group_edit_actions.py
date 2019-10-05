# coding=utf-8

from kataja.KatajaAction import KatajaAction
from kataja.saved.movables.Node import Node
from kataja.singletons import ctrl, log
from kataja.ui_widgets.embeds.GroupLabelEmbed import GroupLabelEmbed


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


class ToggleGroupOptions(KatajaAction):
    k_action_uid = 'toggle_group_options'
    k_command = 'Inspect, edit and keep this group'

    def prepare_parameters(self, args, kwargs):
        group_uid = self.get_host().uid
        return [group_uid], kwargs

    def method(self, group_uid: str):
        """ Open group editing embed.
        :type group_uid: object
        """
        if ctrl.ui.selection_group and ctrl.ui.selection_group.uid == group_uid:
            group = ctrl.ui.selection_group
        elif group_uid in ctrl.forest.groups:
            group = ctrl.forest.groups[group_uid]
        else:
            log.error(f'No such group: {group_uid}.')
            return
        ctrl.ui.toggle_group_label_editing(group)


class MakeSelectionGroupPersistent(KatajaAction):
    k_action_uid = 'make_selection_group_persistent'
    k_command = 'Save this selection as a group'

    def method(self):
        """ Open group editing embed."""
        ctrl.forest.drawing.turn_selection_group_to_group(ctrl.ui.selection_group)


class ToggleGroupPersistence(KatajaAction):
    k_action_uid = 'remove_group_persistence'
    k_command = 'Remove this grouping'

    def prepare_parameters(self, args, kwargs):
        group_uid = self.get_host().uid
        return [group_uid], kwargs

    def method(self, group_uid: str):
        """ Open group editing embed.
        :type group_uid: object
        """
        if group_uid in ctrl.forest.groups:
            group = ctrl.forest.groups[group_uid]
            if group.persistent:
                group.persistent = False


class DeleteGroupItems(KatajaAction):
    k_action_uid = 'delete_group_items'
    k_command = 'Delete nodes in this selection'

    def method(self):
        for item in ctrl.selected:
            if isinstance(item, Node):
                ctrl.drawing.delete_node(item, touch_edges=True, fade=True)
        ctrl.ui.remove_selection_group()

    def enabler(self):
        return ctrl.ui.selection_group and not ctrl.ui.selection_group.persistent


class ChangeGroupColor(KatajaAction):
    k_action_uid = 'change_group_color'
    k_command = 'Change color for group'

    def prepare_parameters(self, args, kwargs):
        sender = self.sender()
        group_uid = self.get_host().uid
        color_key = sender.currentData()
        return [group_uid, color_key], kwargs

    def method(self, group_uid, color_key):
        group = None
        if ctrl.ui.selection_group and ctrl.ui.selection_group.uid == group_uid:
            group = ctrl.ui.selection_group
        elif group_uid in ctrl.forest.groups:
            group = ctrl.forest.groups[group_uid]
        if group:
            group.set_color_key(color_key)
        log.info('Group color changed to %s' % ctrl.cm.get_color_name(color_key))

    def getter(self):
        if ctrl.ui.active_embed and isinstance(ctrl.ui.active_embed, GroupLabelEmbed):
            group = ctrl.ui.active_embed.host
            return group.get_color_key()


class ChangeGroupFill(KatajaAction):
    k_action_uid = 'change_group_fill'
    k_command = 'Group is filled with color'

    def method(self):
        """ """
        sender = self.sender()
        if sender:
            group = self.get_host()
            group.fill = sender.isChecked()
            group.update()


class ChangeGroupOutline(KatajaAction):
    k_action_uid = 'change_group_outline'
    k_command = 'Group has visible outline'

    def method(self):
        """ """
        sender = self.sender()
        if sender:
            group = self.get_host()
            group.outline = sender.isChecked()
            group.update()


class DeleteGroup(KatajaAction):
    k_action_uid = 'delete_group'
    k_command = 'Remove this group'

    def method(self):
        group = self.get_host()
        group.persistent = False
        ctrl.ui.close_group_label_editing(group)
        if ctrl.ui.selection_group is group:
            ctrl.deselect_objects()
            # deselecting will remove the (temporary) selection group
        else:
            ctrl.ui.remove_ui_for(group)
            ctrl.ui.remove_ui(group)


class SaveGroupChanges(KatajaAction):
    k_action_uid = 'save_group_changes'
    k_command = 'Save this group'

    # k_shortcut = 'Return'
    # k_shortcut_context = 'parent_and_children'

    def method(self):
        """ """
        sender = self.sender()
        if sender:
            embed = sender.parent()
            group = self.get_host() or ctrl.ui.selection_group
            ctrl.ui.close_group_label_editing(group)
            group.set_label_text(embed.input_line_edit.text())
            group.update_shape()
            name = group.get_label_text() or ctrl.cm.get_color_name(group.color_key)
            if not group.persistent:
                ctrl.forest.drawing.turn_selection_group_to_group(group)
                ctrl.deselect_objects()

            log.info("Saved group '%s'" % name)
