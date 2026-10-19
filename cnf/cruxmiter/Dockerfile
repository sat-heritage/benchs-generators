# CRUX miters (Armin Biere): a miter between two trees of bit-vector adders
# over the same inputs, added in a random order on each side.  Hard for
# resolution, and used well beyond the competitions, in work on cube and
# conquer and on tuning for cubing.
#
# The chain is the author's own: gencruxmitersmt writes an SMT formula,
# Boolector turns it into an AIG with the normalisation of adders disabled,
# and aigtocnf writes the CNF.
FROM debian:bookworm-slim AS fetch
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates git \
    && rm -rf /var/lib/apt/lists/*
# aiger of May 2021: a later aigtocnf simplifies more and gives smaller,
# different formulas than the ones the author distributed
ARG AIGER_REPO=https://github.com/arminbiere/aiger.git
ARG AIGER_COMMIT=5f8ce5ca5fc42a06e5d713309f99195a740ac2b4
ARG AIGER_TREE=7a9f000b9718b50d15bd9b7ab3cf7b889c50ddad
ARG BOOLECTOR_REPO=https://github.com/Boolector/boolector.git
ARG BOOLECTOR_COMMIT=43dae91c1070e5e2633e036ebd75ffb13fe261e1
ARG BOOLECTOR_TREE=e6691a062cbf001a8eedcfe2f861a7b48504b2b7
RUN git clone -q "$AIGER_REPO" /src/aiger \
    && cd /src/aiger && git checkout -q "$AIGER_COMMIT" \
    && test "$(git rev-parse HEAD^{tree})" = "$AIGER_TREE" && rm -rf .git
RUN git clone -q "$BOOLECTOR_REPO" /src/boolector \
    && cd /src/boolector && git checkout -q "$BOOLECTOR_COMMIT" \
    && test "$(git rev-parse HEAD^{tree})" = "$BOOLECTOR_TREE" && rm -rf .git

FROM debian:bookworm-slim AS build
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl g++ gcc git cmake make patch python3 zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*
COPY --from=fetch /src /src
# Boolector pulls its solver backends with its own scripts
WORKDIR /src/boolector
RUN ./contrib/setup-lingeling.sh && ./contrib/setup-btor2tools.sh && ./contrib/setup-cadical.sh \
    && ./configure.sh && cd build && make -j"$(nproc)"
WORKDIR /src/aiger
RUN ./configure.sh && make aigtocnf
COPY upstream/gencruxmitersmt.c /src/crux/
WORKDIR /src/crux
RUN gcc -g -Wall -o gencruxmitersmt gencruxmitersmt.c

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends libstdc++6 zlib1g \
    && rm -rf /var/lib/apt/lists/*
COPY --from=build /src/boolector/build/bin/boolector /usr/local/bin/
COPY --from=build /src/aiger/aigtocnf /usr/local/bin/
COPY --from=build /src/crux/gencruxmitersmt /usr/local/bin/
COPY upstream /usr/local/share/cruxmiter
COPY crux-gen.sh /usr/local/bin/crux-gen
RUN chmod +x /usr/local/bin/crux-gen
WORKDIR /data
ENTRYPOINT ["/usr/local/bin/crux-gen"]
