# Oddball: find the wrongly weighted ball among N with W weighings
# (Andrew Mihal, SAT Competition 2025).  The repository declares no licence,
# so this recipe is published but the image is not: build it yourself.
FROM debian:bookworm-slim AS fetch
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates git \
    && rm -rf /var/lib/apt/lists/*
ARG SOURCE_REPO=https://github.com/acmihal/oddball.git
ARG SOURCE_COMMIT=e1c977c6daedfa295caf911c6b08f2b516e782c4
ARG SOURCE_TREE=227f5e953c1cb858d91e8191e2fef9db71e97792
RUN git clone -q "$SOURCE_REPO" /src \
    && cd /src && git checkout -q "$SOURCE_COMMIT" \
    && test "$(git rev-parse HEAD^{tree})" = "$SOURCE_TREE" \
    && rm -rf /src/.git

FROM python:3.12.7-slim-bookworm
ARG Z3_VERSION=4.14.1.0
RUN pip install --no-cache-dir "z3-solver==${Z3_VERSION}"
COPY --from=fetch /src /src
RUN pip install --no-cache-dir -e /src
COPY oddball-gen.sh /usr/local/bin/oddball-gen
RUN chmod +x /usr/local/bin/oddball-gen
ENV PYTHONHASHSEED=0
WORKDIR /data
ENTRYPOINT ["/usr/local/bin/oddball-gen"]
