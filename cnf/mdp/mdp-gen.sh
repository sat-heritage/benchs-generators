#!/bin/sh
# mdp-gen.py writes its formula to a file named after its parameters; this
# wrapper runs it in a scratch directory and puts the CNF on standard output.
set -e
d=$(mktemp -d)
cd "$d"
python3 /src/src/mdp-gen.py "$@" >/dev/null
cat ./*.cnf
cd /
rm -rf "$d"
