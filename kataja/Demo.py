# -*- coding: UTF-8 -*-
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

from PyQt5 import QtCore

t1 = """
 *** Visualizing Biolinguistics (C) Jukka Purma ***
  ** Doctoral Seminar presentation 17.2. 2011   **
   *                                            *
Ready.








""".upper()

t2 = """


 Biolinguistics = 
 
    finding minimal system for 
 human-like language capability 
 (syntax, learning syntax, universal grammar)


"""

t3 = """
        LEXICON 
     ("cat", [kissa])  
           /\  
phonology /  \ semantics 
"cat"    /    \   [kissa] =... 
=...    /syntax\    
       /________\    
"""

t4 = """

Syntactic analysis is separate from
semantic analysis:

1.          Scissors are on the table.
   syntax      pl    pl 
   semantics   sg    sg 

2.          Viisi tuoppia kaatui.
   syntax           sg     sg
   semantics        pl     pl

"""

t5 = """
       *************************
     **  Visualization testbed  **
       ********* 1/8 ***********
       
   - PyQt4 = Python + Qt
   - Animated changes between states (always)
   - Skins / themes
   - Radial menus
   - Three views: 
        - Classic tree
        - Linearized view
        - Elastic
   - 'Dumb syntax': Merge operation, reading structures from file
   - Modular: syntax engines, visualizations, settings
   - Presentation mode (this!)
"""

ss = QtCore.QRectF(0, 0, 640, 400)
big = QtCore.QRectF(0, 0, 1024, 768)
