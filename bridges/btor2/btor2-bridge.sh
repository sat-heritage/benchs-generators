#!/bin/sh
# Usage: btor2-bridge unroll K MODEL.btor2   bit blast, expand over K time frames, encode
#        btor2-bridge aig MODEL.btor2        the bit blasted AIG, for inspection
#        btor2-bridge info MODEL.btor2       what the bit blasted model holds
#
# The file may be named .btor or .btor2, as the competitions name them both
# ways.  The encoder is poormanaigtocnf, the plain Tseitin encoder of the aiger
# examples, the same one bridges/aiger uses, so a BTOR2 model and an AIGER model
# of the same competition are encoded the same way.  Add -o/--optimised for
# aigtocnf, which simplifies more and writes a different formula.
# The CNF goes to standard output, like every image here.  The models come from
# the upstream collection, fetched into the cache by tools/fetch_upstream.py and
# mounted on /data; nothing is redistributed by this repository.
set -e
ENCODE=poormanaigtocnf
case "$1" in
    -o|--optimised) ENCODE=aigtocnf; shift ;;
esac
cmd="$1"
case "$cmd" in
    unroll) [ $# -eq 3 ] || { echo "usage: btor2-bridge unroll K MODEL.btor2" >&2; exit 2; }
            k="$2"; model="$3" ;;
    aig|info) [ $# -eq 2 ] || { echo "usage: btor2-bridge $cmd MODEL.btor2" >&2; exit 2; }
            model="$2" ;;
    *) echo "usage: btor2-bridge unroll K MODEL.btor2 | aig MODEL.btor2 | info MODEL.btor2" >&2; exit 2 ;;
esac
[ -f "$model" ] || { echo "btor2-bridge: no such model: $model" >&2; exit 2; }
d=$(mktemp -d)
trap 'rm -rf "$d"' EXIT
# exit 3: the model is not one this chain takes. Arrays and the word level
# constructs Boolector cannot bit blast end here, and the message says which.
btor2aiger "$model" > "$d/m.aig" 2>"$d/err" || {
    echo "btor2-bridge: btor2aiger could not bit blast this model" >&2
    tail -3 "$d/err" >&2; exit 3; }
[ -s "$d/m.aig" ] || { echo "btor2-bridge: btor2aiger wrote nothing" >&2
                       tail -3 "$d/err" >&2; exit 3; }
case "$cmd" in
    aig)  cat "$d/m.aig"; exit 0 ;;
    # the header of an AIGER file says what the bit blasted model holds, and
    # that is the useful answer: how many latches is how much state to unroll
    info) head -1 "$d/m.aig" | awk '{printf "variables %s, inputs %s, latches %s, outputs %s, and gates %s, bad states %s\n", $2, $3, $4, $5, $6, ($7 == "" ? 0 : $7)}'
          exit 0 ;;
esac
# A BTOR2 model states its property as a bad state, and aigunroll refuses
# those: aigmove turns them into outputs first.
aigmove "$d/m.aig" "$d/moved.aig" >/dev/null
aigunroll "$k" "$d/moved.aig" "$d/u.aig" >/dev/null
"$ENCODE" "$d/u.aig"
