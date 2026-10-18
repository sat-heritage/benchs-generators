#!/bin/sh
# Usage: aiger-bridge unroll K MODEL.aig     expand the model over K time frames, then encode
#        aiger-bridge cnf MODEL.aig          encode a combinational circuit as it is
#        aiger-bridge miter A.aig B.aig      the miter of two circuits, encoded
# The CNF goes to standard output, like every image here.  The model files come
# from the upstream collection, fetched into the cache by tools/fetch_upstream.py
# and mounted on /data; nothing is redistributed by this repository.
set -e
case "$1" in
    unroll) [ $# -eq 3 ] || { echo "usage: aiger-bridge unroll K MODEL.aig" >&2; exit 2; }
            aigunroll "$2" "$3" | aigtocnf ;;
    cnf)    [ $# -eq 2 ] || { echo "usage: aiger-bridge cnf MODEL.aig" >&2; exit 2; }
            aigtocnf "$2" ;;
    miter)  [ $# -eq 3 ] || { echo "usage: aiger-bridge miter A.aig B.aig" >&2; exit 2; }
            d=$(mktemp -d); aigmiter -o "$d/m.aig" "$2" "$3" >/dev/null; aigtocnf "$d/m.aig"; rm -rf "$d" ;;
    *)      echo "usage: aiger-bridge (unroll K MODEL.aig | cnf MODEL.aig | miter A.aig B.aig)" >&2; exit 2 ;;
esac
