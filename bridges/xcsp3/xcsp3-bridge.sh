#!/bin/sh
# Usage: xcsp3-bridge INSTANCE.xml            an XCSP3 instance, .xml, .xml.lzma or .xml.xz
#        xcsp3-bridge MODEL.py [-data=...]    a PyCSP3 model, compiled then encoded
#        xcsp3-bridge --builtin queens 12
#        xcsp3-bridge --list
# Everything after a PyCSP3 model is handed to it, so its own options work:
# -data for the data, -variant for a variant of the model.  Those are what make
# the family scale.  The CNF goes to standard output, like every image here.
set -e
MODELS=/opt/xcsp3/models
DUMP=/opt/xcsp3/xcsp-dump.pi

if [ "$1" = "--list" ]; then
    for m in "$MODELS"/*.py; do
        n=$(basename "$m" .py)
        printf '%-14s %s\n' "$n" "$(sed -n '2s/^# *//p' "$m")"
    done
    exit 0
fi

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

if [ "$1" = "--builtin" ]; then
    [ $# -eq 3 ] || { echo "usage: xcsp3-bridge --builtin NAME N" >&2; exit 2; }
    [ -f "$MODELS/$2.py" ] || { echo "xcsp3-bridge: no built-in model $2, try --list" >&2; exit 2; }
    set -- "$MODELS/$2.py" "-data=$3"
fi

[ -f "$1" ] || { echo "xcsp3-bridge: no such file: $1" >&2; exit 2; }
case "$1" in
    *.py)
        model=$(readlink -f "$1"); dir=$(dirname "$model"); shift
        # a data file given relative to the model is resolved there, since the
        # model is compiled in a directory of ours and not where it lives
        i=0
        while [ "$i" -lt "$#" ]; do
            a="$1"; shift
            case "$a" in
                -data=/*) ;;
                -data=*) v=${a#-data=}; [ -e "$dir/$v" ] && a="-data=$dir/$v" ;;
            esac
            set -- "$@" "$a"; i=$((i + 1))
        done
        # PyCSP3 writes the instance in the current directory, which is why the
        # model is given by its path and the work is done elsewhere
        # exit 3: the model is not accepted, which is PyCSP3's business, not ours
        (cd "$work" && python3 "$model" "$@" >"$work/pycsp3.log" 2>&1) || {
            echo "xcsp3-bridge: PyCSP3 did not compile the model" >&2
            tail -5 "$work/pycsp3.log" >&2; exit 3; }
        instance=$(ls "$work"/*.xml 2>/dev/null | head -1)
        [ -n "$instance" ] || { echo "xcsp3-bridge: PyCSP3 wrote no instance" >&2
                                tail -5 "$work/pycsp3.log" >&2; exit 3; }
        ;;
    *.lzma) xz --format=lzma -dc "$1" > "$work/instance.xml"; instance="$work/instance.xml" ;;
    *.xz)   xz -dc "$1" > "$work/instance.xml"; instance="$work/instance.xml" ;;
    *)      instance="$1" ;;
esac

cnf="$work/out.cnf"
# Picat writes the whole formula before it starts solving it, and we only want
# the formula: stop it as soon as the file holds the clauses its header counts.
picat "$DUMP" "$instance" "$cnf" >"$work/picat.log" 2>&1 &
pid=$!
while kill -0 "$pid" 2>/dev/null; do
    if [ -s "$cnf" ]; then
        read -r p _ _ nc < "$cnf"
        if [ "$p" = p ] && [ "$(wc -l < "$cnf")" -ge "$((nc + 1))" ]; then
            kill "$pid" 2>/dev/null || true
            break
        fi
    fi
    sleep 0.2
done
wait "$pid" 2>/dev/null || true

if [ ! -s "$cnf" ]; then
    # the interpreter answers UNSATISFIABLE when its own propagation settles the
    # instance while reading it, and there is no formula to write then
    if grep -q UNSATISFIABLE "$work/picat.log"; then
        echo "xcsp3-bridge: PicatSAT decided the instance while reading it," >&2
        echo "  its propagation found it unsatisfiable, so no formula was written" >&2
        exit 5
    fi
    echo "xcsp3-bridge: no formula was written" >&2
    tail -5 "$work/picat.log" >&2
    exit 4
fi
cat "$cnf"
