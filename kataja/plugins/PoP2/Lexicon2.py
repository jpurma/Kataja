ALL_HEADS = {'v*', 'C', 'v', 'n', 'the', 'a', "D", "in"}
HEADS = {'v*', 'v', 'C', 'n', 'v~', "D", "D_Top", "in"}
DET_HEADS = {'the', 'a', "d", "no"}
PHASE_HEADS = {"v*", "C", "C_Q", "that", "C_Null", "C_Top", "in","if","C_if","ni","no","CASE","C_Q_e"}
THETA_ASSIGNERS = {"v*", "vUnerg", 'v', 'v_be'}
SHARED_FEAT_LABELS = {"Phi", "Q", "Top", "Per"}
TENSE_ELEMS = {'PRES', 'PAST'}
PHI_FEATS = {"iPerson:", "iNumber:", "iGender:"}
OTHER_FTS = {'ThetaAgr', 'EF', 'MergeF', 'ExplMerge', 'NoProject'}
SHARED_LABELS = {"Phi", "Q", "Top"}
ADJUNCT_LABELS = {"P_in", "in"}
VERBAL_ROOTS = {"V_shite","V_kuda"}
TENSES = {"Tpres","Tpast"}
NO_PF = {"vUnerg","v*"}
COUNTED_FEATURES = {'uPerson', 'uNumber', 'uGender', 'Case:Nom', 'Case:Acc', 'Case:Dat', 'Root',
                    'uCase', 'uCase', 'iTop', 'uScp', 'iQ', 'iv', 'Case:Top', 'Case:X'}
COUNTED_PHI_FEATURES = {'iPerson:', 'iNumber:', 'iGender:'}
LEXICON = {
    'v*': {'uPerson', 'uNumber', 'uGender', 'Phase', 'MergeF', 'Head', 'Case:Acc', 'Affix', 'Theta'},
    'P_': {'uPerson', 'uNumber', 'uGender', 'MergeF', 'Head', 'Case:Dat', 'Theta', 'P'},
    'ni': {'uPerson', 'uNumber', 'uGender', 'MergeF', 'Head', 'Case:Dat', 'P'}, # Japanese?
    'CASE': {'uPerson', 'uNumber', 'uGender', 'MergeF', 'Head', 'Case:X', 'P'}, 
    'no': {'uPerson', 'uNumber', 'uGender', 'MergeF', 'Head', 'Case:Gen', 'P'}, # Japanese, conflict with latter no 
    'C': {'uPerson', 'uNumber', 'uGender', 'MergeF', 'Head', 'Phase', 'Case:Nom'},
    #'P_in': {'uPerson', 'uNumber', 'uGender', 'MergeF', 'Head', 'Case:Dat'},
    'that': {'uPerson', 'uNumber', 'uGender', 'MergeF', 'Phase' 'Head', 'iC', 'Case:Nom'},
    'C_Q': {'uPerson', 'uNumber', 'uGender', 'MergeF', 'Phase', 'Head', 'Case:Nom', 'uQ', 'iScp', 'iC', 'Affix'},
    'C_Q_e': {'uPerson', 'uNumber', 'uGender', 'MergeF', 'Phase', 'Head', 'Case:Nom', 'uQ', 'iScp', 'iC'},    
    'C_if': {'uPerson', 'uNumber', 'uGender', 'MergeF', 'Phase', 'Head', 'Case:Nom', 'iQ', 'iC'},    
    'C_Top': {'iTop','uPerson', 'uNumber', 'uGender', 'Phase' 'MergeF', 'Head', 'Case:Top', 'iScp', 'iC'},
    'C_Null': {'uPerson', 'uNumber', 'uGender', 'Phase', 'MergeF', 'Head', 'Case:Nom', 'Delete', 'iC'},
    # LI name is "C"
    'v': {'MergeF', 'Root', 'iv', 'Affix'}, 'v_be': {'MergeF', 'iv', 'Root'},
    'vUnerg': {'MergeF', 'iv', 'Root', 'Affix', 'Theta'}, 'v~': {'MergeF', 'ThetaAgr'},
    'n_Top': {'iPerson:', 'iNumber:', 'iGender:', 'MergeF', 'uCase', 'iTheta', 'Head', 'iN', 'iD',
              'iTop', 'uScp'},

    'n_Expl': {'uPerson', 'uNumber', 'uGender', 'MergeF', 'Head', 'iN', 'Expl'},  # LI name is "n"
    #'n': {'iPerson:', 'iNumber:', 'iGender:', 'MergeF', 'uCase', 'iTheta', 'Head', 'iN'},
    # +'iD' for Japanese
    # n is now a special case, complexes like 'n_3rd_pl' need to be parsed
    'adj': {'MergeF', 'Head', 'iAdj'},
    '-na': {'MergeF', 'Head', 'iAdj'},
    'adv': {'MergeF', 'Head', 'iAdv', 'uCase'},
    #'there': {'MergeF', 'ThetaAgr'}, 'the': {'MergeF', 'Head', 'uPhi', 'iD'},
    'the': {'MergeF', 'Head', 'uPerson', 'uNumber', 'uGender', 'iD', 'uCase'},  # DET_HEADS 
    'a': {'MergeF', 'Head', 'uPerson', 'uNumber', 'uGender', 'iD', 'uCase'},  # DET_HEADS 
    'd': {'MergeF', 'Head', 'uPerson', 'uNumber', 'uGender', 'iD', 'uCase'},  # DET_HEADS 
    'no': {'MergeF', 'Head', 'uPerson', 'uNumber', 'uGender', 'iD', 'uCase'},  # DET_HEADS 
    'Poss': {'MergeF', 'Head', 'uPerson', 'uNumber', 'uGender', 'Case:Gen'},
    'Q': {'MergeF', 'Head', 'uPhi', 'iD', 'iQ', 'uScp', 'uCase'},
    'which': {'MergeF', 'Head', 'uPhi', 'iQ', 'uScp'}, 
    'how': {'MergeF', 'Head', 'uPhi', 'iQ', 'uScp'}, 
    'which_NouF': {'MergeF', 'Head', 'uPhi', 'iQ'},  # presents as 'which' 
    'TPres': {'MergeF', 'Root', 'Affix'}, # TENSES
    'TPast': {'MergeF', 'Root', 'Affix'}, # TENSES
    'V_shite': {'MergeF', 'root', 'iV'},  # Japanese
    'V_kuda': {'MergeF', 'root', 'iV'},  # Japanese
    'root': {'MergeF', 'Root'},
}
