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


def load(root: Path):
    gens = json.load(open(root / "generators.json"))
    rankings = json.load(open(root / "data" / "rankings.json"))
    fam_of = {h: tuple(v) for h, v in rankings["instance_family"].items()}
    for key, g in gens.items():
        refs = json.load(open(root / "references" / f"{key}.json"))["references"] \
            if (root / "references" / f"{key}.json").exists() else []
        levels = {}
        for path in sorted((root / "results").glob(f"{key}*.json")):
            for r in json.load(open(path))["results"]:
                levels[r["instance"]] = r
        for r in refs:
            got = levels.get(r["instance"])
            r["level"] = got["level"] if got else None
            r["matched"] = (got or {}).get("matched")
            r["family"], r["family_author"] = fam_of.get(r["gbdhash"], ("unknown", ""))
        g["key"] = key
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
.toolbar { display:flex; flex-wrap:wrap; gap:10px; align-items:center; margin:8px 0 18px; padding:12px 14px; background:var(--bg2); border:1px solid var(--line); border-radius:14px; }
.toolbar input, .toolbar select { font:inherit; padding:8px 10px; border:1px solid var(--line); border-radius:999px; background:var(--card); color:var(--ink); }
.count { color:var(--muted); margin-left:auto; font-size:14px; }
footer { color:var(--muted); font-size:13px; text-align:center; padding:20px 24px 28px; max-width:900px; margin:0 auto; }
"""

NAV = [("index.html", "Overview", "overview"), ("generators.html", "Generators", "generators"),
       ("families.html", "Families", "families"), ("verification.html", "Verification", "verification")]


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
<p>The programs that produced the SAT competition benchmarks, each as a Docker image, checked by regenerating the instances the competitions actually used.</p></header>
<div class="warning"><b>A pilot, and a collective one: please check, correct and contribute.</b> Everything here is generated from the data of the <a href="{REPO_URL}">sat-heritage/benchs-generators</a> repository. A generator whose licence is unknown has its recipe published but no image, and a family with no generator is one we could not find or could not run: corrections, missing generators and licence clarifications are welcome as <a href="{REPO_URL}/pulls">pull requests</a> or <a href="{REPO_URL}/issues">issues</a>. The companion project for solvers is <a href="{SOLVERS_SITE}">SAT Heritage</a>.</div>
<main>{body}</main>
<footer>Generated from the <a href="{REPO_URL}">sat-heritage/benchs-generators</a> repository · solver rankings computed from the detailed results published by the SAT competitions, joined with <a href="{GBD_URL}">GBD</a> · a project by {esc(AUTHORS)}, assembled with the help of an AI assistant: check every claim against the original competition material.</footer></body></html>
"""


def level_badge(level: str) -> str:
    if not level:
        return '<span class="badge none">not checked</span>'
    return f'<span class="badge {LEVEL_CLASS[level]}" title="{esc(LEVEL_LABEL[level])}">{level}</span>'


def gen_card(g: dict) -> str:
    exact, checked = len(g["exact"]), len(g["checked"])
    pub = "image published" if g.get("publish_image") else "recipe only, licence unknown"
    return f"""<a class="card" href="generators/{esc(g['key'])}.html">
<h3>{esc(g['name'])}</h3>
<div class="meta">{esc(g.get('authors',''))} · {esc(g.get('year',''))}</div>
<div class="tags"><span class="tag">{esc(g.get('language',''))}</span><span class="tag">{esc(g.get('license',''))}</span><span class="tag cap">{esc(pub)}</span></div>
<div class="tags"><span class="badge {'ok' if exact == checked and checked else 'warn'}">{exact} of {checked} instances exact</span>{"".join(f'<span class="tag">{esc(f)}</span>' for f in g['families'][:3])}</div>
</a>"""


def overview_page(gens: dict, rankings: dict) -> str:
    refs = sum(len(g["references"]) for g in gens.values())
    checked = sum(len(g["checked"]) for g in gens.values())
    exact = sum(len(g["exact"]) for g in gens.values())
    published = sum(1 for g in gens.values() if g.get("publish_image"))
    covered = {f for g in gens.values() for f in g["families"]}
    all_fams = {f for y in rankings["years"].values() for f in y["families"] if f != "ALL"}
    body = f"""<div class="hero"><h1>Benchmark generators of the SAT competitions</h1>
<p>A benchmark is only reproducible if the program that produced it still runs. This repository packages those programs as Docker images, pins their sources to one commit, and checks each image by regenerating the instances the competitions used: same GBD hash, same instance.</p></div>
<div class="stats">
<div class="stat"><div class="n">{len(gens)}</div><div class="l">generators packaged</div></div>
<div class="stat"><div class="n">{exact}</div><div class="l">instances regenerated exactly</div></div>
<div class="stat"><div class="n">{checked}</div><div class="l">reference instances checked, of {refs} recorded</div></div>
<div class="stat"><div class="n">{published}</div><div class="l">images publishable, the others lack a licence</div></div>
<div class="stat"><div class="n">{len(covered)}</div><div class="l">competition families with a generator here</div></div>
</div>
<h2>Generators</h2><div class="grid">{"".join(gen_card(g) for g in sorted(gens.values(), key=lambda g: g['name'].lower()))}</div>
<div class="section"><h2>Where the rankings come from</h2>
<p>For the years whose detailed results are published, every solver's runtime on every instance is known, keyed by the same GBD hash we use. That gives, for each benchmark family, the ranking the solvers would have had on that family alone, which is regularly not the overall ranking. See the <a href="families.html">families</a>.</p>
<p class="legend">Years covered: {", ".join(sorted(rankings["years"]))} · {len(all_fams)} families with at least eight instances · measure: {esc(rankings["measure"])}.</p></div>"""
    return page("Overview", body, 0, "overview")


def generators_page(gens: dict) -> str:
    rows = []
    for g in sorted(gens.values(), key=lambda g: g["name"].lower()):
        rows.append(f"""<tr><td><a href="generators/{esc(g['key'])}.html">{esc(g['name'])}</a></td>
<td>{esc(g.get('authors',''))}</td><td>{esc(g.get('year',''))}</td><td>{esc(g.get('language',''))}</td>
<td>{esc(g.get('license',''))}</td><td>{'yes' if g.get('publish_image') else 'no'}</td>
<td class="num">{len(g['exact'])} / {len(g['checked'])}</td>
<td>{", ".join(esc(f) for f in g['families']) or '<span class="tag">no competition family recorded</span>'}</td></tr>""")
    body = f"""<div class="hero"><h1>Generators</h1><p>One image per generator, built from the author's own sources at a pinned commit.</p></div>
<div class="section tablewrap"><table><tr><th>Generator</th><th>Authors</th><th>Year</th><th>Language</th><th>Licence</th><th>Image published</th><th class="num">Exact / checked</th><th>Families</th></tr>{"".join(rows)}</table></div>"""
    return page("Generators", body, 0, "generators")


def generator_page(g: dict, rankings: dict) -> str:
    meta = [("Authors", g.get("authors")), ("Source of the author list", g.get("authors_source")),
            ("Language", g.get("language")), ("Licence", g.get("license")),
            ("Competitions", ", ".join(g.get("competitions", [])) or "—"),
            ("Repository", f'<a href="{esc(g.get("source_repo",""))}">{esc(g.get("source_repo",""))}</a>' if g.get("source_repo") else g.get("source_url", "—")),
            ("Pinned commit", g.get("source_commit")), ("Pinned git tree", g.get("source_tree")),
            ("Seed", g.get("seed")), ("Notes", g.get("notes")), ("Licence note", g.get("license_note"))]
    dl = "".join(f"<dt>{esc(k)}</dt><dd>{v if k in ('Repository',) else esc(v)}</dd>" for k, v in meta if v)
    build = f"docker build -t {g['image']} {g['key']}\n{'docker run --rm ' + g['image'] + ' ...  > instance.cnf'}"
    counts = defaultdict(int)
    for r in g["references"]:
        counts[r["level"] or "not checked"] += 1
    summary = " · ".join(f"{n} {LEVEL_LABEL.get(lvl, lvl)}" for lvl, n in sorted(counts.items()))
    rows = []
    for r in g["references"]:
        fam = r["family"]
        famlink = f'<a href="../families/{slug(fam)}.html">{esc(fam)}</a>' if fam != "unknown" else "—"
        rows.append(f"""<tr><td>{esc(r['instance'])}</td><td>{famlink}</td>
<td><code>{esc(' '.join(r['args']))}</code></td>
<td><a href="{GBD_URL}/file/{esc(r['gbdhash'])}" title="download this instance from GBD">{esc(r['gbdhash'][:12])}…</a></td>
<td>{level_badge(r['level'])}{(' <span class="tag">' + esc(r['matched']) + '</span>') if r.get('matched') else ''}</td></tr>""")
    notes = {r["note"] for r in g["references"] if r.get("note")}
    body = f"""<div class="crumbs"><a href="../index.html">Overview</a> · <a href="../generators.html">Generators</a></div>
<div class="hero"><h1>{esc(g['name'])}</h1><p>{esc(g.get('usage',''))}</p></div>
<div class="section"><h2>What it is</h2><dl>{dl}</dl></div>
<div class="section"><h2>Build it and run it</h2><pre>{esc(build)}</pre>
<p class="legend">{"The image can be published: the licence allows it." if g.get('publish_image') else "The image is not published: the generator declares no licence, so only this recipe is distributed. Building it locally is fine."}</p></div>
<div class="section"><h2>Reference instances</h2><p class="legend">{esc(summary)}. Each line regenerates one instance used by a competition; the level says how close the result is. See <a href="../verification.html">verification</a>.</p>
<div class="tablewrap"><table><tr><th>Instance</th><th>Family</th><th>Command arguments</th><th>GBD hash</th><th>Level</th></tr>{"".join(rows)}</table></div></div>
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
<p>{esc(g.get('usage',''))}</p><p class="legend">{len([r for r in g['references'] if r['family'] == fam and r['level'] == 'N1'])} of {len([r for r in g['references'] if r['family'] == fam])} instances of this family regenerated exactly. <a href="../generators/{esc(g['key'])}.html">Details and commands</a>.</p></div>""" for g in gs)
    else:
        gl = """<div class="section"><h2>No generator here yet</h2><p>We have not packaged a generator for this family. If you wrote it, or know where its code lives, a <a href="%s/issues">issue</a> is very welcome.</p></div>""" % REPO_URL
    body = f"""<div class="crumbs"><a href="../index.html">Overview</a> · <a href="../families.html">Families</a></div>
<div class="hero"><h1>{esc(fam)}</h1><p>Solver rankings on this family, and the generator that reproduces it.</p></div>
{gl}{"".join(sections)}"""
    return page(fam, body, 1)


def verification_page(gens: dict, rankings: dict) -> str:
    rows = "".join(f"<tr><td><b>{lvl}</b></td><td>{esc(LEVEL_LABEL[lvl])}</td></tr>" for lvl in LEVELS)
    per_gen = "".join(
        f"<tr><td><a href='generators/{esc(g['key'])}.html'>{esc(g['name'])}</a></td>"
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
docker build -t satex-gen/gbd:0.4.2 tools/gbd
python3 tools/verify.py sgen1</pre>
<p class="legend">The verifier builds the image, regenerates every reference instance and prints one line per instance. Hashes are computed with the official <code>gbdc</code> package of <a href="{GBD_URL}">GBD</a>.</p></div>"""
    return page("Verification", body, 0, "verification")


def build(root: Path, out: Path) -> int:
    gens, rankings = load(root)
    out.mkdir(parents=True, exist_ok=True)
    (out / "style.css").write_text(CSS)
    (out / "index.html").write_text(overview_page(gens, rankings))
    (out / "generators.html").write_text(generators_page(gens))
    (out / "families.html").write_text(families_page(gens, rankings))
    (out / "verification.html").write_text(verification_page(gens, rankings))
    (out / "generators").mkdir(exist_ok=True)
    for g in gens.values():
        (out / "generators" / f"{g['key']}.html").write_text(generator_page(g, rankings))
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
