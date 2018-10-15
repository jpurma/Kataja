import subprocess
import os

# This is an example for using Kataja to launch a visualisation from a python script that doesn't use kataja
# structures, but can output bracket trees. Kataja is launched as a separate process so it doesn't stop the
# main script.


def send_to_kataja(*args):
    return subprocess.Popen(['python', 'Kataja.py', *args], preexec_fn=os.setpgrp, stdout=subprocess.DEVNULL)


word = 'shit'

tree = f'[ [ A {word} ] [.T did [.V happen ] ] ]'

send_to_kataja(tree)

print(f"I just sent {tree} to kataja.")

print("thanks, I'm done now!")