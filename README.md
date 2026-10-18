# SAT Heritage generators (pilot)

`sat-heritage/benchs-generators`

Docker images of SAT benchmark **generators**, from the competitions and
beyond: several of these families were never submitted to a competition and
serve in papers, in solver tuning or in cube and conquer experiments. In the
spirit of
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
| genxormiter | `satex-gen/genxormiter:2025` | none | — | — |
| CRUX miters | `satex-gen/cruxmiter:2021` | 230 | 230 | 0 |

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

- **genxormiter**: a parametric generator with no competition instance to check
  against, kept for the family it produces, miters of two random parity
  circuits. Its seed parser assigns where it should accumulate, so only the last
  digit of a multi-digit seed is used: seeds 2, 42, 12 and 102 all produce the
  same formula. Use single-digit seeds until that is fixed upstream.

- **CRUX miters**: all 230 instances the author generated in December 2021, of
  sizes 10 to 32 with ten seeds each, are regenerated exactly. Four of them were
  used in the SAT Race 2019; the copies GBD keeps of those have their variables
  renamed, so they match only up to a renaming, and both hashes are recorded.
  Two pins matter here: Boolector needs `-rwl 2 -nadd 0`, since at its default
  rewriting level it proves the miter away and dumps an empty circuit, and aiger
  must be the May 2021 one, since a later `aigtocnf` writes smaller, different
  formulas. The generator itself is not on any public repository: Armin Biere
  agreed in September 2026 that it be part of SAT Heritage, and it is kept under
  `cruxmiter/upstream` with that notice, so the image stays unpublished.

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

## Adding a generator

Your generator belongs here if it writes CNF (or AIG, or SMT that a pinned tool
turns into CNF) and takes parameters. It does not have to come from a
competition, and it does not have to be a beautiful well coded project. We know
what is like to produce benchs in a rush. We have some generators that are just
one big C file and it is fine. This is a start and people can benefit from it!

**The short way.** Open an issue with a link to the code and one example command
line. We do the rest and send you the page for checking.

**The whole thing, four files.** Say your generator is called `wombat`:

    wombat/Dockerfile          how to build it
    wombat/wombat-gen.sh       optional, when the tool needs a wrapper
    generators.json            one entry describing it
    references/wombat.json     optional, the instances it should reproduce

**1. The recipe.** Copy an existing `Dockerfile`; they all follow the same
shape. The first stage clones your repository at one commit and checks the git
tree hash, which is git's own content digest, so the build fails if the files
ever change under us:

```dockerfile
FROM debian:bookworm-slim AS fetch
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates git \
    && rm -rf /var/lib/apt/lists/*
ARG SOURCE_REPO=https://github.com/you/wombat.git
ARG SOURCE_COMMIT=<the full commit sha>
ARG SOURCE_TREE=<git rev-parse <commit>^{tree}>
RUN git clone -q "$SOURCE_REPO" /src && cd /src && git checkout -q "$SOURCE_COMMIT" \
    && test "$(git rev-parse HEAD^{tree})" = "$SOURCE_TREE" && rm -rf .git

FROM debian:bookworm-slim AS build
RUN apt-get update && apt-get install -y --no-install-recommends gcc libc6-dev make \
    && rm -rf /var/lib/apt/lists/*
COPY --from=fetch /src /src
WORKDIR /src
RUN make

FROM debian:bookworm-slim
COPY --from=build /src/wombat /usr/local/bin/
WORKDIR /data
ENTRYPOINT ["/usr/local/bin/wombat"]
```

**2. One rule for the interface:** the image writes the CNF on standard output
and nothing else, so that `docker run --rm satex-gen/wombat:2026 40 7 > x.cnf`
is all a user needs. If your tool writes to a file, or prints a report first,
add a three-line wrapper like `cruxmiter/crux-gen.sh` and make it the entry
point.

**3. Pin whatever decides the output.** The compiler version, the interpreter
version, every tool in the chain. Python's `random` does not promise the same
draws across versions, and a C library's `rand` differs across platforms: pin
the image, not just the sources. If your generator seeds itself from the clock,
say so, and add an option for an explicit seed if you can.

**4. Describe it** in `generators.json`:

```json
"wombat": {
  "name": "Wombat", "authors": "Your Name", "authors_source": "your repository",
  "year": 2026, "competitions": ["SAT Competition 2026"], "language": "C",
  "license": "MIT", "publish_image": true,
  "source_repo": "https://github.com/you/wombat.git",
  "source_commit": "...", "source_tree": "...",
  "image": "satex-gen/wombat:2026",
  "usage": "wombat SIZE SEED",
  "seed": "the second argument"
}
```

`license` and `publish_image` are the two that matter to you: with a licence we
build and publish the image, without one we publish only the recipe, and
readers build it themselves. Adding a licence file to your repository is the
single most useful thing you can do for us.

**5. Reference instances, if you have any.** They are what turns a recipe into a
checked one. List the instances your generator should reproduce, with the
arguments that produce them and their GBD hash, in `references/wombat.json`:

```json
{"generator": "wombat",
 "source": "where these hashes come from",
 "references": [
   {"instance": "wombat-40-7.cnf", "gbdhash": "…", "args": ["40", "7"],
    "note": "parameters read from the file name"}
 ]}
```

The hash is the GBD identifier, the MD5 of the normalised CNF. Compute it with
the tool image of this repository:

```sh
docker build -t satex-gen/gbd:0.4.2 tools/gbd
docker run --rm -v "$PWD:/data" satex-gen/gbd:0.4.2 wombat-40-7.cnf
```

If your instances are in the competitions, their hashes are already in
[GBD](https://benchmark-database.de) and we can look them up from the file
names. If they are not, send the files and we hash them, as was done for the
230 CRUX miters.

**6. Check it:**

```sh
docker build -t satex-gen/wombat:2026 wombat
python3 tools/verify.py wombat
```

One line per instance, from `N1`, the same GBD hash, down to `--`. Anything
below `N1` is worth reading rather than hiding: it usually means an archived
copy was shuffled or a tool changed, which is exactly what this repository is
for.

Then open a pull request. The site rebuilds itself and your generator gets its
page.

## Bridges

A generator makes an instance out of parameters. A **bridge** starts from an
artefact that another competition distributes, a circuit of the Hardware Model
Checking Competition for instance, and encodes it into CNF with a pinned
toolchain. Hundreds of SAT competition instances come from such artefacts, and
the parameter of the encoding, the number of time frames of an unrolling, is
what lets the family scale.

We do not redistribute the benchmarks of another competition. `upstream/` keeps
one manifest per collection: where the archive lives, its checksum, its terms,
and the checksum of every member. `tools/fetch_upstream.py` downloads it into a
cache outside the repository:

```sh
tools/fetch_upstream.py hwmcc10            # into ~/.cache/satex-benchs by default
tools/fetch_upstream.py hwmcc10 --record   # write the checksums back into the manifest
docker run --rm -v "$CACHE/hwmcc10/files:/data:ro" satex-gen/aiger:2021 unroll 45 bobsm5378d2.aig > x.cnf
```

A reference instance of a bridge names the upstream file it starts from, and
the verifier fetches and mounts it:

```json
{"instance": "hwmcc10-timeframe-expansion-k45-bobsm5378d2-tseitin.cnf",
 "gbdhash": "f7d34470d887c8fd66afeb28ba2911d3",
 "upstream": {"collection": "hwmcc10", "file": "bobsm5378d2.aig"},
 "args": ["unroll", "45", "{file}"]}
```

**The first bridge, and an open question.** `bridges/aiger` builds the AIGER
toolbox and unrolls the HWMCC 2010 models. It produces the right family at any
depth, but it does not reproduce the 31 unrolled instances the SAT competitions
used. The model is identical in the 2010 and 2011 AIGER distributions and the
depth is right, yet for `bobsm5378d2` at depth 45 our encoding has 82006
variables and 223815 clauses where the submitted file has 82007 and 241364.
Neither the 2011 nor the 2021 `aigtocnf`, nor ABC's `frames` command,
reproduces it. If you know which tool did the timeframe expansion for those
submissions, please tell us.

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
