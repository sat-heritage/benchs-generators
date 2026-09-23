#!/bin/sh
# Usage: oddball-gen BALLS WEIGHINGS [--strategy NAME]
# The submitted instances used --strategy TruthTableForced, as recorded in
# generate_benchmarks.sh of the repository.  The formula is built through z3,
# which writes it to a file; this wrapper puts it on standard output.
set -e
d=$(mktemp -d)
oddball "$@" --cnf "$d/out.cnf" --skip-solver >/dev/null
cat "$d/out.cnf"
rm -rf "$d"
