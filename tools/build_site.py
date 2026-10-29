#!/usr/bin/env python3
"""Build the static website of the SAT Heritage benchmark generators.

Reads generators.json, references/*.json, results/*.json and data/rankings.json,
and writes a small static site: an overview, one page per generator, one page per
competition benchmark family with the solver ranking on that family, and a page
explaining how the regenerated instances are checked.
"""
import argparse, html, json, re, shutil, sys
from collections import defaultdict
from pathlib import Path

REPO_URL = "https://github.com/sat-heritage/benchs-generators"
SOLVERS_URL = "https://github.com/sat-heritage/docker-images"
SOLVERS_SITE = "https://sat-heritage.github.io/docker-images/"
GBD_URL = "https://benchmark-database.de"
AUTHORS = "Gilles Audemard, Loïc Paulevé and Laurent Simon"

LEVELS = ["N1", "N2", "N3", "N4", "--"]
LEVEL_LABEL = {
    "N1": "same GBD hash",
    "N2": "same up to the order of clauses",
    "N3": "same up to a renaming of the variables",
    "N4": "same number of variables and clauses",
    "--": "no match",
}
LEVEL_CLASS = {"N1": "ok", "N2": "ok", "N3": "warn", "N4": "warn", "--": "fail"}


def esc(v) -> str:
    return html.escape(str(v if v is not None else ""), quote=True)


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(name).lower()).strip("-") or "unnamed"


UPSTREAM = {}
SAMPLES = {}
ROOT_DIR = Path(".")
SOLVERS = {}
PACKS = []


def load(root: Path):
    sys.path.insert(0, str((root / "tools").resolve()))
    import catalogue
    if (root / "data" / "samples.json").exists():
        SAMPLES.update(json.load(open(root / "data" / "samples.json")))
    if (root / "data" / "solvers.json").exists():
        SOLVERS.update(json.load(open(root / "data" / "solvers.json"))["years"])
    UPSTREAM.update(catalogue.collections(root))
    for spec_path in sorted((root / "packs").glob("*.json")):
        spec = json.load(open(spec_path))
        index_path = root / "data" / "packs" / f"{spec['pack']}.json"
        PACKS.append((spec, json.load(open(index_path)) if index_path.exists() else None))
    rankings = json.load(open(root / "data" / "rankings.json"))
    fam_of = {h: tuple(v) for h, v in rankings["instance_family"].items()}
    size_of = {h: n for h, n in rankings.get("instance_file", {}).items()}
    gens = {}
    for key, entry in catalogue.entries(root).items():
        g = dict(entry["meta"])
        g["kind"], g["collection"] = entry["kind"], entry.get("collection")
        g["dirpath"] = str(entry["dir"].relative_to(root))
        gens[key] = g
        refs = json.load(open(entry["references"]))["references"] if entry["references"] else []
        levels = {}
        for path in sorted((root / "results").glob(f"{catalogue.slug(key)}*.json")):
            for r in json.load(open(path))["results"]:
                levels[r["instance"]] = r
        for r in refs:
            got = levels.get(r["instance"])
            r["level"] = got["level"] if got else None
            r["matched"] = (got or {}).get("matched")
            r["family"], r["family_author"] = fam_of.get(r["gbdhash"], ("unknown", ""))
            r["size"] = size_of.get(r["gbdhash"])
            for a in r.get("alternates", []):
                a["size"] = size_of.get(a["gbdhash"])
        g["key"] = key
        g["slug"] = catalogue.slug(key)
        g["references"] = refs
        g["checked"] = [r for r in refs if r["level"]]
        g["exact"] = [r for r in refs if r["level"] == "N1"]
        g["families"] = sorted({r["family"] for r in refs if r["family"] != "unknown"})
    return gens, rankings


CSS = """
:root { --bg:#ffffff; --bg2:#f8f9fb; --card:#ffffff; --ink:#0b0b0b; --muted:#5e6572; --line:#e5e7eb;
        --ok:#1a7f37; --warn:#9a6700; --fail:#cf222e; --none:#8c959f; --accent:#0b57d0; --hf:#6fd3c7;
        --hfdark:#2aa197; --cap:#0550ae; --capbg:#e8f1ff; --warnbg:#effbf9; --grid:#e5e7eb; }
@media (prefers-color-scheme: dark) { :root { --bg:#0b0f19; --bg2:#111827; --card:#161b26; --ink:#f3f4f6;
        --muted:#9aa3b2; --line:#2a3140; --ok:#3fb950; --warn:#d29922; --fail:#f85149; --none:#6e7681;
        --accent:#7ab4ff; --hf:#2aa197; --hfdark:#6fd3c7; --cap:#9ecbff; --capbg:#12305c; --warnbg:#0d2b29; --grid:#2a3140; } }
* { box-sizing:border-box; }
body { margin:0; font:15px/1.5 -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; color:var(--ink); background:var(--bg); }
a { color:var(--accent); text-decoration:none; } a:hover { text-decoration:underline; }
header { padding:16px 24px; border-bottom:1px solid var(--line); background:var(--card); display:flex; align-items:center; gap:18px; flex-wrap:wrap; }
header .logo { display:flex; align-items:center; gap:10px; font-weight:700; font-size:20px; color:inherit; }
header .logo span.dot { width:26px; height:26px; border-radius:8px; background:var(--hf); display:inline-block; }
header nav a { margin-right:16px; color:var(--ink); font-weight:500; } header nav a.active { border-bottom:2px solid var(--hf); }
header p { margin:0; color:var(--muted); margin-left:auto; max-width:620px; }
.warning { max-width:1200px; margin:16px auto 0; padding:12px 18px; border:1px solid var(--hfdark); border-left:6px solid var(--hf); background:var(--warnbg); border-radius:10px; font-size:15px; }
main { max-width:1200px; margin:0 auto; padding:20px 24px 60px; }
.hero { padding:22px 0 6px; } .hero h1 { font-size:32px; margin:0 0 6px; } .hero p { color:var(--muted); font-size:17px; margin:0 0 16px; max-width:820px; }
.stats { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:12px; margin:8px 0 22px; }
.stat { background:var(--card); border:1px solid var(--line); border-radius:12px; padding:14px 16px; }
.stat .n { font-size:28px; font-weight:700; } .stat .l { color:var(--muted); font-size:13px; }
.grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); gap:14px; }
.card { background:var(--card); border:1px solid var(--line); border-radius:12px; padding:14px 16px; display:flex; flex-direction:column; gap:6px; }
a.card:hover { text-decoration:none; border-color:var(--accent); }
.card h3 { margin:0; font-size:16px; } .card .meta { color:var(--muted); font-size:13px; }
.tags { display:flex; flex-wrap:wrap; gap:6px; margin-top:4px; }
.tag { font-size:12px; padding:2px 8px; border-radius:999px; border:1px solid var(--line); color:var(--muted); }
.tag.cap { border-color:transparent; background:var(--capbg); color:var(--cap); }
.badge { font-size:12px; padding:2px 8px; border-radius:999px; color:#fff; }
.badge.ok { background:var(--ok); } .badge.warn { background:var(--warn); } .badge.fail { background:var(--fail); } .badge.none { background:var(--none); }
.section { background:var(--card); border:1px solid var(--line); border-radius:12px; padding:16px 18px; margin:16px 0; }
.section h2 { margin:0 0 10px; font-size:17px; }
dl { display:grid; grid-template-columns:max-content 1fr; gap:6px 16px; margin:0; } dt { color:var(--muted); } dd { margin:0; word-break:break-word; }
pre { background:var(--bg2); border:1px solid var(--line); border-radius:8px; padding:10px 12px; overflow-x:auto; font-size:13px; }
code { background:var(--bg2); padding:1px 5px; border-radius:4px; font-size:13px; }
table { border-collapse:collapse; width:100%; font-size:14px; } td, th { text-align:left; padding:5px 8px; border-bottom:1px solid var(--line); vertical-align:top; }
th { color:var(--muted); font-weight:600; } td.num, th.num { text-align:right; font-variant-numeric:tabular-nums; }
.tablewrap { overflow-x:auto; }
.crumbs { color:var(--muted); font-size:14px; margin-bottom:8px; }
.rank1 td { font-weight:600; }
.bar { display:block; height:8px; border-radius:4px; background:var(--hf); }
.legend { color:var(--muted); font-size:13px; margin:-6px 0 14px; }
a.dl { display:inline-flex; align-items:baseline; gap:5px; white-space:nowrap; }
svg.dl { width:13px; height:13px; align-self:center; stroke:currentColor; fill:none; stroke-width:2; stroke-linecap:round; stroke-linejoin:round; }
.sz { color:var(--muted); font-size:12px; font-variant-numeric:tabular-nums; }
.nolink { color:var(--muted); }
.toolbar { display:flex; flex-wrap:wrap; gap:10px; align-items:center; margin:8px 0 18px; padding:12px 14px; background:var(--bg2); border:1px solid var(--line); border-radius:14px; }
.toolbar input, .toolbar select { font:inherit; padding:8px 10px; border:1px solid var(--line); border-radius:999px; background:var(--card); color:var(--ink); }
.count { color:var(--muted); margin-left:auto; font-size:14px; }
footer { color:var(--muted); font-size:13px; text-align:center; padding:20px 24px 28px; max-width:900px; margin:0 auto; }
"""

NAV = [("index.html", "Overview", "overview"), ("your-problem.html", "Your problem", "yours"),
       ("generators.html", "Generators", "generators"), ("bridges.html", "Bridges", "bridges"),
       ("packs.html", "Packs", "packs"), ("families.html", "Families", "families"), ("verification.html", "Verification", "verification")]


def page(title: str, body: str, depth: int, active: str = "") -> str:
    root = "../" * depth
    cls = ' class="active"'
    nav = "".join(f'<a href="{root}{href}"{cls if active == key else ""}>{label}</a>'
                  for href, label, key in NAV) + f'<a href="{REPO_URL}">GitHub</a>'
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · SAT Heritage generators</title><link rel="stylesheet" href="{root}style.css"></head>
<body><header><a class="logo" href="{root}index.html"><span class="dot"></span>SAT Heritage generators</a>
<nav>{nav}</nav>
<p>The programs that produce SAT benchmarks, each as a Docker image: the families the competitions used, and others that live outside them, in papers and in solver tuning.</p></header>
<div class="warning"><b>A pilot, and a collective one: please check, correct and contribute.</b> Everything here is generated from the data of the <a href="{REPO_URL}">sat-heritage/benchs-generators</a> repository. A generator whose licence is unknown has its recipe published but no image, and a family with no generator is one we could not find or could not run: corrections, missing generators and licence clarifications are welcome as <a href="{REPO_URL}/pulls">pull requests</a> or <a href="{REPO_URL}/issues">issues</a>. Adding your own generator takes four files, or just an issue with a link to your code: see <a href="{REPO_URL}#adding-a-generator">adding a generator</a>. The companion project for solvers is <a href="{SOLVERS_SITE}">SAT Heritage</a>.</div>
<main>{body}</main>
<footer>Generated from the <a href="{REPO_URL}">sat-heritage/benchs-generators</a> repository · solver rankings computed from the detailed results published by the SAT competitions, joined with <a href="{GBD_URL}">GBD</a> · a project by {esc(AUTHORS)}, assembled with the help of an AI assistant: check every claim against the original competition material.</footer></body></html>
"""


DOWNLOAD_ICON = ('<svg class="dl" viewBox="0 0 24 24" aria-hidden="true">'
                 '<path d="M12 3v12M7 11l5 5 5-5M5 21h14"/></svg>')


def human_size(n: int) -> str:
    if n >= 1024 * 1024:
        return f"{n / (1024 * 1024):.1f} MB"
    if n >= 1024:
        return f"{n / 1024:.0f} kB"
    return f"{n} B"


def gbd_link(h: str, size, label: str = "") -> str:
    """Download link to the instance GBD serves, with its compressed size."""
    if size is None:
        return f'<span class="nolink" title="GBD does not serve this instance">{esc(h[:12])}…</span>'
    title = f"download {label or 'this instance'} from GBD, {human_size(size)} compressed"
    return (f'<a class="dl" href="{GBD_URL}/file/{esc(h)}" title="{esc(title)}">{DOWNLOAD_ICON}'
            f'{esc(h[:12])}… <span class="sz">{human_size(size)}</span></a>')


def level_badge(level: str) -> str:
    if not level:
        return '<span class="badge none">not checked</span>'
    return f'<span class="badge {LEVEL_CLASS[level]}" title="{esc(LEVEL_LABEL[level])}">{level}</span>'


def gen_card(g: dict) -> str:
    exact, checked = len(g["exact"]), len(g["checked"])
    pub = "image published" if g.get("publish_image") else "recipe only, licence unknown"
    kind = '<span class="tag cap">bridge</span>' if g.get("kind") == "bridge" else ""
    return f"""<a class="card" href="generators/{esc(g['slug'])}.html">
<h3>{esc(g['name'])}{(' · ' + esc(g['collection'])) if g.get('collection') else ''}</h3>
<div class="meta">{esc(g.get('authors',''))} · {esc(g.get('year',''))}</div>
<div class="tags">{kind}<span class="tag">{esc(g.get('language',''))}</span><span class="tag">{esc(g.get('license',''))}</span><span class="tag cap">{esc(pub)}</span></div>
<div class="tags">{f'<span class="badge ok">{exact} of {checked} instances exact</span>' if checked else '<span class="badge none">no competition instance to check against</span>' if not g['references'] else f'<span class="badge warn">{exact} of {checked} instances exact</span>'}{"".join(f'<span class="tag">{esc(f)}</span>' for f in g['families'][:3])}</div>
</a>"""


def overview_page(gens: dict, rankings: dict) -> str:
    refs = sum(len(g["references"]) for g in gens.values())
    checked = sum(len(g["checked"]) for g in gens.values())
    exact = sum(len(g["exact"]) for g in gens.values())
    published = sum(1 for g in gens.values() if g.get("publish_image"))
    covered = {f for g in gens.values() for f in g["families"]}
    all_fams = {f for y in rankings["years"].values() for f in y["families"] if f != "ALL"}
    body = f"""<div class="hero"><h1>SAT benchmark generators, from the competitions and beyond</h1>
<p>A benchmark is only reproducible if the program that produced it still runs. This repository packages those programs as Docker images, pins their sources to one commit, and checks each image by regenerating known instances: same GBD hash, same instance. Many of these families were used by the competitions; others were never submitted to one, and serve in papers, in solver tuning or in cube and conquer experiments.</p></div>
<div class="stats">
<div class="stat"><div class="n">{len(gens)}</div><div class="l">generators packaged</div></div>
<div class="stat"><div class="n">{exact}</div><div class="l">instances regenerated exactly</div></div>
<div class="stat"><div class="n">{checked}</div><div class="l">reference instances checked, of {refs} recorded</div></div>
<div class="stat"><div class="n">{published}</div><div class="l">images publishable, the others lack a licence</div></div>
<div class="stat"><div class="n">{len(covered)}</div><div class="l">competition families with a generator here</div></div>
<div class="stat"><div class="n">{sum(1 for g in gens.values() if not g.get("competitions"))}</div><div class="l">generators whose families never went to a competition</div></div>
<div class="stat"><div class="n">{sum(1 for g in gens.values() if g.get("kind") == "bridge")}</div><div class="l">bridges: they encode what another competition distributes</div></div>
</div>
<h2>Generators</h2>
<p class="legend">They make instances out of parameters alone.</p>
<div class="grid">{"".join(gen_card(g) for g in sorted((g for g in gens.values() if g.get('kind') != 'bridge'), key=lambda g: g['name'].lower()))}</div>
<h2 style="margin-top:26px">Bridges</h2>
<p class="legend">They encode what another competition distributes, and never redistribute it. See <a href="bridges.html">bridges</a>.</p>
<div class="grid">{"".join(gen_card(g) for g in sorted((g for g in gens.values() if g.get('kind') == 'bridge'), key=lambda g: (g['name'].lower(), g.get('collection') or '')))}</div>
<div class="section"><h2>Where everything lives</h2>
<p>Three kinds of content, three places, on purpose. The <b>recipes and the metadata</b> are in the repository,
and nothing else is. The <b>sources of a generator that exists on no public repository</b> travel in a release,
with their author's permission and a record of where they come from. The <b>instances we produce ourselves</b>
travel in another release, as <a href="packs.html">packs</a>. The <b>benchmarks of other competitions</b> are
never copied here at all: we keep their manifest and fetch them into a local cache when a bridge runs.</p></div>
<div class="section"><h2>Instances nobody submitted</h2>
<p>Reproducing what a competition used is one half of the work; making new instances is the other. Every
generator page carries sample runs across its parameters, with the size of the formula each one produces, so
that a family can be taken further than the dozen instances a competition happened to keep. Those instances
are in no database, ours included: they are made on demand.</p></div>
<div class="section"><h2>Generators and bridges</h2>
<p>A generator makes an instance out of parameters alone. A bridge starts from an artefact another competition distributes, a circuit of the hardware model checking competition for instance, and encodes it into CNF with a pinned toolchain. We keep the manifest of each upstream collection, with its checksums and its terms, and fetch the files into a local cache: the benchmarks of another competition are never redistributed here.</p></div>
<div class="section"><h2>Where the rankings come from</h2>
<p>For the years whose detailed results are published, every solver's runtime on every instance is known, keyed by the same GBD hash we use. That gives, for each benchmark family, the ranking the solvers would have had on that family alone, which is regularly not the overall ranking. See the <a href="families.html">families</a>.</p>
<p class="legend">Years covered: {", ".join(sorted(rankings["years"]))} · {len(all_fams)} families with at least eight instances · measure: {esc(rankings["measure"])}.</p></div>"""
    return page("Overview", body, 0, "overview")


def generators_page(gens: dict) -> str:
    rows = []
    for g in sorted((g for g in gens.values() if g.get("kind") != "bridge"), key=lambda g: g["name"].lower()):
        rows.append(f"""<tr><td><a href="generators/{esc(g['slug'])}.html">{esc(g['name'])}</a></td>
<td>{esc(g.get('authors',''))}</td><td>{esc(g.get('year',''))}</td><td>{esc(g.get('language',''))}</td>
<td>{esc(g.get('license',''))}</td><td>{'yes' if g.get('publish_image') else 'no'}</td>
<td class="num">{len(g['exact'])} / {len(g['checked'])}</td>
<td>{", ".join(esc(f) for f in g['families']) or '<span class="tag">no competition family recorded</span>'}</td></tr>""")
    body = f"""<div class="hero"><h1>Generators</h1><p>A generator makes an instance out of parameters alone. One image each, built from the author's own sources at a pinned commit. The programs that start from someone else's artefacts are on the <a href="bridges.html">bridges</a> page.</p></div>
<div class="section tablewrap"><table><tr><th>Generator</th><th>Authors</th><th>Year</th><th>Language</th><th>Licence</th><th>Image published</th><th class="num">Exact / checked</th><th>Families</th></tr>{"".join(rows)}</table></div>"""
    return page("Generators", body, 0, "generators")


def bridges_page(gens: dict, rankings: dict) -> str:
    rows = []
    for g in sorted((g for g in gens.values() if g.get("kind") == "bridge"),
                    key=lambda g: (g["name"].lower(), g.get("collection") or "")):
        # a bridge with no reference instances has no collection in its key, but
        # its recipe still says which collections it consumes: that is the row
        name = g.get("collection") or next(iter(g.get("collections", {})), None)
        up = UPSTREAM.get(name) or {}
        size = f"{up['archive']['bytes'] / 1e6:.0f} MB" if up.get("archive", {}).get("bytes") else "—"
        rows.append(f"""<tr><td><a href="generators/{esc(g['slug'])}.html">{esc(g['name'])}</a></td>
<td>{esc(name or '—')}</td>
<td>{(f'<a href="{esc(up["homepage"])}">' + esc(up['name']) + '</a>') if up.get('homepage') else esc(up.get('name', '—'))}</td>
<td class="num">{size}</td>
<td class="num">{f"{len(g['exact'])} / {len(g['checked'])}" if g['references'] else '<span class="tag">no published formula to check against</span>'}</td>
<td>{esc(up.get('terms', ''))}</td></tr>""")
    body = f"""<div class="hero"><h1>Bridges</h1>
<p>A bridge does not invent instances: it encodes artefacts that another competition distributes, a circuit of a
hardware verification competition for example, with a pinned toolchain. The parameter of the encoding, the depth
of an unrolling, is what lets the family scale beyond the handful of instances a SAT competition kept.</p></div>
<div class="section"><h2>Your own files work too</h2>
<p>A bridge reads whatever file of its format you give it: mount your directory on <code>/data</code> and it
encodes your circuit, not only the ones a competition kept. See <a href="your-problem.html">your problem</a>.</p></div>
<div class="section"><h2>What we never do</h2>
<p>We do not redistribute the benchmarks of another competition. The repository keeps a manifest per collection,
with its address, its checksum and its terms, and the files are fetched into a local cache when a bridge runs.
The sizes below are what a download costs, not what this project stores.</p></div>
<div class="section tablewrap"><table><tr><th>Bridge</th><th>Collection</th><th>Upstream distribution</th><th class="num">Archive</th><th class="num">Exact / checked</th><th>Terms</th></tr>{"".join(rows)}</table></div>"""
    return page("Bridges", body, 0, "bridges")


ROUTES = [
    ("A circuit in AIGER format, combinational", "ready",
     "bridges/aiger", 'docker run --rm -v "$PWD:/data" satex-gen/aiger:2021 cnf mycircuit.aig > mine.cnf'),
    ("A sequential model to unroll over k steps, bounded model checking", "ready",
     "bridges/aiger", 'docker run --rm -v "$PWD:/data" satex-gen/aiger:2021 unroll 20 mymodel.aig > mine.cnf'),
    ("Two circuits whose equivalence you want to check", "ready",
     "bridges/aiger", 'docker run --rm -v "$PWD:/data" satex-gen/aiger:2021 miter a.aig b.aig > mine.cnf'),
    ("A planning problem in PDDL, domain and problem", "ready",
     "bridges/freelunch, through Fast Downward's translator",
     'docker run --rm -v "$PWD:/data" satex-gen/freelunch:2022 domain.pddl problem.pddl cr 12 > mine.cnf'),
    ("A planning task already in SAS+", "ready",
     "bridges/freelunch",
     'docker run --rm -v "$PWD:/data" satex-gen/freelunch:2022 task.sas cr 12 > mine.cnf'),
    ("A constraint model in MiniZinc, with its data file or with -D", "ready",
     "bridges/minizinc, through the MiniZinc compiler and PicatSAT",
     'docker run --rm -v "$PWD:/data" satex-gen/minizinc:2.10.1 model.mzn data.dzn > mine.cnf'),
    ("A FlatZinc file, already flattened", "ready",
     "bridges/minizinc, PicatSAT alone",
     'docker run --rm -v "$PWD:/data" satex-gen/minizinc:2.10.1 --fzn model.fzn > mine.cnf'),
    ("A constraint instance in XCSP3, .xml or .xml.lzma", "partly",
     "bridges/xcsp3, through Picat's SAT module. The interpreter it uses carries no licence, "
     "so no image is published: build the recipe yourself with "
     "docker build -t satex-gen/xcsp3:2023 bridges/xcsp3",
     'docker run --rm -v "$PWD:/data" satex-gen/xcsp3:2023 instance.xml > mine.cnf'),
    ("A constraint problem as a PyCSP3 model and its data", "partly",
     "bridges/xcsp3, which compiles the model with the pinned PyCSP3 first",
     'docker run --rm -v "$PWD:/data" satex-gen/xcsp3:2023 Model.py -data=12 > mine.cnf'),
    ("A hardware model in BTOR2, the format since HWMCC 2019", "ready",
     "bridges/btor2: bit blasted by btor2aiger, then unrolled and encoded as an AIG",
     'docker run --rm -v "$PWD:/data" satex-gen/btor2:2026 unroll 20 model.btor2 > mine.cnf'),
    ("A C program with an assertion, or a whole SV-COMP verification task", "ready",
     "bridges/svcomp: CBMC unwinds every loop k times, bit blasts the C semantics and writes the formula",
     'docker run --rm -v "$PWD:/data" satex-gen/svcomp:2025 unwind 20 myprogram.c > mine.cnf'),
    ("A bit-vector formula in SMT-LIB", "partly",
     "the circuits of the SMT-LIB benchmarks are already there; encoding your own formula needs Boolector or "
     "Bitwuzla in the chain, as the CRUX recipe does", ""),
]


def your_problem_page(gens: dict, rankings: dict) -> str:
    rows = []
    for what, state, how, cmd in ROUTES:
        badge = {"ready": '<span class="badge ok">ready</span>',
                 "partly": '<span class="badge warn">partly</span>',
                 "planned": '<span class="badge none">planned</span>'}[state]
        rows.append(f"""<tr><td>{esc(what)}</td><td>{badge}</td><td>{esc(how)}
{f'<pre class="cmd">{esc(cmd)}</pre>' if cmd else ''}</td></tr>""")
    year = sorted(rankings["years"])[-1]
    best = rankings["years"][year]["families"]["ALL"]["solvers"][:3]
    solvers = "".join(
        f"""<tr><td>{esc(s['solver'])}</td><td class="num">{s['solved']} of {rankings['years'][year]['families']['ALL']['instances']}</td>
<td>{(f'<pre class="cmd">docker run --rm -v "$PWD:/data" ' + esc((SOLVERS.get(year) or {}).get(s['solver'], {}).get('image', '')) + ' mine.cnf</pre>') if (SOLVERS.get(year) or {}).get(s['solver']) else '<span class="muted-inline">no image published</span>'}</td></tr>"""
        for s in best)
    body = f"""<div class="hero"><h1>You have a problem; what do you run?</h1>
<p>The bridges here are not tied to the competitions: they encode any file of the formats they understand, yours
included. Encode your problem, then pick the solver that does best on problems of that kind rather than the one
that won overall.</p></div>
<div class="section"><h2>Step one: turn it into CNF</h2>
<div class="tablewrap"><table><tr><th>What you have</th><th></th><th>How</th></tr>{"".join(rows)}</table></div>
<p class="legend">Mount the directory holding your file on <code>/data</code> and the image reads it there. Nothing
is uploaded anywhere: the whole chain runs on your machine.</p></div>
<div class="section"><h2>Step two: pick a solver</h2>
<p class="legend">The best three of the SAT Competition {esc(year)} overall, as images of the companion project.</p>
<div class="tablewrap"><table><tr><th>Solver</th><th class="num">Solved</th><th>Command</th></tr>{solvers}</table></div></div>
<div class="section"><h2>Step three, the one that pays: find your family</h2>
<p>A solver that wins overall is not the one to run on every kind of problem. On the Ascon cryptography family of
2023, SeqFROST solved all twenty instances while the overall winner did not; on the 2024 scheduling family,
AMSAT solved more than the winner. If your problem resembles one of the families of the competitions, the
<a href="families.html">families</a> page gives the ranking on that family alone and the command for each
solver.</p>
<p class="legend">If your problem resembles nothing there, that is interesting in itself: a new family is exactly
what a competition is short of, and the <a href="{REPO_URL}/issues">issues</a> are the place to say so.</p></div>"""
    return page("Your problem", body, 0, "yours")


def packs_page() -> str:
    built = [(s, idx) for s, idx in PACKS if s.get("status") == "published"]
    specs = [(s, idx) for s, idx in PACKS if s.get("status") != "published"]
    rows = []
    for s, idx in built:
        dist = s.get("distribution", {})
        cl = [f["clauses"] for f in (idx or {}).get("files", [])] or [0]
        rows.append(f"""<div class="section"><h2>{esc(s['title'])}</h2>
<p>{esc(s['why'])}</p>
<div class="stats">
<div class="stat"><div class="n">{(idx or {}).get('instances', '—')}</div><div class="l">instances, none of them in GBD</div></div>
<div class="stat"><div class="n">{((idx or {}).get('bytes', 0) / 1e6):.0f} MB</div><div class="l">compressed</div></div>
<div class="stat"><div class="n">{min(cl):,}</div><div class="l">clauses in the smallest</div></div>
<div class="stat"><div class="n">{max(cl):,}</div><div class="l">clauses in the largest</div></div>
</div>
<pre class="cmd">curl -LO {esc(dist.get('url', ''))}
tar xf {esc(dist.get('asset', ''))}</pre>
{f'<p class="legend">{esc(s["example_note"])}</p><p>Make your own, at the size you need:</p><pre class="cmd">{esc(s["regenerate"])}</pre>' if s.get('regenerate') else ''}
<p class="legend">Produced by {esc((idx or {}).get('chain') or s.get('built', {}).get('chain', ''))}, pinned in this
repository. The archive carries an <code>index.json</code> giving, for every file, the hash GBD uses, the command
that produced it and its size. {esc(s.get('size_note', ''))}</p></div>""")
    for s, _ in specs:
        rows.append(f"""<div class="section"><h2>{esc(s['title'])} <span class="badge none">proposed</span></h2>
<p>{esc(s['why'])}</p><p class="legend">{esc(s.get('permission', ''))}</p></div>""")
    body = f"""<div class="hero"><h1>Packs</h1>
<p>A pack is a set of instances we produce and distribute ourselves, because nobody else does. It exists for a
stated reason: a paper that needs them, or a collection worth having in CNF as a whole, such as every circuit of a
hardware verification competition or every task of a planning one.</p></div>
<div class="warning"><b>These formulas are examples, not a benchmark suite.</b> A pack holds small instances, so
that anyone can look at one, check it, and see what the encoding does. The sizes a solver author actually wants
are made on demand: take the same pinned chain, change the plan length or the unrolling depth, pick a bigger
task, and you have as many as you like. Every pack below says the command that regenerates it, and the
<a href="your-problem.html">your problem</a> page says how to run the chain on a file of your own.</div>
<div class="section"><h2>Two rules</h2>
<p><b>We never republish what GBD already serves.</b> An instance whose hash is in GBD is linked, not copied. A
pack holds what nobody else has: other parameters, other depths, other plan lengths.</p>
<p><b>The hash is the one GBD uses</b>, the MD5 of the normalised CNF. An instance of a pack is named exactly as a
competition instance is, which is what lets the two sit side by side.</p></div>
{"".join(rows)}"""
    return page("Packs", body, 0, "packs")


def samples_section(g: dict) -> str:
    """What this generator can produce, which is not limited to the instances a competition kept."""
    rows = SAMPLES.get(g["key"])
    if not rows:
        return ""
    worst = max(r["clauses"] for r in rows) or 1
    body = "".join(
        f"""<tr><td>{esc(r['label'])}</td><td><code>{esc(' '.join(r['args']))}</code></td>
<td class="num">{r['variables']:,}</td><td class="num">{r['clauses']:,}</td>
<td><span class="bar" style="width:{100 * r['clauses'] / worst:.0f}%"></span></td>
<td>{'' if r['reproducible'] else '<span class="badge warn">not reproducible</span>'}</td></tr>"""
        for r in rows)
    return f"""<div class="section"><h2>What it can produce</h2>
<p class="legend">A generator is not limited to the instances a competition happened to keep: these are sample
runs across its parameters, measured on the built image. Each command was run twice, to see whether it gives
the same formula every time.</p>
<div class="tablewrap"><table><tr><th>Sample</th><th>Command arguments</th><th class="num">Variables</th><th class="num">Clauses</th><th></th><th></th></tr>{body}</table></div></div>"""


def pack_section(g: dict) -> str:
    """The formulas this recipe actually ships, instance by instance.

    A pack is the only CNF this project distributes, so a recipe page that has one
    says what is in it: the page a reader lands on is the page that must show it.
    """
    mine = [(s, idx) for s, idx in PACKS if s.get("generator") == g["key"] and s.get("status") == "published"]
    out = []
    for s, idx in mine:
        dist, files = s.get("distribution", {}), (idx or {}).get("files", [])
        cl = [f["clauses"] for f in files] or [0]
        rows = "".join(
            f"""<tr><td>{esc(f['file'].removesuffix('.cnf.xz'))}
{(f'<span class="tag" title="' + esc(", ".join(f["aliases"])) + f'">and {len(f["aliases"])} more name' + ("s" if len(f["aliases"]) > 1 else "") + ' for this same formula</span>') if f.get('aliases') else ''}</td>
<td><code>{esc(' '.join(f['args']))}</code></td>
<td class="num">{f['variables']:,}</td><td class="num">{f['clauses']:,}</td>
<td class="num">{human_size(f['bytes'])}</td>
<td><span class="nolink">{esc(f['hash'][:12])}…</span></td></tr>"""
            for f in sorted(files, key=lambda f: f["clauses"]))
        skipped = (idx or {}).get("skipped", [])
        out.append(f"""<div class="section"><h2>Formulas we distribute: {esc(s['title'])}</h2>
<p class="legend">{esc(s.get('example_note', ''))} The whole pack is one archive, which also carries an
<code>index.json</code> with these lines in machine form. See <a href="../packs.html">packs</a>.</p>
<div class="stats">
<div class="stat"><div class="n">{len(files)}</div><div class="l">formulas in the pack</div></div>
<div class="stat"><div class="n">{((idx or {}).get('bytes', 0) / 1e6):.1f} MB</div><div class="l">compressed</div></div>
<div class="stat"><div class="n">{min(cl):,}</div><div class="l">clauses in the smallest</div></div>
<div class="stat"><div class="n">{max(cl):,}</div><div class="l">clauses in the largest</div></div>
</div>
<pre class="cmd">curl -LO {esc(dist.get('url', ''))}
tar xf {esc(dist.get('asset', ''))}</pre>
<div class="tablewrap"><table><tr><th>Formula</th><th>Command arguments</th><th class="num">Variables</th>
<th class="num">Clauses</th><th class="num">Compressed</th><th>Hash GBD would give it</th></tr>{rows}</table></div>
<p class="legend">{f"{len(skipped)} more were produced and left out, over the limits this pack set itself: " if skipped else ""}{esc(s.get('size_note', ''))}</p>
{f'<p>Any other size, with the same pinned chain:</p><pre class="cmd">{esc(s["regenerate"])}</pre>' if s.get('regenerate') else ''}</div>""")
    return "".join(out)


def verdict_section(g: dict) -> str:
    """What a bridge is checked against when nobody published its formulas.

    A generator is checked by regenerating a known instance and comparing the
    hash.  A bridge onto a competition that distributes programs rather than
    formulas has nothing to compare, so what is checked is the question: the
    task declares the verdict its organisers expect, and the formula has to
    agree with it.
    """
    path = ROOT_DIR / g["dirpath"] / "verdicts.json"
    if not path.exists():
        return ""
    d = json.load(open(path))
    rows = "".join(
        f"""<tr><td>{esc(r['task'])}</td><td>{esc(r['property'])}</td>
<td>{esc(r['expected'])}</td><td>{esc(r['cbmc'])}</td>
<td>{'<span class="badge ok">agrees</span>' if r['agreement'] == 'agrees'
     else '<span class="badge warn">' + esc(r['agreement']) + '</span>'}
{(' <span class="tag">' + esc(r['note']) + '</span>') if r.get('note') else ''}</td>
<td class="num">{r['clauses']:,}</td></tr>""" if r.get("clauses") else
        f"""<tr><td>{esc(r['task'])}</td><td>{esc(r['property'])}</td>
<td>{esc(r['expected'])}</td><td>{esc(r['cbmc'])}</td>
<td>{'<span class="badge ok">agrees</span>' if r['agreement'] == 'agrees'
     else '<span class="badge warn">' + esc(r['agreement']) + '</span>'}</td>
<td class="muted-inline">{esc(r['formula'])}</td></tr>"""
        for r in d["rows"])
    agree = sum(1 for r in d["rows"] if r["agreement"] == "agrees")
    return f"""<div class="section"><h2>Does the formula ask the right question?</h2>
<p class="legend">{esc(d['what'])}</p>
<div class="stats"><div class="stat"><div class="n">{agree} of {len(d['rows'])}</div><div class="l">agree with the competition's verdict</div></div>
<div class="stat"><div class="n">{d['bound']}</div><div class="l">unwindings, the bound used here</div></div></div>
<div class="tablewrap"><table><tr><th>Task</th><th>Property encoded</th><th>Expected</th><th>Answer at this bound</th><th></th><th class="num">Clauses</th></tr>{rows}</table></div>
<p class="legend">{esc(d['caveat'])}</p></div>"""


def generator_page(g: dict, rankings: dict) -> str:
    meta = [("Authors", g.get("authors")), ("Source of the author list", g.get("authors_source")),
            ("Language", g.get("language")), ("Licence", g.get("license")),
            ("Competitions", ", ".join(g.get("competitions", [])) or "—"),
            ("Repository", (f'<a href="{esc(g["source_repo"])}">{esc(g["source_repo"])}</a>'
                            if str(g.get("source_repo", "")).startswith("http") else esc(g.get("source_repo") or g.get("source_url") or "—"))),
            ("Pinned commit", g.get("source_commit")), ("Pinned git tree", g.get("source_tree")),
            ("Seed", g.get("seed")),
            ("Upstream collection", (f'{esc(up["name"])} — {esc(up["terms"])}'
                                     if (up := UPSTREAM.get(g.get("upstream"))) else None)),
            ("Notes", g.get("notes")), ("Licence note", g.get("license_note"))]
    dl = "".join(f"<dt>{esc(k)}</dt><dd>{v if k in ('Repository', 'Upstream collection') else esc(v)}</dd>" for k, v in meta if v)
    build = f"docker build -t {g['image']} {g['dirpath']}\n{'docker run --rm ' + g['image'] + ' ...  > instance.cnf'}"
    counts = defaultdict(int)
    for r in g["references"]:
        counts[r["level"] or "not checked"] += 1
    summary = " · ".join(f"{n} with the {LEVEL_LABEL[lvl]}" if lvl in LEVEL_LABEL else f"{n} {lvl}"
                         for lvl, n in sorted(counts.items()))
    rows = []
    for r in g["references"]:
        fam = r["family"]
        famlink = f'<a href="../families/{slug(fam)}.html">{esc(fam)}</a>' if fam != "unknown" else "—"
        rows.append(f"""<tr><td>{esc(r['instance'])}</td><td>{famlink}</td>
<td><code>{esc(' '.join(r['args']))}</code></td>
<td>{gbd_link(r['gbdhash'], r.get('size'))}{"".join('<br>' + gbd_link(a['gbdhash'], a.get('size'), a['provenance']) + f' <span class="tag">{esc(a["provenance"][:40])}…</span>' for a in r.get('alternates', []))}</td>
<td>{level_badge(r['level'])}{(' <span class="tag">' + esc(r['matched']) + '</span>') if r.get('matched') else ''}</td></tr>""")
    notes = {r["note"] for r in g["references"] if r.get("note")}
    body = f"""<div class="crumbs"><a href="../index.html">Overview</a> · <a href="../generators.html">Generators</a></div>
<div class="hero"><h1>{esc(g['name'])}</h1><p>{esc(g.get('usage',''))}</p></div>
<div class="section"><h2>What it is</h2><dl>{dl}</dl></div>
<div class="section"><h2>Build it and run it</h2><pre>{esc(build)}</pre>
<p class="legend">{"The image can be published: the licence allows it." if g.get('publish_image') else "The image is not published: the generator declares no licence, so only this recipe is distributed. Building it locally is fine."}</p></div>
{pack_section(g)}{samples_section(g)}{verdict_section(g)}
{f'''<div class="section"><h2>Reference instances</h2><p class="legend">{esc(summary)}. Each line regenerates one known instance, from a competition or from the set its author published; the level says how close the result is. See <a href="../verification.html">verification</a>.</p>
<div class="tablewrap"><table><tr><th>Instance</th><th>Family</th><th>Command arguments</th><th>GBD hash</th><th>Level</th></tr>{"".join(rows)}</table></div></div>''' if rows else '' if verdict_section(g) else '''<div class="section"><h2>No reference instance to check against</h2>
<p class="legend">No competition published the formulas this recipe produces, so there is nothing whose hash we
could compare ours to: what is checked here is the chain itself, by rebuilding it from pinned sources and
producing the samples above twice. The formulas we distribute are in the pack.</p></div>'''}
{('<div class="section"><h2>Notes</h2><ul>' + "".join(f"<li>{esc(n)}</li>" for n in sorted(notes)) + "</ul></div>") if notes else ""}"""
    return page(g["name"], body, 1)


def family_rows(fam: str, rankings: dict):
    for year in sorted(rankings["years"]):
        block = rankings["years"][year]["families"].get(fam)
        if block:
            yield year, block


def families_page(gens: dict, rankings: dict) -> str:
    gen_of = defaultdict(list)
    for g in gens.values():
        for fam in g["families"]:
            gen_of[fam].append(g)
    rows = []
    fams = sorted({f for y in rankings["years"].values() for f in y["families"] if f != "ALL"})
    for fam in fams:
        years = list(family_rows(fam, rankings))
        n = max(b["instances"] for _, b in years)
        best = years[-1][1]["solvers"][0]
        gs = gen_of.get(fam, [])
        gl = ", ".join(f'<a href="generators/{esc(x["key"])}.html">{esc(x["name"])}</a>' for x in gs) or '<span class="tag">none here yet</span>'
        rows.append(f"""<tr><td><a href="families/{slug(fam)}.html">{esc(fam)}</a></td>
<td>{", ".join(y for y, _ in years)}</td><td class="num">{n}</td>
<td>{esc(best['solver'])} <span class="tag">{best['solved']} solved</span></td><td>{gl}</td></tr>""")
    covered = sum(1 for f in fams if f in gen_of)
    body = f"""<div class="hero"><h1>Benchmark families</h1>
<p>Every family of the covered competitions with at least eight instances, the solver that did best on it in the most recent of those years, and the generator that reproduces it when we have one.</p></div>
<div class="stats"><div class="stat"><div class="n">{len(fams)}</div><div class="l">families</div></div>
<div class="stat"><div class="n">{covered}</div><div class="l">with a generator here</div></div>
<div class="stat"><div class="n">{len(fams) - covered}</div><div class="l">still without one</div></div></div>
<div class="section tablewrap"><table><tr><th>Family</th><th>Years</th><th class="num">Instances</th><th>Best solver on it</th><th>Generator</th></tr>{"".join(rows)}</table></div>"""
    return page("Families", body, 0, "families")


def what_to_run(fam: str, rankings: dict) -> str:
    """The solvers that did best on this family, as commands anyone can run."""
    blocks = list(family_rows(fam, rankings))
    if not blocks:
        return ""
    year, block = blocks[-1]
    rows = []
    for s in block["solvers"][:3]:
        img = (SOLVERS.get(year) or {}).get(s["solver"])
        cmd = (f'<pre class="cmd">docker run --rm -v "$PWD:/data" {esc(img["image"])} your-instance.cnf</pre>'
               if img else '<span class="muted-inline">no image published for this solver yet</span>')
        rows.append(f"""<tr><td>{esc(s['solver'])}</td><td class="num">{s['solved']} / {block['instances']}</td>
<td>{cmd}</td></tr>""")
    return f"""<div class="section"><h2>What to run on a problem of this kind</h2>
<p class="legend">The solvers that did best on this family in the SAT Competition {esc(year)}, as images of the
companion project. They are a better bet on such a problem than the overall winner of that year, which this
family often disagrees with.</p>
<div class="tablewrap"><table><tr><th>Solver</th><th class="num">Solved</th><th>Command</th></tr>{"".join(rows)}</table></div></div>"""


def family_page(fam: str, gens: dict, rankings: dict) -> str:
    blocks = list(family_rows(fam, rankings))
    sections = []
    for year, block in blocks:
        worst = max(s["par2"] for s in block["solvers"]) or 1
        rows = []
        for i, s in enumerate(block["solvers"], 1):
            width = 100 * (1 - s["par2"] / worst) if worst else 0
            rows.append(f"""<tr class="{'rank1' if i == 1 else ''}"><td class="num">{i}</td><td>{esc(s['solver'])}</td>
<td class="num">{s['solved']} / {block['instances']}</td><td class="num">{s['par2']:.0f} s</td>
<td><span class="bar" style="width:{width:.0f}%"></span></td></tr>""")
        overall = rankings["years"][year]["families"]["ALL"]["solvers"][0]["solver"]
        sections.append(f"""<div class="section"><h2>SAT Competition {esc(year)} · {block['instances']} instances</h2>
<p class="legend">Ranked by PAR-2 on this family alone. Winner of the whole main track that year: {esc(overall)}.</p>
<div class="tablewrap"><table><tr><th class="num">#</th><th>Solver</th><th class="num">Solved</th><th class="num">PAR-2 per instance</th><th></th></tr>{"".join(rows)}</table></div></div>""")
    gs = [g for g in gens.values() if fam in g["families"]]
    if gs:
        gl = "".join(f"""<div class="section"><h2>Generator: {esc(g['name'])}</h2>
<p>{esc(g.get('usage',''))}</p><p class="legend">{len([r for r in g['references'] if r['family'] == fam and r['level'] == 'N1'])} of {len([r for r in g['references'] if r['family'] == fam])} instances of this family regenerated exactly. <a href="../generators/{esc(g['slug'])}.html">Details and commands</a>.</p></div>""" for g in gs)
    else:
        gl = """<div class="section"><h2>No generator here yet</h2><p>We have not packaged a generator for this family. If you wrote it, or know where its code lives, a <a href="%s/issues">issue</a> is very welcome.</p></div>""" % REPO_URL
    body = f"""<div class="crumbs"><a href="../index.html">Overview</a> · <a href="../families.html">Families</a></div>
<div class="hero"><h1>{esc(fam)}</h1><p>Solver rankings on this family, and the generator that reproduces it.</p></div>
{what_to_run(fam, rankings)}{gl}{"".join(sections)}"""
    return page(fam, body, 1)


def verification_page(gens: dict, rankings: dict) -> str:
    rows = "".join(f"<tr><td><b>{lvl}</b></td><td>{esc(LEVEL_LABEL[lvl])}</td></tr>" for lvl in LEVELS)
    per_gen = "".join(
        f"<tr><td><a href='generators/{esc(g['slug'])}.html'>{esc(g['name'])}</a></td>"
        f"<td class='num'>{len(g['references'])}</td><td class='num'>{len(g['checked'])}</td>"
        f"<td class='num'>{len(g['exact'])}</td></tr>"
        for g in sorted(gens.values(), key=lambda g: g["name"].lower()))
    body = f"""<div class="hero"><h1>How a generator is checked</h1>
<p>An instance is identified by its GBD hash, the MD5 of the normalised CNF, which ignores comments, header and whitespace. We run the image with the parameters recorded for one competition instance and compare.</p></div>
<div class="section"><h2>The levels</h2><table>{rows}</table>
<p class="legend">A level below N1 is not necessarily the generator's fault: an archived copy can differ from what its author produced, a set can have been shuffled by the organisers, or a script can have changed after the submission. Those cases are recorded on each generator's page.</p></div>
<div class="section tablewrap"><h2>Where we stand</h2><table><tr><th>Generator</th><th class="num">References</th><th class="num">Checked</th><th class="num">Exact</th></tr>{per_gen}</table></div>
<div class="section"><h2>Reproduce it yourself</h2><pre>git clone {REPO_URL}.git
cd benchs-generators
python3 tools/check_repo.py                  # no Docker needed: the recipes hold together
docker build -t satex-gen/gbd:0.4.2 tools/gbd
docker build -t satex-gen/sgen1:2009 cnf/sgen1
python3 tools/verify.py sgen1</pre>
<p class="legend">The verifier regenerates every reference instance of the target and prints one line per instance. Hashes are computed with the official <code>gbdc</code> package of <a href="{GBD_URL}">GBD</a>.</p></div>"""
    return page("Verification", body, 0, "verification")


def build(root: Path, out: Path) -> int:
    global ROOT_DIR
    ROOT_DIR = root
    gens, rankings = load(root)
    out.mkdir(parents=True, exist_ok=True)
    (out / "style.css").write_text(CSS)
    (out / "index.html").write_text(overview_page(gens, rankings))
    (out / "generators.html").write_text(generators_page(gens))
    (out / "bridges.html").write_text(bridges_page(gens, rankings))
    (out / "your-problem.html").write_text(your_problem_page(gens, rankings))
    (out / "packs.html").write_text(packs_page())
    (out / "families.html").write_text(families_page(gens, rankings))
    (out / "verification.html").write_text(verification_page(gens, rankings))
    (out / "generators").mkdir(exist_ok=True)
    for g in gens.values():
        (out / "generators" / f"{g['slug']}.html").write_text(generator_page(g, rankings))
    (out / "families").mkdir(exist_ok=True)
    fams = {f for y in rankings["years"].values() for f in y["families"] if f != "ALL"}
    fams |= {f for g in gens.values() for f in g["families"]}
    for fam in sorted(fams):
        (out / "families" / f"{slug(fam)}.html").write_text(family_page(fam, gens, rankings))
    print(f"{len(gens)} generators, {len(fams)} families -> {out}", file=sys.stderr)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".")
    ap.add_argument("--output", default="_site")
    args = ap.parse_args(argv)
    return build(Path(args.root), Path(args.output))


if __name__ == "__main__":
    sys.exit(main())
