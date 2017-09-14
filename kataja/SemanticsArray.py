
from kataja.singletons import ctrl, classes, qt_prefs
from kataja.SemanticsItem import SemanticsItem


class SemanticsArray:

    def __init__(self, sm, array_id, model, array_type, x=0, y=0):
        print(f'creating new array: array_id: {array_id}, model:{model}, array_type:{array_type}')
        self.array_id = array_id
        self.array_type = array_type
        self.array = []
        self.x = x
        self.y = y
        for label in model:
            item = SemanticsItem(label, array_id, sm.colors[label], x, y)
            self.array.append(item)
            y += item.label_rect().height()

    def total_size(self):
        h = 0
        w = 0
        for item in self.array:
            r = item.label_rect()
            if r.width() > w:
                w = r.width()
            h += r.height()
        return w, h

    def move_to(self, x, y):
        for item in self.array:
            item.prepareGeometryChange()
            item.setPos(x, y)
            y += item.label_rect().height()
            item.update()
