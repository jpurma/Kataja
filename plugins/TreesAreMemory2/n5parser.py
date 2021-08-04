
class Tree:
    def __init__(self):
        self.head = None
        self.last = None

    def __str__(self):
        return self.head

    def add(self,  word):
        self.last = word
        self.head = word
        return self

    def spec(self, word):
        self.head = f'{self.head}>{word}'
        self.last = word
        return self

    def comp(self, word):
        self.head = f'{self.head}<{word}'
        self.last = word
        return self

    def compX(self, word):
        self.head = f'{self.head}<={word}'
        self.last = word
        return self

t = Tree()
t.add('Pekka').spec('sanoi').comp('että').compX('se').comp('että').compX('teoria').spec('kumoutui').spec('kumoutui')

# Pekka>sanoi<että<se>että<teoria>kumoutui>kumoutui

print(t)

# [.sanoi Pekka [.sanoi sanoi [.että että [.kumoutui [.se se [.että että [.kumoutui teoria kumoutui]]] kumoutui]]]]

# [.sanoi Pekka>[.sanoi sanoi<[.että että<[.kumoutui [.se se<[.että että>[.kumoutui teoria< kumoutui<]]] kumoutui]]]]

# Mitä Pekka sanoi että kumoutui?

# Pekka sanoi, että [se, että teoria kumoutui] kumoutui.