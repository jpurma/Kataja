import os, csv, itertools
# Fully automated version from semi-automated path analyser in Evelina Leivada's dissertation 
# (2015, The nature and limits of variation across languages and pathologies 
# (Doctoral dissertation, Universitat de Barcelona).
# http://www.evelina.biolinguistics.eu/dissertation.pdf 
# The analyser is just few lines, 'scan_child_path'-method, rest of the code is to 
# read a csv file with the data of 63 binary parameters within the DP domain 
# (Longobardi & Guardiano 2009: 1697), build networks of dependant parameters defined there and
# finally build all of the possible routes to each parameter, 'setability paths' in Leivada's 
# Appendix S2.


class Path:
    def __init__(self, sign, number, parent):
        self.sign = sign
        try:
            self.number = int(number)
        except ValueError:
            self.number = number
        self.parent = parent

    def __repr__(self):
        if self.parent:
            return '%s%s(%s)' % (self.number, self.sign, self.parent)
        else:
            return '%s%s' % (self.number, self.sign)

class AndPath:
    def __init__(self, paths):
        self.paths = paths

    def __repr__(self):
        return 'And%s' % self.paths

class OrPath:
    def __init__(self, paths):
        self.paths = paths

    def __repr__(self):
        return 'Or%s' % self.paths


class Parameter:

    def __init__(self, i, name, dependency_string, values):
        self.index = int(i)
        self.name = name
        self.dependency_string = dependency_string.strip()
        self.values = values
        self.plus_path = []
        self.minus_path = [] 
        self.parent = None
        self.paths_to_test = [] 

    def __repr__(self):
        return 'P%s' % self.index

    def build_paths(self):
        """ This parses path definitions like 
        "+7, -22, ( -25, +26 )  or +27, +42 or +45 or -50" 
        into Path, AndPath and OrPath -trees.
        """  
        words = self.dependency_string.split()
        stack = []

        def parse(command, words, stack=None):
            def _flush(cmd, my_stack):
                if not my_stack:
                    return
                if cmd == 'and':
                    return AndPath(my_stack)
                elif cmd == 'or':
                    return OrPath(my_stack)
                elif cmd == '':
                    return my_stack[0]

            if not stack:
                stack = []
            package = None
            and_suffix = False
            while words:
                item = words.pop(0)
                if item.startswith('('):                    
                    item = item[1:]
                    words, package = parse('', [item] + words)
                    stack.append(package)
                if item == ')':
                    package = _flush(command, stack)
                    return words, package
                if item.endswith(','):
                    item = item[:-1]
                    and_suffix = True
                if item.startswith(('+','-')):                
                    sign = item[0]
                    number = item[1:]
                    stack.append(Path(sign, number, None))
                elif item == 'or':
                    if not command:
                        command = 'or'
                    elif command == 'and':
                        prev = stack.pop()
                        words, package = parse('or', words, [prev])
                        stack.append(package)                        
                if and_suffix: # AND has priority over OR 
                    # a OR b OR c AND d OR e  = (a OR B OR c) AND (d OR e)
                    # so if previous command was OR, fold it up and use the package  
                    and_suffix = False
                    if not command:
                        command = 'and'
                    elif command == 'or': 
                        package = _flush(command, stack)                        
                        stack = [package]
                        return parse('and', words, stack)
            package = _flush(command, stack)
            return words, package

        words, package = parse('', words)
        self.parent = package

    def connect_paths(self, params):
        """ Path objects in Path, AndPath and OrPath -trees are replaced with actual Parameters,
        connecting Parameters to each other or to AndPath or OrPath -nodes. """
        def connect(child, parent):
            if isinstance(parent, Path):
                if isinstance(parent.number, int):
                    if parent.sign == '+':
                        pp = params[parent.number].plus_path
                        if child not in pp:
                            pp.append(child)
                    elif parent.sign == '-':
                        pp = params[parent.number].minus_path
                        if child not in pp:
                            pp.append(child)
                    return params[parent.number]
                else:
                    return parent.number
            elif isinstance(parent, (AndPath, OrPath)):
                new_paths = []
                for item in parent.paths:
                    new_paths.append(connect(parent, item))
                parent.paths = new_paths

                return parent
        self.parent = connect(self, self.parent)


def recursive_build(my_path, node):
    my_path.append(node)
    if isinstance(node, Parameter):
        if not node.parent:
            return my_path
        my_path = recursive_build(my_path, node.parent)
        return my_path
    elif isinstance(node, OrPath):
        divide = []
        for item in node.paths:
            res = recursive_build([], item)
            if res and isinstance(res[0], list):
                divide += res
            elif res:
                divide.append(res)
        my_path = [my_path.copy() + new_p for new_p in divide]
        return my_path
    elif isinstance(node, AndPath):
        new_paths = []
        parts = []
        for item in node.paths:
            res = recursive_build([], item)
            if res and isinstance(res[0], list):
                parts.append(res)
            else:
                parts.append([res])
        path_endings = itertools.product(*parts)
        for tupleitem in path_endings:
            new_path = my_path.copy()            
            for item in tupleitem:
                if isinstance(item, list):
                    new_path += item
                else:
                    new_path.append(item)
            new_paths.append(new_path)
        return new_paths


def turn_to_valued_paths(paths, params):
    valpaths = []
    for path in paths:
        revpath = list(reversed(path))
        valpath = []
        parent_node = None
        for node in revpath:
            if parent_node:
                if node in parent_node.plus_path:
                    valpath.append((parent_node.index, '+'))
                elif node in parent_node.minus_path:
                    valpath.append((parent_node.index, '-'))
            if isinstance(node, Parameter):
                parent_node = node
        valpaths.append(list(reversed(valpath)))
    valpaths.sort(key=len)
    return valpaths


def scan_child_path(langdata, path_tuples):
    for key, value in path_tuples:
        if isinstance(key, str) and key.startswith('~'):
            if value == langdata[int(key[1:]) - 1]:
                return False
        elif value != langdata[int(key) - 1]:
            return False
    return True


#### Preparing data 

file = open('parameterdata.csv')
header, *reader = list(csv.reader(file, delimiter=';'))
lang_names = header[3:]
lang_data = [[] for x in lang_names]
params = [None] # spend the index 0, so parameter numbering and their indexes match 

for n, name, dependency_string, *row in reader:
    new_param = Parameter(n, name, dependency_string, row)
    params.append(new_param)
    for i, value in enumerate(row):
        lang_data[i].append(value)

lang_dict = dict(zip(lang_names, lang_data))

### Parsing dependency strings ("+7, -22, ( -25, +26 )  or +27, +42 or +45 or -50" in csv)
for param in params:
    if param and param.dependency_string and not param.parent:
        param.build_paths()
        param.connect_paths(params)

## Figuring all possible paths to set each parameter
for param in params:
    if param: 
        tree = recursive_build([], param)
        if tree and isinstance(tree[0], list):
            param.paths_to_test = turn_to_valued_paths(tree, params)

# Actual testing
def test_parameter(param):
    print(' ****************** Param %s : %s *******************' % (param.index, param.name))
    s = []
    for lang_name in lang_names:
        s.append(lang_name.center(5))
    print(''.join(s))
    for path in param.paths_to_test:        
        s = []
        for lang_name in lang_names:
            lang = lang_dict[lang_name]
            if scan_child_path(lang, path):
                s.append('  1  ')
            else:
                s.append('  .  ')
        print(''.join(s))

test_only = 0
if test_only:
    test_parameter(params[test_only])
else:
    for param in params:
        if param and param.paths_to_test: 
            if len(param.paths_to_test) > 20:
                continue
            test_parameter(param)

