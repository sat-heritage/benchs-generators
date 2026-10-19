#!/bin/sh
# Usage: rr-gen rr N ROUNDS           (roundrobin.py: RoundRobin_n<N>_d<ROUNDS>)
#        rr-gen mv N ROUNDS VENUES    (mvts.py: MVRoundRobin_n<N>_d<ROUNDS>_v<VENUES>)
# The author's script keeps its list of instances at the top of the file; the
# only change made here is to replace that list with the single instance asked
# for on the command line.  The encoding code itself runs verbatim.
set -e
kind="$1"; shift
d=$(mktemp -d)
case "$kind" in
    rr) sed "s/^instances = .*/instances = [($1, $2)]/" /src/roundrobin.py > "$d/gen.py" ;;
    mv) sed "s/^instances = .*/instances = [($1, $2, $3)]/" /src/mvts.py > "$d/gen.py" ;;
    *)  echo "usage: rr-gen (rr N ROUNDS | mv N ROUNDS VENUES)" >&2; exit 2 ;;
esac
grep -q "^instances = \[(" "$d/gen.py" || { echo "rr-gen: could not set the instance list" >&2; exit 3; }
cd "$d"
python3 gen.py >/dev/null
cat ./*.cnf
cd /
rm -rf "$d"
