# coding=utf-8

from kataja.singletons import ctrl, prefs, running_environment
from kataja.KatajaAction import KatajaAction


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


class DeriveFromLexicon(KatajaAction):
    k_action_uid = 'derive_from_lexicon'
    k_command = 'Derive again from lexicon'
    k_undoable = False
    k_tooltip = 'Derive current sentence again with this lexicon'
    k_shortcut = 'Ctrl+r'

    def enabler(self):
        return ctrl.syntax and ctrl.syntax.supports_editable_lexicon

    def method(self):
        panel = ctrl.ui.get_panel('LexiconPanel')
        if panel:
            input_text = panel.input_text.text()
            lexicon = panel.lextext.text()
            semantics = panel.semantics_text.text()
            forest = ctrl.forest
            forest.clear()
            ctrl.syntax.create_derivation(input_text=input_text,
                                          lexicon=lexicon,
                                          semantics=semantics,
                                          forest=forest)
            forest.is_parsed = True
            ds = forest.derivation_steps
            ds.derivation_step_index = len(ds.derivation_steps) - 1
            ds.jump_to_derivation_step(ds.derivation_step_index)
            forest.forest_edited()
            forest.prepare_for_drawing()
            ctrl.graph_view.setFocus()
