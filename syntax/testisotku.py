class Noob:
    def __init__(self):
        pass

    def testi(self, kw):
        print kw['hei']


a = {'hei': 'jukka', 'goo': 'goo'}

n = Noob()

n.testi(a)
