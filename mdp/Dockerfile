# Minimum-disagreement parity formulas (Randal E. Bryant, SAT Competition 2022).
# The repository also ships src/generate.sh, the script that produced the
# submitted set, so the parameters of every instance are known.
FROM debian:bookworm-slim AS fetch
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates git \
    && rm -rf /var/lib/apt/lists/*
ARG SOURCE_REPO=https://github.com/rebryant/mdp-benchmark.git
ARG SOURCE_COMMIT=9d7199acc6ae7cedb9f9581c5a0a147351228a84
ARG SOURCE_TREE=61abbdd6b0cde3f001040e8f2e9a4e9ff3614977
# the git tree hash is git's own content digest: it pins the files themselves,
# unlike the tarballs GitHub generates on the fly
RUN git clone -q "$SOURCE_REPO" /src \
    && cd /src && git checkout -q "$SOURCE_COMMIT" \
    && test "$(git rev-parse HEAD^{tree})" = "$SOURCE_TREE" \
    && rm -rf /src/.git

FROM python:3.12.7-slim-bookworm
COPY --from=fetch /src /src
COPY mdp-gen.sh /usr/local/bin/mdp-gen
RUN chmod +x /usr/local/bin/mdp-gen
ENV PYTHONHASHSEED=0
WORKDIR /data
ENTRYPOINT ["/usr/local/bin/mdp-gen"]
