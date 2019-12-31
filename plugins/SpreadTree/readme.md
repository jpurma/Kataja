AmbiTree
---------
Jukka Purma, 2019

This is a version of MultiTree where headedness of structure is not decided at merge, but when the merged element is raised at the next merge. Then the branch that has the feature justifying the merge is the one which is designated as head. 

It may seem like that this idea would be tampering with an already built structure, but it can be done without tampering if the headedness is seen as a derivative property from previous feature checks. Headedness of a given structure is determined by looking at which of its children can provide features justifying the next merge. 'This merge A|B + C used features from A, not from B, so this merge is A|C'.

If merge A|B+C can be justified with features from either A or C, then it becames important to handle situations where both are able to justify the merge and also the usual problem of what to do when there are many possible feature matches from a single constituent. Should they be ordered somehow?

Are there ways around having features in a fixed or language specific order? If one element can be merged into several places (if it can move) then these merges should be done in specific order to build the desired structure. Word order is the first candidate to give order, but if we rely solely on that, then there shouldn't be more than one matching feature.

One problem that immediately rises is the handling of a complex noun as an object: 'Pekka bought a switch box'. Here we would be eagerly building 'Pekka bought a switch', as 'a switch' would be a solid DP that can merge with 'bought'. We would need the parser to be so lazy that it would rather take the next word -- if it can be merged with current top -- than to start repairing the current structure. But that is not right either. If we would have 'the runners fell asleep', then 'runners' alone would be acceptable DP that could lazily take 'fell' and leave the initial 'the' hanging.

 A distinction can probably be made between '...DP V' and 'V DP...'-problem. Crudely it would be that arguments for predicate should be eagerly built, but merged into predicate only when they are finished, e.g. they have completed their internal merges. '...DP V'.
 
 The concept of 'the next element' seems to be important for these problems. What parser does at its current state would depend on merge potential of current state with the next element. And if we do eagerly merge into it (A) then we'd have [A X] and then [X [A X]]. Why wouldn't we have directly [X A] for external merge? If we would have [X A], then we wouldn't have the situation where X c-commands A. Let's see. If we want to get D-N1-N2 to [ D [ N1 N2 ]] , merging [ D N1] and then the result with N2 would create [[D N1] N2] which would not work. With EM-IM two-step we could have [N1 D] -> [N2 [N1 D]] -> [[N1 D] [N2 [N1 D]]] -> [D [[N1 D] [N2 [N1 D]]]] -> [D [[N1 -] [N2 [- -]]]].

 Alternatively we could have EM to the right and IM. [D N1] -> [[D N1] N2] -> [[D N1] [N2 [D N1]]]. Well. What if we add PP? [[[D N1] [N2 [D N1]]] PP] What would it mean to have [[[D N1] [N2 [D N1]]] [[[D N1] [N2 [D N1]]] PP]]? 