# coding=utf-8

from PyQt5 import QtCore
from kataja.KatajaAction import KatajaAction
from kataja.ui_widgets.embeds.GroupLabelEmbed import GroupLabelEmbed

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


class ToggleGroupOptions(KatajaAction):
    k_action_uid = 'toggle_group_options'
    k_command = 'Inspect, edit and keep this group'

    def method(self):
        group = self.get_host()
        ctrl.ui.toggle_group_label_editing(group)


class ChangeGroupColor(KatajaAction):
    k_action_uid = 'change_group_color'
    k_command = 'Change color for group'

    def method(self):
        """ """
        sender = self.sender()
        if sender:
            group = self.get_host()
            color_key = sender.currentData()
            sender.model().selected_color = color_key
            if color_key:
                group.update_colors(color_key)
                embed = sender.parent()
                if embed and hasattr(embed, 'update_colors'):
                    embed.update_colors()
                log.info('Group color changed to %s' % ctrl.cm.get_color_name(color_key))

    def enabler(self):
        return ctrl.ui.active_embed and isinstance(ctrl.ui.active_embed, GroupLabelEmbed)

    def getter(self):
        if ctrl.ui.active_embed and isinstance(ctrl.ui.active_embed, GroupLabelEmbed):
            group = ctrl.ui.active_embed.host
            return group.get_color_id()


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


class ChangeGroupOverlaps(KatajaAction):
    k_action_uid = 'change_group_overlaps'
    k_command = 'Allow group to overlap other groups'

    def method(self):
        """ """
        sender = self.sender()
        if sender:
            group = self.get_host()
            group.allow_overlap = sender.isChecked()
            group.update_selection(group.selection)
            group.update_shape()
            if group.allow_overlap:
                log.info('Group can overlap with other groups')
            else:
                log.info('Group cannot overlap with other groups')


class ChangeGroupChildren(KatajaAction):
    k_action_uid = 'change_group_children'
    k_command = 'Include children'
    k_tooltip = 'Include children of the selected nodes in group'

    def method(self):
        """ """
        sender = self.sender()
        if sender:
            group = self.get_host()
            group.include_children = sender.isChecked()
            group.update_selection(group.selection)
            group.update_shape()
            if group.include_children:
                log.info('Group includes children of its orginal members')
            else:
                log.info('Group does not include children')


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
    #k_shortcut = 'Return'
    #k_shortcut_context = 'parent_and_children'

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
                ctrl.forest.free_drawing.turn_selection_group_to_group(group)
                ctrl.deselect_objects()

            log.info("Saved group '%s'" % name)
