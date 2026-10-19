# genxormiter

The image builds the author's sources verbatim, so it carries the seed bug of
the pinned commit: `parse_seed` assigns where it should accumulate, so only the
last digit of a multi-digit seed is used. Seeds 2, 42, 12 and 102 all produce
the same formula, which leaves ten distinct seeds. Without a seed the generator
takes one from the clock, and the instance cannot be reproduced at all.

`seed-fix.patch` is the two-line fix, proposed upstream and **not applied
here**: recipes in this repository build what their authors published. It also
repairs the neighbouring error message, which passed the integer seed to a
`%s` format instead of the string argument.

Checked on the patched binary:

    seed 2      -> c genxormiter 12 2
    seed 42     -> c genxormiter 12 42
    seed 12345  -> c genxormiter 12 12345

Until the fix lands upstream, use single-digit seeds.
