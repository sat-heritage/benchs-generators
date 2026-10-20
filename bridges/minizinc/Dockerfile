# MiniZinc and PicatSAT: the constraint-programming bridge.  A MiniZinc model is
# flattened to FlatZinc by the MiniZinc compiler, and PicatSAT turns the
# FlatZinc into CNF.  The model's own parameters are what make the family
# scale, exactly as the depth does for a bounded model checking unrolling.
#
# Picat's SAT module can write the formula it would solve, with the dump option
# of solve/2.  Its FlatZinc front end does not expose that option, so the
# bridge adds it to the Picat program the front end writes.  That one line is
# ours; nothing in Picat or MiniZinc is modified.
FROM debian:bookworm-slim AS picat
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates git g++ gcc libc6-dev make \
    && rm -rf /var/lib/apt/lists/*
ARG PICAT_REPO=https://github.com/picat-lang/Picat.git
ARG PICAT_COMMIT=f76c0094bae9bc5a74455817b56533062191ae16
ARG PICAT_TREE=7cbdf9060b7e0dfc2aff84211a750f76c3c4f20b
RUN git clone -q "$PICAT_REPO" /picat \
    && cd /picat && git checkout -q "$PICAT_COMMIT" \
    && test "$(git rev-parse HEAD^{tree})" = "$PICAT_TREE" && rm -rf .git
RUN cd /picat/emu && make -f Makefile.linux64 >/dev/null && test -x /picat/emu/picat

# The MiniZinc compiler, built from source: the release tarball of the same
# version carries the IDE and the whole of Qt, which this bridge never uses.
FROM debian:bookworm-slim AS minizinc
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates git g++ cmake make \
    && rm -rf /var/lib/apt/lists/*
ARG MZN_REPO=https://github.com/MiniZinc/libminizinc.git
ARG MZN_COMMIT=c3448c48e7f05f13805616cfd1b9e94972eef58c
ARG MZN_TREE=930fcc3f46ff71224883251bc398e2bc7be1b8a4
RUN git clone -q "$MZN_REPO" /src \
    && cd /src && git checkout -q "$MZN_COMMIT" \
    && test "$(git rev-parse HEAD^{tree})" = "$MZN_TREE" && rm -rf .git
RUN cd /src && cmake -S . -B build -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX=/opt/minizinc >/dev/null \
    && cmake --build build -j"$(nproc)" >/dev/null && cmake --install build >/dev/null \
    && /opt/minizinc/bin/minizinc --version

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends libstdc++6 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=picat /picat /picat
COPY --from=minizinc /opt/minizinc /opt/minizinc
ENV PATH=/opt/minizinc/bin:/picat/emu:$PATH \
    PICATPATH=/picat/lib:/picat/lib2
# The MiniZinc compiler needs a solver configuration to know which library to
# flatten against.  PicatSAT reads standard FlatZinc, so this one asks for the
# standard library and nothing else.
COPY picatsat.msc /opt/minizinc/share/minizinc/solvers/picatsat.msc
# Four small models of our own, each with one parameter, to show the chain and
# how a family scales.  Any MiniZinc model works: these are only examples.
COPY models /opt/minizinc-bridge/models
COPY minizinc-bridge.sh /usr/local/bin/minizinc-bridge
RUN chmod +x /usr/local/bin/minizinc-bridge \
    && minizinc --solvers | grep -q PicatSAT
WORKDIR /data
ENTRYPOINT ["/usr/local/bin/minizinc-bridge"]
