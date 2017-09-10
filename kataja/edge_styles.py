from kataja.globals import *

# start_connects_to and end_connects_to
CENTER = 0
BOTTOM_CENTER = 1
MAGNETS = 2
BORDER = 3
SPECIAL = 4

master_styles = {
    'fancy': {
        ARROW: {
            'shape_name': 'cubic',
            'color_id': 'accent4',
            'pull': 0,
            'visible': True,
            'arrowheads': AT_END,
            'font': MAIN_FONT,
            'labeled': True,
            'start_connects_to': BORDER,
            'end_connects_to': BORDER,
            'z_value': 130
        },
        DIVIDER: {
            'shape_name': 'linear',
            'color_id': 'accent4',
            'pull': 0,
            'visible': True,
            'arrowheads': 0,
            'font': MAIN_FONT,
            'labeled': True,
            'style': 'dashed',
            'start_connects_to': BORDER,
            'end_connects_to': BORDER,
            'z_value': 120
        },
        CHECKING_EDGE: {
            'shape_name': 'low_arc',
            'color_id': '',
            'pull': .40,
            'visible': True,
            'arrowheads': 0,
            'font': MAIN_FONT,
            'labeled': False,
            'style': 'dashed',
            'start_connects_to': SPECIAL,
            'end_connects_to': SPECIAL,
            'z_value': 5
        },
        COMMENT_EDGE: {
            'shape_name': 'linear',
            'color_id': '',
            'pull': 0,
            'visible': True,
            'arrowheads': 0,
            'labeled': False,
            'start_connects_to': BORDER,
            'end_connects_to': BORDER,
            'z_value': 100
        },
        CONSTITUENT_EDGE: {
            'shape_name': 'shaped_cubic',
            'color_id': '',
            'pull': .24,
            'visible': True,
            'arrowheads': 0,
            'labeled': False,
            'start_connects_to': MAGNETS,
            'end_connects_to': MAGNETS,
            'z_value': 4
        },
        FEATURE_EDGE: {
            'shape_name': 'cubic',
            'color_id': '',
            'pull': .20,
            'visible': True,
            'arrowheads': 0,
            'labeled': False,
            'start_connects_to': BORDER,
            'end_connects_to': BORDER,
            'z_value': 5
        },
        GLOSS_EDGE: {
            'shape_name': 'cubic',
            'color_id': '',
            'pull': .40,
            'visible': True,
            'arrowheads': 0,
            'labeled': False,
            'start_connects_to': BORDER,
            'end_connects_to': BORDER,
            'z_value': 5
        }
    },
    'plain': {
        ARROW: {
            'shape_name': 'cubic',
            'color_id': 'accent4',
            'pull': 0,
            'visible': True,
            'arrowheads': AT_END,
            'font': MAIN_FONT,
            'labeled': True,
            'start_connects_to': BORDER,
            'end_connects_to': BORDER
        },
        DIVIDER: {
            'shape_name': 'linear',
            'color_id': 'accent4',
            'pull': 0,
            'visible': True,
            'arrowheads': 0,
            'font': MAIN_FONT,
            'labeled': True,
            'style': 'dashed',
            'start_connects_to': BORDER,
            'end_connects_to': BORDER
        },
        CHECKING_EDGE: {
            'shape_name': 'low_arc',
            'color_id': '',
            'pull': .40,
            'visible': True,
            'arrowheads': 0,
            'font': MAIN_FONT,
            'labeled': False,
            'style': 'dashed',
            'start_connects_to': BORDER,
            'end_connects_to': BORDER
        },
        COMMENT_EDGE: {
            'shape_name': 'linear',
            'color_id': '',
            'pull': 0,
            'visible': True,
            'arrowheads': 0,
            'labeled': False,
            'start_connects_to': BORDER,
            'end_connects_to': BORDER
        },
        CONSTITUENT_EDGE: {
            'shape_name': 'linear',
            'color_id': '',
            'pull': .24,
            'visible': True,
            'arrowheads': 0,
            'labeled': False,
            'start_connects_to': BOTTOM_CENTER,
            'end_connects_to': BOTTOM_CENTER
        },
        FEATURE_EDGE: {
            'shape_name': 'linear',
            'color_id': '',
            'pull': .40,
            'visible': True,
            'arrowheads': 0,
            'labeled': False,
            'start_connects_to': BORDER,
            'end_connects_to': BORDER
        },
        GLOSS_EDGE: {
            'shape_name': 'linear',
            'color_id': '',
            'pull': .40,
            'visible': True,
            'arrowheads': 0,
            'labeled': False,
            'start_connects_to': BOTTOM_CENTER,
            'end_connects_to': BOTTOM_CENTER
        },
        ABSTRACT_EDGE: {
            'shape_name': 'linear',
            'color_id': 'content3',
            'pull': .40,
            'visible': True,
            'arrowheads': 0,
            'labeled': False,
            'start_connects_to': BORDER,
            'end_connects_to': BORDER
        }
    }
}

names = {
    ARROW: ('Arrow', 'Arrows'),
    DIVIDER: ('Divider', 'Dividers'),
    CHECKING_EDGE: ('Checking edge', 'Checking edges'),
    COMMENT_EDGE: ('Comment edge', 'Comment edges'),
    CONSTITUENT_EDGE: ('Constituent edge', 'Constituent edges'),
    FEATURE_EDGE: ('Feature edge', 'Feature edges'),
    GLOSS_EDGE: ('Gloss edge', 'Gloss edges'),
    ABSTRACT_EDGE: ('Abstract edge', 'Abstract edges')
}
