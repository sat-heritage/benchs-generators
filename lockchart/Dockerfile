# Lock-charts, that is mechanical master-key systems (Nikolaus Riedl-Ehrenreich,
# SAT Competition 2025).  The repository also ships the submitted CNF files.
FROM debian:bookworm-slim AS fetch
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates git \
    && rm -rf /var/lib/apt/lists/*
ARG SOURCE_REPO=https://github.com/nrilu/lockchart-to-cnf.git
ARG SOURCE_COMMIT=6ba6ec0539bab3e690c5e65419315d0dcebf917b
ARG SOURCE_TREE=4b7926400c08ba03675770796777e5ec8253f22d
RUN git clone -q "$SOURCE_REPO" /clone \
    && cd /clone && git checkout -q "$SOURCE_COMMIT" \
    && test "$(git rev-parse HEAD^{tree})" = "$SOURCE_TREE" \
    && mkdir -p /src && cp /clone/lockchart_to_cnf.py /clone/README.md /clone/LICENSE /src/

FROM python:3.12.7-slim-bookworm
RUN pip install --no-cache-dir matplotlib==3.9.2 numpy==2.1.3
COPY --from=fetch /src /src
COPY lockchart-gen.sh /usr/local/bin/lockchart-gen
RUN chmod +x /usr/local/bin/lockchart-gen
ENV PYTHONHASHSEED=0 MPLBACKEND=Agg
WORKDIR /data
ENTRYPOINT ["/usr/local/bin/lockchart-gen"]
