Stackless shifter
-----------------

This plugin is a proof of concept for constituent trees that are created bottom-up, by merging simple leaves on top 
of the tree (External Merge, EM) and remerging already merged parts of the tree on top of the tree (Internal Merge, IM).

The point is that IM makes it possible to implement shift-reduce-parsing without keeping the unfinished structures in a 
separate memory or a stack. The tree itself is its own stack and 'reduce' action seeks the reducible element from down 
the tree, essentially folding its previous trunk or spine as its branches.  

The resulting tree is not tree in a graph-theoretical sense, it is just an acyclic graph where many nodes have 
multiple parents. For this reason the standard tree drawing algorithms and -libraries generally cannot handle them.   

The first goal of stackless shifter is to prove that structures with deep branches can be built with application of EM 
and IM on topmost node of the tree. For this it loads a sample of treebank trees, which then are turned into binary 
trees (Chomsky normal form). These are loaded from file sentences.txt in format familiar from LaTeX Qtree-package. 
'Derivation step 1' of each tree in Kataja is the tree built from this bracket tree representation. Derivation step 2 is
the tree as rebuilt with application of IM and EM, and steps from 3 onwards show how the bottom-up, left-first building 
proceeds.

One goal of stackless building is to argue against a common objection against bottom-up parsing, where the structures
are seen as incomplete and thus inactive for semantic processing until they are merged from stack into the main 
structure. By immediately merging all elements into one large structure, each element's possible semantic interpretation
becomes gradual business: it has to take part in many intermediate steps before it can end up in its final position.
 
There is much more movement (IM) in stackless building than generally assumed in other minimalist models, and instead
 of requiring a surface justification for each assumed move, there is one structural hypothesis: element is merged 
 into structure first time it is met, and all movement is the elements' climb back into positions where the structure
  can be spelled out in the same order in which it was received. 
  
The second goal of stackless shifter is to recreate some of the standard minimalist/GB structures where movement is 
assumed.

A typical finite clause has 
