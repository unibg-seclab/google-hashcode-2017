import subprocess
import time
import sys

best_score = 0
best_seed = None

infile = sys.argv[1]


while True:
    process = subprocess.Popen('pypy solve.py < %s' % infile,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell = True)
    stdout, stderr = process.communicate()

    stderr_lines = [line.strip() for line in stderr.split('\n') if line.strip()]
    score_line = stderr_lines[-1]

    seed = int(stderr_lines[0].strip())
    score = int(score_line.split(' ')[1].strip(','))

    if score > best_score:
        best_score, best_seed = score, seed
        print best_score, best_seed

    time.sleep(0.2) # allow to stop long pressing Ctrl-C
