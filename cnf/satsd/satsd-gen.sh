#!/bin/sh
# Usage: satsd-gen sd N SEED [--format CNF1|CNF2|XNF1|XNF2] [--cc K] [--pb K]
#        satsd-gen raw N SEED       the instance itself: the matrix and the syndrome
#
# A syndrome decoding instance is a random parity-check matrix H of n/2 rows and
# n columns, a syndrome s, and a weight w the authors set to 1.05 times the
# Gilbert-Varshamov distance; the question is whether an error of weight w
# explains the syndrome.  N and SEED are the family's two parameters: the seed
# fixes the matrix, N makes the formula grow, from 636 clauses at n=10 to 187682
# at n=150 in the default model.
#
# The default model is the authors' own: CNF1 with the cardinality encoding 3
# and the pseudo-Boolean encoding 5, the configuration of the instances they
# committed.  --format CNF2 is their second model, smaller; the two XNF formats
# write XOR constraints as 'x' lines, which is not DIMACS CNF and only a solver
# that reads XNF will take them.
#
# The low-weight codeword side of the repository produces MaxSAT, in WCNF, so
# it is not exposed here: this image writes CNF, like every image in this
# project. Its code travels in the image all the same, under /opt/satsd/lw.
# The formula goes to standard output.
set -e
cmd="$1"
case "$cmd" in
    sd|raw) [ $# -ge 3 ] || { echo "usage: satsd-gen $cmd N SEED [options]" >&2; exit 2; } ;;
    *) echo "usage: satsd-gen sd N SEED [--format CNF1|CNF2|XNF1|XNF2] [--cc K] [--pb K] | satsd-gen raw N SEED" >&2
       exit 2 ;;
esac
n="$2"; seed="$3"; shift 3
format=CNF1; cc=3; pb=5
while [ $# -gt 0 ]; do
    case "$1" in
        -f|--format) format="$2"; shift 2 ;;
        --cc) cc="$2"; shift 2 ;;
        --pb) pb="$2"; shift 2 ;;
        *) echo "satsd-gen: unknown option $1" >&2; exit 2 ;;
    esac
done
case "$n$seed" in
    *[!0-9]*) echo "satsd-gen: N and SEED are integers" >&2; exit 2 ;;
esac

# the authors' scripts write beside themselves, under Challenges/, so the code
# is copied to a writable directory and the formula read back from there
d=$(mktemp -d)
trap 'rm -rf "$d"' EXIT
cp -r /opt/satsd/sd/. "$d/"
cd "$d"
python3 syndrome_generate.py "$n" "$seed" >&2
raw="Challenges/seed_$seed/SD/SD_${n}_$seed"
[ -f "$raw" ] || { echo "satsd-gen: the generator wrote no instance" >&2; exit 4; }
if [ "$cmd" = "raw" ]; then
    exec cat "$raw"
fi

case "$format" in
    CNF1|CNF2) out="Challenges/seed_$seed/$format/PB_$pb/encoding_$cc/SD_${n}_$seed.cnf"
               python3 models.py "$raw" -f "$format" --cc "$cc" --pb "$pb" >&2 ;;
    XNF1|XNF2) out="Challenges/seed_$seed/$format/encoding_$cc/SD_${n}_$seed.cnf"
               python3 models.py "$raw" -f "$format" --cc "$cc" >&2 ;;
    *) echo "satsd-gen: --format takes CNF1, CNF2, XNF1 or XNF2" >&2; exit 2 ;;
esac
# exit 4: the model script took the instance and wrote nothing, which is what an
# encoding it cannot build ends as
[ -f "$out" ] || { echo "satsd-gen: no formula was written for $format cc=$cc pb=$pb" >&2; exit 4; }
exec cat "$out"
