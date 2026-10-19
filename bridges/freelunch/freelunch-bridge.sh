#!/bin/sh
# Usage: freelunch-bridge TASK.sas METHOD MAKESPAN
#        freelunch-bridge DOMAIN.pddl PROBLEM.pddl METHOD MAKESPAN
#        freelunch-bridge --builtin barman-pfile06-022.sas compactReinforced 37
#        freelunch-bridge --list
# METHOD is one of sase, isase, linear, reinforced, exist, disertDirect,
# compactDirect, compactReinforced, selective; the competition instances use
# "ex" for exist and "cr" for compactReinforced in their names.  MAKESPAN is the
# number of parallel steps the plan may take: it is what makes the formula
# bigger and harder, and what decides whether it is satisfiable at all.
# The CNF goes to standard output, like every image here.
set -e
CP=/opt/freelunch/classes
if [ "$1" = "--list" ]; then
    find /opt/freelunch/testfiles -name '*.sas' -printf '%f\n' | sed 's/\.sas$//' | sort
    exit 0
fi
task="$1"
if [ "$1" = "--builtin" ]; then
    task=$(find /opt/freelunch/testfiles -name "$2" | head -1); shift
fi
# A planning problem usually comes as two PDDL files: translate them first.
if [ $# -eq 4 ]; then
    [ -f "$1" ] && [ -f "$2" ] || { echo "freelunch-bridge: $1 or $2 is not a file" >&2; exit 2; }
    tmp=$(mktemp -d)
    dom=$(readlink -f "$1"); prob=$(readlink -f "$2")
    (cd "$tmp" && PYTHONPATH=/opt/downward/translate python3 -m fast_downward.translate "$dom" "$prob" >/dev/null)
    task=$(ls "$tmp"/*.sas 2>/dev/null | head -1)
    [ -n "$task" ] || { echo "freelunch-bridge: the PDDL could not be translated" >&2; exit 3; }
    shift
fi
[ $# -eq 3 ] || { echo "usage: freelunch-bridge TASK.sas METHOD MAKESPAN" >&2; exit 2; }
[ -f "$task" ] || { echo "freelunch-bridge: no such task: $2" >&2; exit 2; }
case "$2" in ex) method=exist ;; cr) method=compactReinforced ;; *) method="$2" ;; esac
d=$(mktemp -d)
java -Xmx8g -cp "$CP" freelunch.planning.cmdline.Translator encode "$task" "$method" "$3" > "$d/out.cnf"
if grep -q "^p cnf" "$d/out.cnf"; then
    cat "$d/out.cnf"
else                                  # some versions write the file next to the task
    f=$(ls "$d"/*.cnf 2>/dev/null | grep -v out.cnf | head -1)
    [ -n "$f" ] || { echo "freelunch-bridge: the translator produced no formula" >&2; exit 3; }
    cat "$f"
fi
rm -rf "$d"
