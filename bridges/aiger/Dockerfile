# A bridge, not a generator: it does not invent instances, it encodes artefacts
# that another competition distributes.  Here the AIGER toolbox (Armin Biere,
# MIT) turns the circuits of the Hardware Model Checking Competition into CNF:
# aigunroll expands a model over k time frames, aigtocnf writes the Tseitin
# encoding, aigmiter builds the miter of two circuits, aigmove turns bad state
# properties into outputs, which is what aigunroll needs before it will touch a
# model written the AIGER 1.9 way.
#
# aiger of May 2021: a later aigtocnf simplifies more and writes different
# formulas, as the CRUX miters showed.
FROM debian:bookworm-slim AS fetch
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates git \
    && rm -rf /var/lib/apt/lists/*
ARG SOURCE_REPO=https://github.com/arminbiere/aiger.git
ARG SOURCE_COMMIT=5f8ce5ca5fc42a06e5d713309f99195a740ac2b4
ARG SOURCE_TREE=7a9f000b9718b50d15bd9b7ab3cf7b889c50ddad
RUN git clone -q "$SOURCE_REPO" /src \
    && cd /src && git checkout -q "$SOURCE_COMMIT" \
    && test "$(git rev-parse HEAD^{tree})" = "$SOURCE_TREE" && rm -rf .git

FROM debian:bookworm-slim AS build
RUN apt-get update && apt-get install -y --no-install-recommends gcc libc6-dev make \
    && rm -rf /var/lib/apt/lists/*
COPY --from=fetch /src /src
WORKDIR /src
RUN ./configure.sh && make aigunroll aigtocnf aigmiter aiginfo aigtoaig aigmove \
    && gcc -O2 -o poormanaigtocnf examples/code/poormanaigtocnf.c aiger.c -I.

FROM debian:bookworm-slim
COPY --from=build /src/aigunroll /src/aigtocnf /src/aigmiter /src/aiginfo /src/aigtoaig /src/aigmove /src/poormanaigtocnf /usr/local/bin/
COPY --from=fetch /src /usr/local/share/aiger
COPY aiger-bridge.sh /usr/local/bin/aiger-bridge
RUN chmod +x /usr/local/bin/aiger-bridge
WORKDIR /data
ENTRYPOINT ["/usr/local/bin/aiger-bridge"]
