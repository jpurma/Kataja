__author__ = 'purma'

# (Order of actions is irrelevant, menus are built according to instructions at another dict.)
# key : used internally to fetch the action
# command : displayed in menus
# method : method that is called when the action is activated
# shortcut : keyboard shortcut to activate the action
# context : where the method is called 'main' is default, referring to KatajaMain
#           other values: 'app', 'selected', 'node'...
# checkable : True/False -- as a menu item, does the action have two states
actions = {
    # ### File ######
    'open': {
        'command': '&Open',
        'method': 'open_kataja_file',
        'shortcut': 'Ctrl+o'},
    'save': {
        'command': '&Save',
        'method': 'save_kataja_file',
        'shortcut': 'Ctrl+s'},
    'save_as': {
        'command': '&Save as',
        'method': 'save_as'},
    'print_pdf': {
        'command': '&Print',
        'method': 'print_to_file',
        'shortcut': 'Ctrl+p'},
    'blender_render': {
        'command': '&Render in Blender',
        'method': 'render_in_blender',
        'shortcut': 'Ctrl+r'},
    'preferences': {
        'command': '&Preferences',
        'method': 'main.open_preferences'},
    'quit': {
        'command': '&Quit',
        'method': 'closeAllWindows',
        'context': 'app',
        'shortcut': 'Ctrl+q'},
    # ### Build ######
    'next_forest': {
        'command': 'Next forest',
        'method': 'next_structure',
        'shortcut': '.',
        'button': 'next_tree',
        'tooltip': 'Switch to next forest',
        'no_undo': True},
    'prev_forest': {
        'command': 'Previous forest',
        'method': 'previous_structure',
        'shortcut': ',',
        'button': 'prev_tree',
        'tooltip': 'Switch to previous forest',
        'no_undo': True},
    'next_derivation_step': {
        'command': 'Animation step forward',
        'method': 'animation_step_forward',
        'shortcut': '>', 'button': 'next_der'},
    'prev_derivation_step': {
        'command': 'Animation step backward',
        'method': 'animation_step_backward',
        'shortcut': '<',
        'button': 'prev_der'},
    # Rules ######
    'label_visibility': {
        'command': 'Show &labels in middle nodes',
        'method': 'toggle_label_visibility',
        'shortcut': 'l',
        'checkable': True, },
    'bracket_mode': {
        'command': 'Show &brackets',
        'method': 'toggle_brackets',
        'shortcut': 'b',
        'checkable': True, },
    'trace_mode': {
        'command': 'Show &traces',
        'method': 'toggle_traces',
        'shortcut': 't',
        'checkable': True, },
    'merge_edge_shape': {
        'command': 'Change branch &shape',
        'method': 'change_node_edge_shape',
        'shortcut': 's'},
    'feature_edge_shape': {
        'command': 'Change feature branch &shape',
        'method': 'change_feature_edge_shape',
        'shortcut': 'Shift+s'},
    'merge_order_attribute': {
        'command': 'Show merge &order',
        'method': 'show_merge_order',
        'shortcut': 'o',
        'checkable': True},
    'select_order_attribute': {
        'command': 'Show select &Order',
        'method': 'show_select_order',
        'shortcut': 'Shift+o',
        'checkable': True},
    # View ####
    'change_colors': {
        'command': 'Change %Colors',
        'method': 'change_colors',
        'shortcut': 'Shift+c'},
    'adjust_colors': {
        'command': 'Adjust colors',
        'method': 'change_colors',
        'shortcut': 'Shift+Alt+c'},
    'zoom_to_fit': {
        'command': '&Zoom to fit',
        'method': 'fit_to_window',
        'shortcut': 'z'},
    'fullscreen_mode': {
        'command': '&Fullscreen',
        'method': 'toggle_full_screen',
        'shortcut': 'f',
        'checkable': True},
    # Panels ####
    'toggle_all_panels': {
        'command': 'Hide all panels',
        'command_alt': 'Show all panels',
        'method': 'toggle_all_panels',
        'toggleable': True,
        'condition': 'are_panels_visible',
        'context': 'ui'
    },
    'edge_shape_scope': {
        'command': 'Select shape for...',
        'method': 'change_edge_panel_scope',
        'selection': 'line_type_target',
        'tooltip': 'Which relations are affected?',
        'no_undo': True
    },
    'change_edge_shape': {
        'command': 'Change relation shape',
        'method': 'change_edge_shape',
        'selection': 'line_type',
        'tooltip': 'Change shape of relations (lines, edges) between objects'
    },
    # Help ####
    'help': {
        'command': '&Help',
        'method': 'show_help_message',
        'shortcut': 'h', },
    # Generic keys ####
    'key_esc': {
        'command': 'key_esc',
        'method': 'key_esc',
        'shortcut': 'Escape'},
    'key_backspace': {
        'command': 'key_backspace',
        'method': 'key_backspace',
        'shortcut': 'Backspace'},
    'key_return': {
        'command': 'key_return',
        'method': 'key_return',
        'shortcut': 'Return'},
    'key_left': {
        'command': 'key_left',
        'method': 'key_left',
        'shortcut': 'Left'},
    'key_right': {
        'command': 'key_right',
        'method': 'key_right',
        'shortcut': 'Right'},
    'key_up': {
        'command': 'key_up',
        'method': 'key_up',
        'shortcut': 'Up'},
    'key_down': {
        'command': 'key_down',
        'method': 'key_down',
        'shortcut': 'Down'},
    'key_tab': {
        'command': 'key_tab',
        'method': 'key_tab',
        'shortcut': 'Tab'},
    'undo': {
        'command': 'undo',
        'method': 'undo',
        'shortcut': 'Ctrl+z'},
    'redo': {
        'command': 'redo',
        'method': 'redo',
        'shortcut': 'Ctrl+Shift+z'},
    'key_m': {
        'command': 'key_m',
        'method': 'key_m',
        'shortcut': 'm'}
}

