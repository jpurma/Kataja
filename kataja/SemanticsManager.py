
import itertools

from collections import defaultdict

from kataja.Projection import Projection
from kataja.singletons import ctrl
from kataja.globals import CONSTITUENT_NODE
from kataja.utils import time_me


class SemanticsManager:

    def __init__(self, forest):
        self.forest = forest
        self.clause = self.forest.syntax.clause_hierarchy
        self.dp = self.forest.syntax.dp_hierarchy
        self.clause_graphics = []
        self.dp_graphics = []

