# coding=utf-8

# Here is data to define KatajaActions and the methods they trigger. Each file defines a dict 'a'
# that is on startup added into the one big dict of actions. So the order and hierarchy in these
# actions is not maintained: actions are split into many files just to avoid it growing
# too cumbersome. _utils.py is the only exception, it doesn't define actions but has helper methods
# generally useful for action methods: reaching the ui_support-object that triggered the action,
# or the panel where the ui_support-object is.

import kataja.actions.edit
import kataja.actions.file
import kataja.actions.forest
import kataja.actions.help
import kataja.actions.keyboard
import kataja.actions.preferences
import kataja.actions.quick_edit
import kataja.actions.settings
import kataja.actions.tree_edit
import kataja.actions.view
import kataja.actions.window

actions_dict = edit.a
actions_dict.update(file.a)
actions_dict.update(forest.a)
actions_dict.update(help.a)
actions_dict.update(keyboard.a)
actions_dict.update(preferences.a)
actions_dict.update(quick_edit.a)
actions_dict.update(settings.a)
actions_dict.update(tree_edit.a)
actions_dict.update(view.a)
actions_dict.update(window.a)
