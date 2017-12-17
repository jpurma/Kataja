""" Create profile data with command:
python3 -m cProfile -o profile Kataja.py

Play around, then close Kataja and run this script with:

python3 profiler.py

Refresh profiler_results.log.
"""

import pstats

f = open('profiler_results.log', 'w')
p = pstats.Stats('profile', stream=f)
p.strip_dirs()
p.sort_stats('cumtime')
p.print_stats(50)
p.print_callers(50)
p.print_callees(50)
f.close()
