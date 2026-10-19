#!/bin/sh
# Usage: lockchart-gen -l LOCKS [-p POSITIONS] [-d DEPTHS] [-r DENSITY]
# The script prints the lock-chart on standard output and writes the formula to
# results/lockchart-...cnf; this wrapper keeps only the formula.
# After writing the formula the script draws the lock-chart, which needs LaTeX
# and fails in this image: that failure is ignored on purpose, the formula is
# already complete.
# With -r the lock-chart is randomised with Python's unseeded random module, so
# those instances cannot be reproduced.
set -e
d=$(mktemp -d)
cd "$d"
mkdir -p results
python3 /src/lockchart_to_cnf.py "$@" >/dev/null 2>&1 || true
ls results/*.cnf >/dev/null 2>&1 || { echo "lockchart-gen: no formula produced" >&2; exit 1; }
cat results/*.cnf
cd /
rm -rf "$d"
