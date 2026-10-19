"""The catalogue: one recipe per directory, read by every tool here.

A direct CNF generator lives in cnf/<name>/ with its Dockerfile, its meta.json
and, when it has any, its references.json.  A bridge lives in bridges/<name>/
with one reference file per upstream collection it consumes, under references/.
Nothing is shared between recipes, so adding one is adding a directory.

A target is the name of a generator, "sgen1", or a bridge and one of its
collections, "aiger/hwmcc10".
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def entries(root: Path = ROOT) -> dict:
    """target -> {meta, references path, kind, recipe directory}"""
    out = {}
    for d in sorted((root / "cnf").glob("*/")):
        meta_path = d / "meta.json"
        if not meta_path.exists():
            continue
        refs = d / "references.json"
        out[d.name] = {"key": d.name, "name": d.name, "dir": d, "kind": "generator",
                       "meta": json.load(open(meta_path)),
                       "references": refs if refs.exists() else None}
    for d in sorted((root / "bridges").glob("*/")):
        meta_path = d / "meta.json"
        if not meta_path.exists():
            continue
        meta = json.load(open(meta_path))
        sets = sorted((d / "references").glob("*.json")) if (d / "references").exists() else []
        if not sets:
            out[d.name] = {"key": d.name, "name": d.name, "dir": d, "kind": "bridge",
                           "meta": meta, "references": None}
        for s in sets:
            out[f"{d.name}/{s.stem}"] = {"key": f"{d.name}/{s.stem}", "name": d.name, "dir": d, "kind": "bridge",
                                         "collection": s.stem, "meta": meta, "references": s}
    return out


def one(target: str, root: Path = ROOT) -> dict:
    cat = entries(root)
    if target not in cat:
        raise SystemExit(f"unknown target {target!r}; known: {', '.join(sorted(cat))}")
    return cat[target]


def slug(target: str) -> str:
    """A target as a file name: aiger/hwmcc10 -> aiger-hwmcc10."""
    return target.replace("/", "-")


def collections(root: Path = ROOT) -> dict:
    out = {}
    for path in sorted((root / "collections").glob("*.json")):
        m = json.load(open(path))
        out[m["collection"]] = m
    return out
