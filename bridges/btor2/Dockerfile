# BTOR2 to CNF: the bridge for the hardware competitions since 2019.  The
# Hardware Model Checking Competition distributed AIGER until 2017 and BTOR2,
# word level, from 2019 on.  btor2aiger bit blasts a BTOR2 model into an AIG,
# and from there the road is the one bridges/aiger already walks: move the bad
# state properties to outputs, expand over k time frames, encode with the plain
# Tseitin encoder.  The depth k is what makes the family scale.
#
# btor2aiger is not built by default and needs two things the released
# Boolector does not give: it calls a bit blasting API that lives only on
# Boolector's bitblast-api branch, which is what the authors' own
# setup-deps.sh checks out.  Both are pinned here, branch and all.
FROM debian:bookworm-slim AS aiger
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates git \
    && rm -rf /var/lib/apt/lists/*
ARG AIGER_REPO=https://github.com/arminbiere/aiger.git
ARG AIGER_COMMIT=5f8ce5ca5fc42a06e5d713309f99195a740ac2b4
ARG AIGER_TREE=7a9f000b9718b50d15bd9b7ab3cf7b889c50ddad
RUN git clone -q "$AIGER_REPO" /aiger \
    && cd /aiger && git checkout -q "$AIGER_COMMIT" \
    && test "$(git rev-parse HEAD^{tree})" = "$AIGER_TREE" && rm -rf .git

FROM debian:bookworm-slim AS boolector
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl git g++ gcc libc6-dev cmake make python3 \
    && rm -rf /var/lib/apt/lists/*
ARG BTOR_REPO=https://github.com/boolector/boolector.git
# the bitblast-api branch, not master: master does not export the calls
# btor2aiger makes, and the compile fails on them
ARG BTOR_COMMIT=0eafd0c0d98f5e14aca7cc105c7eab8e2ba29916
RUN git clone -q "$BTOR_REPO" /btor && cd /btor && git checkout -q "$BTOR_COMMIT" \
    && ./contrib/setup-btor2tools.sh >/dev/null && ./contrib/setup-lingeling.sh >/dev/null \
    && ./configure.sh --prefix /src/deps/install >/dev/null && cd build \
    && make -j"$(nproc)" install >/dev/null && test -f /src/deps/install/lib/libboolector.a

FROM debian:bookworm-slim AS build
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl git g++ gcc libc6-dev cmake make python3 \
    && rm -rf /var/lib/apt/lists/*
ARG SOURCE_REPO=https://github.com/hwmcc/btor2tools.git
ARG SOURCE_COMMIT=e6941e37e056084ab6e51c5c1eee6233089a330d
ARG SOURCE_TREE=8227aa41b2fd6016cdbac40ed4e7f000d87b23e5
RUN git clone -q "$SOURCE_REPO" /src && cd /src && git checkout -q "$SOURCE_COMMIT" \
    && test "$(git rev-parse HEAD^{tree})" = "$SOURCE_TREE" && rm -rf .git
# btor2aiger compiles against the AIGER 1.9.4 release, the one their setup
# script fetches: the library of the current aiger repository has moved on and
# the compile fails on it.  So this stage carries both, 1.9.4 to build against
# and the pinned repository for the tools that run.
ARG AIGER_TARBALL=http://fmv.jku.at/aiger/aiger-1.9.4.tar.gz
ARG AIGER_TARBALL_SHA256=bd7bb89f51deef8c5681753c861bf0ab7f85f166fb30da0caf83c2d31f6df2d1
RUN mkdir -p /src/deps && cd /src/deps \
    && curl -sLO "$AIGER_TARBALL" \
    && echo "$AIGER_TARBALL_SHA256  aiger-1.9.4.tar.gz" | sha256sum -c - \
    && tar xf aiger-1.9.4.tar.gz && mv aiger-1.9.4 aiger && rm aiger-1.9.4.tar.gz
COPY --from=boolector /src/deps/install /src/deps/install
# Boolector's installed CMake config names the libraries of its own build tree
# by absolute path, so they have to be where it left them
COPY --from=boolector /btor/deps/install /btor/deps/install
RUN cd /src && ./configure.sh >/dev/null && cd build \
    && cmake -DBUILD_BTOR2AIGER=ON .. >/dev/null && make -j"$(nproc)" btor2aiger >/dev/null \
    && test -x bin/btor2aiger
# the AIGER tools of the same commit bridges/aiger uses, so a BTOR2 model and
# an AIGER model of the same competition end up in the same encoder
COPY --from=aiger /aiger /aigersrc
RUN cd /aigersrc && ./configure.sh >/dev/null && make aigmove aigunroll aigtocnf aiginfo >/dev/null \
    && gcc -O2 -o poormanaigtocnf examples/code/poormanaigtocnf.c aiger.c -I.

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends libstdc++6 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=build /src/build/bin/btor2aiger /usr/local/bin/
# btor2aiger links the BTOR2 parser as a shared library
COPY --from=build /src/build/lib/libbtor2parser.so /usr/local/lib/
RUN ldconfig
COPY --from=build /aigersrc/aigmove /aigersrc/aigunroll /aigersrc/aigtocnf /aigersrc/aiginfo \
     /aigersrc/poormanaigtocnf /usr/local/bin/
COPY btor2-bridge.sh /usr/local/bin/btor2-bridge
RUN chmod +x /usr/local/bin/btor2-bridge
WORKDIR /data
ENTRYPOINT ["/usr/local/bin/btor2-bridge"]
