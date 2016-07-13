from globals import *

master_styles = {
    'fancy': {
        ARROW: {
            'shape_name': 'linear', 'color_id': 'accent4', 'pull': 0, 'visible': True,
            'arrowhead_at_start': False, 'arrowhead_at_end': True, 'font': MAIN_FONT,
            'labeled': True
        }, DIVIDER: {
            'shape_name': 'linear', 'color_id': 'accent6', 'pull': 0, 'visible': True,
            'arrowhead_at_start': False, 'arrowhead_at_end': False, 'font': MAIN_FONT,
            'labeled': True, 'style': 'dashed'
        }, CHECKING_EDGE: {
            'shape_name': 'cubic', 'color_id': 'accent1tr', 'pull': 0.4, 'visible': True,
            'arrowhead_at_start': False, 'arrowhead_at_end': True, 'font': MAIN_FONT,
            'labeled': False, 'style': 'dashed'
        }, ATTRIBUTE_EDGE: {
            'shape_name': 'linear', 'color_id': 'content1', 'pull': .50, 'visible': True,
            'arrowhead_at_start': False, 'arrowhead_at_end': False, 'labeled': False
        }, COMMENT_EDGE: {
            'shape_name': 'linear', 'color_id': 'accent4', 'pull': 0, 'visible': True,
            'arrowhead_at_start': True, 'arrowhead_at_end': False, 'labeled': False
        }, CONSTITUENT_EDGE: {
            'shape_name': 'shaped_cubic', 'color_id': 'content1', 'pull': .24, 'visible': True,
            'arrowhead_at_start': False, 'arrowhead_at_end': False, 'labeled': False
        }, FEATURE_EDGE: {
            'shape_name': 'cubic', 'color_id': 'accent2tr', 'pull': .40, 'visible': True,
            'arrowhead_at_start': False, 'arrowhead_at_end': False, 'labeled': False
        }, GLOSS_EDGE: {
            'shape_name': 'cubic', 'color_id': 'accent5', 'pull': .40, 'visible': True,
            'arrowhead_at_start': False, 'arrowhead_at_end': False, 'labeled': False
        }, PROPERTY_EDGE: {
            'shape_name': 'linear', 'color_id': 'accent5', 'pull': .40, 'visible': True,
            'arrowhead_at_start': False, 'arrowhead_at_end': False, 'labeled': False
        }

    }, 'plain': {
        ARROW: {
            'shape_name': 'linear', 'color_id': 'accent4', 'pull': 0, 'visible': True,
            'arrowhead_at_start': False, 'arrowhead_at_end': True, 'font': MAIN_FONT,
            'labeled': True
        }, DIVIDER: {
            'shape_name': 'linear', 'color_id': 'accent6', 'pull': 0, 'visible': True,
            'arrowhead_at_start': False, 'arrowhead_at_end': False, 'font': MAIN_FONT,
            'labeled': True, 'style': 'dashed'
        }, CHECKING_EDGE: {
            'shape_name': 'cubic', 'color_id': 'accent1tr', 'pull': 0.4, 'visible': True,
            'arrowhead_at_start': False, 'arrowhead_at_end': False, 'font': MAIN_FONT,
            'labeled': False, 'style': 'dashed'
        }, ATTRIBUTE_EDGE: {
            'shape_name': 'linear', 'color_id': 'content1', 'pull': .50, 'visible': True,
            'arrowhead_at_start': False, 'arrowhead_at_end': False, 'labeled': False
        }, COMMENT_EDGE: {
            'shape_name': 'linear', 'color_id': 'accent4', 'pull': 0, 'visible': True,
            'arrowhead_at_start': True, 'arrowhead_at_end': False, 'labeled': False
        }, CONSTITUENT_EDGE: {
            'shape_name': 'linear', 'color_id': 'content1', 'pull': .24, 'visible': True,
            'arrowhead_at_start': False, 'arrowhead_at_end': False, 'labeled': False
        }, FEATURE_EDGE: {
            'shape_name': 'linear', 'color_id': 'accent2tr', 'pull': .40, 'visible': True,
            'arrowhead_at_start': False, 'arrowhead_at_end': False, 'labeled': False
        }, GLOSS_EDGE: {
            'shape_name': 'linear', 'color_id': 'accent5', 'pull': .40, 'visible': True,
            'arrowhead_at_start': False, 'arrowhead_at_end': False, 'labeled': False
        }, PROPERTY_EDGE: {
            'shape_name': 'linear', 'color_id': 'accent5', 'pull': .40, 'visible': True,
            'arrowhead_at_start': False, 'arrowhead_at_end': False, 'labeled': False
        }, ABSTRACT_EDGE: {
            'shape_name': 'linear', 'color': 'content1', 'pull': .40, 'visible': True,
            'arrowhead_at_start': False, 'arrowhead_at_end': False, 'labeled': False,
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