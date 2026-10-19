#!/usr/bin/env python3
"""Match the solvers of the competition results with the images of SAT Heritage.

The detailed results name a solver as the competition did, "anders_satsuma-iter-kissat"
or "SBVA-sbva_cadical"; the companion project publishes it as satex/<name>:<year>.
This walks the rankings, guesses the image name, asks Docker Hub whether it
exists, and writes data/solvers.json, so that a family page can say not only
which solver was best but the command that runs it.
"""
import argparse, json, re, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HUB = "https://hub.docker.com/v2/repositories/satex/{}/tags?page_size=50"
ALIASES = {"sbva-sbva-cadical": "sbva-cadical", "kissat-sc2024": "kissat"}


def candidates(solver: str) -> list[str]:
    name = solver.split("[")[0]
    name = re.sub(r"^[a-z]+_(?=[a-z])", "", name)          # the submitting author's prefix, as in anders_satsuma
    name = name.lower().replace("_", "-").replace(".sh", "")
    out = [name, ALIASES.get(name, name), re.sub(r"-v?\d+(\.\d+)*$", "", name)]
    seen, uniq = set(), []
    for c in out:
        if c and c not in seen:
            seen.add(c); uniq.append(c)
    return uniq


def tags(repo: str, cache: dict) -> list:
    if repo in cache:
        return cache[repo]
    try:
        with urllib.request.urlopen(HUB.format(repo), timeout=40) as r:
            cache[repo] = [t["name"] for t in json.load(r).get("results", [])]
    except Exception:
        cache[repo] = []
    return cache[repo]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", default="data/solvers.json")
    args = ap.parse_args(argv)
    rankings = json.load(open(ROOT / "data" / "rankings.json"))
    cache, out, misses = {}, {}, 0
    for year, y in sorted(rankings["years"].items()):
        wanted = {s["solver"] for fam in y["families"].values() for s in fam["solvers"][:5]}
        for solver in sorted(wanted):
            hit = None
            for repo in candidates(solver):
                if year in tags(repo, cache):
                    hit = {"image": f"satex/{repo}:{year}", "repository": repo}
                    break
            out.setdefault(year, {})[solver] = hit
            misses += hit is None
        found = sum(1 for v in out[year].values() if v)
        print(f"{year}: {found} of {len(out[year])} solvers have an image", file=sys.stderr)
    json.dump({"note": "competition solver names matched with the images of sat-heritage/docker-images",
               "years": out}, open(ROOT / args.output, "w"), indent=1, sort_keys=True)
    print(f"wrote {args.output}; {misses} without an image", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
