# CRUX miters (Armin Biere): a miter between two trees of bit-vector adders
# over the same inputs, added in a random order on each side.  Hard for
# resolution, and used well beyond the competitions, in work on cube and
# conquer and on tuning for cubing.
#
# The chain is the author's own: gencruxmitersmt writes an SMT formula,
# Boolector turns it into an AIG with the normalisation of adders disabled,
# and aigtocnf writes the CNF.
FROM debian:bookworm-slim AS fetch
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl git \
    && rm -rf /var/lib/apt/lists/*
# The generator is on no public repository: its sources travel in a release of
# this repository, with the author's permission and a record of where they come
# from.  They are checked here like any other pinned source.
ARG CRUX_URL=https://github.com/sat-heritage/benchs-generators/releases/download/sources-2026/cruxmiter-gencruxmitersmt-20211222.tar.gz
ARG CRUX_SHA256=18fb318b74db1a28ac26a9bd3908e5e6ebccf482b078e6c35e1626b157df3c92
RUN curl -fsSL -o /tmp/crux.tar.gz "$CRUX_URL" \
    && echo "$CRUX_SHA256  /tmp/crux.tar.gz" | sha256sum -c - \
    && mkdir -p /vendor && tar xzf /tmp/crux.tar.gz -C /vendor && rm /tmp/crux.tar.gz
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
COPY --from=fetch /vendor/gencruxmitersmt/src/gencruxmitersmt.c /src/crux/
WORKDIR /src/crux
RUN gcc -g -Wall -o gencruxmitersmt gencruxmitersmt.c

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends libstdc++6 zlib1g \
    && rm -rf /var/lib/apt/lists/*
COPY --from=build /src/boolector/build/bin/boolector /usr/local/bin/
COPY --from=build /src/aiger/aigtocnf /usr/local/bin/
COPY --from=build /src/crux/gencruxmitersmt /usr/local/bin/
COPY --from=fetch /vendor/gencruxmitersmt /usr/local/share/cruxmiter
COPY crux-gen.sh /usr/local/bin/crux-gen
RUN chmod +x /usr/local/bin/crux-gen
WORKDIR /data
ENTRYPOINT ["/usr/local/bin/crux-gen"]
