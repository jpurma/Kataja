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
CONSTITUENT_EDGE = 1
FEATURE_EDGE = 2
GLOSS_EDGE = 3
ARROW = 4
PROPERTY_EDGE = 5
ABSTRACT_EDGE = 7
ATTRIBUTE_EDGE = 6
DIVIDER = 8

# Node types
ABSTRACT_NODE = 0
CONSTITUENT_NODE = 1
FEATURE_NODE = 2
ATTRIBUTE_NODE = 3
GLOSS_NODE = 4
PROPERTY_NODE = 5

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
DRAWING = 'drawing'
LINE_OPTIONS = 'line_options'

# Alignment of edges
NO_ALIGN = 0
LEFT = 1
RIGHT = 2

# code for deleting a value
DELETE = 9999

# FONTS
MAIN_FONT = 'main_font'
BIG_FONT = 'big_font'
MENU_FONT = 'menu_font'
UI_FONT = 'ui_font'
ITALIC_FONT = 'italic_font'
PHRASE_LABEL_FONT = 'phrase_label_font'
SMALL_FEATURE = 'small_feature'
SMALL_CAPS = 'small_caps_font'
SYMBOL_FONT = 'symbol_font'

# Control point roles
START_POINT = 'start'
END_POINT = 'end'
LABEL_START = 'label_start'