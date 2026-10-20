# XCSP3 to CNF: the other constraint-programming bridge.  XCSP3 is the format
# of the XCSP competitions, and an instance of that competition is either an
# XCSP3 file or a PyCSP3 model with its data.  Both go in here and a CNF comes
# out, encoded by Picat's SAT module.
#
# Neng-Fa Zhou's XCSP3 interpreter reads an instance and posts its constraints
# to that module, then solves.  It has no option to write the formula, so the
# bridge adds one in a Picat program of its own: it loads the interpreter, calls
# its parser, and calls the solver itself with the dump option.  The
# interpreter is not modified, nor even patched.
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

FROM debian:bookworm-slim AS xcsp
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates git \
    && rm -rf /var/lib/apt/lists/*
ARG XCSP_REPO=https://github.com/nfzhou/xcsp.git
ARG XCSP_COMMIT=6951243a8772b5c64379b2b8996a7b3c0e695ef2
ARG XCSP_TREE=bd1106ca8bd51d2a0787bec510a2903675915afb
RUN git clone -q "$XCSP_REPO" /xcsp \
    && cd /xcsp && git checkout -q "$XCSP_COMMIT" \
    && test "$(git rev-parse HEAD^{tree})" = "$XCSP_TREE" && rm -rf .git

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
        libstdc++6 python3 python3-pip xz-utils \
    && rm -rf /var/lib/apt/lists/*
# PyCSP3 is how the competition's problems are written: a model and its data,
# compiled to an XCSP3 instance.  Pinned, like everything else here.
ARG PYCSP3_VERSION=2.6.1
RUN pip3 install --no-cache-dir --break-system-packages "pycsp3==$PYCSP3_VERSION" \
    && python3 -c "import pycsp3"
COPY --from=picat /picat /picat
COPY --from=xcsp /xcsp /opt/xcsp3/interpreter
ENV PATH=/picat/emu:$PATH \
    PICATPATH=/picat/lib:/picat/lib2
# our own Picat program: it reuses the interpreter's parser and asks the SAT
# module for the formula instead of a solution
COPY xcsp-dump.pi /opt/xcsp3/xcsp-dump.pi
# two small models of ours, each with one parameter, to show the chain without
# any file; any XCSP3 instance or PyCSP3 model works
COPY models /opt/xcsp3/models
COPY xcsp3-bridge.sh /usr/local/bin/xcsp3-bridge
RUN chmod +x /usr/local/bin/xcsp3-bridge
WORKDIR /data
ENTRYPOINT ["/usr/local/bin/xcsp3-bridge"]
