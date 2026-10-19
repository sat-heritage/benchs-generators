#!/usr/bin/env python3
"""Fetch an upstream benchmark collection into a local cache.

This repository never redistributes the benchmarks of another competition: it
keeps a manifest in collections/<collection>.json, with the address of the archive
and its checksum, and this tool downloads it into a cache directory outside the
repository.  With --record it writes back the checksums it observed, so that a
later run can verify them.

    tools/fetch_upstream.py hwmcc10                 # download and extract
    tools/fetch_upstream.py hwmcc10 --record        # and write the checksums
    tools/fetch_upstream.py hwmcc10 --path bobsm5378d2.aig   # print one path
"""
import argparse, hashlib, json, os, shutil, subprocess, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CACHE = Path(os.environ.get("SATEX_BENCH_CACHE", Path.home() / ".cache" / "satex-benchs"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"fetching {url}", file=sys.stderr)
    with urllib.request.urlopen(url, timeout=600) as r, open(dest, "wb") as f:
        shutil.copyfileobj(r, f)


def extract(archive: Path, fmt: str, into: Path) -> None:
    into.mkdir(parents=True, exist_ok=True)
    if fmt == "7z":
        tool = shutil.which("7z") or shutil.which("7za") or shutil.which("7zr")
        if tool:
            subprocess.run([tool, "x", "-y", f"-o{into}", str(archive)], check=True, stdout=subprocess.DEVNULL)
        else:   # no 7z on this machine: borrow one from a container, like everything else here
            subprocess.run(["docker", "run", "--rm", "-v", f"{archive.parent}:/a", "-v", f"{into}:/out",
                            "debian:bookworm-slim", "sh", "-c",
                            "apt-get update -qq && apt-get install -y -qq p7zip-full >/dev/null && "
                            f"7z x -y -o/out /a/{archive.name} >/dev/null"], check=True)
    elif fmt in ("tar.bz2", "tar.gz", "tar.xz", "tar"):
        subprocess.run(["tar", "xf", str(archive), "-C", str(into)], check=True)
    elif fmt == "zip":
        subprocess.run(["unzip", "-q", "-o", str(archive), "-d", str(into)], check=True)
    else:
        sys.exit(f"unknown archive format: {fmt}")


def collection_dir(name: str, cache: Path) -> Path:
    return cache / name


def ensure(name: str, cache: Path = DEFAULT_CACHE, record: bool = False) -> Path:
    manifest_path = ROOT / "collections" / f"{name}.json"
    manifest = json.load(open(manifest_path))
    spec = manifest["archive"]
    here = collection_dir(name, cache)
    archive = here / Path(spec["url"]).name
    if not archive.exists():
        download(spec["url"], archive)
    digest = sha256(archive)
    if spec.get("sha256") and spec["sha256"] != digest:
        sys.exit(f"{name}: the archive changed upstream\n  expected {spec['sha256']}\n  found    {digest}")
    files = here / "files"
    if not files.exists() or not any(files.iterdir()):
        extract(archive, spec.get("format", "7z"), files)
    if record:
        spec["sha256"] = digest
        spec["bytes"] = archive.stat().st_size
        members = sorted(p for p in files.rglob("*") if p.is_file())
        manifest["members"] = {str(p.relative_to(files)): {"bytes": p.stat().st_size, "sha256": sha256(p)}
                               for p in members}
        json.dump(manifest, open(manifest_path, "w"), indent=1, sort_keys=False)
        print(f"recorded {len(members)} members in {manifest_path.relative_to(ROOT)}", file=sys.stderr)
    return files


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("collection")
    ap.add_argument("--cache", default=str(DEFAULT_CACHE))
    ap.add_argument("--record", action="store_true", help="write the observed checksums back into the manifest")
    ap.add_argument("--path", help="print the cached path of one member and exit")
    args = ap.parse_args(argv)
    files = ensure(args.collection, Path(args.cache), args.record)
    if args.path:
        hits = [p for p in files.rglob(args.path)]
        if not hits:
            sys.exit(f"{args.path}: not in the collection")
        print(hits[0])
    else:
        print(files)
    return 0


if __name__ == "__main__":
    sys.exit(main())
