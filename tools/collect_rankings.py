#!/usr/bin/env python3
"""Per-family solver rankings from the detailed results published by the SAT competitions.

The competitions publish, for some years, the runtime of every solver on every
instance, keyed by the GBD hash.  GBD gives the family of each instance.  Joining
the two gives, for one family, the ranking the solvers would have had on that
family alone, which is often not the overall ranking.

Writes data/rankings.json, used by tools/build_site.py.  Run it again to refresh.
"""
import argparse, csv, io, json, sqlite3, sys, tempfile, urllib.request, zipfile
from collections import defaultdict
from pathlib import Path

GBD_DB = "https://benchmark-database.de/getdatabase"
SOURCES = {
    "2023": {"zip": "https://satcompetition.github.io/2023/downloads/sc2023-detailed-results.zip",
             "member": "results_main_detailed.csv", "meta": "bench_meta.csv", "timeout": 5000.0},
    "2024": {"zip": "https://satcompetition.github.io/2024/downloads/detailed_results.zip",
             "member": "detailed_main.csv", "meta_url": "https://satcompetition.github.io/2024/downloads/meta.csv",
             "timeout": 5000.0},
    "2026": {"csv": "https://satcompetition.github.io/2026/downloads/scores.csv",
             "track": "[main]", "timeout": 5000.0},
}
MIN_INSTANCES = 8      # below that a family ranking says little
KEEP_SOLVERS = 12      # solvers kept per family in the data file


def fetch(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=600) as r:
        return r.read()


def gbd_families(cache: Path) -> dict:
    """hash -> (family, author), from the live GBD database."""
    db = cache / "gbd.db"
    if not db.exists():
        db.write_bytes(fetch(GBD_DB))
    con = sqlite3.connect(db)
    return {h: (fam, auth) for h, fam, auth in con.execute("select hash, family, author from features")}


def wide_table(text: str, timeout: float) -> dict:
    """One row per instance, one column per solver, runtime as the value."""
    rows = list(csv.DictReader(io.StringIO(text)))
    solvers = [k for k in rows[0] if k not in ("hash", "result", "aresult") and k]
    out = {}
    for r in rows:
        times = {}
        for s in solvers:
            try:
                times[s] = float(r[s])
            except (TypeError, ValueError):
                times[s] = timeout      # no verified answer counts as a timeout
        out[r["hash"]] = times
    return out


def load(year: str, spec: dict, families: dict, cache: Path):
    if "zip" in spec:
        blob = cache / f"{year}.zip"
        if not blob.exists():
            blob.write_bytes(fetch(spec["zip"]))
        z = zipfile.ZipFile(blob)
        data = wide_table(z.read(spec["member"]).decode(), spec["timeout"])
        if "meta" in spec:
            meta = {r["hash"]: (r["family"], r["author"])
                    for r in csv.DictReader(io.StringIO(z.read(spec["meta"]).decode()))}
        else:
            meta = {r["hash"]: (r["family"], r["author"])
                    for r in csv.DictReader(io.StringIO(fetch(spec["meta_url"]).decode()), delimiter=" ")}
    else:
        blob = cache / f"{year}.csv"
        if not blob.exists():
            blob.write_bytes(fetch(spec["csv"]))
        data = defaultdict(dict)
        for r in csv.DictReader(open(blob)):
            if spec["track"] not in r["solverid"]:
                continue
            try:
                data[r["instanceid"]][r["solverid"].split("[")[0]] = float(r["runtime"])
            except ValueError:
                continue
        meta = {}
    meta = {h: meta.get(h) or families.get(h, ("unknown", "unknown")) for h in data}
    return data, meta


def rank(data: dict, meta: dict, timeout: float):
    """PAR-2 per solver, overall and per family: solved runs count their time, the others twice the limit."""
    groups = defaultdict(list)
    for h, times in data.items():
        groups[meta[h][0]].append(times)
        groups["ALL"].append(times)
    out = {}
    for fam, rows in groups.items():
        if fam != "ALL" and len(rows) < MIN_INSTANCES:
            continue
        score, solved = defaultdict(float), defaultdict(int)
        for times in rows:
            for s, t in times.items():
                if t >= timeout:
                    score[s] += 2 * timeout
                else:
                    score[s] += t
                    solved[s] += 1
        order = sorted(score, key=lambda s: (score[s], -solved[s]))
        out[fam] = {"instances": len(rows),
                    "solvers": [{"solver": s, "par2": round(score[s] / len(rows), 1), "solved": solved[s]}
                                for s in order[:KEEP_SOLVERS]]}
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", default="data/rankings.json")
    ap.add_argument("--cache", default=None, help="directory keeping the downloads between runs")
    args = ap.parse_args(argv)
    cache = Path(args.cache) if args.cache else Path(tempfile.mkdtemp(prefix="satrank-"))
    cache.mkdir(parents=True, exist_ok=True)

    families = gbd_families(cache)
    doc = {"source": "detailed results published by the SAT competitions, joined with the GBD database",
           "measure": "PAR-2 per instance: the runtime when solved, twice the time limit otherwise",
           "years": {}, "instance_family": {}}
    for year, spec in SOURCES.items():
        data, meta = load(year, spec, families, cache)
        doc["years"][year] = {"instances": len(data), "timeout": spec["timeout"], "families": rank(data, meta, spec["timeout"])}
        print(f"{year}: {len(data)} instances, {len(doc['years'][year]['families']) - 1} families kept", file=sys.stderr)

    # the families of the instances our own generators reproduce
    for ref in sorted(Path("references").glob("*.json")):
        for entry in json.load(open(ref))["references"]:
            fam = families.get(entry["gbdhash"])
            if fam:
                doc["instance_family"][entry["gbdhash"]] = list(fam)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    json.dump(doc, open(args.output, "w"), indent=1, sort_keys=True)
    print(f"wrote {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
