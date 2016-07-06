ALL_HEADS = {'v*', 'C', 'v', 'n', 'the', 'a', "D", "in"}
HEADS = {'v*', 'v', 'C', 'n', 'v~', "D", "D_Top", "in"}
DET_HEADS = {'the', 'a', "D"}
PHASE_HEADS = {"v*", "C", "C_Q", "that", "C_Null", "C_Top", "in"}
THETA_ASSIGNERS = {"v*", "vUnerg", 'v', 'v_be'}
SHARED_FEAT_LABELS = {"Phi", "Q", "Top", "Per"}
TENSE_ELEMS = {'PRES', 'PAST'}
PHI_FEATS = {"iPerson:", "iNumber:", "iGender:"}
OTHER_FTS = {'ThetaAgr', 'EF', 'MergeF', 'ExplMerge', 'NoProject'}
SHARED_LABELS = {"Phi", "Q", "Top"}
ADJUNCT_LABELS = {"P_in"}
NUM_PATTERN = r'[0-9]+'
COUNTED_FEATURES = {'uPerson', 'uNumber', 'uGender', 'Case:Nom', 'Case:Acc', 'Case:Dat', 'Root',
                    'uCase', 'uCase', 'iTop', 'uScp', 'iQ'}
COUNTED_PHI_FEATURES = {'iPerson:', 'iNumber:', 'iGender:'}
LEXICON = {
    'v*': {'uPerson', 'uNumber', 'uGender', 'MergeF', 'Head', 'Case:Acc'},
    'C': {'uPerson', 'uNumber', 'uGender', 'MergeF', 'Head', 'Case:Nom'},
    'P_in': {'uPerson', 'uNumber', 'uGender', 'MergeF', 'Head', 'Case:Dat'},
    'that': {'uPerson', 'uNumber', 'uGender', 'MergeF', 'Head', 'iC', 'Case:Nom'},
    'C_Q': {'uPerson', 'uNumber', 'uGender', 'MergeF', 'Head', 'Case:Nom', 'uQ', 'iScp', 'iC'},
    'C_Top': {'uPerson', 'uNumber', 'uGender', 'MergeF', 'Head', 'Case:Nom', 'uTop', 'iScp', 'iC'},
    'C_Null': {'uPerson', 'uNumber', 'uGender', 'MergeF', 'Head', 'Case:Nom', 'Delete', 'iC'},
    # LI name is "C"
    'v': {'MergeF', 'Head', 'iv'}, 'v_be': {'MergeF', 'iv', 'Root'},
    'vUnerg': {'MergeF', 'iv', 'Root'}, 'v~': {'MergeF', 'ThetaAgr'},
    'n_Top': {'iPerson:', 'iNumber:', 'iGender:', 'MergeF', 'uCase', 'iTheta', 'Head', 'iN', 'iD',
              'iTop', 'uScp'},
    'n': {'iPerson:', 'iNumber:', 'iGender:', 'MergeF', 'uCase', 'iTheta', 'Head', 'iN'},
    # +'iD' for Japanese
    'n_Expl': {'uPerson', 'uNumber', 'uGender', 'MergeF', 'Head', 'iN'},  # LI name is "n"
    'there': {'MergeF', 'ThetaAgr'}, 'the': {'MergeF', 'Head', 'uPhi', 'iD'},
    'a': {'MergeF', 'Head', 'uPhi', 'iD'}, 'D': {'MergeF', 'Head', 'uPhi', 'iD'},
    'Q': {'MergeF', 'Head', 'uPhi', 'iQ', 'uScp'},
    'which': {'MergeF', 'Head', 'uPhi', 'iQ', 'uScp'}, 'root': {'MergeF', 'Root'},
}