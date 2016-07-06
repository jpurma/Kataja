import re
from Constituent import Constituent

Labels = {"V", "T", "C", "C*", "v", "v*", "Adj", "P", "P*", "D", "D*", "Perf", "N", 'Prt'}


def texify(line):
    temp1 = re.sub("_", "\_", line)
    temp4 = re.sub("'", "", temp1)
    temp5 = re.sub("\~", "$\sim$", temp4)
    line = temp5
    return line


def strikethrough(line):
    ctr = 0
    newline = str()
    while ctr < len(line):
        current = line[ctr]
        if current == "_":
            if line[ctr + 1] != " ":
                newline += "\st{"
                cont = True
                ctr += 1
                while cont:
                    chunkCur = line[ctr]
                    if chunkCur == " ":
                        newline += "}"
                        newline += chunkCur
                        cont = False
                    else:
                        newline += chunkCur
                    ctr += 1
            else:
                newline += current
                ctr += 1
        else:
            newline += current
            ctr += 1
    return newline


def remove_numbers(line):
    return re.sub(r'[0-9]', ' ', line)


class ProduceFile:

    def __init__(self, path_prefix=''):
        self.path_prefix = path_prefix
        self.F1 = open(self.path_prefix + "OutputFull.txt", 'w')
        self.F2 = open(self.path_prefix + "Output.txt", 'w')
        self.F3 = open(self.path_prefix + "TreeViewer.txt", 'w')
        self.F4 = open(self.path_prefix + "TexOutput.tex", 'w')
        tex_in = open("TexInput.tex", 'r')
        lines = tex_in.readlines()
        for line in lines:
            self.F4.write(line)
            if "begin{document" in line:
                break
        self.start_itemize = True

    def push(self, x, y, z):
        if isinstance(x, Constituent):
            fx = x.featureless_str()
        else:
            fx = x
        if isinstance(y, Constituent):
            fy = y.featureless_str()
        else:
            fy = y
        if isinstance(z, Constituent):
            fz = z.featureless_str()
        else:
            fz = z
        self.print_readable_output(fx, fy, fz)
        self.print_full_output(x, y, z)
        self.print_treeviewer_file(fx, fy, fz)
        self.print_tex_file(fx, fy, fz)

    def close(self):
        if self.F1:
            self.F1.close()
        if self.F2:
            self.F2.close()
        if self.F3:
            self.F3.close()
        if self.F4:
            self.F4.write("\\end{itemize}\n\n")
            self.F4.write("\n\n\\end{document}")
            self.F4.close()

    def print_treeviewer_file(self, x, y, z):
        if z:
            num, sent, numeration = x, y, z
            self.F3.write("\n%s %s\n" % (num, sent))
        else:
            description, data_orig = x, y
            data2 = str(data_orig)
            if "Label" in description:
                self.F3.write("%s\n" % data2)
            elif "Dephase" in description:
                self.F3.write("%s\n" % data2)
            elif "UnlabeledM" in description:
                self.F3.write("%s\n" % data2)
            elif "LbAfterMove" in description:
                self.F3.write("%s labels\n" % data2)
            elif "LbM" in description:
                self.F3.write("%s\n" % data2)

    def print_full_output(self, x, y, z):
        if z:
            num, sent, numeration = x, y, z
            self.F1.write("\n%s %s\n%s\n\n\n" % (num, sent, numeration))
        else:
            description, data2 = x, y
            data2 = str(data2)
            self.F1.write("%s\n%s\n\n" % (description, data2))
            if "Label" in description:
                descript = ""
                if "Head" in description:
                    descript = "Label from Head: " + data2
                elif "Move" in description:
                    descript = "Label via movement: " + data2
                elif "SharedFeats" in description:
                    descript = "Label via shared features: " + data2
                elif "Strengthened" in description:
                    descript = "Label (Checked Phi): " + data2
                elif "None" in description:
                    descript = "Unlabeled: " + data2
                self.F1.write("%s\n\n" % descript)
            elif "Unification" in description:
                self.F1.write("Unify Features: %s\n\n" % data2)

    def print_readable_output(self, x, y, z):

        if z:
            self.F2.write("\n%s %s\n%s\n\n\n" % (x, y, z))
        else:
            description, data_orig = x, y
            data2 = str(data_orig)
            if "Label" in description:
                if "Head" in description:
                    s = "Label from Head: "
                elif "Move" in description:
                    s = "Label via movement: "
                elif "SharedFeats" in description:
                    s = "Label via shared features: "
                elif "Strengthened" in description:
                    s = "Label (Checked Phi): "
                elif "None" in description:
                    s = "Unlabeled: "
                self.F2.write(s + data2 + "\n\n")
            elif "merge" in description:
                self.F2.write(data2 + "\n\n")
            elif "Dephase" in description:
                if " v" in description:
                    s = "Root movement (dephase): "
                elif "DeleteC" in description:
                    s = "Delete C (dephase): "
                self.F2.write(s + data2 + "\n\n")
            elif "Transfer" in description:
                self.F2.write("Transfer: %s\n\n" % data2)
            elif "UnlabeledM" in description:
                self.F2.write("Unlabeled merge: %s\n\n" % data2)
            elif "PassFs" in description:
                self.F2.write(data2 + "\n\n")
            elif "FeaturesPassed" in description:
                self.F2.write("Passed Features: %s\n\n" % data2)
            elif "CheckedFeatures" in description:
                self.F2.write("Checked Features: %s\n\n" % data2)
            elif "LbAfterMove" in description:
                self.F2.write("%s labels\n\n" % data2)
            elif "LbM" in description:
                self.F2.write("Labeled After Move: %s\n\n" % data2)
            elif "PhiPassing" in description:
                self.F2.write("Phi Passed from N to D\n\n")
            if "Push" in description:
                self.F2.write("Push: %s\n\n" % data2)
            elif "ClearStack" in description:
                stack = eval(data_orig)
                stack.reverse()
                self.F2.write("Clear Stack: \n\n")
                stack_ctr = 1
                for elem in stack:
                    print_elem = "%s POP: %s" % (stack_ctr, elem)
                    self.F2.write("%s\n\n" % print_elem)
                    stack_ctr += 1
            elif "Unification" in description:
                self.F2.write("Unify Features: %s\n\n" % data_orig)
            elif "SubStream" in description:
                self.F2.write("Substream\n\n")
            elif "MainStream" in description:
                self.F2.write("Main Stream\n\n")
            elif "Stack" in description:
                stack = eval(data_orig)
                stack.reverse()
                if "Transfer" in description:
                    self.F2.write("Stack after Transfer: \n\n")
                else:
                    self.F2.write("Stack: \n\n")
                stack_ctr = 1
                for elem in stack:
                    print_elem = "%s: %s" % (stack_ctr, elem)
                    self.F2.write("%s\n\n" % print_elem)

    def print_tex_file(self, x, y, z):
        descript = ""
        if z:
            if self.start_itemize:
                self.start_itemize = False
            else:
                self.F4.write("\\end{itemize}\n\n")
            num, sent, numeration = x, y, z
            self.F4.write("\\begin{example}\n %s\n%s\n\\end{example}\n\n\\begin{itemize}\n" % (
                sent, texify(str(numeration))))
        else:
            description, data_orig = x, y
            data2 = str(data_orig)
            data2 = re.sub("\~", "$\sim$", data2)

            if "Label" in description:
                if "Head" in description:
                    descript = "Label from Head: " + data2
                elif "Move" in description:
                    descript = "Label via movement: " + data2
                elif "SharedFeats" in description:
                    descript = "Label via shared features: " + data2
                elif "Strengthened" in description:
                    descript = "Label (Checked Phi): " + data2
                elif "None" in description:
                    descript = "Unlabeled: " + data2
                self.F4.write("\\item %s\n\n" % texify(descript))
            elif "merge" in description:
                self.F4.write("\\item %s\n\n" % texify(data_orig))
            elif "Dephase" in description:
                if " v" in description:
                    descript = "Root movement (dephase): " + data2
                elif "DeleteC" in description:
                    descript = "Delete C (dephase): " + data2
                self.F4.write("\\item %s\n\n" % texify(descript))
            elif "MRGOperations" in description:
                descript = "Number of merge Operations: " + data2
                self.F4.write("%s\n\n" % descript)
            elif "FTInheritanceOp" in description:
                descript = "Number of Feature Inheritance Operations: " + data2
                self.F4.write("%s\n\n" % descript)
            elif "FTCheckOp" in description:
                descript = "Number of Feature Checking Operations: " + data2
                self.F4.write("%s\n\n" % descript)
            elif "Transfer" in description:
                descript = "Transfer: " + data2
                self.F4.write("\\item %s\n\n" % texify(descript))
            elif "UnlabeledM" in description:
                descript = "Unlabeled merge: " + data2
                descript = strikethrough(descript)
                self.F4.write("\\item %s\n\n" % texify(descript))
            elif "PassFs" in description:
                descript = data_orig
                self.F4.write("\\item %s\n\n" % texify(descript))
            elif "FeaturesPassed" in description:
                descript = "Passed Features: " + data2
                descript = remove_numbers(descript)
                self.F4.write("\\item %s\n\n" % texify(descript))
            elif "CheckedFeatures" in description:
                descript = "Checked Features: " + data2
                descript = remove_numbers(descript)
                self.F4.write("\\item %s\n\n" % texify(descript))
            elif "LbAfterMove" in description:
                descript = data2 + " labels"
                self.F4.write("\\item %s\n\n" % texify(descript))
            elif "LbM" in description:
                descript = "Labeled After Move: " + data2
                self.F4.write("\\item %s\n\n" % texify(descript))
            elif "PhiPassing" in description:
                descript = "Phi Passed from N to D"
                self.F4.write("\\item %s\n\n" % texify(descript))
            if "Push" in description:
                descript = "Push: " + data2
                self.F4.write("\\item %s\n\n" % texify(descript))
            elif "ClearStack" in description:
                stack = eval(data_orig)
                stack.reverse()
                descript = "Clear Stack: "
                self.F4.write("\\item %s\n\n" % descript)
                stack_ctr = 1
                for elem in stack:
                    print("Elem", elem)
                    print_elem = str(stack_ctr) + " POP: " + elem
                    tex_elem = texify(print_elem)
                    self.F4.write("\\item %s\n\n" % tex_elem)
                    stack_ctr += 1
            elif "Unification" in description:
                descript = "Unify Features: " + data2
                self.F4.write("\\item %s\n\n" % texify(descript))
            elif "SubStream" in description:
                self.F4.write("\\item Substream\n\n")
            elif "MainStream" in description:
                self.F4.write("\\item Main Stream\n\n")
            elif "Stack" in description:
                stack = eval(data_orig)
                stack.reverse()
                if "Transfer" in description:
                    descript = "Stack after Transfer: "
                else:
                    descript = "Stack: "
                self.F4.write("\\item %s\n\n" % descript)
                stack_ctr = 1
                for elem in stack:
                    print_elem = str(stack_ctr) + ": " + elem
                    self.F4.write("\\item %s\n\n" % texify(print_elem))
                    stack_ctr += 1
            elif "Crash" in description:
                if "Unchecked Feature" in description:
                    descript = "Crash (Unchecked Feature): " + data2
                    self.F4.write("\\item %s\n\n" % texify(descript))
                elif "Unlabeled" in description:
                    descript = "Crash (Unlabeled): " + data2
                    self.F4.write("\\item %s\n\n" % texify(descript))
