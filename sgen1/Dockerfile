# sgen1, Ivor Spence, SAT Competition 2009: small, hard crafted instances.
# Built the way its page says ("gcc -o sgen1 sgen1.c -lm") on Debian lenny,
# the Debian release of 2009.  sgen1 carries its own linear congruential
# generator, so its output does not depend on the C library.
FROM debian:bookworm-slim AS fetch
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*
ARG SOURCE_URL=https://www.eeecs.qub.ac.uk/~I.Spence/sgen/sgen1.c
ARG SOURCE_SHA256=922b32758ad77724e8bfefe0b675ddf92ca86c46bd09c7d43972c9c25f70a2d0
RUN curl -fsSL -o /sgen1.c "$SOURCE_URL" && echo "$SOURCE_SHA256  /sgen1.c" | sha256sum -c -

FROM debian/eol:lenny AS build
RUN apt-get update && apt-get install -y --force-yes gcc libc6-dev
COPY --from=fetch /sgen1.c /src/sgen1.c
WORKDIR /src
RUN gcc -o sgen1 sgen1.c -lm

FROM debian/eol:lenny-slim
COPY --from=build /src/sgen1 /usr/local/bin/sgen1
COPY --from=fetch /sgen1.c /usr/local/share/sgen1/sgen1.c
WORKDIR /data
ENTRYPOINT ["/usr/local/bin/sgen1"]
