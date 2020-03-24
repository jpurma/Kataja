from kataja.ui_widgets.Panel import PanelAction


class ToggleParsePanelVisualisationMode(PanelAction):
    k_action_uid = 'toggle_parse_panel_visualisation_mode'
    k_command = 'Switch circle or tree visualisation for parses'
    k_undoable = False
    k_checkable = True

    def prepare_parameters(self, args, kwargs):
        sender = self.sender()
        return [sender.isChecked()], {}

    def method(self, checked):
        self.panel and self.panel.change_mode(checked)

    def getter(self):
        return self.panel and self.panel.tree_mode

    def enabler(self):
        return self.panel.isVisible()
