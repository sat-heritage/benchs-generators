# SAT Heritage generators (pilot)

`sat-heritage/benchs-generators`

Docker images of SAT benchmark **generators**, in the spirit of
[SAT Heritage](https://github.com/sat-heritage/docker-images) for solvers: each
generator is built from its archived sources in a pinned environment, and each
image is checked against the instances actually used in the SAT Competitions.

This is a pilot with two generators, sgen1 and CNFgen.

## Verification

A reference instance is identified by its [GBD](https://benchmark-database.de)
hash, the MD5 of the normalised CNF, which ignores comments, header and
whitespace. `tools/verify.py GENERATOR` regenerates every reference instance
listed in `references/GENERATOR.json` and grades it:

| Level | Meaning |
|---|---|
| N1 | same GBD hash: the image regenerates the competition instance exactly |
| N2 | same after sorting literals and clauses: only the order differs |
| N3 | same GBD `isohash2`: equal up to a renaming of the variables |
| N4 | same numbers of variables and clauses |
| -- | none of the above |

Hashes are computed with the official `gbdc` 0.4.2 package, in the
`satex-gen/gbd` image built from `tools/gbd`. The reference lists come from the
GBD metadata shipped with the SAT Competition 2026 benchmark compilation script.
Note that `isohash2` is the column that matches that metadata; `isohash` has
changed algorithm since.

The MIT licence of this repository covers what is in it: the recipes, the
metadata, the reference lists and the tools. It says nothing about the
generators themselves, which stay under their own authors' terms and are never
copied here: each recipe downloads its sources from the author's own
repository at a pinned commit.

## Sources and licences

Each recipe pins its source: the repository URL, the exact commit, and the git
tree hash of that commit, which is git's own content digest and, unlike the
tarballs GitHub generates on the fly, does not change under us. The build fails
if the tree does not match.

Pinning fixes provenance, not permission, so `generators.json` also carries a
`publish_image` flag:

| Licence of the generator | What we do |
|---|---|
| clear (MIT, GPL, CC0, ...) | build the image and publish it; for the GPL the image also carries the sources |
| none stated | publish the recipe, the references and the results, but **not** the image: a public repository without a licence file stays under plain copyright, and publishing the image would redistribute the code |

Either way the verification below runs the same, since it builds the image
locally before comparing hashes. Authors who add a licence file to their
repository move their generator from the second row to the first.

## Results

| Generator | Image | References | N1 | N3 |
|---|---|---|---|---|
| sgen1 | `satex-gen/sgen1:2009` | 30 | 28 | 2 |
| CNFgen | `satex-gen/cnfgen:0.9.6` | 24 | 24 | 0 |
| mdp-benchmark | `satex-gen/mdp:2022` | 30 | 28 | 0 |
| Round-robin | `satex-gen/roundrobin:2025` | 20 | 20 | 0 |
| lockchart-to-cnf | `satex-gen/lockchart:2025` | 20 (5 checked) | 3 | 0 |
| Oddball | `satex-gen/oddball:2025` | 40 | 40 | 0 |
| Community Attachment | `satex-gen/commattach:2015` | 56 | 54 | 1 |

- **sgen1**: 27 instances match their GBD hash. The GBD copy of
  `sgen1-sat-140-100` lacks one clause, (-25 -23), of the author's file; the
  image reproduces the author's file exactly, recorded as an alternate
  reference. The two `-sc2009` variants, as published by the 2009 organisers,
  match up to a renaming of the variables.
- **CNFgen**: the binary and relativized pigeonhole families recorded in GBD
  under the authors `oertel` and `yldirimoglu` are CNFgen output. GBD links
  them to the proceedings handles 10138/359079, 10138/563824 and 10138/584822
  (the last one is the SAT Competition 2024).
  Their parameters come from the file names; `rphp` uses P-1 holes, found by
  matching variable and clause counts.

- **mdp-benchmark**: the repository ships the script that produced the submitted
  set, so every parameter is known. Two GBD copies differ from what the script
  produces: `mdp-32-14-unsat` lacks one clause and `mdp-36-10-unsat` lacks one
  literal of a clause. No other threshold or seed reproduces them, and the
  author's own copies are not published, so the difference is recorded, not
  resolved.
- **Round-robin**: all 20 submitted instances, single and multi-venue, are
  regenerated exactly.
- **lockchart-to-cnf**: only the five small instances of group 3 were checked,
  since those of group 1 are tens of megabytes each. Three match exactly; two
  have the right size but different clauses, which suggests the submitted set
  came from an earlier revision of the script. The generator is deterministic:
  two runs give the same formula. The group 2 instances are randomised from the
  clock and cannot be reproduced at all.

- **Oddball**: all 40 instances are regenerated exactly, once z3 is pinned to
  4.14.1 and the symmetry-breaking strategies of `generate_benchmarks.sh` are
  passed: `ttf` is TruthTableForced, `tto_zp` is TruthTableOrdering plus
  ZeroPlus. The repository declares no licence, so the image is not published.
- **Community Attachment**: 54 of the 56 modularity instances of the
  competitions are exact. The digits of the `modgen` file names are shifted, so
  the real size, 2200 variables and 9086 clauses, comes from the instance
  headers rather than the names. One shuffled variant of 2015 matches up to a
  renaming. This repository declares no licence either.

## Building and running

```sh
docker build -t satex-gen/gbd:0.4.2 tools/gbd
docker build -t satex-gen/sgen1:2009 sgen1
docker build -t satex-gen/cnfgen:0.9.6 cnfgen
docker run --rm satex-gen/sgen1:2009 -unsat -n 121 -s 100 > sgen1-unsat-121-100.cnf
docker run --rm satex-gen/cnfgen:0.9.6 -S 1 rphp 20 20 19 > rphp_p20_r20.cnf
python3 tools/verify.py sgen1
```

Every image writes the CNF on standard output.

## Things to know

- **sgen1** has no licence, neither in its source nor on its page: ask Ivor
  Spence before publishing the image. Its `main()` always returns 1, so the
  verifier ignores exit statuses and checks the output instead. It carries its
  own linear congruential generator, so its output does not depend on the C
  library; it is built with gcc 4.3 on Debian lenny, as in 2009.
- **CNFgen** is GPL-3.0. Without `-S`, its seed is the current time: always
  pass a seed. The image pins CNFgen 0.9.6 and Python 3.12.7, since Python's
  `random` module does not promise identical draws across versions; a fixed
  seed gives identical output from run to run.

## Website

`tools/build_site.py` writes a static site from the repository: an overview, one
page per generator, one page per competition benchmark family, and a page on how
instances are checked. The family pages carry the solver ranking on that family
alone, computed by `tools/collect_rankings.py` from the detailed results the
competitions publish, joined with GBD; the result is kept in
`data/rankings.json` so that building the site needs no network.

```sh
python3 tools/collect_rankings.py     # refresh data/rankings.json (downloads)
python3 tools/build_site.py --output _site
```

A GitHub Actions workflow publishes the site on GitHub Pages at every push to
`main`, and once a month so that newly published competition results are picked
up.

## Layout

- `generators.json`: one entry per generator (authors and their source, licence, image, usage, seed)
- `<generator>/Dockerfile`: the recipe; sources are downloaded and checked against a SHA-256
- `references/<generator>.json`: reference instances with GBD hashes and parameters
- `results/<generator>.json`: output of the last verification
- `tools/gbd`: the GBD hash image; `tools/verify.py`: the verifier
