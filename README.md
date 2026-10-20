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

**N3 has a limit, and we ran into it.** The Dubois family, 2d exclusive ors of
three variables chained into one contradiction, has very little structure for an
isomorphism hash to work with. Seventeen instances of the SAT competitions, in
the families `tseitin-formulas` and `random-graph-xorsat` and submitted by five
different authors, carry the same `isohash2` as a Dubois instance of the same
size — and they are not the same formula under any renaming: a Dubois instance
has four of its exclusive ors sharing two variables with a neighbour, where
those competition instances have none. Same size, same clause shape, same
parity class, different structure, one hash. So N3 is evidence on most families
and no evidence at all on exclusive-or systems; only N1 and N2 are conclusive,
and a structural check is worth doing before claiming a family is reproduced.

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

| Generator or bridge | Image | References | Exact | Up to renaming |
|---|---|---|---|---|
| sgen1 | `satex-gen/sgen1:2009` | 30 | 28 | 2 |
| CNFgen | `satex-gen/cnfgen:0.9.6` | 24 | 24 | 0 |
| mdp-benchmark | `satex-gen/mdp:2022` | 30 | 28 | 0 |
| Round-robin | `satex-gen/roundrobin:2025` | 20 | 20 | 0 |
| lockchart-to-cnf | `satex-gen/lockchart:2025` | 5 (5 small ones checked) | 3 | 0 |
| Oddball | `satex-gen/oddball:2025` | 40 | 40 | 0 |
| Community Attachment | `satex-gen/commattach:2015` | 56 | 54 | 1 |
| CRUX miters | `satex-gen/cruxmiter:2021` | 230 | 230 | 0 |
| AIGER bridge, model checking circuits | `satex-gen/aiger:2021` | 31 | 30 | 0 |
| AIGER bridge, bit-vector circuits | `satex-gen/aiger:2021` | 31 | 30 | 0 |
| genxormiter | `satex-gen/genxormiter:2025` | none | — | — |

487 of 497 reference instances are regenerated exactly, every image rebuilt from its recipe before the check.

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
  `cnf/cruxmiter/vendor` with that notice, so the image stays unpublished.

## Building and running

```sh
docker build -t satex-gen/gbd:0.4.2 tools/gbd
docker build -t satex-gen/sgen1:2009 cnf/sgen1
docker build -t satex-gen/cnfgen:0.9.6 cnf/cnfgen
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

    cnf/wombat/Dockerfile        how to build it
    cnf/wombat/wombat-gen.sh     optional, when the tool needs a wrapper
    cnf/wombat/meta.json         what it is: authors, licence, usage, seed
    cnf/wombat/references.json   optional, the instances it should reproduce

Nothing outside that directory changes, so two contributors never meet in the
same file.

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

**4. Describe it** in `cnf/wombat/meta.json`:

```json
{
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
arguments that produce them and their GBD hash, in `cnf/wombat/references.json`:

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
docker build -t satex-gen/wombat:2026 cnf/wombat
python3 tools/verify.py wombat
```

One line per instance, from `N1`, the same GBD hash, down to `--`. Anything
below `N1` is worth reading rather than hiding: it usually means an archived
copy was shuffled or a tool changed, which is exactly what this repository is
for.

Then open a pull request. The site rebuilds itself and your generator gets its
page.

## A generator found by following a bridge

The `dubois` family sits in every early benchmark suite and had no generator
here: nobody we asked had the code. The XCSP competitions turned out to carry a
`Dubois.py` model, and following it back led to the contributed directory of the
Second DIMACS Implementation Challenge, where Olivier Dubois' own
`gensathard.c` has been sitting since 1993. `cnf/dubois` builds it, from the
copy kept with its provenance in our `old-sources` release, and reproduces
exactly what those sources produce:

```sh
docker run --rm satex-gen/dubois:1993 20 > dubois20.cnf     # 60 variables, 160 clauses
docker run --rm satex-gen/dubois:1993 400 > big.cnf         # as far as you like
```

The files carry no licence, as a 1993 contribution to a challenge, so the recipe
is published and the image is not. The XCSP3 bridge produces the same formulas
from the competition's own model, which is how the two met.

## Instances nobody submitted

Reproducing the instances a competition kept is one half of the point; making
new ones is the other. A dozen files were submitted, the generator can make a
thousand, at any size, and those instances are in no database, GBD included.

`generators.json` can declare sample invocations across a generator's
parameters, and `tools/sample_generators.py` runs each of them twice on the
built image, records the size of the formula and checks that the same command
gives the same formula:

```sh
python3 tools/sample_generators.py           # every generator that declares samples
python3 tools/sample_generators.py aiger     # only this one
```

The result lands in `data/samples.json` and becomes the "What it can produce"
table of each generator page. Today's 34 samples are all reproducible, and they
span, for example, the unrolling of one model checking circuit from 35 thousand
to 362 thousand clauses by changing one number.

## Your own problem

The bridges are not tied to the competitions. A bridge reads any file of the
format it understands, so a circuit of yours goes through the same chain as one
the organisers distributed:

```sh
docker run --rm -v "$PWD:/data" satex-gen/aiger:2021 cnf mycircuit.aig > mine.cnf
docker run --rm -v "$PWD:/data" satex-gen/aiger:2021 unroll 20 mymodel.aig > mine.cnf
docker run --rm -v "$PWD:/data" satex-gen/freelunch:2022 domain.pddl problem.pddl cr 12 > mine.cnf
docker run --rm -v "$PWD:/data" satex-gen/minizinc:2.10.1 mymodel.mzn mydata.dzn > mine.cnf
```

Nothing leaves the machine: the directory you mount is the only thing the image
sees.

Then comes the part that is worth more than the encoding: **which solver to
run**. The winner of a competition is not the best choice on every kind of
problem. On the Ascon cryptography family of 2023, SeqFROST solved all twenty
instances while the overall winner did not; on the 2024 scheduling family,
AMSAT solved more than the winner did. `tools/collect_solvers.py` matches the
solvers of the detailed results with the images of the companion project, and
each family page then carries the ranking on that family alone with the command
that runs each solver.

The website gathers this as a three-step page: turn your problem into CNF, pick
a solver, and find the family your problem resembles.

## Sources that exist nowhere else

A few generators are on no public repository: their author wrote them, used
them, and never published them. When one reaches us with the author's
permission, it goes into a release of this repository rather than into git, so
that every recipe keeps fetching and checking its sources the same way.

One release per year, `sources-<year>`, one archive per tool, named after the
date of the source rather than of the upload:

```
sources-2026/cruxmiter-gencruxmitersmt-20211222.tar.gz
└── gencruxmitersmt/
    ├── NOTICE           who wrote it, who allowed what, and when
    ├── PROVENANCE.json  origin, permission, and the checksum of every file
    ├── README.upstream  the author's own notes, untouched
    └── src/             the files exactly as received
```

The recipe then pins the archive's SHA-256, exactly as another recipe pins a
commit. If a newer version arrives, it becomes another archive with its own
date, and the old one stays where it is.

## Old competitions, encoded today

A planning competition distributes PDDL, a hardware verification competition
distributes circuits; neither distributes formulas. The collections are
declared in `collections/`, fetched into a local cache, and encoded on demand:

```sh
tools/fetch_upstream.py mznc       # the MiniZinc Challenge, 2008 to 2026
tools/fetch_upstream.py ipc        # the planning competitions, 1998 to 2014
docker run --rm -v "$CACHE/ipc/files/ipc-1998/domains/gripper-round-1-strips:/data:ro" \
  satex-gen/freelunch:2022 domain.pddl instances/instance-10.pddl cr 10 > gripper.cnf
```

A collection may be an archive or a repository: `collections/ipc.json` pins a
commit and its git tree, the same digest the recipes use, so the instances
cannot change under us.

Measured on fifteen instances of the 1998 competition at three plan lengths:
339 thousand clauses in the median, 8.9 MB compressed. Sizes vary wildly with
the task, from 23 thousand clauses for a gripper problem to 61 million for a
hundred-block one, so a pack picks its instances rather than taking everything.
`packs/ipc-cnf.json` is the spec of that one, still proposed.

### The packs of the planning competitions

Seven packs, one per competition, all built the same way: classical strips
domains only, two instances each, plan lengths six and ten, nothing past 300
thousand clauses.

| Competition | Instances | Left out | Size |
|---|---|---|---|
| 1998 and 2000 | 47 | 17 over the clause limit | 2.8 MB |
| 2002 | 29 | 11 over the limit, 4 by the encoder | 2.2 MB |
| 2004 | 4 | 4 refused by the translator | 0.04 MB |
| 2006 | 16 | 8 by the encoder | 0.1 MB |
| 2008 | 48 | 12 refused by the translator | 2.0 MB |
| 2011 | 82 | 46 over the limit, 16 by the encoder | 6.4 MB |
| 2014 | 79 | 107 over the limit, 22 by the encoder | 9.9 MB |

305 formulas, 23 MB in all, in the `packs-2026` release, with an `index.json`
in each archive giving the GBD hash of every file and the command that made it.

**What is left out, and why it matters which.** A domain that is temporal,
numeric, metric or carries preferences is not classical planning: Fast
Downward's translator refuses it, and the packs now exclude those domains
instead of trying them. A formula past the clause limit is a deliberate choice,
since a pack holds examples. What remains, 50 tasks over the seven packs, is
freeLunch failing on a task the translator accepted; those are recorded one by
one in the indexes. The first run of these packs reported 515 refusals in one
undifferentiated heap, which told nobody anything.

### The packs of the constraint competition

Five packs: one per four editions of the MiniZinc Challenge from 2008 to 2023,
one instance per problem, and the 2024 edition on its own with two instances per
problem. The organisers' own models and data, through the MiniZinc compiler
2.10.1 and Picat's SAT module, nothing past 300 thousand clauses and five
minutes per instance.

| Editions | Instances | Left out | Size |
|---|---|---|---|
| 2008 to 2011 | 25 | 24 do not compile with 2.10.1, 3 over the clause limit | 3.3 MB |
| 2012 to 2015 | 60 | 16 over the limit, 2 empty formulas, 1 by the encoder | 9.3 MB |
| 2016 to 2019 | 54 | 22 over the limit, 2 by the encoder, 1 over time, 1 does not compile | 7.4 MB |
| 2020 to 2023 | 46 | 18 over the limit, 8 settled by propagation, 6 do not compile, 1 over time, 1 by the encoder | 6.5 MB |
| 2024 | 29 | 4 over the limit, 3 over time, 2 settled by propagation, 2 do not compile | 6.6 MB |

214 formulas, 33 MB in all, in the `packs-2026` release beside the planning
packs, with an `index.json` in each archive giving the GBD hash of every file
and the command that made it.

```sh
curl -LO https://github.com/sat-heritage/benchs-generators/releases/download/packs-2026/mznc-cnf-2024.tar
tar xf mznc-cnf-2024.tar
```

**What is left out, and the drift it uncovered.** A formula past the clause
limit or an instance past the five minutes is our choice, since a pack holds
examples. Two other reasons are the chain's: PicatSAT settles some instances by
propagation while it reads the FlatZinc, so there is no formula to write, and it
refuses a few flattened models outright. The third is the interesting one. **31
models of the archive no longer compile with MiniZinc 2.10.1**, almost all of
them in the early editions: the 2009 edition compiles nowhere, 2008 keeps two
problems of ten, 2010 six of eleven, and 2011 all seventeen. Those models use
the search annotations of MiniZinc 1.x, `int_search` with four arguments for
instance, which the modern compiler refuses. The competition's own archive has
drifted away from the competition's own compiler, and reaching the early
editions means pinning the compiler of their year as well: the challenge
archive names the version it used edition by edition, from 2.9.3 in 2025 back to
the 1.x of the first years.

## Bridges

A generator makes an instance out of parameters. A **bridge** starts from an
artefact that another competition distributes, a circuit of the Hardware Model
Checking Competition for instance, and encodes it into CNF with a pinned
toolchain. Hundreds of SAT competition instances come from such artefacts, and
the parameter of the encoding, the number of time frames of an unrolling, is
what lets the family scale.

We do not redistribute the benchmarks of another competition. `collections/` keeps
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

**The fourth bridge takes an XCSP3 instance.** `bridges/xcsp3` carries Neng-Fa
Zhou's XCSP3 interpreter and the same Picat encoder, so the format of the XCSP
competitions goes in and a CNF comes out, either as an instance or as the
PyCSP3 model and data the organisers write their problems in:

```sh
docker run --rm -v "$PWD:/data" satex-gen/xcsp3:2023 instance.xml > mine.cnf
docker run --rm -v "$PWD:/data" satex-gen/xcsp3:2023 Model.py -data=12 > mine.cnf
docker run --rm satex-gen/xcsp3:2023 --builtin queens 30 > queens30.cnf
```

The interpreter posts the constraints of an instance to Picat's SAT module and
then solves; it has no option to write the formula. So the bridge adds one in a
Picat program of its own, which loads the interpreter, calls its parser and
calls the solver itself with the `dump` option: nothing upstream is modified,
not even patched, since its predicates are reached through `call/N` after
`cl/1`. The two constraint bridges agree where they overlap: pigeonhole at n=9
is 40 variables and 750 clauses through either road.

The interpreter carries no licence file, so the recipe is published here and the
image is not. Its author also wrote Picat, which is MPL-2.0; a word from him
would settle it.

**The third bridge takes a constraint model.** `bridges/minizinc` carries the
MiniZinc compiler and PicatSAT, so a model in the language the CP competition is
written in goes in and a CNF comes out:

```sh
docker run --rm -v "$PWD:/data" satex-gen/minizinc:2.10.1 mymodel.mzn mydata.dzn > mine.cnf
docker run --rm -v "$PWD:/data" satex-gen/minizinc:2.10.1 mymodel.mzn -D "n=25" > mine.cnf
docker run --rm satex-gen/minizinc:2.10.1 --builtin queens 30 > queens30.cnf
docker run --rm satex-gen/minizinc:2.10.1 --list
```

The model's own parameters make the family scale: n queens goes from 1208
clauses at n=8 to 13950 at n=20 and 28915 at n=30, with the same encoder
throughout. Four small models of ours are built in, behind `--builtin`, to show
the chain without any file; everything else is the user's model.

Two things are worth knowing. PicatSAT's FlatZinc front end can write the Picat
program it would run, but has no option to write the CNF, so the bridge adds the
`dump` option of `solve/2` to that generated program — one line of `awk`, and
nothing upstream is modified. And Picat writes the whole formula before it
starts solving it, so the bridge stops it as soon as the file holds the clauses
its header announces. For a model with an objective, the formula is the
satisfaction problem Picat encodes first, with no bound on the objective: to get
the usual "is there a solution of cost at most k" family, put that bound in the
model and let k be the parameter.

**The second bridge takes a planning problem.** `bridges/freelunch` carries
freeLunch, the encoder of Tomas Balyo and Vojtech Bardiovsky, and Fast
Downward's translator, so two PDDL files go in and a CNF comes out:

```sh
docker run --rm -v "$PWD:/data" satex-gen/freelunch:2022 domain.pddl problem.pddl cr 12 > mine.cnf
```

The makespan, the number of steps the plan may take, is what makes the family
scale: on the gripper problem it goes from 1649 clauses at four steps to 4313
at twelve, and on a barman task from 585 thousand at five steps to 976 thousand
at nine. The same command twice gives the same formula.

It comes with its own open question. The planning instances of the competitions
cannot be reproduced: their tasks were submitted in 2016 and 2017, the public
history of freeLunch starts in December 2017, and its `exist` encoder fails on
the three tasks we have. The `compactReinforced` encoder works, but no
competition instance uses it on a task the repository carries.

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

One recipe is one directory, and nothing is shared between recipes: adding a
generator is adding a directory.

- `cnf/<name>/`: a generator that writes CNF from parameters — `Dockerfile`,
  `meta.json` (authors and their source, licence, image, usage, seed, samples)
  and `references.json` when it has reference instances
- `bridges/<name>/`: a bridge that encodes what another competition distributes —
  the same files, plus one reference file per upstream collection under
  `references/`
- `collections/<name>.json`: the manifest of an upstream collection, with its
  terms and checksums; never the benchmarks themselves
- `packs/<name>.json`: the spec of a pack we distribute, and why it exists
- `results/`, `data/`: produced by the tools, regenerated at will
- `tools/`: `catalogue.py` reads the recipes, `verify.py` checks them,
  `build_site.py` writes the site, `gbd/` is the hashing image

A target names what the tools work on: a generator, `sgen1`, or a bridge and one
of its collections, `aiger/hwmcc10`.
