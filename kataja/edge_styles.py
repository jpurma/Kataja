from kataja.globals import *

# start_connects_to and end_connects_to
CENTER = 0
BOTTOM_CENTER = 1
MAGNETS = 2
BORDER = 3
SPECIAL = 4
ARROW: {
    'shape_name': 'cubic',
    'color_key': 'accent4',
    'pull': 0,
    'visible': True,
    'arrowheads': AT_END,
    'font': MAIN_FONT,
    'start_connects_to': BORDER,
    'end_connects_to': BORDER,
    'z_value': 130
}

master_styles = {
    'fancy': {
        CHECKING_EDGE: {
            'shape_name': 'low_arc',
            'color_key': '',
            'pull': .40,
            'visible': True,
            'arrowheads': 0,
            'font': MAIN_FONT,
            'style': 'dashed',
            'start_connects_to': SPECIAL,
            'end_connects_to': SPECIAL,
            'z_value': 15
        },
        COMMENT_EDGE: {
            'shape_name': 'linear',
            'color_key': '',
            'pull': 0,
            'visible': True,
            'arrowheads': 0,
            'start_connects_to': BORDER,
            'end_connects_to': BORDER,
            'z_value': 100
        },
        CONSTITUENT_EDGE: {
            'shape_name': 'shaped_cubic',
            'color_key': '',
            'pull': .24,
            'visible': True,
            'arrowheads': 0,
            'start_connects_to': MAGNETS,
            'end_connects_to': MAGNETS,
            'z_value': 14
        },
        FEATURE_EDGE: {
            'shape_name': 'cubic',
            'color_key': '',
            'pull': .20,
            'visible': True,
            'arrowheads': 0,
            'start_connects_to': BORDER,
            'end_connects_to': BORDER,
            'z_value': 15
        },
        GLOSS_EDGE: {
            'shape_name': 'cubic',
            'color_key': '',
            'pull': .40,
            'visible': False,
            'arrowheads': 0,
            'start_connects_to': BORDER,
            'end_connects_to': BORDER,
            'z_value': 5
        },
        ADJUNCT_EDGE: {
            'shape_name': 'linear',
            'color_key': 'accent7',
            'pull': .10,
            'visible': True,
            'arrowheads': 0,
            'start_connects_to': MAGNETS,
            'end_connects_to': MAGNETS,
            'z_value': 5
        }
    },
    'plain': {
        CHECKING_EDGE: {
            'shape_name': 'low_arc',
            'color_key': '',
            'pull': .40,
            'visible': True,
            'arrowheads': 0,
            'font': MAIN_FONT,
            'style': 'dashed',
            'start_connects_to': BORDER,
            'end_connects_to': BORDER
        },
        COMMENT_EDGE: {
            'shape_name': 'linear',
            'color_key': '',
            'pull': 0,
            'visible': True,
            'arrowheads': 0,
            'start_connects_to': BORDER,
            'end_connects_to': BORDER
        },
        CONSTITUENT_EDGE: {
            'shape_name': 'linear',
            'color_key': '',
            'pull': .24,
            'visible': True,
            'arrowheads': 0,
            'start_connects_to': BOTTOM_CENTER,
            'end_connects_to': BOTTOM_CENTER
        },
        FEATURE_EDGE: {
            'shape_name': 'linear',
            'color_key': '',
            'pull': .40,
            'visible': True,
            'arrowheads': 0,
            'start_connects_to': BORDER,
            'end_connects_to': BORDER
        },
        GLOSS_EDGE: {
            'shape_name': 'linear',
            'color_key': '',
            'pull': .40,
            'visible': False,
            'arrowheads': 0,
            'start_connects_to': BOTTOM_CENTER,
            'end_connects_to': BOTTOM_CENTER
        },
        ABSTRACT_EDGE: {
            'shape_name': 'linear',
            'color_key': 'content3',
            'pull': .40,
            'visible': True,
            'arrowheads': 0,
            'start_connects_to': BORDER,
            'end_connects_to': BORDER
        },
        ADJUNCT_EDGE: {
            'shape_name': 'linear',
            'color_key': 'content1tr',
            'pull': .10,
            'visible': True,
            'arrowheads': 0,
            'start_connects_to': BOTTOM_CENTER,
            'end_connects_to': BOTTOM_CENTER,
            'z_value': 5
        }
    }
}

names = {
    CHECKING_EDGE: ('Checking edge', 'Checking edges'),
    COMMENT_EDGE: ('Comment edge', 'Comment edges'),
    CONSTITUENT_EDGE: ('Constituent edge', 'Constituent edges'),
    FEATURE_EDGE: ('Feature edge', 'Feature edges'),
    GLOSS_EDGE: ('Gloss edge', 'Gloss edges'),
    ABSTRACT_EDGE: ('Abstract edge', 'Abstract edges')
}
