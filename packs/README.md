# Packs

A pack is a set of CNF instances we produce and distribute ourselves. It exists
for a reason, and the reason is written in its spec: a paper that needs the
instances, or a collection worth having in CNF as a whole, such as every circuit
of a hardware verification competition, or every instance of a constraint
programming competition.

Two rules keep packs honest.

**We do not republish what GBD already serves.** An instance whose hash is in
GBD is linked, not copied. A pack holds the instances nobody else has: other
parameters, other depths, other sizes.

**The hash is the same one GBD uses**, the MD5 of the normalised CNF. An
instance in a pack is identified exactly as a competition instance is, which is
what lets the two sit side by side.

Each spec here is a file `packs/<name>.json`. `tools/make_pack.py <name>`
produces the files outside the repository and writes the index to
`data/packs/<name>.json`; the files are then attached to a GitHub release, and
to a Zenodo record when the pack is meant to be cited.
