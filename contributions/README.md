# contributions

**Drop your generator here as it is, and we put it where it belongs.**

This directory has no rules on purpose. If you wrote a program that produces SAT
benchmarks and you would rather not learn our layout to give it to us, open a
pull request that adds one directory here, named after your generator, and put
in whatever you already have:

    contributions/wombat/wombat.c          the source, in whatever shape it is
    contributions/wombat/Makefile          or the compile line, in a text file
    contributions/wombat/run-it.sh         the script you really ran
    contributions/wombat/NOTES             what it wants: a compiler, a library, a seed

Nothing has to be tidy, nothing has to build on a machine other than yours, and
nothing outside your own directory changes, so two contributors never meet in
the same file.

What helps most, if you have it: **one example command line**, and the name or
the hash of **one instance it should produce**. That is what lets us check the
packaged version against what you actually submitted, rather than hope.

## What we do with it

We move the code into `cnf/<name>/` or `bridges/<name>/`, write the three or
four files the repository wants around it — a `Dockerfile` that builds it from a
pinned source, a `meta.json` saying what it is, and a `references.json` when
there are instances to reproduce — build the image, check it by regenerating
what you gave us, and send you the page before anything is published. See
[adding a generator](../README.md#adding-a-generator) for what those files are,
if you are curious; you do not need to write them.

Once the recipe exists, your files leave this directory: the recipe builds from
your own repository at a pinned commit, or from an archive with its checksum,
and `meta.json` records where the code came from. This directory is a doorstep,
not a second copy of the repository. Nothing in it is built by CI.

## About the licence

Two different things, and only the second needs a decision from you. We publish
the **recipe** for every generator, which lets anyone rebuild your program
themselves. We publish the **image** only when the licence allows it: a
`LICENSE` file in your own repository, or one line in the pull request saying
under what terms the code may be used, is enough. Without one we publish the
recipe and say plainly that the image is withheld, which is how several
generators here stand today.

If you would rather the whole thing stayed unpublished, say so in the pull
request and we record that instead of guessing.
