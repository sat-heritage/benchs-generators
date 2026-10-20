#!/usr/bin/env python3
"""Produce a pack: instances we distribute ourselves, for a stated reason.

A pack is not the by-product of a generator, it is a publication.  Its spec, in
packs/<name>.json, says why it exists: a paper that needs the instances, or a
collection worth having in CNF as a whole, such as every circuit of a hardware
verification competition.

Two rules.  We do not republish what GBD already serves: an instance whose hash
is in GBD is linked, not copied, unless --keep-known is given.  And the hash of
a pack instance is the one GBD uses, so the instances nobody else has are
identified exactly like the competition ones.

    tools/make_pack.py hwmcc10-cnf --out ~/satheritage/packs
    tools/make_pack.py hwmcc10-cnf --out ~/satheritage/packs --limit 20   # a taste of it

The files land outside the repository, ready for a release; the index, which is
small, is written to data/packs/<name>.json.
"""
import argparse, json, re, sqlite3, subprocess, sys, tempfile, urllib.request, uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GBD_IMAGE = "satex-gen/gbd:0.4.2"
GBD_DB = "https://benchmark-database.de/getdatabase"
GBD_FILE = "https://benchmark-database.de/file"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import catalogue, fetch_upstream


def gbd_hashes(cache: Path) -> set:
    """Every instance GBD serves, so that a pack can leave them out."""
    db = cache / "gbd.db"
    if not db.exists():
        db.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(GBD_DB, timeout=600) as r:
            db.write_bytes(r.read())
    return {h for (h,) in sqlite3.connect(db).execute("select hash from features")}


def items_of(spec: dict) -> list[dict]:
    it = spec["items"]
    if it["kind"] == "list":
        return it["entries"]
    if it["kind"] == "pddl-grid":
        files = fetch_upstream.ensure(it["upstream_collection"])
        out = []
        for comp in it["competitions"]:
            for domain in sorted((files / comp / "domains").glob("*/")):
                if not (domain / "domain.pddl").exists():
                    continue
                if re.search(it.get("exclude_domains", "adl"), domain.name):
                    continue
                # instance-2 before instance-100: a planning task numbers its size
                def rank(path):
                    m = re.search(r"(\d+)", path.stem)
                    return (int(m.group(1)) if m else 0, path.stem)
                problems = sorted((domain / "instances").glob("*.pddl"), key=rank)[:it.get("instances_per_domain", 3)]
                for prob in problems:
                    for k in it["k"]:
                        out.append({"name": f"{comp}-{domain.name}-{prob.stem}-k{k}.cnf",
                                    "args": ["domain.pddl", f"instances/{prob.name}", it.get("method", "cr"), str(k)],
                                    "upstream": {"collection": it["upstream_collection"],
                                                 "dir": str(domain.relative_to(files))}})
        return out
    if it["kind"] == "mzn-grid":
        files = fetch_upstream.ensure(it["upstream_collection"])
        n = it.get("instances_per_problem", 2)
        out = []
        for year in it["years"]:
            for prob in sorted((files / str(year)).glob("*/")):
                models = sorted(prob.glob("*.mzn"), key=lambda q: q.stat().st_size)
                data = sorted((q for q in prob.iterdir() if q.suffix in (".dzn", ".json")),
                              key=lambda q: q.stat().st_size)
                if not models:
                    continue
                up = {"collection": it["upstream_collection"], "dir": f"{year}/{prob.name}"}
                if not data:
                    # some problems are self-contained models, one per instance
                    pairs = [(m, None) for m in models[:n]]
                else:
                    named = prob / f"{prob.name}.mzn"
                    model = named if named.exists() else models[0]
                    pairs = [(model, d) for d in data[:n]]
                for model, d in pairs:
                    stem = re.sub(r"[^A-Za-z0-9._-]", "-", (d or model).name.rsplit(".", 1)[0])
                    out.append({"name": f"mznc{year}-{prob.name}-{stem}.cnf",
                                "args": [model.name] + ([d.name] if d else []),
                                "upstream": up})
        return out
    if it["kind"] != "grid":
        sys.exit(f"unknown item kind: {it['kind']}")
    files = fetch_upstream.ensure(it["upstream_collection"])
    models = sorted(p.name for p in files.rglob("*.aig")) if it.get("models") == "all" else it["models"]
    out = []
    for model in models:
        for k in it.get("k", [None]):
            args = [a.replace("{k}", str(k)) for a in it["args"]]
            out.append({"name": f"{Path(model).stem}-k{k}.cnf" if k is not None else f"{Path(model).stem}.cnf",
                        "args": args,
                        "upstream": {"collection": it["upstream_collection"], "file": model}})
    return out


def produce(meta: dict, item: dict, dest: Path, timeout: int | None = None) -> int:
    mount, args = [], list(item["args"])
    if "upstream" in item and "dir" in item["upstream"]:      # a directory, as a planning domain needs
        files = fetch_upstream.ensure(item["upstream"]["collection"])
        mount = ["-v", f"{files / item['upstream']['dir']}:/data:ro"]
    elif "upstream" in item:
        files = fetch_upstream.ensure(item["upstream"]["collection"])
        member = next(files.rglob(item["upstream"]["file"]), None)
        if member is None:
            sys.exit(f"{item['upstream']['file']} is not in the collection")
        mount = ["-v", f"{member.parent}:/src:ro"]
        args = [a.replace("{file}", f"/src/{member.name}") for a in args]
    name = f"satex-pack-{uuid.uuid4().hex[:12]}"
    with open(dest / item["name"], "w") as f:
        try:
            return subprocess.run(["docker", "run", "--rm", "--name", name, *mount, meta["image"], *args],
                                  stdout=f, stderr=subprocess.DEVNULL, timeout=timeout).returncode
        except subprocess.TimeoutExpired:
            # the client is gone but the container is not: stop it by name
            subprocess.run(["docker", "kill", name], capture_output=True)
            return 124


def measure(directory: Path, names: list[str]) -> dict:
    out = subprocess.run(["docker", "run", "--rm", "-v", f"{directory}:/data", GBD_IMAGE, *names],
                         check=True, capture_output=True, text=True).stdout
    return {l.split("\t")[0]: l.split("\t")[1:] for l in out.splitlines()}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pack")
    ap.add_argument("--out", required=True, help="directory for the files, outside the repository")
    ap.add_argument("--limit", type=int, help="stop after this many instances, to size a pack before producing it")
    ap.add_argument("--keep-known", action="store_true", help="keep the instances GBD already serves")
    args = ap.parse_args(argv)

    spec = json.load(open(ROOT / "packs" / f"{args.pack}.json"))
    limit_clauses = spec.get("max_clauses")
    # what a non-zero exit of this image means, in the words of the pack
    reasons = {3: "not a classical planning domain: the translator refused it",
               4: "the encoder failed on a task the translator accepted",
               124: f"over the time limit of {spec.get('timeout_seconds')} seconds"}
    reasons.update({int(k): v for k, v in spec.get("skip_reasons", {}).items()})
    meta = catalogue.one(spec["generator"])["meta"]
    cache = fetch_upstream.DEFAULT_CACHE
    known = set() if args.keep_known else gbd_hashes(cache)
    items = items_of(spec)
    if args.limit:
        items = items[:args.limit]

    out = Path(args.out).expanduser() / args.pack
    out.mkdir(parents=True, exist_ok=True)
    index, linked, skipped, done = [], [], [], 0
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for item in items:
            code = produce(meta, item, tmp, spec.get("timeout_seconds"))
            path = tmp / item["name"]
            # an encoder refuses some inputs, an ADL domain for instance: note and move on
            if not path.exists() or not any(l.startswith("p cnf") for l in open(path, errors="replace")):
                why = reasons.get(code, f"exit {code}")
                skipped.append({"name": item["name"], "args": item["args"],
                                "upstream": item.get("upstream"), "reason": why})
                path.unlink(missing_ok=True)
                done += 1
                continue
            # an empty formula is a model with nothing to decide, and the hasher
            # segfaults on it rather than refusing it
            header = next((l.split() for l in open(path, errors="replace") if l.startswith("p cnf")), [])
            if len(header) == 4 and header[3] == "0":
                skipped.append({"name": item["name"], "args": item["args"], "clauses": 0,
                                "upstream": item.get("upstream"),
                                "reason": "an empty formula: the flattened model has nothing to decide"})
                path.unlink(missing_ok=True)
                done += 1
                continue
            try:
                h, iso2, nv, nc = measure(tmp, [item["name"]])[item["name"]]
            except (subprocess.CalledProcessError, KeyError, ValueError) as e:
                # the hash is what names an instance, so one we cannot hash is one
                # we cannot publish: note it and keep going rather than lose the pack
                skipped.append({"name": item["name"], "args": item["args"],
                                "upstream": item.get("upstream"),
                                "reason": f"the hasher could not read the formula ({type(e).__name__})"})
                path.unlink(missing_ok=True)
                done += 1
                continue
            done += 1
            if limit_clauses and int(nc) > limit_clauses:   # a pack is meant to be downloaded
                skipped.append({"name": item["name"], "args": item["args"], "clauses": int(nc),
                                "reason": f"over the limit of {limit_clauses} clauses"})
                path.unlink(missing_ok=True)
                continue
            if h in known:          # GBD already serves it: link, do not copy
                linked.append({"hash": h, "args": item["args"], "upstream": item.get("upstream"),
                               "gbd_url": f"{GBD_FILE}/{h}"})
                (tmp / item["name"]).unlink()
            else:
                subprocess.run(["xz", "-9", "-T0", "-f", str(tmp / item["name"])], check=True)
                packed = out / (item["name"] + ".xz")
                packed.write_bytes((tmp / (item["name"] + ".xz")).read_bytes())
                (tmp / (item["name"] + ".xz")).unlink()
                index.append({"file": packed.name, "bytes": packed.stat().st_size, "hash": h,
                              "isohash2": iso2, "variables": int(nv), "clauses": int(nc),
                              "args": item["args"], "upstream": item.get("upstream")})
            if done % 25 == 0:
                print(f"  {done}/{len(items)}: {len(index)} kept, {len(linked)} already in GBD", file=sys.stderr)

    doc = {"pack": args.pack, "title": spec["title"], "why": spec["why"], "generator": spec["generator"],
           "image": meta["image"], "instances": len(index), "bytes": sum(e["bytes"] for e in index),
           "linked_to_gbd": len(linked), "not_encodable": len(skipped),
           "files": index, "linked": linked, "skipped": skipped}
    (ROOT / "data" / "packs").mkdir(parents=True, exist_ok=True)
    json.dump(doc, open(ROOT / "data" / "packs" / f"{args.pack}.json", "w"), indent=1)
    print(f"{len(index)} instances kept ({doc['bytes'] / 1e6:.1f} MB), {len(linked)} left to GBD, "
          f"{len(skipped)} the encoder refused -> {out}",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
