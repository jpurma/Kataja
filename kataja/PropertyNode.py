#############################################################################
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
#############################################################################

from kataja.Controller import colors, qt_prefs
from kataja.Node import Node
from kataja.globals import PROPERTY_EDGE

# ctrl = Controller object, gives accessa to other modules

class PropertyNode(Node):
    width = 20
    height = 20
    default_edge_type = PROPERTY_EDGE
    saved_fields = ['label_font', 'color']
    saved_fields = list(set(Node.saved_fields + saved_fields))


    def __init__(self, property=None, host=None):
        Node.__init__(self, syntactic_object=property, host=host)
        self.level = 1
        self.save_key = 'PN%s' % id(self)
        intern(self.save_key)
        self.label_font = qt_prefs.feature_small
        self.color = colors.text
        self.update_identity()
