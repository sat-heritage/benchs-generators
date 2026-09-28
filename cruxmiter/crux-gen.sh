#!/bin/sh
# Usage: crux-gen SIZE SEED
# SIZE is the number of input bits added by each CRUX tree, SEED the seed of the
# random partition.  The three steps are the author's own: the SMT formula, the
# AIG produced by Boolector with the normalisation of adders disabled, and the
# CNF written by aigtocnf.
set -e
[ $# -eq 2 ] || { echo "usage: crux-gen SIZE SEED" >&2; exit 2; }
# -rwl 2 keeps the adder trees: at its default rewriting level this Boolector
# proves the miter trivially and dumps an empty AIG, which the 2021 version the
# author used did not do.
gencruxmitersmt "$1" "$2" | boolector -rwl 2 -nadd 0 -dai | aigtocnf
