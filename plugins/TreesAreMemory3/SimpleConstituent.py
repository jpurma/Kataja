
class SimpleConstituent:

    def __init__(self, label='', features=None):
        self.label = label
        self.features = list(features) if features else []
        self.uid = id(self)

    def __str__(self):
        return self.label
        #return f'{self.label}: {self.features}'

    def __repr__(self):
        return str(self)

    def copy(self):
        const = SimpleConstituent(label=self.label, features=[f.copy() for f in self.features])
        for f in const.features:
            f.host = const
        return const
