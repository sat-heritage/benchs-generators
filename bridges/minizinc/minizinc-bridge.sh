#!/bin/sh
# Usage: minizinc-bridge MODEL.mzn [DATA.dzn ...] [-D "n=20"]
#        minizinc-bridge --fzn MODEL.fzn
#        minizinc-bridge --builtin queens 12
#        minizinc-bridge --list
# Everything after the model is handed to the MiniZinc compiler, so the usual
# ways of giving a model its parameters all work: a data file, -D, or a model
# that fixes them itself.  Those parameters are what make the family scale.
# The CNF goes to standard output, like every image here.
set -e
MODELS=/opt/minizinc-bridge/models
FZN2PICAT=/picat/lib2/fzn2picat_dump.pi

if [ "$1" = "--list" ]; then
    for m in "$MODELS"/*.mzn; do
        n=$(basename "$m" .mzn)
        printf '%-14s %s\n' "$n" "$(sed -n '2s/^% *//p' "$m")"
    done
    exit 0
fi

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

if [ "$1" = "--builtin" ]; then
    [ $# -eq 3 ] || { echo "usage: minizinc-bridge --builtin NAME N" >&2; exit 2; }
    [ -f "$MODELS/$2.mzn" ] || { echo "minizinc-bridge: no built-in model $2, try --list" >&2; exit 2; }
    set -- "$MODELS/$2.mzn" -D "n=$3"
fi

if [ "$1" = "--fzn" ]; then
    [ -f "$2" ] || { echo "minizinc-bridge: no such FlatZinc file: $2" >&2; exit 2; }
    cp "$2" "$work/model.fzn"
else
    [ -f "$1" ] || { echo "minizinc-bridge: no such model: $1" >&2; exit 2; }
    # exit 3: the model is not accepted, which is the compiler's business and
    # not ours; its own message says why.
    minizinc --compile --solver org.picat.sat --no-output-ozn \
        --output-fzn-to-file "$work/model.fzn" "$@" \
        >/dev/null || exit 3
fi

cd "$work"
# PicatSAT's FlatZinc front end writes the Picat program it would run...
picat "$FZN2PICAT" model.fzn >/dev/null 2>"$work/fzn2picat.err" \
    || { echo "minizinc-bridge: PicatSAT could not read the FlatZinc" >&2
         tail -3 "$work/fzn2picat.err" >&2; exit 4; }
[ -f model.pi ] || { echo "minizinc-bridge: PicatSAT wrote no program" >&2; exit 4; }
# ...and this is the one line we add to it: solve/1 over the variables becomes
# solve/2 with the dump option, which writes the CNF the solver would be given.
# A model with an objective already uses solve/2, so there the option joins the
# list that is there.
awk -v f="$work/out.cnf" '
    !done && /^[ \t]*solve[_a-z]*\(\[/ {
        if ($0 ~ /solve[_a-z]*\(\[[^]]*\],[ \t]*\[/)
            sub(/\(\[/, "([$dump(\"" f "\"),")
        else
            sub(/\(\[/, "([$dump(\"" f "\")],[")
        done = 1
    } { print }' model.pi > dump.pi
grep -q '\$dump(' dump.pi || { echo "minizinc-bridge: no solve call to hook into" >&2; exit 4; }

# Picat writes the whole formula before it starts solving it, and we only want
# the formula: stop it as soon as the file holds the clauses its header counts.
picat dump.pi >/dev/null 2>"$work/picat.err" &
pid=$!
while kill -0 "$pid" 2>/dev/null; do
    if [ -s out.cnf ]; then
        read -r p _ _ nc < out.cnf
        if [ "$p" = p ] && [ "$(wc -l < out.cnf)" -ge "$((nc + 1))" ]; then
            kill "$pid" 2>/dev/null || true
            break
        fi
    fi
    sleep 0.2
done
wait "$pid" 2>/dev/null || true

if [ ! -s out.cnf ]; then
    echo "minizinc-bridge: PicatSAT produced no formula, the model may have been" >&2
    echo "  decided before the encoding (an empty or inconsistent domain)" >&2
    tail -3 "$work/picat.err" >&2
    exit 4
fi
cat out.cnf
