import kataja.globals as g
import plugins.FreeDrawing.OverlayButtons as OB
import plugins.FreeDrawing.TouchAreas as TA
from kataja.SavedField import SavedField
from kataja.parser.INodes import as_html, extract_triangle, join_lines
from plugins.FreeDrawing.ConstituentNodeEditEmbed import ConstituentNodeEditEmbed
from kataja.saved.movables.nodes.ConstituentNode import ConstituentNode
from kataja.singletons import classes, ctrl


class EditableConstituentNode(ConstituentNode):
    allowed_child_types = [g.CONSTITUENT_NODE, g.FEATURE_NODE, g.GLOSS_NODE, g.COMMENT_NODE]

    # Touch areas are UI elements that scale with the trees: they can be
    # temporary shapes suggesting to drag or click here to create the
    # suggested shape.

    # touch_areas_when_dragging and touch_areas_when_selected are lists of strings, where strings
    # are names of classes found in TouchArea. There are ways for plugins to inject new
    # TouchAreas.
    #
    # TouchAreas have classmethods 'select_condition' and 'drop_condition' which are used to
    # check if this is an appropriate toucharea to draw for given node or edge.
    # format.

    touch_areas_when_dragging = ConstituentNode.touch_areas_when_selected + \
                                [TA.LeftAddTop, TA.LeftAddSibling, TA.RightAddSibling, TA.AddBelowTouchArea]
    touch_areas_when_selected = ConstituentNode.touch_areas_when_selected + \
                                [TA.LeftAddTop, TA.RightAddTop, TA.MergeToTop, TA.LeftAddInnerSibling,
                                 TA.RightAddInnerSibling,
                                 TA.LeftAddUnaryChild, TA.RightAddUnaryChild, TA.LeftAddLeafSibling,
                                 TA.RightAddLeafSibling]

    buttons_when_selected = ConstituentNode.buttons_when_selected + \
                            [OB.RemoveMergerButton, OB.RemoveNodeButton, OB.RotateButton]

    embed_edit = ConstituentNodeEditEmbed
    quick_editable = True

    def __init__(self, label, *args, **kwargs):
        super().__init__(label, *args, **kwargs)
        self.heads = []
        self.syntactic_object = classes.Constituent(label)

    def label_as_editable_html(self):
        """ This is used to build the html when quickediting a label. It should reduce the label
        into just one field value that is allowed to be edited, in constituentnode this is
        either label or synobj's label. This can be overridden in syntactic object by having
        'label_as_editable_html' -method there. The method returns a tuple,
          (field_name, setter, html).
        :return:
        """
        label_text_mode = self.label_text_mode
        if (label_text_mode == g.NODE_LABELS or label_text_mode == g.NODE_LABELS_FOR_LEAVES) and self.label:
            return 'node label', as_html(self.label)
        return 'node label', ''

    def parse_edited_label(self, label_name, value):
        action = None
        if label_name == 'node label':
            action = ctrl.ui.get_action('set_label')
        elif label_name == 'index':
            action = ctrl.ui.get_action('set_index')
        if action:
            action.run_command(self.uid, value)

    def load_values_from_parsernode(self, parsernode):
        """ Update constituentnode with values from parsernode """

        def remove_dot_label(inode, row_n):
            for i, part in enumerate(list(inode.parts)):
                if isinstance(part, str):
                    if part.startswith('.'):
                        inode.parts[i] = part[1:]
                    return True
                else:
                    return remove_dot_label(part, row_n)

        extract_triangle(self.label, remove_from_original=True)

        if parsernode.index:
            self.index = parsernode.index
        rows = parsernode.label_rows

        # Remove dotlabel
        for i, row in enumerate(list(rows)):
            if isinstance(row, str):
                if row.startswith('.'):
                    rows[i] = row[1:]
                break
            stop = remove_dot_label(row, i)
            if stop:
                break
        self.label = join_lines(rows)
        if self.index:
            base = as_html(self.label)
            if base.strip().startswith('t<sub>'):
                self.is_trace = True

    # Conditions ##########################
    # These are called from templates with getattr, and may appear unused for IDE's analysis.
    # Check their real usage with string search before removing these.

    def inner_add_sibling(self):
        """ Node has child and it is not unary child. There are no other reasons preventing
        adding siblings
        :return: bool
        """
        return self.get_children() and not self.is_unary()

    def has_one_child(self):
        return len(self.get_children()) == 1

    def is_unnecessary_merger(self):
        """ This merge can be removed, if it has only one child
        :return:
        """
        return len(self.get_children()) == 1

    def get_heads(self):
        return self.heads

    def set_heads(self, head):
        """ Set projecting head to be Node, list of Nodes or empty. Notice that this doesn't
        affect syntactic objects.
        :param head:
        :return:
        """
        if isinstance(head, list):
            self.heads = list(head)
        elif isinstance(head, ConstituentNode):
            self.heads = [head]
        elif not head:
            self.heads = []
        else:
            raise ValueError

    def rotate_children(self):
        self.edges_down = list(reversed(self.edges_down))

    heads = SavedField("heads")
