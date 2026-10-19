#!/usr/bin/env python3
"""Run each generator across its parameter range and record what it produces.

Reproducing the instances a competition used is only half of what a generator
is for: the other half is making new ones, bigger, smaller, or simply never
submitted anywhere.  This tool runs the sample invocations declared in
generators.json, records the size of each formula and checks that the same
command twice gives the same formula, and writes data/samples.json for the site.

    tools/sample_generators.py              # every generator that declares samples
    tools/sample_generators.py aiger crux   # only these
"""
import argparse, json, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GBD_IMAGE = "satex-gen/gbd:0.4.2"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import catalogue, fetch_upstream


def measure(directory: Path, names: list[str]) -> dict:
    out = subprocess.run(["docker", "run", "--rm", "-v", f"{directory}:/data", GBD_IMAGE, *names],
                         check=True, capture_output=True, text=True).stdout
    table = {}
    for line in out.splitlines():
        path, h, iso2, nv, nc = line.split("\t")
        table[path] = {"hash": h, "variables": int(nv), "clauses": int(nc)}
    return table


def run(gen: str, meta: dict, samples: list[dict]) -> list[dict]:
    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        names = []
        for i, s in enumerate(samples):
            mount, args = [], list(s["args"])
            if "upstream" in s:
                files = fetch_upstream.ensure(s["upstream"]["collection"])
                member = next(files.rglob(s["upstream"]["file"]), None)
                if member is None:
                    sys.exit(f"{gen}: {s['upstream']['file']} is not in the collection")
                mount = ["-v", f"{member.parent}:/src:ro"]
                args = [a.replace("{file}", f"/src/{member.name}") for a in args]
            for run_id in (1, 2):          # twice, to see whether the command is reproducible
                name = f"s{i}-{run_id}.cnf"
                with open(tmp / name, "w") as f:
                    subprocess.run(["docker", "run", "--rm", *mount, meta["image"], *args], stdout=f)
                names.append(name)
        table = measure(tmp, names)
        for i, s in enumerate(samples):
            a, b = table[f"s{i}-1.cnf"], table[f"s{i}-2.cnf"]
            rows.append({"label": s.get("label") or " ".join(s["args"]),
                         "args": s["args"],
                         **({"upstream": s["upstream"]} if "upstream" in s else {}),
                         "variables": a["variables"], "clauses": a["clauses"],
                         "reproducible": a["hash"] == b["hash"]})
            print(f"{gen:12} {rows[-1]['label']:34} {a['variables']:9} vars {a['clauses']:10} clauses"
                  f"{'' if rows[-1]['reproducible'] else '   NOT REPRODUCIBLE'}", file=sys.stderr)
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("generators", nargs="*")
    ap.add_argument("--output", default="data/samples.json")
    args = ap.parse_args(argv)
    doc = json.load(open(ROOT / args.output)) if (ROOT / args.output).exists() else {}
    for target, entry in catalogue.entries().items():
        if args.generators and target not in args.generators:
            continue
        samples = entry["meta"].get("samples")
        if not samples:
            continue
        doc[target] = run(target, entry["meta"], samples)
    json.dump(doc, open(ROOT / args.output, "w"), indent=1)
    print(f"wrote {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
