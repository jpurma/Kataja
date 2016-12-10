from kataja.globals import *

# start_connects_to and end_connects_to
CENTER = 0
BOTTOM_CENTER = 1
MAGNETS = 2
BORDER = 3


master_styles = {
    'fancy': {
        ARROW: {
            'shape_name': 'cubic', 'color_id': 'accent4', 'pull': 0, 'visible': True,
            'arrowhead_at_start': False, 'arrowhead_at_end': True, 'font': MAIN_FONT,
            'labeled': True, 'start_connects_to': BORDER, 'end_connects_to': BORDER
        }, DIVIDER: {
            'shape_name': 'linear', 'color_id': 'accent6', 'pull': 0, 'visible': True,
            'arrowhead_at_start': False, 'arrowhead_at_end': False, 'font': MAIN_FONT,
            'labeled': True, 'style': 'dashed', 'start_connects_to': BORDER,
            'end_connects_to': BORDER
        }, CHECKING_EDGE: {
            'shape_name': 'cubic', 'color_id': 'accent1tr', 'pull': .40, 'visible': True,
            'arrowhead_at_start': False, 'arrowhead_at_end': False, 'font': MAIN_FONT,
            'labeled': False, 'style': 'dashed', 'start_connects_to': BORDER,
            'end_connects_to': BORDER
        }, ATTRIBUTE_EDGE: {
            'shape_name': 'linear', 'color_id': 'content1', 'pull': .50, 'visible': True,
            'arrowhead_at_start': False, 'arrowhead_at_end': False, 'labeled': False,
            'start_connects_to': BORDER, 'end_connects_to': BORDER
        }, COMMENT_EDGE: {
            'shape_name': 'linear', 'color_id': 'accent4', 'pull': 0, 'visible': True,
            'arrowhead_at_start': True, 'arrowhead_at_end': False, 'labeled': False,
            'start_connects_to': BORDER, 'end_connects_to': BORDER
        }, CONSTITUENT_EDGE: {
            'shape_name': 'shaped_cubic', 'color_id': 'content1', 'pull': .24, 'visible': True,
            'arrowhead_at_start': False, 'arrowhead_at_end': False, 'labeled': False,
            'start_connects_to': MAGNETS, 'end_connects_to': MAGNETS
        }, FEATURE_EDGE: {
            'shape_name': 'cubic', 'color_id': 'accent2tr', 'pull': .40, 'visible': True,
            'arrowhead_at_start': False, 'arrowhead_at_end': False, 'labeled': False,
            'start_connects_to': BORDER, 'end_connects_to': BORDER
        }, GLOSS_EDGE: {
            'shape_name': 'cubic', 'color_id': 'accent5', 'pull': .40, 'visible': True,
            'arrowhead_at_start': False, 'arrowhead_at_end': False, 'labeled': False,
            'start_connects_to': BORDER, 'end_connects_to': BORDER
        }, PROPERTY_EDGE: {
            'shape_name': 'linear', 'color_id': 'accent5', 'pull': .40, 'visible': True,
            'arrowhead_at_start': False, 'arrowhead_at_end': False, 'labeled': False,
            'start_connects_to': BORDER, 'end_connects_to': BORDER
        }

    }, 'plain': {
        ARROW: {
            'shape_name': 'cubic', 'color_id': 'accent4', 'pull': 0, 'visible': True,
            'arrowhead_at_start': False, 'arrowhead_at_end': True, 'font': MAIN_FONT,
            'labeled': True, 'start_connects_to': BORDER, 'end_connects_to': BORDER
        }, DIVIDER: {
            'shape_name': 'linear', 'color_id': 'accent6', 'pull': 0, 'visible': True,
            'arrowhead_at_start': False, 'arrowhead_at_end': False, 'font': MAIN_FONT,
            'labeled': True, 'style': 'dashed', 'start_connects_to': BORDER,
            'end_connects_to': BORDER
        }, CHECKING_EDGE: {
            'shape_name': 'cubic', 'color_id': 'accent1tr', 'pull': .40, 'visible': True,
            'arrowhead_at_start': False, 'arrowhead_at_end': False, 'font': MAIN_FONT,
            'labeled': False, 'style': 'dashed', 'start_connects_to': BORDER,
            'end_connects_to': BORDER
        }, ATTRIBUTE_EDGE: {
            'shape_name': 'linear', 'color_id': 'content1', 'pull': .50, 'visible': True,
            'arrowhead_at_start': False, 'arrowhead_at_end': False, 'labeled': False,
            'start_connects_to': BORDER, 'end_connects_to': BORDER
        }, COMMENT_EDGE: {
            'shape_name': 'linear', 'color_id': 'accent4', 'pull': 0, 'visible': True,
            'arrowhead_at_start': True, 'arrowhead_at_end': False, 'labeled': False,
            'start_connects_to': BORDER, 'end_connects_to': BORDER
        }, CONSTITUENT_EDGE: {
            'shape_name': 'linear', 'color_id': 'content1', 'pull': .24, 'visible': True,
            'arrowhead_at_start': False, 'arrowhead_at_end': False, 'labeled': False,
            'start_connects_to': BOTTOM_CENTER, 'end_connects_to': BOTTOM_CENTER
        }, FEATURE_EDGE: {
            'shape_name': 'linear', 'color_id': 'accent2tr', 'pull': .40, 'visible': True,
            'arrowhead_at_start': False, 'arrowhead_at_end': False, 'labeled': False,
            'start_connects_to': BORDER, 'end_connects_to': BORDER
        }, GLOSS_EDGE: {
            'shape_name': 'linear', 'color_id': 'accent5', 'pull': .40, 'visible': True,
            'arrowhead_at_start': False, 'arrowhead_at_end': False, 'labeled': False,
            'start_connects_to': BOTTOM_CENTER, 'end_connects_to': BOTTOM_CENTER
        }, PROPERTY_EDGE: {
            'shape_name': 'linear', 'color_id': 'accent5', 'pull': .40, 'visible': True,
            'arrowhead_at_start': False, 'arrowhead_at_end': False, 'labeled': False,
            'start_connects_to': BORDER, 'end_connects_to': BORDER
        }, ABSTRACT_EDGE: {
            'shape_name': 'linear', 'color_id': 'content1', 'pull': .40, 'visible': True,
            'arrowhead_at_start': False, 'arrowhead_at_end': False, 'labeled': False,
            'start_connects_to': BORDER, 'end_connects_to': BORDER
        }
    }
}

names = {
    ARROW: ('Arrow', 'Arrows'),
    DIVIDER: ('Divider', 'Dividers'),
    CHECKING_EDGE: ('Checking edge', 'Checking edges'),
    ATTRIBUTE_EDGE: ('Attribute edge', 'Attribute edges'),
    COMMENT_EDGE: ('Comment edge', 'Comment edges'),
    CONSTITUENT_EDGE: ('Constituent edge', 'Constituent edges'),
    FEATURE_EDGE: ('Feature edge', 'Feature edges'),
    GLOSS_EDGE: ('Gloss edge', 'Gloss edges'),
    PROPERTY_EDGE: ('Property edge', 'Property edges'),
    ABSTRACT_EDGE: ('Abstract edge', 'Abstract edges')
}