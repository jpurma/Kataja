# coding=utf-8
from enum import Enum

# ## Global enums

SELECTION = 66
AMBIGUOUS_VALUES = 88

# Edge types
CONSTITUENT_EDGE = 'c'
FEATURE_EDGE = 'f'
CHECKING_EDGE = 'f2'
GLOSS_EDGE = 'g'
ARROW = 'r'
ABSTRACT_EDGE = 'z'
DIVIDER = 'd'
COMMENT_EDGE = '!'

# Node types
ABSTRACT_NODE = 7
CONSTITUENT_NODE = 1
FEATURE_NODE = 2
GLOSS_NODE = 3
COMMENT_NODE = 4

# Special node types used in parsing
TREE = 100
GUESS_FROM_INPUT = 99

# ## Our custom signals



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
CUSTOM_FONT1 = 'custom1'
CUSTOM_FONT2 = 'custom2'
CUSTOM_FONT3 = 'custom3'

# Control point roles
START_POINT = 'start'
END_POINT = 'end'
LABEL_START = 'label_start'
CURVE_ADJUSTMENT = 'adjust'

# Linearization modes
IMPLICIT_ORDERING = 0
NO_LINEARIZATION = 1
USE_LINEARIZATION = 2
RANDOM_NO_LINEARIZATION = 3

# Creation/Deletion flags
CREATED = 1
DELETED = -1

# Font roles
FONT_ROLES = [(MAIN_FONT, 'main'), (CONSOLE_FONT, 'console'), (BOLD_FONT, 'bold'),
              (ITALIC_FONT, 'italic'), (UI_FONT, 'ui_support'), (SMALL_FEATURE, 'small'),
              (SMALL_CAPS, 'small caps'), (CUSTOM_FONT1, 'custom 1'), (CUSTOM_FONT2, 'custom 2'),
              (CUSTOM_FONT3, 'custom 3')]

# Vertical align
TOP = 0
MIDDLE = 2
BOTTOM = 4

# Horizontal align
# NO_ALIGN = 0  -- this is already defined as edge alignment
LEFT_ALIGN = 1
CENTER_ALIGN = 2
RIGHT_ALIGN = 3

# Possible node shapes
NORMAL = 0
SCOPEBOX = 1
BRACKETED = 2
BOX = 3
CARD = 4
FEATURE_SHAPE = 5

# Settings layers
HIGHEST = 0
OBJECT = 1
FOREST = 2
DOCUMENT = 3
PREFS = 4
CONFLICT = 666666

# Arrowheads
AT_START = 1
AT_END = 2
AT_BOTH = 3

# Trace strategies
USE_MULTIDOMINATION = 0
USE_TRACES = 1
TRACES_GROUPED_TOGETHER = 2

# label text modes
NODE_LABELS = 2
NODE_LABELS_FOR_LEAVES = 3
CHECKED_FEATURES = 5
NO_LABELS = 6

# How to show checking
NO_CHECKING_EDGE = 0
PUT_CHECKED_TOGETHER = 1
SHOW_CHECKING_EDGE = 2

# Positioning of features
FREE_FLOATING = 0
HORIZONTAL_ROW = 1
VERTICAL_COLUMN = 2
TWO_COLUMNS = 3

# Edge ends
EDGE_PLUGGED_IN = 4
EDGE_RECEIVING_NOW = 3
EDGE_OPEN = 2
EDGE_CAN_INSERT = 5
EDGE_OPEN_DOMINANT = 6
EDGE_RECEIVING_NOW_DOMINANT = 7


class ViewUpdateReason(Enum):
    """ Reasons for updating viewport """
    NEW_FOREST = 0
    MAJOR_REDRAW = 1
    MANUAL_ZOOM = 2
    ACTION_FINISHED = 3
    FIT_IN_TRIGGERED = 4
    ANIMATION_STEP = 5
