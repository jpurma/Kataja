import subprocess
import os
import sys

# This is an example for using Kataja to launch a visualisation from a python script that doesn't use kataja
# structures, but can output bracket trees. Kataja is launched as a separate process so it doesn't stop the
# main script.


def send_to_kataja(tree, image_file=''):
    #return os.system(f'python Kataja.py -image_out test.pdf "{tree}"')
    args = ['python', 'Kataja.py']
    if image_file:
        args.append('-image_out')
        args.append(image_file)
    args.append(tree)
    if os.name == 'posix':
        #return os.spawnv(os.P_NOWAIT, '', args)
        return subprocess.Popen(args, preexec_fn=os.setpgrp, stdout=subprocess.DEVNULL)
    elif os.name == 'nt':
        return os.spawnv(os.P_DETACH, 'python', args)

    # python Kataja.py -image_out test.pdf "[ [ A {word} ] [.T did [.V happen ] ] ]"


tree = """[.{CP} [.{DP(0)} [.{D'} [.{D} which ] [.{NP} [.{N'} [.N wine ] ] ] ] ] [.{C'} [.C \epsilon [.{VP} [.{DP} [.{D'} [.D the ] [.{NP} [.{N'} [.N queen ] ] ] ] ] [.{V'} [.V prefers ] [.{DP} t(0) ] ] ] ] ] ]
"""

tree = """[.{FP} {Graham Greene_i} [.{F'} on_j [.{TP} t_i [.{T'} t_j [.{AuxP} t_j [.{PrtP} kirjoittanut_k [.{VP} t_i [.{V'} t_k [.{DP} tämän kirjan ] ] ] ] ] ] ] ] ]
"""

send_to_kataja(tree, 'test.pdf')

print(f"I just sent {tree} to kataja.")

print("thanks, I'm done now!")