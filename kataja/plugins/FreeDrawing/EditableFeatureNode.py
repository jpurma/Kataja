
# coding=utf-8
# ############################################################################
#
# *** Kataja - Biolinguistic Visualization tool ***
#
# Copyright 2013 Jukka Purma
#
# This file is part of Kataja.
#
# Kataja is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Kataja is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Kataja.  If not, see <http://www.gnu.org/licenses/>.
#
# ############################################################################

from kataja.saved.movables.nodes.FeatureNode import FeatureNode
from kataja.singletons import classes



class EditableFeatureNode(FeatureNode):

    editable = {}
    viewable = {'name': dict(name='Name', prefill='X',
                             tooltip='Name of the feature, used as identifier',
                             syntactic=True),
                'value': dict(name='Value',
                              prefill='',
                              tooltip='Value given to this feature',
                              syntactic=True),
                'sign': dict(name='Sign',
                             prefill='',
                             tooltip='Sign of this feature, e.g. +, -, u, =...'),
                'family': dict(name='Family', prefill='',
                               tooltip='Several distinct features can be '
                                       'grouped under one family (e.g. '
                                       'phi-features)',
                               syntactic=True)
                }
    quick_editable = True

    def __init__(self, label='', sign='', value='', family='', forest=None):
        super().__init__(forest=forest)
        self.syntactic_object = classes.Feature(label=label, sign=sign, value=value, family=family)

        # implement color() to map one of the d['rainbow_%'] colors here.
        # Or if bw mode is on, then something else.

    def label_as_editable_html(self):
        """ This is used to build the html when quickediting a label. It should reduce the label
        into just one field value that is allowed to be edited, in constituentnode this is
        either label synobj's label. This can be overridden in syntactic object by having
        'label_as_editable_html' -method there. The method returns a tuple,
          (field_name, html).
        :return:
        """

        # Allow custom syntactic objects to override this
        if hasattr(self.syntactic_object, 'label_as_editable_html'):
            return self.syntactic_object.label_as_editable_html(self)

        return 'name', self.label_as_html()[0]

    def parse_quick_edit(self, text):
        """ This is an optional method for node to parse quick edit information into multiple
        fields. Usually nodes do without this: quickediting only changes one field at a time and
        interpretation is straightforward. E.g. features can have more complex parsing.
        :param text:
        :return:
        """
        parts = text.split(':')
        name = ''
        value = ''
        family = ''
        synobj = self.syntactic_object
        if len(parts) >= 3:
            name, value, family = parts
        elif len(parts) == 2:
            name, value = parts
        elif len(parts) == 1:
            name = parts[0]
        if len(name) > 1 and name.startswith('u') and name[1].isupper():
            name = name[1:]
        if name and name[0] in classes.Feature.simple_signs:
            synobj.sign = name[0]
            name = name[1:]
        synobj.name = name
        synobj.value = value
        synobj.family = family
