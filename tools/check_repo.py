#!/usr/bin/env python3
"""Check that the repository holds together, without building anything.

It is the cheap half of the verification: every recipe readable, every field
present, every path real, every reference pointing at a collection we know.
The expensive half, building the images and regenerating the instances, needs
Docker and runs on a machine with it.
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import catalogue

ROOT = catalogue.ROOT
REQUIRED = ["name", "authors", "authors_source", "license", "image", "usage"]


def main() -> int:
    problems = []
    cat = catalogue.entries()
    cols = catalogue.collections()
    if not cat:
        problems.append("no recipe found under cnf/ or bridges/")
    for target, entry in cat.items():
        meta, d = entry["meta"], entry["dir"]
        for field in REQUIRED:
            if not meta.get(field):
                problems.append(f"{target}: meta.json has no {field}")
        if "publish_image" not in meta:
            problems.append(f"{target}: meta.json does not say whether the image may be published")
        if not (d / "Dockerfile").exists():
            problems.append(f"{target}: no Dockerfile in {d}")
        if entry["kind"] == "bridge" and entry.get("collection") and entry["collection"] not in cols:
            problems.append(f"{target}: collection {entry.get('collection')!r} has no manifest in collections/")
        if entry["references"]:
            refs = json.load(open(entry["references"]))["references"]
            for r in refs:
                if not r.get("gbdhash") or len(r["gbdhash"]) != 32:
                    problems.append(f"{target}: {r.get('instance')} has no usable hash")
                if "upstream" in r and r["upstream"]["collection"] not in cols:
                    problems.append(f"{target}: {r['instance']} needs unknown collection {r['upstream']['collection']}")
                if "{file}" in " ".join(r["args"]) and "upstream" not in r:
                    problems.append(f"{target}: {r['instance']} asks for a file but names no collection")
    for name, m in cols.items():
        for field in ("name", "archive", "terms", "redistribute"):
            if field not in m:
                problems.append(f"collections/{name}.json has no {field}")
    for spec in sorted((ROOT / "packs").glob("*.json")):
        s = json.load(open(spec))
        if s.get("generator") not in cat:
            problems.append(f"packs/{spec.name}: unknown target {s.get('generator')!r}")
        if not s.get("why"):
            problems.append(f"packs/{spec.name}: a pack must say why it exists")
    for p in problems:
        print(p, file=sys.stderr)
    print(f"{len(cat)} recipes, {len(cols)} collections, {len(problems)} problems", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
