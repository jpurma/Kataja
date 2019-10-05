import os


# Analyser from Evelina Leivada (2015). The nature and limits of variation across languages and pathologies (Doctoral dissertation, Universitat de Barcelona).
# http://www.evelina.biolinguistics.eu/dissertation.pdf 
# This is functionally equivalent rewrite of both analysers from the Java sources in 
# dissertation's appendix.
# Since I don't have the datafiles in same format (1 file per language), this is just an exercise
# to see what the code aims to do. There is a working version langAnalyserTrue.py, which takes
# data from a single .csv file containing all of the paths and feature values. 
# It aims to fully automate what Leivada semi-automated here.    

class ChildPath:
    def __init__(self, langdata, path_data):
        self.langdata = langdata
        self.dependency_table = dict(path_data)

    def scan_child_path(self):
        for key, entry in self.dependency_table.items():
            if isinstance(key, str) and key.startswith('~'):
                if entry == self.langdata[int(key[1:]) - 1]:
                    return False
            elif entry != self.langdata[int(key) - 1]:
                return False
        return True


os.chdir('Input_Language_Data')

list_of_files = [x for x in os.listdir(path='.') if x.endswith('.txt')]
list_of_files.sort()  # listdir returns files in random order, but results should be comparable
for file_name in list_of_files:
    lines = open(file_name).readlines()

    # =============== EDITABLE CODE SECTION ================ 
    # The realization of each path depends on the status of the relevant input nodes 
    # For each dependency, specify first the number of the input node(s) and 
    # then the state(s), as shown in the following example

    paths = [[(7, '+')],  # path 0
             [(5, '-'), (2, '+'), (1, '+')],  # path 1
             [(6, '-'), (5, '+'), (2, '+'), (1, '+')]]  # path 2

    # Example 2 has following:
    # paths = [
    #   [('~18', '+'), (5, '-'), (17, '-'), (7, '+'), (8, '+'), (6, '+'), (1, '+'), (2, '+')],
    #   [('~18', '+'), (6, '+'), (5, '+'), (1, '+'), (2, '+'), (8, '+'), (17, '-'), (2, '+')]
    # ]
    # =========== END OF EDITABLE CODE SECTION ============= 
    print('Language ', file_name[:-4])  # snip .txt from the end
    for i, path_data in enumerate(paths):
        path = ChildPath(lines, path_data)
        print('Path[%s]={ %s }\t' % (i, path.scan_child_path()), )
    print('')
