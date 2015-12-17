from PyQt5 import QtWidgets, QtCore, QtGui

import kataja.globals as g
from kataja.parser.latex_to_unicode import latex_to_unicode
from kataja.singletons import qt_prefs, ctrl
from kataja.ui.panels.UIPanel import UIPanel
from kataja.ui.panels.field_utils import box_row

__author__ = 'purma'

table_names = ['common', 'greek', 'arrows', 'more arrows', 'latin', 'combining', 'rest', 'cyrchar',
               'ding', 'ElsevierGlyph', 'mathbb', 'mathbf', 'mathbit', 'mathfrak', 'mathmit',
               'mathscr', 'mathsfbfsl', 'mathsfbf', 'mathsfsl', 'mathsf', 'mathslbb', 'mathsl',
               'mathtt']

table_dict = {'common': 'common', 'greek': 'greek alphabet', 'latin': 'extended latin',
              'combining': 'combining diacritics', 'arrows': 'arrows',
              'more arrows': 'more arrows etc.', 'rest': 'miscallenous symbols',
              'cyrchar': 'cyrillic', 'ding': 'dingbats', 'ElsevierGlyph': 'Elsevier Glyphs',
              'mathbb': 'mathbb', 'mathbf': 'mathbf', 'mathbit': 'mathbit', 'mathfrak': 'mathfrak',
              'mathmit': 'mathmit', 'mathscr': 'mathscr', 'mathsfbfsl': 'mathsfbfsl',
              'mathsfbf': 'mathsfbf', 'mathsfsl': 'mathsfsl', 'mathsf': 'mathsf',
              'mathslbb': 'mathslbb', 'mathsl': 'mathsl', 'mathtt': 'mathtt'}

common = ['alpha', 'beta', 'gamma', 'phi', 'theta', 'lambda', 'tau', 'leftarrow', 'rightarrow',
          'prec', 'preccurlyeq', 'succ', 'succcurlyeq', 'oplus', 'surd', 'subset', 'subseteq',
          'supset', 'supseteq']

greek_letters = ['Alpha', 'alpha', 'Beta', 'beta', 'Gamma', 'gamma', 'Delta', 'delta', 'Epsilon',
                 'epsilon', 'Zeta', 'zeta', 'Eta', 'eta', 'Theta', 'theta', 'Iota', 'iota', 'Kappa',
                 'kappa', 'Lambda', 'lambda', 'Mu', 'mu', 'Nu', 'nu', 'Xi', 'xi', 'Omicron',
                 'omicron', 'Pi', 'pi', 'Rho', 'rho', 'Sigma', 'sigma', 'Tau', 'tau', 'Upsilon',
                 'upsilon', 'Phi', 'phi', 'Chi', 'chi', 'Psi', 'psi', 'Omega', 'omega',
                 "'{$\\alpha$}", "'{A}", "'{E}", "'{H}", "'{o}", "'{}O", "'{}{I}", 'Digamma',
                 'ElsevierGlyph{2129}', 'Koppa', 'Pisymbol{ppi022}{87}', 'Sampi', 'Stigma',
                 'acute{\\ddot{\\iota}}', 'acute{\\ddot{\\upsilon}}', 'acute{\\epsilon}',
                 'acute{\\eta}', 'acute{\\iota}', 'acute{\\omega}', 'acute{\\upsilon}',
                 'backepsilon', 'ddot{\\iota}', 'ddot{\\upsilon}', 'digamma', "mathrm{'Y}",
                 "mathrm{'\\Omega}", 'mathrm{\\ddot{I}}', 'mathrm{\\ddot{Y}}', 'textTheta',
                 'texttheta', 'textvartheta', 'varkappa', 'varphi', 'varpi', 'varrho', 'varsigma']

arrows = ['leftarrow', 'rightarrow', 'uparrow', 'downarrow', 'nearrow', 'nwarrow', 'searrow',
          'swarrow', 'leftrightarrow', 'updownarrow', 'leftleftarrows', 'leftrightarrows',
          'rightrightarrows', 'rightleftarrows', 'upuparrows', 'downdownarrows', 'circlearrowleft',
          'circlearrowright', 'arrowwaveright', 'curvearrowleft', 'curvearrowright',
          'hookleftarrow', 'hookrightarrow', 'langle', 'rangle', 'lbrace', 'rbrace',
          'longleftarrow', 'longrightarrow', 'longleftrightarrow', 'openbracketleft',
          'openbracketright', 'rightsquigarrow', 'twoheadleftarrow', 'twoheadrightarrow']

more_arrows = ['Angle', 'DownArrowBar', 'DownArrowUpArrow', 'DownLeftRightVector',
               'DownLeftTeeVector', 'DownLeftVectorBar', 'DownRightTeeVector', 'DownRightVectorBar',
               'Downarrow', 'Elolarr', 'Elorarr', 'Elroang', 'ElsevierGlyph{21B3}',
               'ElsevierGlyph{300A}', 'ElsevierGlyph{300B}', 'ElsevierGlyph{3018}',
               'ElsevierGlyph{3019}', 'ElsevierGlyph{E20A}', 'ElsevierGlyph{E20B}',
               'ElsevierGlyph{E20C}', 'ElsevierGlyph{E20D}', 'ElsevierGlyph{E20E}',
               'ElsevierGlyph{E20F}', 'ElsevierGlyph{E210}', 'ElsevierGlyph{E211}',
               'ElsevierGlyph{E212}', 'ElsevierGlyph{E214}', 'ElsevierGlyph{E215}',
               'ElsevierGlyph{E219}', 'ElsevierGlyph{E21A}', 'ElsevierGlyph{E21C}',
               'ElsevierGlyph{E21D}', 'ElsevierGlyph{E25C}', 'ElsevierGlyph{E25D}',
               'ElsevierGlyph{E25E}', 'ElsevierGlyph{E291}', 'ElzRlarr', 'Elzcirfl', 'Elzcirfr',
               'Elzdlcorn', 'Elzlpargt', 'ElzrLarr', 'Elzrarrx', 'Elzsblhr', 'Elzsbrhr', 'Elzsqfl',
               'Elzsqfnw', 'Elzsqfr', 'Elzsqfse', 'LeftDownTeeVector', 'LeftDownVectorBar',
               'LeftRightVector', 'LeftTeeVector', 'LeftTriangleBar', 'LeftUpDownVector',
               'LeftUpTeeVector', 'LeftUpVectorBar', 'LeftVectorBar', 'Leftarrow', 'Leftrightarrow',
               'Lleftarrow', 'Longleftarrow', 'Longleftrightarrow', 'Longrightarrow', 'Lsh',
               'NotLeftTriangleBar', 'NotRightTriangleBar', 'ReverseUpEquilibrium',
               'RightDownTeeVector', 'RightDownVectorBar', 'RightTeeVector', 'RightTriangleBar',
               'RightUpDownVector', 'RightUpTeeVector', 'RightUpVectorBar', 'RightVectorBar',
               'Rightarrow', 'RoundImplies', 'Rrightarrow', 'Rsh', 'UpArrowBar', 'UpEquilibrium',
               'Uparrow', 'Updownarrow', 'VDash', 'Vvdash', '\\kern-0.58em(', 'blacktriangleleft',
               'blacktriangleright', 'dashv', 'dblarrowupdown', 'diagup', 'ding{111}', 'ding{112}',
               'ding{113}', 'ding{114}', 'ding{119}', 'ding{212}', 'ding{216}', 'ding{217}',
               'ding{218}', 'ding{219}', 'ding{220}', 'ding{221}', 'ding{222}', 'ding{223}',
               'ding{224}', 'ding{225}', 'ding{226}', 'ding{227}', 'ding{228}', 'ding{229}',
               'ding{230}', 'ding{231}', 'ding{232}', 'ding{233}', 'ding{234}', 'ding{235}',
               'ding{236}', 'ding{237}', 'ding{238}', 'ding{239}', 'ding{241}', 'ding{242}',
               'ding{243}', 'ding{244}', 'ding{245}', 'ding{246}', 'ding{247}', 'ding{248}',
               'ding{249}', 'ding{250}', 'ding{251}', 'ding{252}', 'ding{253}', 'ding{254}',
               'ding{42}', 'ding{43}', 'ding{46}', 'ding{48}', 'downharpoonleft',
               'downharpoonright', 'downslopeellipsis', 'guillemotleft', 'guillemotright',
               'guilsinglleft', 'guilsinglright', 'lceil', 'leftarrowtail', 'leftharpoondown',
               'leftharpoonup', 'leftrightharpoons', 'leftrightsquigarrow', 'leftthreetimes',
               'lfloor', 'llcorner', 'lmoustache', 'longmapsto', 'looparrowleft', 'looparrowright',
               'lrcorner', 'ltimes', 'mapsto', 'nLeftarrow', 'nLeftrightarrow', 'nRightarrow',
               'nVDash', 'nleftarrow', 'nleftrightarrow', 'nrightarrow', 'rceil', 'rfloor',
               'rightangle', 'rightanglearc', 'rightarrowtail', 'rightharpoondown',
               'rightharpoonup', 'rightleftharpoons', 'rightthreetimes', 'rmoustache', 'rtimes',
               'sim\\joinrel\\leadsto', 'textcopyright', 'textquotedblleft', 'textquotedblright',
               'triangleleft', 'triangleright', 'ulcorner', 'upharpoonleft', 'upharpoonright',
               'upslopeellipsis', 'urcorner', 'vdash']


class SymbolPanel(UIPanel):
    """
        Panel for rapid testing of various UI elements that otherwise may be hidden behind
        complex screens or logic.
    """

    def __init__(self, name, key, default_position='right', parent=None, ui_manager=None,
                 folded=False):
        """
        All of the panel constructors follow the same format so that the construction can be
        automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        """
        UIPanel.__init__(self, name, key, default_position, parent, ui_manager, folded)
        inner = QtWidgets.QWidget()
        inner.preferred_size = QtCore.QSize(220, 130)
        inner.setMinimumSize(160, 130)
        inner.setMaximumSize(220, 400)

        layout = QtWidgets.QVBoxLayout()
        self.selector = QtWidgets.QComboBox()
        for item in table_names:
            self.selector.addItem(table_dict[item], item)
        self.selector.activated.connect(self.change_symbol_set)
        self.selector.setFocusPolicy(QtCore.Qt.TabFocus)
        layout.addWidget(self.selector)
        self.symlist = QtWidgets.QListWidget()
        self.symlist.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
         QtWidgets.QSizePolicy.Expanding)
        self.symlist.setSpacing(8)
        self.symlist.setMouseTracking(True)
        self.symlist.setFocusPolicy(QtCore.Qt.NoFocus)
        self.symlist.setViewMode(QtWidgets.QListWidget.IconMode)
        f = QtGui.QFont(qt_prefs.fonts[g.MAIN_FONT])
        f.setPointSize(f.pointSize() * 1.5)
        self.symlist.setFont(f)
        self.symlist.itemEntered.connect(self.item_entered)
        self.symlist.itemClicked.connect(self.item_clicked)
        layout.addWidget(self.symlist)
        hlayout = box_row(layout)
        self.info = QtWidgets.QLabel('')
        hlayout.addWidget(self.info)
        self.resize_grip = QtWidgets.QSizeGrip(self)
        self.resize_grip.hide()
        hlayout.addWidget(self.resize_grip, 0, QtCore.Qt.AlignRight)
        inner.setLayout(layout)
        self.tables = {}
        keys = list(latex_to_unicode.keys())
        for name in table_names:
            self.tables[name] = []
        keys.sort()
        for key in keys:
            char, description, table_key = latex_to_unicode[key]
            self.tables[table_key].append(key)
        self.tables['greek'] = greek_letters
        self.tables['arrows'] = arrows
        self.tables['more arrows'] = more_arrows
        self.tables['common'] = common
        # self.tables['arrows'] = arrows

        self.prepare_symbols('common')
        self.setWidget(inner)
        self.finish_init()

    def prepare_symbols(self, key):
        self.symlist.clear()
        # debug_dict = OrderedDict()
        for key in self.tables[key]:
            char, description, table = latex_to_unicode[key]
            # debug_dict[key] = (char, description)
            command = '\\' + key
            item = QtWidgets.QListWidgetItem(char)
            if ctrl.main.use_tooltips:
                item.setToolTip(command)
            item.setData(55, {'char': char, 'description': description, 'command': command})
            self.symlist.addItem(item)
            # pp = pprint.PrettyPrinter(indent=4)
            # pp.pprint(list(debug_dict.keys()))

    def item_entered(self, item):
        self.info.setText(item.data(55)['description'])
        self.info.update()

    def item_clicked(self, item):
        """ Clicked on a symbol: launch activity that tries to insert it to focused text field
        :param item:
        :return:
        """
        focus = ctrl.get_focus_object() or ctrl.main.graph_view.focusWidget()
        if focus and isinstance(focus, QtWidgets.QLineEdit):
            focus.insert(item.data(55)['char'])
            focus.setFocus()

    def change_symbol_set(self):
        key = self.selector.currentData()
        self.prepare_symbols(key)
