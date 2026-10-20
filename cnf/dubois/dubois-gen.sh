#!/bin/sh
# Usage: dubois-gen D                 the hard contradictory family, 3D variables and 8D clauses
#        dubois-gen --random N P R    the other generator of the same directory, uniform random
# The generators write their own file in a fixed format of their own, so the
# wrapper runs them in a directory of ours and turns that file into DIMACS.
# The CNF goes to standard output, like every image here.
set -e
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
cd "$work"
if [ "$1" = "--random" ]; then
    [ $# -eq 4 ] || { echo "usage: dubois-gen --random N P R" >&2; exit 2; }
    printf '%s\n%s\n%s\n' "$2" "$3" "$4" | gensat >/dev/null 2>&1 || true
else
    [ $# -eq 1 ] || { echo "usage: dubois-gen D  (or --random N P R)" >&2; exit 2; }
    case "$1" in ''|*[!0-9]*) echo "dubois-gen: the degree is a positive integer" >&2; exit 2 ;; esac
    gensathard "$1" >/dev/null 2>&1 || true
fi
[ -f in.dat ] || { echo "dubois-gen: the generator wrote nothing" >&2; exit 4; }
# in.dat: four lines of header, d = , n = , p = , r = , then one clause per line
awk 'NR<=4 { split($0, a, "="); h[NR] = a[2] + 0; next }
     NR == 5 { printf "p cnf %d %d\n", h[2], h[3] }
     NF > 0 { for (i = 1; i <= NF; i++) printf "%s ", $i; print "0" }' in.dat
