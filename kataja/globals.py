# coding=utf-8

# ## Global enums

SELECTION = 66
AMBIGUOUS_VALUES = 88

# How to show labels
ONLY_LEAF_LABELS = 0
ALL_LABELS = 1
ALIASES = 2

NO_LABEL = 0
SHOW_LABEL_WITHOUT_INDEX = 1  #
SHOW_LABEL_WITH_INDEX = 2
ONLY_INDEX = 3

# Edge types
CONSTITUENT_EDGE = 'c'
FEATURE_EDGE = 'f'
GLOSS_EDGE = 'g'
ARROW = 'r'
PROPERTY_EDGE = 'p'
ABSTRACT_EDGE = 'z'
ATTRIBUTE_EDGE = 'a'
DIVIDER = 'd'

# Node types
ABSTRACT_NODE = 'z'
CONSTITUENT_NODE = 'c'
FEATURE_NODE = 'f'
ATTRIBUTE_NODE = 'a'
GLOSS_NODE = 'g'
PROPERTY_NODE = 'p'
COMMENT_NODE = 'm'

# Touch area types
LEFT_ADD_ROOT = 0
RIGHT_ADD_ROOT = 1
LEFT_ADD_SIBLING = 2
RIGHT_ADD_SIBLING = 3
TOUCH_ADD_CONSTITUENT = 4

# ## Our custom signals

EDGE_SHAPES_CHANGED = 101
# EDGE_SHAPES_CHANGED = QtCore.pyqtSignal(int, int)

GUESS_FROM_INPUT = 'guess from input'
ADD_CONSTITUENT = 'Constituent'
ADD_FEATURE = 'Feature'
ADD_GLOSS = 'Gloss'
ADD_TEXT_BOX = 'Text box'

#EDGE_SHAPES_CHANGED = QtCore.QEvent.registerEventType()
#print 'EDGE_SHAPES_CHANGED: ', EDGE_SHAPES_CHANGED

# UI_PANELS
LOG = 'log'
TEST = 'test'
NAVIGATION = 'navigation'
VISUALIZATION = 'visualization'
COLOR_THEME = 'color_theme'
COLOR_WHEEL = 'color_wheel'
EDGES = 'drawing'
LINE_OPTIONS = 'line_options'
SYMBOLS = 'symbols'
NODES = 'nodes'

# Alignment of edges
NO_ALIGN = 0
LEFT = 1
RIGHT = 2

# code for deleting a value
DELETE = 9999

# FONTS
MAIN_FONT = 'main_font'
CONSOLE_FONT = 'monospace_font'
BOLD_FONT = 'bold_font'
ITALIC_FONT = 'italic_font'
UI_FONT = 'ui_font'
SMALL_FEATURE = 'small_feature'
SMALL_CAPS = 'small_caps_font'

# Control point roles
START_POINT = 'start'
END_POINT = 'end'
LABEL_START = 'label_start'

# Bracket styles:
NO_BRACKETS = 0
MAJOR_BRACKETS = 1
ALL_BRACKETS = 2

# Overlay buttons
REMOVE_MERGER = 'remove_merger'
START_CUT = 'start_cut'
END_CUT = 'end_cut'
ADD_TRIANGLE = 'add_triangle'
REMOVE_TRIANGLE = 'remove_triangle'
