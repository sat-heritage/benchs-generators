# Round-robin tournament scheduling (Joseph Reeves, SAT Competition 2025).
# The submitted scripts hard-code their list of instances, so the entry point
# runs the author's encoder verbatim on a single (n, rounds) pair given on the
# command line.
FROM debian:bookworm-slim AS fetch
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates git \
    && rm -rf /var/lib/apt/lists/*
ARG SOURCE_REPO=https://github.com/Aeacu2/RR-Benchmarks.git
ARG SOURCE_COMMIT=6735ee973a0f2b0489a2b13fabe3455e90042728
ARG SOURCE_TREE=2e897d2a1e34376ac8a883176ca00368e9518cb1
RUN git clone -q "$SOURCE_REPO" /src \
    && cd /src && git checkout -q "$SOURCE_COMMIT" \
    && test "$(git rev-parse HEAD^{tree})" = "$SOURCE_TREE" \
    && rm -rf /src/.git

FROM python:3.12.7-slim-bookworm
ARG PYSAT_VERSION=1.8.dev17
RUN pip install --no-cache-dir "python-sat==${PYSAT_VERSION}"
COPY --from=fetch /src /src
COPY rr-gen.sh /usr/local/bin/rr-gen
RUN chmod +x /usr/local/bin/rr-gen
ENV PYTHONHASHSEED=0
WORKDIR /data
ENTRYPOINT ["/usr/local/bin/rr-gen"]
