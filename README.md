# SAT Heritage generators (pilot)

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

## Results

| Generator | Image | References | N1 | N3 |
|---|---|---|---|---|
| sgen1 | `satex-gen/sgen1:2009` | 30 | 28 | 2 |
| CNFgen | `satex-gen/cnfgen:0.9.6` | 24 | 24 | 0 |

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

## Layout

- `generators.json`: one entry per generator (authors and their source, licence, image, usage, seed)
- `<generator>/Dockerfile`: the recipe; sources are downloaded and checked against a SHA-256
- `references/<generator>.json`: reference instances with GBD hashes and parameters
- `results/<generator>.json`: output of the last verification
- `tools/gbd`: the GBD hash image; `tools/verify.py`: the verifier
