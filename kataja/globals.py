# coding=utf-8

# ## Global enums

SELECTION = 66
AMBIGUOUS_VALUES = 88

# Edge types
CONSTITUENT_EDGE = 'c'
FEATURE_EDGE = 'f'
GLOSS_EDGE = 'g'
ARROW = 'r'
PROPERTY_EDGE = 'p'
ABSTRACT_EDGE = 'z'
ATTRIBUTE_EDGE = 'a'
DIVIDER = 'd'
COMMENT_EDGE = '!'

# Node types
ABSTRACT_NODE = 7
CONSTITUENT_NODE = 1
FEATURE_NODE = 2
ATTRIBUTE_NODE = 6
GLOSS_NODE = 3
PROPERTY_NODE = 5
COMMENT_NODE = 4

# Special node types used in parsing
TREE = 100
GUESS_FROM_INPUT = 99

# Touch area types
LEFT_ADD_TOP = 0
RIGHT_ADD_TOP = 1
LEFT_ADD_SIBLING = 2
RIGHT_ADD_SIBLING = 3
TOUCH_ADD_CONSTITUENT = 4
TOUCH_CONNECT_FEATURE = 5
TOUCH_CONNECT_GLOSS = 6
TOUCH_CONNECT_COMMENT = 7
DELETE_ARROW = 8
LEFT_ADD_CHILD = 9
RIGHT_ADD_CHILD = 10
ADD_TRIANGLE = 11
REMOVE_TRIANGLE = 12
INNER_ADD_SIBLING_LEFT = 13
INNER_ADD_SIBLING_RIGHT = 14
UNARY_ADD_CHILD_LEFT = 15
UNARY_ADD_CHILD_RIGHT = 16
LEAF_ADD_SIBLING_LEFT = 17
LEAF_ADD_SIBLING_RIGHT = 18


# ## Our custom signals

EDGE_SHAPES_CHANGED = 101
# EDGE_SHAPES_CHANGED = QtCore.pyqtSignal(int, int)

# EDGE_SHAPES_CHANGED = QtCore.QEvent.registerEventType()
# print 'EDGE_SHAPES_CHANGED: ', EDGE_SHAPES_CHANGED

# UI_PANELS
LOG = 'log'
TEST = 'test'
NAVIGATION = 'navigation'
VISUALIZATION = 'visualization'
COLOR_THEME = 'color_theme'
COLOR_WHEEL = 'color_wheel'
EDGES = 'drawing'
LINE_OPTIONS = 'line_options'
VIS_OPTIONS = 'visualization_options'
SYMBOLS = 'symbols'
NODES = 'nodes'
STYLE = 'style'
CAMERA = 'camera'

# Alignment of edges
NO_ALIGN = 0  # default
LEFT = 1  # ordered left edge
RIGHT = 2  # ordered right edge
MIS_LEFT = 3  # shape to use for LEFT when there should be (LEFT, RIGHT), but the ordering fails
MIS_RIGHT = 4  # shape to use for RIGHT when there should be (LEFT, RIGHT), but the ordering fails

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

# Projection styles:
NO_PROJECTIONS = 0
COLORIZE_PROJECTIONS = 1
HIGHLIGHT_PROJECTIONS = 2

# Overlay buttons
REMOVE_MERGER = 'remove_merger'
START_CUT = 'start_cut'
END_CUT = 'end_cut'
AMOEBA_OPTIONS = 'amoeba_options'
NODE_EDITOR_BUTTON = 'node_editor'
REMOVE_NODE = 'delete'

# Creation/Deletion flags
CREATED = 1
DELETED = 2

# Font roles
FONT_ROLES = [(MAIN_FONT, 'main'), (CONSOLE_FONT, 'console'), (BOLD_FONT, 'bold'),
              (ITALIC_FONT, 'italic'), (UI_FONT, 'ui_support'), (SMALL_FEATURE, 'small'),
              (SMALL_CAPS, 'small caps')]

# Vertical align
TOP = 0
TOP_ROW = 1
MIDDLE = 2
BOTTOM_ROW = 3
BOTTOM = 4

# Horizontal align
LEFT_ALIGN = 0
CENTER_ALIGN = 1
RIGHT_ALIGN = 2


# TYPE CODES FOR CUSTOM QGRAPHICSITEMS
#
# Amoeba            65550
# Bracket           65551
# Edge              65552
# EdgeLabel         65553
# Label             65554
# ProjectionVisual  65555
# Tree              65556
# Node              65557
# Movable           65558
# AmoebaLabel       65559
#
# UI:
# ActivityMarker    65650
# ControlPoint      65651
# FadingSymbol      65652
# GlowRing          65653
# HUD               65654
# StretchLine       65655
# TouchArea         65656
#
# UI/embeds:
# MarkerStartPoint  65700
# NewElementMarker  65701
# UIEmbed           65702
