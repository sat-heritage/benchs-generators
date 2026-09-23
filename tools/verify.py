#!/usr/bin/env python3
"""Regenerate the reference instances of a generator and grade each one.

Levels, from strongest to weakest:
  N1  same GBD hash: the regenerated instance is the competition instance
  N2  same after sorting literals and clauses: only the order differs
  N3  same GBD isohash2: equal up to a renaming of the variables
  N4  same numbers of variables and clauses
  --  none of the above
Usage: tools/verify.py GENERATOR [SUBSTRING]
Reads references/GENERATOR.json and writes results/GENERATOR.json.  With a
SUBSTRING, only the reference instances whose name contains it are checked,
which keeps a run short when a family has very large instances.
"""
import json, lzma, os, subprocess, sys, tempfile, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GBD_IMAGE = "satex-gen/gbd:0.4.2"


def gbd(directory, names):
    out = subprocess.run(["docker", "run", "--rm", "-v", f"{directory}:/data", GBD_IMAGE, *names],
                         check=True, capture_output=True, text=True).stdout
    table = {}
    for line in out.splitlines():
        path, h, iso2, nv, nc = line.split("\t")
        table[path] = {"gbdhash": h, "isohash2": iso2, "variables": int(nv), "clauses": int(nc)}
    return table


def sorted_copy(src, dst):
    clauses, cur, header = [], [], None
    for line in open(src):
        if line.startswith("c") or not line.strip():
            continue
        if line.startswith("p"):
            header = line.split()
            continue
        for tok in line.split():
            lit = int(tok)
            if lit == 0:
                clauses.append(tuple(sorted(cur, key=lambda x: (abs(x), x))))
                cur = []
            else:
                cur.append(lit)
    clauses.sort()
    with open(dst, "w") as f:
        f.write(f"p cnf {header[2]} {len(clauses)}\n")
        for cl in clauses:
            f.write(" ".join(map(str, cl)) + " 0\n")


def reference_file(h, cache):
    path = cache / f"{h}.cnf"
    if not path.exists():
        cache.mkdir(parents=True, exist_ok=True)
        data = urllib.request.urlopen(f"https://benchmark-database.de/file/{h}", timeout=120).read()
        path.write_bytes(lzma.decompress(data) if data[:6] == b"\xfd7zXZ\x00" else data)
    return path


def main(gen, only=None):
    meta = json.load(open(ROOT / "generators.json"))[gen]
    refs = json.load(open(ROOT / "references" / f"{gen}.json"))["references"]
    if only:
        refs = [r for r in refs if only in r["instance"]]
        if not refs:
            sys.exit(f"{gen}: no reference instance matches {only!r}")
    cache = ROOT / "references" / "cache"
    results = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        names = []
        for i, r in enumerate(refs):
            name = f"out{i}.cnf"
            with open(tmp / name, "w") as f:
                # the exit status is not checked: sgen1, for one, always returns 1
                subprocess.run(["docker", "run", "--rm", meta["image"], *r["args"]], stdout=f)
            if not any(line.startswith("p cnf") for line in open(tmp / name)):
                sys.exit(f"{gen}: no CNF produced for {r['instance']}")
            names.append(name)
        got = gbd(tmp, names)
        for i, r in enumerate(refs):
            g = got[names[i]]
            level = None
            matched = "GBD"
            if g["gbdhash"] == r["gbdhash"]:
                level = "N1"
            elif any(g["gbdhash"] == a["gbdhash"] for a in r.get("alternates", [])):
                level, matched = "N1", next(a["provenance"] for a in r["alternates"] if a["gbdhash"] == g["gbdhash"])
            else:
                matched = None
                ref = reference_file(r["gbdhash"], cache)
                (tmp / "ref").mkdir(exist_ok=True)
                sorted_copy(tmp / names[i], tmp / "ref" / f"a{i}.cnf")
                sorted_copy(ref, tmp / "ref" / f"b{i}.cnf")
                pair = gbd(tmp / "ref", [f"a{i}.cnf", f"b{i}.cnf"])
                refcounts = gbd(ref.parent, [ref.name])[ref.name]
                if pair[f"a{i}.cnf"]["gbdhash"] == pair[f"b{i}.cnf"]["gbdhash"]:
                    level = "N2"
                elif g["isohash2"] == r["isohash2"]:
                    level = "N3"
                elif (g["variables"], g["clauses"]) == (refcounts["variables"], refcounts["clauses"]):
                    level = "N4"
            results.append({"instance": r["instance"], "args": r["args"], "expected": r["gbdhash"],
                            "got": g["gbdhash"], "level": level or "--",
                            **({"matched": matched} if level == "N1" and matched != "GBD" else {})})
    (ROOT / "results").mkdir(exist_ok=True)
    out = ROOT / "results" / (f"{gen}.json" if not only else f"{gen}-{only}.json")
    json.dump({"generator": gen, "image": meta["image"], "subset": only, "results": results},
              open(out, "w"), indent=2)
    counts = {}
    for x in results:
        counts[x["level"]] = counts.get(x["level"], 0) + 1
        extra = f'  (matches {x["matched"]})' if "matched" in x else ""
        print(f'{x["level"]:3} {x["instance"]:40} {" ".join(x["args"])}{extra}')
    print("summary:", dict(sorted(counts.items())))


if __name__ == "__main__":
    main(*sys.argv[1:3])
