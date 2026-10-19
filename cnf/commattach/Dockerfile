# Community Attachment: random k-CNF with a community structure, that is with
# modularity Q (Jesus Giraldez-Cru and Jordi Levy, IJCAI 2015).  The repository
# declares no licence, so this recipe is published but the image is not.
FROM debian:bookworm-slim AS fetch
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates git \
    && rm -rf /var/lib/apt/lists/*
ARG SOURCE_REPO=https://github.com/jgirald/communityAttachment.git
ARG SOURCE_COMMIT=3230fe8b7f3127f745d5c23fb494f7c1efae3642
ARG SOURCE_TREE=9f9623a8bb35245dc9a6d6c2b16c192457abb3e1
RUN git clone -q "$SOURCE_REPO" /src \
    && cd /src && git checkout -q "$SOURCE_COMMIT" \
    && test "$(git rev-parse HEAD^{tree})" = "$SOURCE_TREE" \
    && rm -rf /src/.git

FROM debian:bookworm-slim AS build
RUN apt-get update && apt-get install -y --no-install-recommends g++ make \
    && rm -rf /var/lib/apt/lists/*
COPY --from=fetch /src /src
WORKDIR /src
RUN make

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends libstdc++6 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=build /src/commAttach /src/random /usr/local/bin/
COPY --from=fetch /src /usr/local/share/communityAttachment
WORKDIR /data
ENTRYPOINT ["/usr/local/bin/commAttach"]
