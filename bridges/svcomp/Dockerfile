# A C program to CNF: the bridge for the Competition on Software Verification.
# SV-COMP distributes verification tasks, a C file and a .yml saying which
# property to prove and under which data model, and CBMC is the bounded model
# checker that turns one into a propositional formula: it unwinds every loop at
# most k times, bit blasts the C semantics, and writes the formula with
# --dimacs.  The bound k is what makes the family scale, exactly as the depth
# does for the hardware bridges.
#
# CBMC comes from the release its authors publish rather than from a build of
# our own, pinned by URL and sha256: the .deb is the binary they tested, it
# carries their own SAT backend, and building CBMC from source downloads a
# solver at build time, which is a pin we could not hold.  The licence, BSD
# four clause, allows the binary to travel provided the notice travels with it,
# so the image keeps the copyright and the acknowledgement at /usr/share/doc
# and the recipe states them too; see the licence note in meta.json.
FROM ubuntu:24.04
# gcc and libc headers are not optional: CBMC preprocesses with the system
# compiler and refuses the task without them
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl gcc libc6-dev \
    && rm -rf /var/lib/apt/lists/*
ARG CBMC_VERSION=6.11.0
ARG CBMC_DEB=https://github.com/diffblue/cbmc/releases/download/cbmc-6.11.0/ubuntu-24.04-cbmc-6.11.0-Linux.deb
ARG CBMC_SHA256=b3721aa541038384d7801ea3aeabbcddc3e8845ac8f1cbff637cf8dec7481ac8
ARG CBMC_COMMIT=820ff0f555b43fb78e0cd9332e498461bd14244b
RUN curl -sL -o /tmp/cbmc.deb "$CBMC_DEB" \
    && echo "$CBMC_SHA256  /tmp/cbmc.deb" | sha256sum -c - \
    && apt-get update && apt-get install -y --no-install-recommends /tmp/cbmc.deb \
    && rm -rf /var/lib/apt/lists/* /tmp/cbmc.deb \
    && cbmc --version
COPY svcomp-bridge.sh /usr/local/bin/svcomp-bridge
RUN chmod +x /usr/local/bin/svcomp-bridge
WORKDIR /data
ENTRYPOINT ["/usr/local/bin/svcomp-bridge"]
