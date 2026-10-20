# Olivier Dubois' generator of hard contradictory 3-SAT instances, contributed to
# the Second DIMACS Implementation Challenge in 1993 and the source of the
# "dubois" family that every early benchmark suite carries.  Given a degree d it
# writes a formula with 3d variables and 8d clauses: 2d exclusive ors of three
# variables each, chained so that their parities cannot all hold.
#
# The sources are the files of the DIMACS contributed directory, kept byte for
# byte in a release of ours with their provenance, since that server could
# change or go.
FROM debian:bookworm-slim AS build
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl gcc libc6-dev \
    && rm -rf /var/lib/apt/lists/*
ARG ARCHIVE=https://github.com/sat-heritage/docker-images/releases/download/old-sources/dimacs-1993-dubois.tar.gz
ARG SHA256=943faa68d1f782c2d6109b4be2b38c65d090ecf4430024ba056d0c1a97fb7db1
RUN curl -sL -o /tmp/dubois.tar.gz "$ARCHIVE" \
    && echo "$SHA256  /tmp/dubois.tar.gz" | sha256sum -c - \
    && mkdir -p /src && tar xzf /tmp/dubois.tar.gz -C /src
# 1993 C: implicit int, no prototypes, malloc undeclared
RUN cd /src/dubois && gcc -std=gnu89 -w -O2 -o /usr/local/bin/gensathard gensathard.c \
    && gcc -std=gnu89 -w -O2 -o /usr/local/bin/gensat gensat.c

FROM debian:bookworm-slim
COPY --from=build /usr/local/bin/gensathard /usr/local/bin/gensat /usr/local/bin/
COPY --from=build /src/dubois/README /src/dubois/PROVENANCE.txt /src/dubois/INDEX /usr/share/doc/dubois/
COPY dubois-gen.sh /usr/local/bin/dubois-gen
RUN chmod +x /usr/local/bin/dubois-gen
WORKDIR /data
ENTRYPOINT ["/usr/local/bin/dubois-gen"]
