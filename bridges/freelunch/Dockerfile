# freeLunch (Tomas Balyo and Vojtech Bardiovsky): SAT encodings of planning
# problems.  It reads a planning task in the SAS+ format, the one Fast Downward
# produces from PDDL, and writes the CNF of "is there a plan of this length",
# under one of its encodings.  The length is the parameter that makes the family
# scale, exactly as the depth does for a bounded model checking unrolling.
FROM debian:bookworm-slim AS fetch
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates git \
    && rm -rf /var/lib/apt/lists/*
ARG SOURCE_REPO=https://github.com/biotomas/freelunch.git
ARG SOURCE_COMMIT=4f2c89ac3af95408baae4724028ed9d533bb3524
ARG SOURCE_TREE=3f08fc32c58205df94eceaa52c8c6ecd4e15af2f
RUN git clone -q "$SOURCE_REPO" /src \
    && cd /src && git checkout -q "$SOURCE_COMMIT" \
    && test "$(git rev-parse HEAD^{tree})" = "$SOURCE_TREE" && rm -rf .git

# Fast Downward's translator turns PDDL into the SAS+ format freeLunch reads.
# Only the translator is needed, and it is pure Python: nothing to build.
FROM debian:bookworm-slim AS downward
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates git \
    && rm -rf /var/lib/apt/lists/*
ARG DOWNWARD_REPO=https://github.com/aibasel/downward.git
ARG DOWNWARD_COMMIT=487e33cd68c8d5ed1a766ac1efb4cc57f37dcf6f
ARG DOWNWARD_TREE=80c078014cc1f9ab9a864c1eef5962cf03b9b145
RUN git clone -q "$DOWNWARD_REPO" /downward \
    && cd /downward && git checkout -q "$DOWNWARD_COMMIT" \
    && test "$(git rev-parse HEAD^{tree})" = "$DOWNWARD_TREE" && rm -rf .git

FROM debian:bookworm-slim AS build
RUN apt-get update && apt-get install -y --no-install-recommends default-jdk-headless ant \
    && rm -rf /var/lib/apt/lists/*
COPY --from=fetch /src /src
WORKDIR /src
RUN ant build && mkdir -p /dist && cp -a bin /dist/classes

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends default-jre-headless python3 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=downward /downward/src/translate /opt/downward/translate
COPY --from=build /dist/classes /opt/freelunch/classes
# the planning tasks the author distributes with his encoder, which are the ones
# behind the planning family of the competitions
COPY --from=fetch /src/testfiles /opt/freelunch/testfiles
COPY freelunch-bridge.sh /usr/local/bin/freelunch-bridge
RUN chmod +x /usr/local/bin/freelunch-bridge
WORKDIR /data
ENTRYPOINT ["/usr/local/bin/freelunch-bridge"]
