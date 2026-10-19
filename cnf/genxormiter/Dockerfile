# genxormiter (Armin Biere): the miter between two random parity circuits over
# a given number of shared inputs.  The DIMACS encoding of the inputs and the
# order of the XOR gates are randomised from the seed, so a seed must always be
# given: without one the generator seeds itself from the clock.
FROM debian:bookworm-slim AS fetch
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates git \
    && rm -rf /var/lib/apt/lists/*
ARG SOURCE_REPO=https://github.com/arminbiere/genxormiter.git
ARG SOURCE_COMMIT=bc0c9600387a7d8d6b70a84ee17194601092ea70
ARG SOURCE_TREE=1362e07edbbbfb61db572735efdb91d91094bc16
RUN git clone -q "$SOURCE_REPO" /src \
    && cd /src && git checkout -q "$SOURCE_COMMIT" \
    && test "$(git rev-parse HEAD^{tree})" = "$SOURCE_TREE" \
    && rm -rf /src/.git

FROM debian:bookworm-slim AS build
RUN apt-get update && apt-get install -y --no-install-recommends gcc libc6-dev make \
    && rm -rf /var/lib/apt/lists/*
COPY --from=fetch /src /src
WORKDIR /src
RUN make

FROM debian:bookworm-slim
COPY --from=build /src/genxormiter /usr/local/bin/genxormiter
COPY --from=fetch /src /usr/local/share/genxormiter
WORKDIR /data
ENTRYPOINT ["/usr/local/bin/genxormiter"]
