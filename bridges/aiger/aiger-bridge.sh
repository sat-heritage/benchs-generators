#!/bin/sh
# Usage: aiger-bridge unroll K MODEL.aig     expand the model over K time frames, then encode
#        aiger-bridge cnf MODEL.aig          encode a combinational circuit as it is
#        aiger-bridge miter A.aig B.aig      the miter of two circuits, encoded
#
# The encoder is poormanaigtocnf, the plain Tseitin encoder of the aiger
# examples: it is the one the 2011 submissions used, as the "-tseitin" in their
# file names says, and aigtocnf simplifies more and gives a different formula.
# Add -o/--optimised to use aigtocnf instead.
# The CNF goes to standard output, like every image here.  The model files come
# from the upstream collection, fetched into the cache by tools/fetch_upstream.py
# and mounted on /data; nothing is redistributed by this repository.
set -e
ENCODE=poormanaigtocnf
case "$1" in
    -o|--optimised) ENCODE=aigtocnf; shift ;;
esac
case "$1" in
    unroll) [ $# -eq 3 ] || { echo "usage: aiger-bridge unroll K MODEL.aig" >&2; exit 2; }
            d=$(mktemp -d)
            # A model written the AIGER 1.9 way states its property as a bad
            # state, and aigunroll refuses those: aigmove turns them into
            # outputs first.  Models of the 2010 competition have none, so they
            # take the direct road and give exactly the formula they always did.
            if ! aigunroll "$2" "$3" "$d/u.aig" >/dev/null 2>"$d/err"; then
                grep -q "bad state" "$d/err" || { cat "$d/err" >&2; rm -rf "$d"; exit 4; }
                aigmove "$3" "$d/moved.aig" >/dev/null
                aigunroll "$2" "$d/moved.aig" "$d/u.aig" >/dev/null
            fi
            "$ENCODE" "$d/u.aig"; rm -rf "$d" ;;
    cnf)    [ $# -eq 2 ] || { echo "usage: aiger-bridge cnf MODEL.aig" >&2; exit 2; }
            "$ENCODE" "$2" ;;
    miter)  [ $# -eq 3 ] || { echo "usage: aiger-bridge miter A.aig B.aig" >&2; exit 2; }
            d=$(mktemp -d); aigmiter -o "$d/m.aig" "$2" "$3" >/dev/null; "$ENCODE" "$d/m.aig"; rm -rf "$d" ;;
    *)      echo "usage: aiger-bridge (unroll K MODEL.aig | cnf MODEL.aig | miter A.aig B.aig)" >&2; exit 2 ;;
esac
