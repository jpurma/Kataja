# coding=utf-8

# ## Global enums

SELECTION = 66
AMBIGUOUS_VALUES = 88

# Edge types
CONSTITUENT_EDGE = 'c'
FEATURE_EDGE = 'f'
CHECKING_EDGE = 'f2'
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

# Touch area types -- values have to match class names in TouchArea.py
LEFT_ADD_TOP = 'LeftAddTop'
RIGHT_ADD_TOP = 'RightAddTop'
LEFT_ADD_SIBLING = 'LeftAddSibling'
RIGHT_ADD_SIBLING = 'RightAddSibling'
TOUCH_ADD_CONSTITUENT = 'AddConstituentTouchArea'
TOUCH_CONNECT_FEATURE = 'ConnectFeatureTouchArea'
TOUCH_CONNECT_GLOSS = 'ConnectGlossTouchArea'
TOUCH_CONNECT_COMMENT = 'ConnectCommentTouchArea'
DELETE_ARROW = 'DeleteArrowTouchArea'
LEFT_ADD_CHILD = 'LeftAddChild'
RIGHT_ADD_CHILD = 'RightAddChild'
ADD_TRIANGLE = 'AddTriangleTouchArea'
REMOVE_TRIANGLE = 'RemoveTriangleTouchArea'
INNER_ADD_SIBLING_LEFT = 'LeftAddInnerSibling'
INNER_ADD_SIBLING_RIGHT = 'RightAddInnerSibling'
UNARY_ADD_CHILD_LEFT = 'LeftAddUnaryChild'
UNARY_ADD_CHILD_RIGHT = 'RightAddUnaryChild'
LEAF_ADD_SIBLING_LEFT = 'LeftAddLeafSibling'
LEAF_ADD_SIBLING_RIGHT = 'RightAddLeafSibling'

# Overlay buttons -- These refer to class names in OverlayButton.py
REMOVE_MERGER = 'RemoveMergerButton'
GROUP_OPTIONS = 'GroupOptionsButton'
NODE_EDITOR_BUTTON = 'NodeEditorButton'
REMOVE_NODE = 'RemoveNodeButton'
CUT_FROM_START_BUTTON = 'CutFromStartButton'
CUT_FROM_END_BUTTON = 'CutFromEndButton'

# ## Our custom signals

EDGE_SHAPES_CHANGED = 101
# EDGE_SHAPES_CHANGED = QtCore.pyqtSignal(int, int)

# EDGE_SHAPES_CHANGED = QtCore.QEvent.registerEventType()
# print 'EDGE_SHAPES_CHANGED: ', EDGE_SHAPES_CHANGED


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

