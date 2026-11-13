# Syndrome decoding as SAT: the generator of Carl Berton, Sami Cherif and
# Claire Delaplace, behind their FM 2026 paper.  Two steps, both theirs: a
# random parity-check matrix and syndrome from a size n and a seed, then a
# model of the decoding problem in CNF, through PySAT's cardinality and
# pseudo-Boolean encodings.
#
# python-sat is pinned at 1.9.dev16, and the version is the whole point.  Up to
# 1.9.dev16 (15 October 2026) PySAT's encodings reproduce the instances the
# authors committed byte for byte; from 1.9.dev17 (20 October 2026) they do not:
# the same command then gives 3630 variables and 8218 clauses where their file
# has 4048 and 8683.  Regenerating their paper's formulas with today's PySAT
# gives different formulas, so the recipe holds the version that agrees with
# them.
#
# The authors' repository also carries 86 MB of instances it produced; only the
# code travels into the image, with the commit and git tree hash checked.
FROM debian:bookworm-slim AS fetch
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates git \
    && rm -rf /var/lib/apt/lists/*
ARG SD_REPO=https://github.com/carlberton/sat-syndrome-decoding.git
ARG SD_COMMIT=7177dc9fbae346b1dd997b61af6ad0208f7a35f2
ARG SD_TREE=4059c751f3c8074c2a08e83cfb2ca787e9977d15
RUN git clone -q "$SD_REPO" /src \
    && cd /src && git checkout -q "$SD_COMMIT" \
    && test "$(git rev-parse HEAD^{tree})" = "$SD_TREE" \
    && rm -rf .git \
    && rm -rf syndrome_decoding_problem/Challenges low_weight_codeword_problem/Challenges

# pypblib compiles from source, so the toolchain stays in a stage of its own
FROM python:3.12-slim-bookworm AS build
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*
ARG PYSAT_VERSION=1.9.dev16
RUN pip install --no-cache-dir --target /pkgs "python-sat[pblib]==${PYSAT_VERSION}"

FROM python:3.12-slim-bookworm
COPY --from=build /pkgs /pkgs
COPY --from=fetch /src/syndrome_decoding_problem /opt/satsd/sd
COPY --from=fetch /src/low_weight_codeword_problem /opt/satsd/lw
COPY --from=fetch /src/README.md /opt/satsd/README.md
ENV PYTHONPATH=/pkgs
COPY satsd-gen.sh /usr/local/bin/satsd-gen
RUN chmod +x /usr/local/bin/satsd-gen \
    && python -c "import pysat.card, pysat.pb; print('pysat ok')"
WORKDIR /data
ENTRYPOINT ["/usr/local/bin/satsd-gen"]
