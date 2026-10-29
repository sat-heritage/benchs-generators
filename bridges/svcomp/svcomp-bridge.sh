#!/bin/sh
# Usage: svcomp-bridge task K TASK.yml       encode a competition task at bound K
#        svcomp-bridge unwind K FILE.c ...   encode C files of your own at bound K
#        svcomp-bridge info TASK.yml         what the task declares
#        svcomp-bridge verdict K TASK.yml    what CBMC answers at that bound
#
# A verification task of SV-COMP is a C file and a .yml beside it saying which
# property is to be proved, under which data model, and what the expected
# answer is.  CBMC no longer reads those property files -- --propertyfile went
# away after it stopped competing -- so this bridge translates the property
# into the checks CBMC does have, and starts from --no-standard-checks so that
# the formula asks the property that was declared and nothing else.  The
# translation is a judgement of ours, not the competition's, and it is written
# out in full below.
#
# The bound K is the unwinding bound, the number of times every loop and every
# recursive call may be taken.  The formula asks whether the property can be
# violated within that bound, so K plays the part the depth plays for the
# hardware bridges: the family scales with it and nothing else changes.
# Unwinding assertions are not added, so the formula is the bounded question
# and not the question whether the bound was enough.
#
# With -p NAME the property is chosen by name, no-overflow for instance, among
# those the task declares; by default the first one that is a verification
# property is taken, the coverage properties of the test generation tracks
# being no question for a SAT solver.
# The CNF goes to standard output, like every image here.  The tasks come from
# the upstream collection, fetched into the cache by tools/fetch_upstream.py
# and mounted on /data; nothing is redistributed by this repository.
set -e
want=""
case "$1" in
    -p|--property) want="$2"; shift 2 ;;
esac
cmd="$1"
case "$cmd" in
    task)   [ $# -eq 3 ] || { echo "usage: svcomp-bridge task K TASK.yml" >&2; exit 2; }
            k="$2"; yml="$3" ;;
    unwind) [ $# -ge 3 ] || { echo "usage: svcomp-bridge unwind K FILE.c ..." >&2; exit 2; }
            k="$2"; shift 2 ;;
    info)   [ $# -eq 2 ] || { echo "usage: svcomp-bridge info TASK.yml" >&2; exit 2; }
            yml="$2" ;;
    verdict) [ $# -eq 3 ] || { echo "usage: svcomp-bridge verdict K TASK.yml" >&2; exit 2; }
            k="$2"; yml="$3" ;;
    *) echo "usage: svcomp-bridge task K TASK.yml | unwind K FILE.c ... | info TASK.yml | verdict K TASK.yml" >&2; exit 2 ;;
esac

if [ "$cmd" = "unwind" ]; then
    for f in "$@"; do
        [ -f "$f" ] || { echo "svcomp-bridge: no such file: $f" >&2; exit 2; }
    done
    out=$(mktemp)
    trap 'rm -f "$out"' EXIT
    # CBMC writes its progress on standard output, so the formula goes to a file
    cbmc --dimacs --outfile "$out" --unwind "$k" "$@" >&2
    exec cat "$out"
fi

[ -f "$yml" ] || { echo "svcomp-bridge: no such task: $yml" >&2; exit 2; }
dir=$(dirname "$yml")
# the fields of a task definition, in the two spellings the collection uses: a
# quoted scalar for a single file, a block list for the validation tasks, which
# are a task and a witness rather than a program to encode
inputs=$(awk '/^input_files:[ \t]*$/ { print "LIST"; exit }
              /^input_files:/ { v = $0; sub(/^input_files:[ \t]*/, "", v); print v; exit }' "$yml" \
         | tr -d '\042\047')
props=$(awk '/^[ \t]*-[ \t]*property_file:/ { v = $0; sub(/^.*property_file:[ \t]*/, "", v); print v }' "$yml" \
        | tr -d '\042\047')
model=$(awk '/^[ \t]*data_model:/ { v = $0; sub(/^.*data_model:[ \t]*/, "", v); print v; exit }' "$yml" \
        | tr -d '\042\047')
expected=$(awk '/^[ \t]*-[ \t]*property_file:/ { p = $0; sub(/^.*property_file:[ \t]*/, "", p) }
               /^[ \t]*expected_verdict:/ { v = $0; sub(/^.*expected_verdict:[ \t]*/, "", v)
                                            gsub(/[\042\047]/, "", p); print p " " v }' "$yml")

# Which property, when a task declares several.  Not the first one in the file:
# a task often puts termination first and the reachability question third, and
# the order in the file carries no meaning.  The order below does: unreach-call
# is the question the main track of the competition asks, and the rest follow it
# by how much of a formula they leave once CBMC has simplified.  Termination,
# no-data-race and the coverage goals of the test generation tracks are taken
# only when named with -p, which is how a reader can ask for the refusal and
# read the reason.
pick=""
if [ -n "$want" ]; then
    for p in $props; do
        [ "$(basename "$p" .prp)" = "$want" ] && { pick="$p"; break; }
    done
else
    for prefer in unreach-call no-overflow valid-memsafety valid-memcleanup def-behavior; do
        for p in $props; do
            [ "$(basename "$p" .prp)" = "$prefer" ] && { pick="$p"; break; }
        done
        [ -n "$pick" ] && break
    done
fi

if [ "$cmd" = "info" ]; then
    echo "task          $yml"
    echo "input files   $inputs"
    echo "data model    ${model:-unstated}"
    for p in $props; do
        echo "property      $(basename "$p")"
    done
    [ -n "$expected" ] && echo "$expected" | while read -r p v; do
        echo "expected      $(basename "$p" .prp) is $v"
    done
    echo "would encode  ${pick:-none: no property this chain takes}"
    exit 0
fi

# exit 3: not a task this chain takes, and the message says which kind
[ "$inputs" = "LIST" ] && { echo "svcomp-bridge: this task names several input files, which is a witness validation task, not a program to encode" >&2; exit 3; }
[ -n "$inputs" ] || { echo "svcomp-bridge: the task names no input file" >&2; exit 3; }
[ -n "$pick" ] || { echo "svcomp-bridge: the task declares no property this chain takes${want:+ named $want}" >&2; exit 3; }
src="$dir/$inputs"
[ -f "$src" ] || { echo "svcomp-bridge: the task names $inputs, which is not beside it" >&2; exit 3; }
prp="$dir/$pick"
[ -f "$prp" ] || { echo "svcomp-bridge: the property file $pick is not where the task says" >&2; exit 3; }
case "$model" in
    ILP32) arch=--32 ;;
    LP64)  arch=--64 ;;
    *)     arch="" ;;
esac

# The property, as checks.  CBMC turns on bounds, pointer and shift checks by
# default, which would put questions in the formula that the task never asked;
# --no-standard-checks takes them away and each property names its own.
# unreach-call needs no check at all: the task defines reach_error as an
# assertion, and user assertions are what CBMC checks unless told otherwise.
case "$(basename "$pick" .prp)" in
    unreach-call)    checks="--no-standard-checks" ;;
    no-overflow)     checks="--no-standard-checks --no-assertions --signed-overflow-check" ;;
    valid-memsafety) checks="--no-standard-checks --no-assertions --bounds-check --pointer-check --pointer-overflow-check --pointer-primitive-check --memory-leak-check" ;;
    valid-memcleanup) checks="--no-standard-checks --no-assertions --memory-cleanup-check" ;;
    def-behavior)    checks="--no-assertions --conversion-check --div-by-zero-check --float-div-by-zero-check --signed-overflow-check --unsigned-overflow-check --pointer-overflow-check --float-overflow-check --nan-check --enum-range-check" ;;
    termination)     echo "svcomp-bridge: termination is not a bounded question: a bounded unwinding cannot express it, and CBMC is not a termination prover" >&2; exit 3 ;;
    no-data-race)    echo "svcomp-bridge: CBMC has no data race check, so this chain cannot encode the no-data-race property" >&2; exit 3 ;;
    coverage-*)      checks="--no-standard-checks" ;;
    *)               echo "svcomp-bridge: no translation for the property $(basename "$pick"); add one to this script rather than guessing" >&2; exit 3 ;;
esac
if [ "$cmd" = "verdict" ]; then
    # the same question, answered by CBMC's own solver rather than written out:
    # this is what checks our translation of the property against the verdict
    # the competition declares for the task
    # shellcheck disable=SC2086
    cbmc --unwind "$k" $checks $arch "$src" > /tmp/cbmc.out 2>&1 && code=0 || code=$?
    case "$code" in
        0)  echo "UNSATISFIABLE  no violation of $(basename "$pick" .prp) within $k unwindings" ;;
        10) echo "SATISFIABLE    $(basename "$pick" .prp) violated within $k unwindings" ;;
        *)  echo "UNDECIDED      CBMC exited $code"; tail -3 /tmp/cbmc.out >&2 ;;
    esac
    exit 0
fi

out=$(mktemp)
trap 'rm -f "$out"' EXIT
# shellcheck disable=SC2086
cbmc --dimacs --outfile "$out" --unwind "$k" $checks $arch "$src" >&2
# exit 4: CBMC took the task but left nothing to decide.  Either it wrote no
# formula at all, or it wrote the empty one, which is what a property that the
# simplifier settles on its own looks like: every array access provably in
# bounds, say.  A true answer, and no question for a solver.
[ -s "$out" ] || { echo "svcomp-bridge: CBMC wrote no formula for this task" >&2; exit 4; }
# no clauses is no question, whichever way it is empty: p cnf 0 0 when the
# property was proved away, p cnf 1 0 when it was violated away
case "$(head -1 "$out")" in
    "p cnf "*" 0") echo "svcomp-bridge: the formula has no clauses: CBMC settled $(basename "$pick" .prp) while simplifying, so there is nothing for a solver to decide" >&2; exit 4 ;;
esac
exec cat "$out"
