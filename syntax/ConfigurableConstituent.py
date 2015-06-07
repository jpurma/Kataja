# coding=utf-8
""" ConfigurableConstituent tries to be theory-editable constituent, whose behaviour can be adjusted
in very specific manner. Configuration is stored in UG-instance.config -dict and can be changed from outside. """

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

from syntax.BaseConstituent import BaseConstituent


class ConfigurableConstituent(BaseConstituent):
    """ ConfigurableConstituent is a constituent whose behaviour is adjusted by properties of UG.
    It inherits mostly everything from BaseConstituent, and overrides those methods that can be
    configured.
    """
    short_name = "CC"

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #
