from kataja.SemanticsArray import SemanticsArray
from kataja.singletons import ctrl


class SemanticsManager:

    def __init__(self, forest):
        self.forest = forest
        self.models = []
        self.colors = {}
        self.all_items = []
        self.arrays = {}
        self.arrays_list = []
        self.total_height = 0
        self.total_length = 0
        self.visible = self.forest.settings.get('show_semantics')

    def hide(self):
        self.visible = False
        for item in self.all_items:
            item.hide()

    def show(self):
        self.visible = True
        self.update_position()
        for item in self.all_items:
            item.show()

    def prepare_semantics(self, syn_state):
        self.visible = self.forest.settings.get('show_semantics')
        self.models = syn_state.semantic_hierarchies
        self.colors = {}
        c = 1
        total_length = 0
        for model in self.models:
            for name in model:
                self.colors[name] = 'accent%s' % c
                c += 1
                total_length += 1
                if c > 8:
                    c = 1
        self.total_length = total_length

    def index_for_feature(self, fname):
        past = 0
        for model in self.models:
            if fname in model:
                return model.index(fname) + past, self.total_length
            past += len(model)
        return -1, self.total_length

    def add_to_array(self, node, label, array_id):
        """ Create new arrays when necessary
        :param node:
        :param label:
        :param array_id:
        :return:
        """
        if array_id not in self.arrays:
            model = None
            for i, model in enumerate(self.models):
                if label in model:
                    model_type = i
                    break
            if not model:
                return
            if self.arrays_list:
                last = self.arrays_list[0]
                x = last.x
                y = last.y - (last.total_size()[1] + 8)
            else:
                x, y = self.find_good_starting_position()
            array = SemanticsArray(self, array_id, model, model_type, x, y)
            self.arrays[array_id] = array
            self.all_items += array.array
            self.arrays_list.append(array)
            if self.visible:
                for item in array.array:
                    self.forest.add_to_scene(item)
        else:
            array = self.arrays[array_id]
        for item in array.array:
            if label == item.label:
                item.add_member(node)
            item.update_text()
        if self.visible:
            self.update_position()

    def update_position(self):
        if self.visible:
            x, y = self.find_good_starting_position()
            self.total_height = 0
            for array in self.arrays_list:
                indent = array.array_type * 8
                height = array.total_size()[1] + 8
                y -= height
                array.move_to(x + indent, y)
                self.total_height += height

    def find_good_starting_position(self):
        x = 0
        y = 0
        for node in self.forest.nodes.values():
            if node.locked_to_node:
                continue
            nx, ny = node.current_position
            cbr = node.future_children_bounding_rect()  # this is fast enough because it is cached
            nx += cbr.width() / 2
            if nx > x:
                x = nx
            if ny < y:
                y = ny
        return x + 40, y

    def clear(self):
        for item in self.all_items:
            self.forest.remove_from_scene(item, fade_out=False)
        self.all_items = []
        self.arrays = {}
        self.arrays_list = []


