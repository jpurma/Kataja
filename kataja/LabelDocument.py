__author__ = 'purma'

from PyQt5 import QtGui, QtCore


class LabelDocument(QtGui.QTextDocument):
    """ This extends QTextDocument with ability to read INodes (intermediary nodes) and turn them
    into
    QTextDocuments RTF presentation """

    def __init__(self):
        QtGui.QTextDocument.__init__(self)
        self.lines = []
        self.new_lines = {}
        self.align = QtCore.Qt.AlignHCenter
        dto = self.defaultTextOption()
        dto.setWrapMode(QtGui.QTextOption.WrapAtWordBoundaryOrAnywhere)
        dto.setAlignment(self.align)
        self.setDefaultTextOption(dto)

    def clear(self):
        QtGui.QTextDocument.clear(self)
        self.clearUndoRedoStacks()

    def set_align(self, align):
        if self.align != align:
            dto = self.defaultTextOption()
            dto.setAlignment(align)
            self.setDefaultTextOption(dto)
            self.align = align

    def analyse(self):
        """ Debug QDocument parsing

        :return:
        """
        b = self.firstBlock()
        count = 0
        while b:
            cf = b.charFormat()
            dat = [b.blockFormat().alignment(), cf.fontCapitalization(), cf.fontFamily(),
                   cf.fontItalic(), cf.fontOverline(), cf.fontStrikeOut(), cf.fontWeight(),
                   cf.fontUnderline(), cf.verticalAlignment()]
            # print(dat)
            # print(int(dat[0]))
            for frange in b.textFormats():
                cf = frange.format
                ndat = [b.blockFormat().alignment(), cf.fontCapitalization(), cf.fontFamily(),
                        cf.fontItalic(), cf.fontOverline(), cf.fontStrikeOut(), cf.fontWeight(),
                        cf.fontUnderline(), cf.verticalAlignment()]
                # if ndat != dat:
                #     print('---- block %s ----' % count)
                #     print(b.text())
                #     print(frange.start, frange.length)
                #     if ndat[0] != dat[0]:
                #         print('align: %s ' % b.blockFormat().alignment())
                #     if ndat[1] != dat[1]:
                #         print('cap: ', cf.fontCapitalization())
                #     if ndat[2] != dat[2]:
                #         print('family: ', cf.fontFamily())
                #     if ndat[3] != dat[3]:
                #         print('italic: ', cf.fontItalic())
                #     if ndat[4] != dat[4]:
                #         print('overline: ', cf.fontOverline())
                #     if ndat[5] != dat[5]:
                #         print('strikeout: ', cf.fontStrikeOut())
                #     if ndat[6] != dat[6]:
                #         print('weight: ', cf.fontWeight())
                #     if ndat[7] != dat[7]:
                #         print('underline: ', cf.fontUnderline())
                #     if ndat[8] != dat[8]:
                #         print('vertical align: ', cf.verticalAlignment())
                dat = ndat
            # print(b.charFormat())
            # print(b.textFormats())

            if b == self.end():
                b = None
            else:
                b = b.next()
            count += 1

            # bc = self.blockCount()
            # for b_i in range(0, bc):
            #    print(b_i)
            #    b = self.findBlockByNumber(b_i)
